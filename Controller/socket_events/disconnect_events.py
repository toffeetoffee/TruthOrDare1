# Controller/socket_events/disconnect_events.py

from flask import request

from .helpers import _broadcast_room_state


def register_disconnect_events(socketio, game_manager):
    """Register disconnection handling events."""

    @socketio.on("disconnect")
    def on_disconnect():
        # Remove player from all rooms
        updated_rooms = game_manager.remove_player_from_all_rooms(request.sid)

        # Broadcast updated state to affected rooms
        for room_code in updated_rooms:
            room = game_manager.get_room(room_code)
            if room:
                _broadcast_room_state(room_code, room)
