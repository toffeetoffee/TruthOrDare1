from flask_socketio import join_room, leave_room, emit
from flask import request
import threading
import time
import random

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
                socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
                
                # Schedule selection phase after preparation
                def start_selection():
                    time.sleep(30)
                    room = game_manager.get_room(room_code)
                    if room and len(room.players) > 0:
                        # Randomly select a player
                        selected_player = random.choice(room.players)
                        room.game_state.set_selected_player(selected_player.name)
                        room.game_state.start_selection(duration=10)
                        
                        socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')
                
                selection_thread = threading.Thread(target=start_selection)
                selection_thread.daemon = True
                selection_thread.start()
        
        thread = threading.Thread(target=start_preparation)
        thread.daemon = True
        thread.start()
    
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
        
        # Add to each target player's list
        successfully_added = []
        for target_name in target_names:
            target_player = room.get_player_by_name(target_name)
            if target_player:
                if item_type == 'truth':
                    target_player.truth_dare_list.add_truth(text)
                elif item_type == 'dare':
                    target_player.truth_dare_list.add_dare(text)
                successfully_added.append(target_name)
        
        # Notify success
        if successfully_added:
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