from flask import request

from .helpers import _broadcast_room_state


def register_disconnect_events(socketio, game_manager):

    @socketio.on("disconnect")
    def on_disconnect():
        try:
            updated = game_manager.remove_player_from_all_rooms(request.sid)

            for room_code in updated:
                room = game_manager.get_room(room_code)
                if room:
                    _broadcast_room_state(room_code, room)
        except Exception as e:
            print(f"[ERROR] disconnect: {e}")
