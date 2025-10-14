from flask_socketio import join_room, leave_room, emit
from flask import request
import threading
import time
import random

from Model.scoring_system import ScoringSystem
from Model.round_record import RoundRecord

def register_socket_events(socketio, game_manager):
    """Register SocketIO event handlers"""

    # --- Helper functions used across handlers ---
    def proceed_to_selection_and_td(room_code):
        """
        Decide whether to run a minigame or a normal selection for the given room,
        start the corresponding phase, and schedule the subsequent truth/dare.
        This function is safe to call from any thread.
        """
        room = game_manager.get_room(room_code)
        if not room or len(room.players) == 0:
            return

        try:
            chance_percent = float(room.settings.get('minigame_chance', 20))
        except Exception:
            chance_percent = 20.0

        if random.random() < (chance_percent / 100.0) and len(room.players) >= 2:
            # Start minigame (staring contest) between two random players
            competitors = random.sample(room.players, 2)
            comp_names = [competitors[0].name, competitors[1].name]
            minigame_duration = int(room.settings.get('minigame_duration', 15))
            room.game_state.start_minigame(competitors=comp_names, duration=minigame_duration)

            socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

            # Start a monitor thread to resolve the minigame (either by majority or timeout)
            t = threading.Thread(target=minigame_monitor, args=(room_code,))
            t.daemon = True
            t.start()
            return
        else:
            # Normal selection: pick a random player
            selected_player = random.choice(room.players)
            room.game_state.set_selected_player(selected_player.name)

            selection_duration = int(room.settings.get('selection_duration', 10))
            room.game_state.start_selection(duration=selection_duration)

            socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

            # After selection duration, start truth/dare flow
            def delayed_start_td():
                time.sleep(selection_duration)
                start_truth_dare_flow(room_code)

            t = threading.Thread(target=delayed_start_td)
            t.daemon = True
            t.start()

    def start_truth_dare_flow(room_code):
        """
        After selection phase completes, pick/assign the truth/dare item,
        start the truth/dare phase, and spawn a monitor to finish the round.
        """
        room = game_manager.get_room(room_code)
        if not room:
            return

        # If no choice was made, randomize
        if room.game_state.selected_choice is None:
            room.game_state.set_selected_choice(random.choice(['truth', 'dare']))

        # Get the selected player
        selected_player = room.get_player_by_name(room.game_state.selected_player)
        if selected_player:
            choice = room.game_state.selected_choice
            if choice == 'truth':
                truths = selected_player.truth_dare_list.truths
                if truths:
                    selected_item = random.choice(truths)
                    selected_player.truth_dare_list.truths.remove(selected_item)
                    room.game_state.set_current_truth_dare(selected_item.to_dict())
            else:  # dare
                dares = selected_player.truth_dare_list.dares
                if dares:
                    selected_item = random.choice(dares)
                    selected_player.truth_dare_list.dares.remove(selected_item)
                    room.game_state.set_current_truth_dare(selected_item.to_dict())

        # Start truth/dare phase
        td_duration = int(room.settings.get('truth_dare_duration', 60))
        room.game_state.start_truth_dare(duration=td_duration)
        socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

        # Spawn monitor thread for end-of-truth/dare
        def end_truth_dare_phase():
            while True:
                time.sleep(0.5)
                room_check = game_manager.get_room(room_code)
                if not room_check:
                    break
                if room_check.game_state.is_phase_complete():
                    # Award points for performing
                    performer = room_check.get_player_by_name(room_check.game_state.selected_player)
                    if performer:
                        ScoringSystem.award_perform_points(performer)

                    # Award points to submitter if custom truth/dare
                    if room_check.game_state.current_truth_dare:
                        submitted_by = room_check.game_state.current_truth_dare.get('submitted_by')
                        if submitted_by:
                            submitter = room_check.get_player_by_name(submitted_by)
                            if submitter:
                                ScoringSystem.award_submission_performed_points(submitter)

                    # Record round history
                    if room_check.game_state.current_truth_dare:
                        round_record = RoundRecord(
                            round_number=room_check.game_state.current_round,
                            selected_player_name=room_check.game_state.selected_player,
                            truth_dare_text=room_check.game_state.current_truth_dare['text'],
                            truth_dare_type=room_check.game_state.current_truth_dare.get('type', room_check.game_state.selected_choice),
                            submitted_by=room_check.game_state.current_truth_dare.get('submitted_by')
                        )
                        room_check.add_round_record(round_record)

                    # Check if game should end
                    if room_check.game_state.should_end_game():
                        room_check.game_state.start_end_game()

                        # Broadcast end game state with statistics
                        end_game_data = {
                            'phase': 'end_game',
                            'round_history': room_check.get_round_history(),
                            'top_players': room_check.get_top_players(5),
                            'all_players': [{'name': p.name, 'score': p.score} for p in room_check.players]
                        }
                        socketio.emit('game_state_update', end_game_data, room=room_code, namespace='/')
                    else:
                        # Continue to next round: start preparation
                        prep_duration = int(room_check.settings.get('preparation_duration', 30))
                        room_check.game_state.start_preparation(duration=prep_duration)

                        # Reset player submission counters
                        room_check.reset_player_round_submissions()

                        socketio.emit('game_state_update', room_check.game_state.to_dict(), room=room_code, namespace='/')

                        # Schedule next selection after the preparation period
                        def schedule_next():
                            time.sleep(0.1)
                            time.sleep(prep_duration)
                            proceed_to_selection_and_td(room_code)
                        t_next = threading.Thread(target=schedule_next)
                        t_next.daemon = True
                        t_next.start()
                    break

        t = threading.Thread(target=end_truth_dare_phase)
        t.daemon = True
        t.start()

    def minigame_monitor(room_code):
        """
        Monitor the minigame voting. Resolve when a competitor reaches required majority
        or when the minigame timer expires.
        """
        while True:
            time.sleep(0.5)
            room_inner = game_manager.get_room(room_code)
            if not room_inner:
                return
            gs = room_inner.game_state
            # compute voters (other players excluding the two competitors)
            other_players_count = max(0, len(room_inner.players) - 2)
            # required majority (more than half of other players) — if no other players, require 1
            required_votes = (other_players_count // 2) + 1 if other_players_count > 0 else 1
            vote_counts = gs.get_minigame_vote_counts()
            # check if any competitor reached required votes
            winner = None
            for comp, cnt in vote_counts.items():
                if cnt >= required_votes:
                    winner = comp
                    break
            if winner is not None:
                # loser is the other competitor
                loser = [c for c in gs.minigame_competitors if c != winner]
                loser_name = loser[0] if loser else None
                # award minigame points to both participants
                for pname in gs.minigame_competitors:
                    p = room_inner.get_player_by_name(pname)
                    if p:
                        ScoringSystem.award_minigame_points(p)
                # set selected player to loser
                if loser_name:
                    gs.set_selected_player(loser_name)
                # Clear minigame and transition to selection
                gs.clear_minigame()
                selection_duration = int(room_inner.settings.get('selection_duration', 10))
                gs.start_selection(duration=selection_duration)
                socketio.emit('game_state_update', gs.to_dict(), room=room_code, namespace='/')

                # After the selection duration, proceed to truth/dare
                def delayed_td_after_selection():
                    time.sleep(selection_duration)
                    start_truth_dare_flow(room_code)
                t2 = threading.Thread(target=delayed_td_after_selection)
                t2.daemon = True
                t2.start()
                return

            # If minigame timed out without majority, resolve by votes (fewest wins -> loser) or random
            if gs.is_phase_complete():
                if other_players_count == 0:
                    # no voters -> pick loser randomly
                    loser_name = random.choice(gs.minigame_competitors) if gs.minigame_competitors else None
                else:
                    counts = gs.get_minigame_vote_counts()
                    if len(gs.minigame_competitors) >= 2:
                        a, b = gs.minigame_competitors[:2]
                        ca = counts.get(a, 0)
                        cb = counts.get(b, 0)
                        if ca == cb:
                            loser_name = random.choice(gs.minigame_competitors)
                        else:
                            loser_name = a if ca < cb else b
                    else:
                        loser_name = gs.minigame_competitors[0] if gs.minigame_competitors else None

                # award minigame points
                for pname in gs.minigame_competitors:
                    p = room_inner.get_player_by_name(pname)
                    if p:
                        ScoringSystem.award_minigame_points(p)
                # set selected player to loser
                if loser_name:
                    gs.set_selected_player(loser_name)
                # clear minigame and transition to selection
                gs.clear_minigame()
                selection_duration = int(room_inner.settings.get('selection_duration', 10))
                gs.start_selection(duration=selection_duration)
                socketio.emit('game_state_update', gs.to_dict(), room=room_code, namespace='/')

                def delayed_td_after_selection_timeout():
                    time.sleep(selection_duration)
                    start_truth_dare_flow(room_code)
                t3 = threading.Thread(target=delayed_td_after_selection_timeout)
                t3.daemon = True
                t3.start()
                return

    # --- Socket event handlers ---
    @socketio.on('join')
    def on_join(data):
        room_code = data.get('room')
        name = data.get('name', 'Anonymous')

        if not room_code:
            return

        join_room(room_code)

        # Add player to room
        room = game_manager.add_player_to_room(room_code, request.sid, name)

        # Broadcast updated state
        _broadcast_room_state(room_code, room)

    @socketio.on('leave')
    def on_leave(data):
        room_code = data.get('room')

        if not room_code:
            return

        # Remove player
        room = game_manager.remove_player_from_room(room_code, request.sid)
        leave_room(room_code)

        # Broadcast updated state if room still exists
        if room:
            _broadcast_room_state(room_code, room)

        # Notify the leaving player
        emit('left_room', {}, to=request.sid)

    @socketio.on('destroy_room')
    def on_destroy_room(data):
        room_code = data.get('room')

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can destroy
        if not room.is_host(request.sid):
            return

        # Notify all players
        emit('room_destroyed', {}, room=room_code)

        # Delete room
        game_manager.delete_room(room_code)

    @socketio.on('update_settings')
    def on_update_settings(data):
        room_code = data.get('room')
        settings = data.get('settings', {})

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can update settings
        if not room.is_host(request.sid):
            return

        # Update settings
        room.update_settings(settings)

        # Broadcast updated settings to all players
        emit('settings_updated', {'settings': room.settings}, room=room_code)

    @socketio.on('get_settings')
    def on_get_settings(data):
        room_code = data.get('room')

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Send current settings to requester
        emit('settings_updated', {'settings': room.settings}, to=request.sid)

    @socketio.on('start_game')
    def on_start_game(data):
        room_code = data.get('room')

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can start
        if not room.is_host(request.sid):
            return

        # Start countdown with configurable duration
        countdown_duration = int(room.settings.get('countdown_duration', 10))
        room.game_state.start_countdown(duration=countdown_duration)

        # Broadcast game state
        emit('game_state_update', room.game_state.to_dict(), room=room_code)

        # Schedule preparation phase after countdown
        def start_preparation():
            time.sleep(countdown_duration)
            room = game_manager.get_room(room_code)
            if room:
                prep_duration = int(room.settings.get('preparation_duration', 30))
                room.game_state.start_preparation(duration=prep_duration)

                # Reset player submission counters for new round
                room.reset_player_round_submissions()

                socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

                # Schedule selection/minigame after preparation
                def delayed_selection():
                    # small sleep already happened above; now wait prep duration
                    time.sleep(prep_duration)
                    proceed_to_selection_and_td(room_code)

                t = threading.Thread(target=delayed_selection)
                t.daemon = True
                t.start()

        thread = threading.Thread(target=start_preparation)
        thread.daemon = True
        thread.start()

    @socketio.on('minigame_vote')
    def on_minigame_vote(data):
        """
        data: { room: <code>, competitor: <name> }
        Only non-competing players can vote. A voter can change their vote.
        If a competitor reaches majority (>50% of voters), the other competitor loses
        and becomes the selected player for the next phase.
        """
        room_code = data.get('room')
        competitor = data.get('competitor')

        if not room_code or not competitor:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only during minigame
        if room.game_state.phase != room.game_state.PHASE_MINIGAME:
            return

        # Voter must be a real player and not one of the competitors
        voter = room.get_player_by_sid(request.sid)
        if not voter:
            return

        if voter.name in room.game_state.minigame_competitors:
            return

        # record vote
        room.game_state.add_minigame_vote(request.sid, competitor)

        # Broadcast update to room
        emit('game_state_update', room.game_state.to_dict(), room=room_code)

        # Check for immediate resolution (majority)
        other_players_count = max(0, len(room.players) - 2)
        if other_players_count == 0:
            required_votes = 1
        else:
            required_votes = (other_players_count // 2) + 1

        counts = room.game_state.get_minigame_vote_counts()
        for comp_name, cnt in counts.items():
            if cnt >= required_votes:
                # we have a winner; loser is the other
                loser_list = [c for c in room.game_state.minigame_competitors if c != comp_name]
                loser_name = loser_list[0] if loser_list else None
                # award minigame points
                for pname in room.game_state.minigame_competitors:
                    p = room.get_player_by_name(pname)
                    if p:
                        ScoringSystem.award_minigame_points(p)
                # set selected player to loser
                if loser_name:
                    room.game_state.set_selected_player(loser_name)
                # clear minigame and transition to selection and then truth/dare
                room.game_state.clear_minigame()
                selection_duration = int(room.settings.get('selection_duration', 10))
                room.game_state.start_selection(duration=selection_duration)
                emit('game_state_update', room.game_state.to_dict(), room=room_code)

                # schedule the same selection->truth/dare flow
                def delayed_td():
                    time.sleep(selection_duration)
                    start_truth_dare_flow(room_code)
                t = threading.Thread(target=delayed_td)
                t.daemon = True
                t.start()
                return

    @socketio.on('select_truth_dare')
    def on_select_truth_dare(data):
        room_code = data.get('room')
        choice = data.get('choice')  # 'truth' or 'dare'

        if not room_code or not choice:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only during selection phase
        if room.game_state.phase != 'selection':
            return

        # Only the selected player can choose
        player = room.get_player_by_sid(request.sid)
        if not player or player.name != room.game_state.selected_player:
            return

        # Set the choice
        room.game_state.set_selected_choice(choice)

        # Broadcast updated state
        emit('game_state_update', room.game_state.to_dict(), room=room_code)

    @socketio.on('vote_skip')
    def on_vote_skip(data):
        room_code = data.get('room')

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only during truth_dare phase
        if room.game_state.phase != 'truth_dare':
            return

        # Only non-selected players can vote
        player = room.get_player_by_sid(request.sid)
        if not player or player.name == room.game_state.selected_player:
            return

        # Add vote
        room.game_state.add_skip_vote(request.sid)

        # Check if at least half of other players voted
        other_players_count = len(room.players) - 1  # Exclude selected player
        required_votes = (other_players_count + 1) // 2  # At least half (ceiling division)

        if room.game_state.get_skip_vote_count() >= required_votes:
            # Reduce timer to configured skip duration
            skip_duration = int(room.settings.get('skip_duration', 5))
            room.game_state.reduce_timer(skip_duration)

        # Broadcast updated state
        emit('game_state_update', room.game_state.to_dict(), room=room_code)

    @socketio.on('submit_truth_dare')
    def on_submit_truth_dare(data):
        room_code = data.get('room')
        text = data.get('text', '').strip()
        item_type = data.get('type')  # 'truth' or 'dare'
        target_names = data.get('targets', [])  # list of player names

        if not room_code or not text or not item_type or not target_names:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only allow during preparation phase
        if room.game_state.phase != 'preparation':
            return

        # Get submitter
        submitter = room.get_player_by_sid(request.sid)
        if not submitter:
            return

        # Check if player can submit more
        if not submitter.can_submit_more():
            emit('submission_error', {
                'message': f'You can only submit {ScoringSystem.MAX_SUBMISSIONS_PER_ROUND} truths/dares per round'
            }, to=request.sid)
            return

        # Add to each target player's list with submitter info
        successfully_added = []
        for target_name in target_names:
            target_player = room.get_player_by_name(target_name)
            if target_player:
                if item_type == 'truth':
                    target_player.truth_dare_list.add_truth(text, submitted_by=submitter.name)
                elif item_type == 'dare':
                    target_player.truth_dare_list.add_dare(text, submitted_by=submitter.name)
                successfully_added.append(target_name)

        # Increment submission counter and award points
        if successfully_added:
            submitter.increment_submissions()
            ScoringSystem.award_submission_points(submitter)

            # Notify success
            emit('submission_success', {
                'text': text,
                'type': item_type,
                'targets': successfully_added
            }, to=request.sid)

    @socketio.on('restart_game')
    def on_restart_game(data):
        room_code = data.get('room')

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can restart
        if not room.is_host(request.sid):
            return

        # Reset room for new game
        room.reset_for_new_game()

        # Start countdown immediately
        countdown_duration = int(room.settings.get('countdown_duration', 10))
        room.game_state.start_countdown(duration=countdown_duration)

        # Broadcast reset state
        emit('game_state_update', room.game_state.to_dict(), room=room_code)

        # Schedule preparation phase after countdown
        def start_preparation():
            time.sleep(countdown_duration)
            room = game_manager.get_room(room_code)
            if room:
                prep_duration = int(room.settings.get('preparation_duration', 30))
                room.game_state.start_preparation(duration=prep_duration)

                # Reset player submission counters for new round
                room.reset_player_round_submissions()

                socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

                # Schedule selection/minigame after preparation
                def delayed_selection():
                    time.sleep(prep_duration)
                    proceed_to_selection_and_td(room_code)

                t = threading.Thread(target=delayed_selection)
                t.daemon = True
                t.start()

        thread = threading.Thread(target=start_preparation)
        thread.daemon = True
        thread.start()

    @socketio.on('disconnect')
    def on_disconnect():
        # Remove player from all rooms
        updated_rooms = game_manager.remove_player_from_all_rooms(request.sid)

        # Broadcast updated state to affected rooms
        for room_code in updated_rooms:
            room = game_manager.get_room(room_code)
            if room:
                _broadcast_room_state(room_code, room)

    def _broadcast_room_state(room_code, room):
        """Helper to broadcast room state to all players"""
        if not room:
            return

        emit('player_list', {
            'players': room.get_player_names(),
            'host_sid': room.host_sid
        }, room=room_code)
