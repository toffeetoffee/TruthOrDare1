from flask_socketio import emit
from flask import request
import json


def register_content_events(socketio, game_manager):
    """Socket events for truth/dare content management."""

    @socketio.on("submit_truth_dare")
    def handle_submit_truth_dare(data):
        room_code = data.get("room")
        room = game_manager.get_room(room_code)
        if not room:
            return

        player = room.get_player_by_sid(request.sid)
        if not player:
            return

        type_ = data.get("type")
        text = data.get("text")
        targets = data.get("targets", [])

        success = room.handle_submission(player, type_, text, targets)
        emit("submission_result", {"success": success}, to=request.sid)
        if success:
            emit("player_list", room.get_player_list(), to=room_code)

    @socketio.on("get_default_lists")
    def handle_get_default_lists(data):
        room_code = data.get("room")
        room = game_manager.get_room(room_code)
        if not room:
            return
        emit("default_lists", {
            "truths": room.default_truths,
            "dares": room.default_dares
        }, to=request.sid)

    @socketio.on("load_preset_file")
    def handle_load_preset(data):
        """Host can load preset truths/dares from uploaded JSON."""
        room_code = data.get("room")
        json_text = data.get("json_text")

        room = game_manager.get_room(room_code)
        if not room:
            return

        try:
            preset = json.loads(json_text)
            truths = preset.get("truths", [])
            dares = preset.get("dares", [])
            if isinstance(truths, list) and isinstance(dares, list):
                room.default_truths = truths
                room.default_dares = dares
                room.apply_default_lists_to_players()
                emit("preset_loaded", {"success": True}, to=room_code)
            else:
                raise ValueError
        except Exception:
            emit("preset_loaded", {"success": False}, to=request.sid)