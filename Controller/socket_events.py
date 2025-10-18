from flask_socketio import join_room, leave_room, emit
from flask import request
import threading
import time
import random
from Model.scoring_system import ScoringSystem
from Model.round_record import RoundRecord
from Model.minigame import StaringContest

def register_socket_events(socketio, game_manager):
    """Register SocketIO event handlers"""
    
    def start_selection_or_minigame(room_code):
        """Helper to decide between minigame or normal selection"""
        room = game_manager.get_room(room_code)
        if not room or len(room.players) < 2:
            return
        
        # Check for minigame chance
        minigame_chance = room.settings.get('minigame_chance', 20) / 100.0
        trigger_minigame = random.random() < minigame_chance
        
        if trigger_minigame and len(room.players) >= 2:
            # Start minigame (staring contest)
            minigame = StaringContest()
            
            # Randomly select 2 players
            participants = random.sample(room.players, 2)
            for participant in participants:
                minigame.add_participant(participant)
            
            # Set total voters (all players except the 2 participants)
            total_voters = len(room.players) - 2
            minigame.set_total_voters(total_voters)
            
            # Award participation points
            for participant in participants:
                ScoringSystem.award_minigame_participate_points(participant)
            
            # Set minigame in game state
            room.game_state.set_minigame(minigame)
            room.game_state.start_minigame()
            
            socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
            
            # Minigame continues until voting completes (handled by on_minigame_vote)
        else:
            # No minigame - proceed to normal selection
            selected_player = random.choice(room.players)
            room.game_state.set_selected_player(selected_player.name)
            
            selection_duration = room.settings['selection_duration']
            room.game_state.start_selection(duration=selection_duration)
            
            socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
            
            # Schedule truth/dare phase after selection
            def start_truth_dare_phase():
                time.sleep(selection_duration)
                start_truth_dare_phase_handler(room_code)
            
            td_thread = threading.Thread(target=start_truth_dare_phase)
            td_thread.daemon = True
            td_thread.start()
    
    def start_truth_dare_phase_handler(room_code):
        """Helper to start truth/dare phase"""
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # If no choice was made, randomize
        if room.game_state.selected_choice is None:
            room.game_state.set_selected_choice(random.choice(['truth', 'dare']))
        
        # Get the selected player
        selected_player = room.get_player_by_name(room.game_state.selected_player)
        list_was_empty = False
        
        if selected_player:
            # Pick random truth or dare based on choice
            choice = room.game_state.selected_choice
            if choice == 'truth':
                truths = selected_player.truth_dare_list.truths
                if truths:
                    selected_item = random.choice(truths)
                    selected_player.truth_dare_list.truths.remove(selected_item)
                    room.game_state.set_current_truth_dare(selected_item.to_dict())
                else:
                    # List is empty!
                    list_was_empty = True
                    room.game_state.list_empty = True
                    room.game_state.set_current_truth_dare({
                        'text': f'{selected_player.name} has no more truths available!',
                        'type': 'truth',
                        'is_default': False,
                        'submitted_by': None
                    })
            else:  # dare
                dares = selected_player.truth_dare_list.dares
                if dares:
                    selected_item = random.choice(dares)
                    selected_player.truth_dare_list.dares.remove(selected_item)
                    room.game_state.set_current_truth_dare(selected_item.to_dict())
                else:
                    # List is empty!
                    list_was_empty = True
                    room.game_state.list_empty = True
                    room.game_state.set_current_truth_dare({
                        'text': f'{selected_player.name} has no more dares available!',
                        'type': 'dare',
                        'is_default': False,
                        'submitted_by': None
                    })
        
        # Start truth/dare phase with configurable duration
        td_duration = room.settings['truth_dare_duration']
        room.game_state.start_truth_dare(duration=td_duration)
        
        # If list was empty, automatically activate skip
        if list_was_empty:
            room.game_state.list_empty = True
            room.game_state.activate_skip()
            skip_duration = room.settings['skip_duration']
            room.game_state.reduce_timer(skip_duration)
        
        socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
        
        # Schedule end of truth/dare phase
        def end_truth_dare_phase():
            # Check timer dynamically
            while True:
                time.sleep(0.5)
                room = game_manager.get_room(room_code)
                if not room:
                    break
                
                # Check if phase is complete
                if room.game_state.is_phase_complete():
                    # Award points for performing
                    performer = room.get_player_by_name(room.game_state.selected_player)
                    if performer:
                        ScoringSystem.award_perform_points(performer)
                    
                    # Award points to submitter if custom truth/dare
                    if room.game_state.current_truth_dare:
                        submitted_by = room.game_state.current_truth_dare.get('submitted_by')
                        if submitted_by:
                            submitter = room.get_player_by_name(submitted_by)
                            if submitter:
                                ScoringSystem.award_submission_performed_points(submitter)
                    
                    # Record round history
                    if room.game_state.current_truth_dare:
                        round_record = RoundRecord(
                            round_number=room.game_state.current_round,
                            selected_player_name=room.game_state.selected_player,
                            truth_dare_text=room.game_state.current_truth_dare['text'],
                            truth_dare_type=room.game_state.current_truth_dare.get('type', room.game_state.selected_choice),
                            submitted_by=room.game_state.current_truth_dare.get('submitted_by')
                        )
                        room.add_round_record(round_record)
                    
                    # Check if game should end
                    if room.game_state.should_end_game():
                        room.game_state.start_end_game()
                        
                        # Broadcast end game state with statistics
                        end_game_data = {
                            'phase': 'end_game',
                            'round_history': room.get_round_history(),
                            'top_players': room.get_top_players(5),
                            'all_players': [{'name': p.name, 'score': p.score} for p in room.players]
                        }
                        socketio.emit('game_state_update', end_game_data, room=room_code, namespace='/')
                    else:
                        # Continue to next round
                        prep_duration = room.settings['preparation_duration']
                        room.game_state.start_preparation(duration=prep_duration)
                        
                        # Reset player submission counters
                        room.reset_player_round_submissions()
                        
                        socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
                        
                        # Continue the loop - start next round
                        def next_round():
                            time.sleep(prep_duration)
                            start_selection_or_minigame(room_code)
                        
                        next_round_thread = threading.Thread(target=next_round)
                        next_round_thread.daemon = True
                        next_round_thread.start()
                    break
        
        td_end_thread = threading.Thread(target=end_truth_dare_phase)
        td_end_thread.daemon = True
        td_end_thread.start()
    
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
    
    # Default lists management
    @socketio.on('get_default_lists')
    def on_get_default_lists(data):
        room_code = data.get('room')
        
        if not room_code:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Send current default lists to requester
        emit('default_lists_updated', {
            'truths': room.get_default_truths(),
            'dares': room.get_default_dares()
        }, to=request.sid)
    
    @socketio.on('add_default_truth')
    def on_add_default_truth(data):
        room_code = data.get('room')
        text = data.get('text', '').strip()
        
        if not room_code or not text:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Only host can modify defaults
        if not room.is_host(request.sid):
            return
        
        # Add the truth
        success = room.add_default_truth(text)
        
        if success:
            # Broadcast updated lists to all players
            emit('default_lists_updated', {
                'truths': room.get_default_truths(),
                'dares': room.get_default_dares()
            }, room=room_code)
    
    @socketio.on('add_default_dare')
    def on_add_default_dare(data):
        room_code = data.get('room')
        text = data.get('text', '').strip()
        
        if not room_code or not text:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Only host can modify defaults
        if not room.is_host(request.sid):
            return
        
        # Add the dare
        success = room.add_default_dare(text)
        
        if success:
            # Broadcast updated lists to all players
            emit('default_lists_updated', {
                'truths': room.get_default_truths(),
                'dares': room.get_default_dares()
            }, room=room_code)
    
    @socketio.on('edit_default_truth')
    def on_edit_default_truth(data):
        room_code = data.get('room')
        old_text = data.get('old_text', '').strip()
        new_text = data.get('new_text', '').strip()
        
        if not room_code or not old_text or not new_text:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Only host can modify defaults
        if not room.is_host(request.sid):
            return
        
        # Edit the truth
        success = room.edit_default_truth(old_text, new_text)
        
        if success:
            # Broadcast updated lists to all players
            emit('default_lists_updated', {
                'truths': room.get_default_truths(),
                'dares': room.get_default_dares()
            }, room=room_code)
    
    @socketio.on('edit_default_dare')
    def on_edit_default_dare(data):
        room_code = data.get('room')
        old_text = data.get('old_text', '').strip()
        new_text = data.get('new_text', '').strip()
        
        if not room_code or not old_text or not new_text:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Only host can modify defaults
        if not room.is_host(request.sid):
            return
        
        # Edit the dare
        success = room.edit_default_dare(old_text, new_text)
        
        if success:
            # Broadcast updated lists to all players
            emit('default_lists_updated', {
                'truths': room.get_default_truths(),
                'dares': room.get_default_dares()
            }, room=room_code)
    
    @socketio.on('remove_default_truths')
    def on_remove_default_truths(data):
        room_code = data.get('room')
        texts_to_remove = data.get('texts', [])
        
        if not room_code or not texts_to_remove:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Only host can modify defaults
        if not room.is_host(request.sid):
            return
        
        # Remove the truths
        room.remove_default_truths(texts_to_remove)
        
        # Broadcast updated lists to all players
        emit('default_lists_updated', {
            'truths': room.get_default_truths(),
            'dares': room.get_default_dares()
        }, room=room_code)
    
    @socketio.on('remove_default_dares')
    def on_remove_default_dares(data):
        room_code = data.get('room')
        texts_to_remove = data.get('texts', [])
        
        if not room_code or not texts_to_remove:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Only host can modify defaults
        if not room.is_host(request.sid):
            return
        
        # Remove the dares
        room.remove_default_dares(texts_to_remove)
        
        # Broadcast updated lists to all players
        emit('default_lists_updated', {
            'truths': room.get_default_truths(),
            'dares': room.get_default_dares()
        }, room=room_code)
    
    @socketio.on('load_preset_file')
    def on_load_preset_file(data):
        room_code = data.get('room')
        file_data = data.get('file_data')  # JSON string
        
        if not room_code or not file_data:
            emit('preset_error', {'message': 'Invalid file data'}, to=request.sid)
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            emit('preset_error', {'message': 'Room not found'}, to=request.sid)
            return
        
        # Only host can load presets
        if not room.is_host(request.sid):
            emit('preset_error', {'message': 'Only host can load presets'}, to=request.sid)
            return
        
        try:
            # Parse JSON
            import json
            preset = json.loads(file_data)
            
            # Validate structure
            if 'truths' not in preset or 'dares' not in preset:
                emit('preset_error', {'message': 'Invalid preset format: missing truths or dares'}, to=request.sid)
                return
            
            if not isinstance(preset['truths'], list) or not isinstance(preset['dares'], list):
                emit('preset_error', {'message': 'Invalid preset format: truths and dares must be arrays'}, to=request.sid)
                return
            
            # Validate all items are strings
            for truth in preset['truths']:
                if not isinstance(truth, str):
                    emit('preset_error', {'message': 'Invalid preset format: all truths must be strings'}, to=request.sid)
                    return
            
            for dare in preset['dares']:
                if not isinstance(dare, str):
                    emit('preset_error', {'message': 'Invalid preset format: all dares must be strings'}, to=request.sid)
                    return
            
            # Check for minimum requirements
            if len(preset['truths']) == 0 and len(preset['dares']) == 0:
                emit('preset_error', {'message': 'Preset must contain at least one truth or dare'}, to=request.sid)
                return
            
            # Replace BOTH defaults
            room.default_truths = [t.strip() for t in preset['truths'] if t.strip()]
            room.default_dares = [d.strip() for d in preset['dares'] if d.strip()]
            
            # Broadcast updated lists to all players
            emit('default_lists_updated', {
                'truths': room.get_default_truths(),
                'dares': room.get_default_dares()
            }, room=room_code)
            
            # Send success message
            emit('preset_loaded', {
                'message': f'Preset loaded successfully!\n{len(room.default_truths)} truths and {len(room.default_dares)} dares loaded.'
            }, to=request.sid)
            
        except json.JSONDecodeError:
            emit('preset_error', {'message': 'Invalid JSON format'}, to=request.sid)
        except Exception as e:
            emit('preset_error', {'message': f'Error loading preset: {str(e)}'}, to=request.sid)
    
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
        countdown_duration = room.settings['countdown_duration']
        room.game_state.start_countdown(duration=countdown_duration)
        
        # Broadcast game state
        emit('game_state_update', room.game_state.to_dict(), room=room_code)
        
        # Schedule preparation phase after countdown
        def start_preparation():
            time.sleep(countdown_duration)
            room = game_manager.get_room(room_code)
            if room:
                prep_duration = room.settings['preparation_duration']
                room.game_state.start_preparation(duration=prep_duration)
                
                # Reset player submission counters for new round
                room.reset_player_round_submissions()
                
                socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
                
                # Schedule selection or minigame after preparation
                def after_prep():
                    time.sleep(prep_duration)
                    start_selection_or_minigame(room_code)
                
                prep_thread = threading.Thread(target=after_prep)
                prep_thread.daemon = True
                prep_thread.start()
        
        thread = threading.Thread(target=start_preparation)
        thread.daemon = True
        thread.start()
    
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
        countdown_duration = room.settings['countdown_duration']
        room.game_state.start_countdown(duration=countdown_duration)
        
        # Broadcast reset state
        emit('game_state_update', room.game_state.to_dict(), room=room_code)
        
        # Trigger start_game logic
        on_start_game({'room': room_code})
    
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
    
    @socketio.on('minigame_vote')
    def on_minigame_vote(data):
        room_code = data.get('room')
        voted_player = data.get('voted_player')  # Name of player who blinked
        
        if not room_code or not voted_player:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Only during minigame phase
        if room.game_state.phase != 'minigame':
            return
        
        minigame = room.game_state.minigame
        if not minigame:
            return
        
        # Only non-participants can vote
        player = room.get_player_by_sid(request.sid)
        if not player:
            return
        
        participant_names = minigame.get_participant_names()
        if player.name in participant_names:
            return  # Participants can't vote
        
        # Check if player already voted
        if request.sid in minigame.votes:
            return  # Already voted
        
        # Add vote
        minigame.add_vote(request.sid, voted_player)
        
        # Check for immediate winner (one player reached at least half of total votes)
        loser = minigame.check_immediate_winner()
        
        if loser:
            # Someone reached the threshold - proceed immediately
            room.game_state.set_selected_player(loser.name)
            
            # Move to selection phase
            selection_duration = room.settings['selection_duration']
            room.game_state.start_selection(duration=selection_duration)
            
            socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
            
            # Schedule truth/dare phase
            def start_td():
                time.sleep(selection_duration)
                start_truth_dare_phase_handler(room_code)
            
            td_thread = threading.Thread(target=start_td)
            td_thread.daemon = True
            td_thread.start()
        elif minigame.check_all_voted():
            # All voters have voted - check for tie
            vote_counts = minigame.get_vote_counts()
            
            if len(vote_counts) == 2:
                counts = list(vote_counts.values())
                if counts[0] == counts[1]:
                    # It's a tie - randomly pick loser
                    loser = minigame.handle_tie()
                else:
                    # Someone has more votes
                    loser = minigame.determine_loser()
            else:
                # One player has all or most votes
                loser = minigame.determine_loser()
            
            if loser:
                # Set loser as selected player
                room.game_state.set_selected_player(loser.name)
                
                # Move to selection phase
                selection_duration = room.settings['selection_duration']
                room.game_state.start_selection(duration=selection_duration)
                
                socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
                
                # Schedule truth/dare phase
                def start_td():
                    time.sleep(selection_duration)
                    start_truth_dare_phase_handler(room_code)
                
                td_thread = threading.Thread(target=start_td)
                td_thread.daemon = True
                td_thread.start()
        else:
            # Just broadcast updated vote count
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
        
        # Can't vote if skip already activated
        if room.game_state.skip_activated:
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
            # Activate skip
            room.game_state.activate_skip()
            
            # Reduce timer to configured skip duration
            skip_duration = room.settings['skip_duration']
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