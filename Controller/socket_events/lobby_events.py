# Controller/socket_events/lobby_events.py

from flask_socketio import join_room, leave_room, emit
from flask import request

from .helpers import _broadcast_room_state


def register_lobby_events(socketio, game_manager):
    """Register lobby / room lifecycle events."""

    @socketio.on("join")
    def on_join(data):
        room_code = data.get("room")
        name = data.get("name", "Anonymous")

        if not room_code:
            return

        join_room(room_code)

        # Add player to room
        room = game_manager.add_player_to_room(room_code, request.sid, name)

        # Broadcast updated state
        _broadcast_room_state(room_code, room)

    @socketio.on("leave")
    def on_leave(data):
        room_code = data.get("room")

        if not room_code:
            return

        # Remove player
        room = game_manager.remove_player_from_room(room_code, request.sid)
        leave_room(room_code)

        # Broadcast updated state if room still exists
        if room:
            _broadcast_room_state(room_code, room)

        # Notify the leaving player
        emit("left_room", {}, to=request.sid)

    @socketio.on("destroy_room")
    def on_destroy_room(data):
        room_code = data.get("room")

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can destroy
        if not room.is_host(request.sid):
            return

        # Notify all players
        emit("room_destroyed", {}, room=room_code)

        # Delete room
        game_manager.delete_room(room_code)
