# socket_events.py
from flask_socketio import join_room, leave_room, emit
from flask import request
import threading
import time

# Import helper modules (placed next to this file)
import selection_helpers
import minigame_helpers

from Model.scoring_system import ScoringSystem

def register_socket_events(socketio, game_manager):
    """Register SocketIO event handlers (delegates heavy logic to helpers)."""

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

    # Default lists management (kept here to avoid scattering too many small handlers)
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

            # CRITICAL: Update all existing players' truth/dare lists with the new defaults
            for player in room.players:
                player.truth_dare_list.set_custom_defaults(
                    room.default_truths.copy(),
                    room.default_dares.copy()
                )

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
                    selection_helpers.start_selection_or_minigame(socketio, game_manager, room_code)

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

        # delegate to minigame helper which contains the full decision logic and emits
        minigame_helpers.handle_minigame_vote(socketio, game_manager, room_code, voted_player, request)

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

    @socketio.on('check_ai_status')
    def on_check_ai_status(data):
        """Check AI generator status and run a test (for debugging)"""
        room_code = data.get('room')

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can check AI status
        if not room.is_host(request.sid):
            return

        # Get AI generator status
        from Model.ai_generator import get_ai_generator
        ai_gen = get_ai_generator()
        status = ai_gen.get_status()

        # Run test if requested
        test_result = None
        if data.get('run_test', False):
            test_result = ai_gen.test_generation()

        # Send status back to requester
        emit('ai_status_result', {
            'status': status,
            'test_result': test_result,
            'room_ai_enabled': room.settings.get('ai_generation_enabled', False)
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
