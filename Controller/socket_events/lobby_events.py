from flask_socketio import join_room, leave_room, emit
from flask import request

from .helpers import _broadcast_room_state


def register_lobby_events(socketio, game_manager):

    @socketio.on("join")
    def on_join(data):
        try:
            rc = data.get("room")
            nm = data.get("name", "Anonymous")

            if not rc:
                return

            join_room(rc)

            # add player server-side then tell everyone
            room = game_manager.add_player_to_room(rc, request.sid, nm)

            _broadcast_room_state(rc, room)
        except Exception as e:
            print(f"[ERROR] join: {e}")

    @socketio.on("leave")
    def on_leave(data):
        try:
            rc = data.get("room")

            if not rc:
                return

            room = game_manager.remove_player_from_room(rc, request.sid)
            leave_room(rc)

            if room:
                _broadcast_room_state(rc, room)

            emit("left_room", {}, to=request.sid)
        except Exception as e:
            print(f"[ERROR] leave: {e}")

    @socketio.on("destroy_room")
    def on_destroy_room(data):
        try:
            rc = data.get("room")

            if not rc:
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            emit("room_destroyed", {}, room=rc)

            game_manager.delete_room(rc)
        except Exception as e:
            print(f"[ERROR] destroy_room: {e}")
