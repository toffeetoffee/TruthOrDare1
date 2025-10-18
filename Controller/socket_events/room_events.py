"""
Socket event handlers for room management (join, leave, settings, etc.)
"""

from flask_socketio import join_room, leave_room, emit
from flask import request


def register_room_events(socketio, game_manager):
    """Register room-related socket events"""
    
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