from flask_socketio import join_room, leave_room, emit
from flask import request
import threading
import time

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
        
        # Start countdown
        room.game_state.start_countdown(duration=10)
        
        # Broadcast game state
        emit('game_state_update', room.game_state.to_dict(), room=room_code)
        
        # Schedule preparation phase after countdown
        def start_preparation():
            time.sleep(10)
            room = game_manager.get_room(room_code)
            if room:
                room.game_state.start_preparation(duration=30)
                # Use socketio instance to emit from background thread
                socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
        
        thread = threading.Thread(target=start_preparation)
        thread.daemon = True
        thread.start()
    
    @socketio.on('submit_truth_dare')
    def on_submit_truth_dare(data):
        room_code = data.get('room')
        text = data.get('text', '').strip()
        item_type = data.get('type')  # 'truth' or 'dare'
        target_name = data.get('target')  # player name
        
        if not room_code or not text or not item_type or not target_name:
            return
        
        room = game_manager.get_room(room_code)
        if not room:
            return
        
        # Only allow during preparation phase
        if room.game_state.phase != 'preparation':
            return
        
        # Find target player
        target_player = room.get_player_by_name(target_name)
        if not target_player:
            return
        
        # Add to target player's list
        if item_type == 'truth':
            target_player.truth_dare_list.add_truth(text)
        elif item_type == 'dare':
            target_player.truth_dare_list.add_dare(text)
        
        # Notify success
        emit('submission_success', {
            'text': text,
            'type': item_type,
            'target': target_name
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