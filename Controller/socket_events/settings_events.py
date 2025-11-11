# Controller/socket_events/settings_events.py

from flask_socketio import emit
from flask import request


def register_settings_events(socketio, game_manager):
    """Register events related to room settings."""

    @socketio.on("update_settings")
    def on_update_settings(data):
        room_code = data.get("room")
        settings = data.get("settings", {})

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
        emit("settings_updated", {"settings": room.settings}, room=room_code)

    @socketio.on("get_settings")
    def on_get_settings(data):
        room_code = data.get("room")

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Send current settings to requester
        emit("settings_updated", {"settings": room.settings}, to=request.sid)
