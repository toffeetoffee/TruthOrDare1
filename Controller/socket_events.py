from flask_socketio import join_room, leave_room, emit
from flask import request
import threading
import time
import random
from Model.scoring_system import ScoringSystem
from Model.round_record import RoundRecord

def register_socket_events(socketio, game_manager):
    """Register SocketIO event handlers"""
    
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
                
                # Schedule selection phase after preparation
                def start_selection():
                    time.sleep(prep_duration)
                    room = game_manager.get_room(room_code)
                    if room and len(room.players) > 0:
                        # Randomly select a player
                        selected_player = random.choice(room.players)
                        room.game_state.set_selected_player(selected_player.name)
                        
                        selection_duration = room.settings['selection_duration']
                        room.game_state.start_selection(duration=selection_duration)
                        
                        socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
                        
                        # Schedule truth/dare phase after selection
                        def start_truth_dare_phase():
                            time.sleep(selection_duration)
                            room = game_manager.get_room(room_code)
                            if room:
                                # If no choice was made, randomize
                                if room.game_state.selected_choice is None:
                                    room.game_state.set_selected_choice(random.choice(['truth', 'dare']))
                                
                                # Get the selected player
                                selected_player = room.get_player_by_name(room.game_state.selected_player)
                                if selected_player:
                                    # Pick random truth or dare based on choice
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
                                
                                # Start truth/dare phase with configurable duration
                                td_duration = room.settings['truth_dare_duration']
                                room.game_state.start_truth_dare(duration=td_duration)
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
                                                
                                                # Continue the loop
                                                start_selection()
                                            break
                                
                                td_end_thread = threading.Thread(target=end_truth_dare_phase)
                                td_end_thread.daemon = True
                                td_end_thread.start()
                        
                        td_thread = threading.Thread(target=start_truth_dare_phase)
                        td_thread.daemon = True
                        td_thread.start()
                
                selection_thread = threading.Thread(target=start_selection)
                selection_thread.daemon = True
                selection_thread.start()
        
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
        
        # Start game loop again
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