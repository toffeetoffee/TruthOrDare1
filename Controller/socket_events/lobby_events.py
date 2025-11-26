from flask_socketio import join_room, leave_room, emit
from flask import request

from .helpers import _broadcast_room_state


def register_lobby_events(socketio, game_manager):
    """Register lobby / room lifecycle events."""

    @socketio.on("join")
    def on_join(data):
        try:
            room_code = data.get("room")
            name = data.get("name", "Anonymous")

            if not room_code:
                return

            join_room(room_code)

            room = game_manager.add_player_to_room(room_code, request.sid, name)

            _broadcast_room_state(room_code, room)
        except Exception as e:
            print(f"[ERROR] join: {e}")

    @socketio.on("leave")
    def on_leave(data):
        try:
            room_code = data.get("room")

            if not room_code:
                return

            room = game_manager.remove_player_from_room(room_code, request.sid)
            leave_room(room_code)

            if room:
                _broadcast_room_state(room_code, room)

            emit("left_room", {}, to=request.sid)
        except Exception as e:
            print(f"[ERROR] leave: {e}")

    @socketio.on("destroy_room")
    def on_destroy_room(data):
        try:
            room_code = data.get("room")

            if not room_code:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            emit("room_destroyed", {}, room=room_code)

            game_manager.delete_room(room_code)
        except Exception as e:
            print(f"[ERROR] destroy_room: {e}")