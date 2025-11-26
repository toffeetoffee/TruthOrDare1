from flask_socketio import emit
from flask import request


def register_settings_events(socketio, game_manager):
    """Register events related to room settings."""

    @socketio.on("update_settings")
    def on_update_settings(data):
        try:
            room_code = data.get("room")
            settings = data.get("settings", {})

            if not room_code:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            room.update_settings(settings)

            emit("settings_updated", {"settings": room.settings}, room=room_code)
        except Exception as e:
            print(f"[ERROR] update_settings: {e}")

    @socketio.on("get_settings")
    def on_get_settings(data):
        try:
            room_code = data.get("room")

            if not room_code:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            emit("settings_updated", {"settings": room.settings}, to=request.sid)
        except Exception as e:
            print(f"[ERROR] get_settings: {e}")