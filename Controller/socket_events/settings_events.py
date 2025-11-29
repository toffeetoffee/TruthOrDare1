from flask_socketio import emit
from flask import request


def register_settings_events(socketio, game_manager):

    @socketio.on("update_settings")
    def on_update_settings(data):
        try:
            rc = data.get("room")
            settings = data.get("settings", {})

            if not rc:
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            if not room.is_host(request.sid):   # host only
                return

            room.update_settings(settings)

            emit("settings_updated", {"settings": room.settings}, room=rc)
        except Exception as e:
            print(f"[ERROR] update_settings: {e}")

    @socketio.on("get_settings")
    def on_get_settings(data):
        try:
            rc = data.get("room")

            if not rc:
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            emit("settings_updated", {"settings": room.settings}, to=request.sid)
        except Exception as e:
            print(f"[ERROR] get_settings: {e}")
