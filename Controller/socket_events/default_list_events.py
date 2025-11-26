from flask_socketio import emit
from flask import request

import json


def register_default_list_events(socketio, game_manager):
    """Register events for managing default truth/dare lists and presets."""

    @socketio.on("get_default_lists")
    def on_get_default_lists(data):
        try:
            room_code = data.get("room")

            if not room_code:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                to=request.sid,
            )
        except Exception as e:
            print(f"[ERROR] get_default_lists: {e}")

    @socketio.on("add_default_truth")
    def on_add_default_truth(data):
        try:
            room_code = data.get("room")
            text = data.get("text", "").strip()

            if not room_code or not text:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            success = room.add_default_truth(text)

            if success:
                emit(
                    "default_lists_updated",
                    {
                        "truths": room.get_default_truths(),
                        "dares": room.get_default_dares(),
                    },
                    room=room_code,
                )
        except Exception as e:
            print(f"[ERROR] add_default_truth: {e}")

    @socketio.on("add_default_dare")
    def on_add_default_dare(data):
        try:
            room_code = data.get("room")
            text = data.get("text", "").strip()

            if not room_code or not text:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            success = room.add_default_dare(text)

            if success:
                emit(
                    "default_lists_updated",
                    {
                        "truths": room.get_default_truths(),
                        "dares": room.get_default_dares(),
                    },
                    room=room_code,
                )
        except Exception as e:
            print(f"[ERROR] add_default_dare: {e}")

    @socketio.on("edit_default_truth")
    def on_edit_default_truth(data):
        try:
            room_code = data.get("room")
            old_text = data.get("old_text", "").strip()
            new_text = data.get("new_text", "").strip()

            if not room_code or not old_text or not new_text:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            success = room.edit_default_truth(old_text, new_text)

            if success:
                emit(
                    "default_lists_updated",
                    {
                        "truths": room.get_default_truths(),
                        "dares": room.get_default_dares(),
                    },
                    room=room_code,
                )
        except Exception as e:
            print(f"[ERROR] edit_default_truth: {e}")

    @socketio.on("edit_default_dare")
    def on_edit_default_dare(data):
        try:
            room_code = data.get("room")
            old_text = data.get("old_text", "").strip()
            new_text = data.get("new_text", "").strip()

            if not room_code or not old_text or not new_text:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            success = room.edit_default_dare(old_text, new_text)

            if success:
                emit(
                    "default_lists_updated",
                    {
                        "truths": room.get_default_truths(),
                        "dares": room.get_default_dares(),
                    },
                    room=room_code,
                )
        except Exception as e:
            print(f"[ERROR] edit_default_dare: {e}")

    @socketio.on("remove_default_truths")
    def on_remove_default_truths(data):
        try:
            room_code = data.get("room")
            texts_to_remove = data.get("texts", [])

            if not room_code or not texts_to_remove:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            room.remove_default_truths(texts_to_remove)

            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                room=room_code,
            )
        except Exception as e:
            print(f"[ERROR] remove_default_truths: {e}")

    @socketio.on("remove_default_dares")
    def on_remove_default_dares(data):
        try:
            room_code = data.get("room")
            texts_to_remove = data.get("texts", [])

            if not room_code or not texts_to_remove:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            room.remove_default_dares(texts_to_remove)

            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                room=room_code,
            )
        except Exception as e:
            print(f"[ERROR] remove_default_dares: {e}")

    @socketio.on("load_preset_file")
    def on_load_preset_file(data):
        try:
            room_code = data.get("room")
            file_data = data.get("file_data")

            if not room_code or not file_data:
                emit(
                    "preset_error",
                    {"message": "Invalid file data"},
                    to=request.sid,
                )
                return

            room = game_manager.get_room(room_code)
            if not room:
                emit(
                    "preset_error",
                    {"message": "Room not found"},
                    to=request.sid,
                )
                return

            if not room.is_host(request.sid):
                emit(
                    "preset_error",
                    {"message": "Only host can load presets"},
                    to=request.sid,
                )
                return

            # Size check for DoS protection
            if len(file_data) > 1024 * 1024:  # 1MB limit
                emit(
                    "preset_error",
                    {"message": "File too large (max 1MB)"},
                    to=request.sid,
                )
                return

            preset = json.loads(file_data)

            if "truths" not in preset or "dares" not in preset:
                emit(
                    "preset_error",
                    {
                        "message": "Invalid preset format: missing truths or dares",
                    },
                    to=request.sid,
                )
                return

            if not isinstance(preset["truths"], list) or not isinstance(
                preset["dares"], list
            ):
                emit(
                    "preset_error",
                    {
                        "message": "Invalid preset format: truths and dares must be arrays",
                    },
                    to=request.sid,
                )
                return

            # Validate counts
            if len(preset["truths"]) > 1000 or len(preset["dares"]) > 1000:
                emit(
                    "preset_error",
                    {"message": "Too many items (max 1000 per type)"},
                    to=request.sid,
                )
                return

            for truth in preset["truths"]:
                if not isinstance(truth, str):
                    emit(
                        "preset_error",
                        {
                            "message": "Invalid preset format: all truths must be strings",
                        },
                        to=request.sid,
                    )
                    return

            for dare in preset["dares"]:
                if not isinstance(dare, str):
                    emit(
                        "preset_error",
                        {
                            "message": "Invalid preset format: all dares must be strings",
                        },
                        to=request.sid,
                    )
                    return

            if len(preset["truths"]) == 0 and len(preset["dares"]) == 0:
                emit(
                    "preset_error",
                    {
                        "message": "Preset must contain at least one truth or dare",
                    },
                    to=request.sid,
                )
                return

            room.default_truths = [
                t.strip() for t in preset["truths"] if t.strip()
            ]
            room.default_dares = [
                d.strip() for d in preset["dares"] if d.strip()
            ]

            for player in room.players:
                player.truth_dare_list.set_custom_defaults(
                    room.default_truths.copy(),
                    room.default_dares.copy(),
                )

            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                room=room_code,
            )

            emit(
                "preset_loaded",
                {
                    "message": (
                        "Preset loaded successfully!\n"
                        f"{len(room.default_truths)} truths and "
                        f"{len(room.default_dares)} dares loaded."
                    )
                },
                to=request.sid,
            )

        except json.JSONDecodeError:
            emit(
                "preset_error",
                {"message": "Invalid JSON format"},
                to=request.sid,
            )
        except Exception as e:
            print(f"[ERROR] load_preset_file: {e}")
            emit(
                "preset_error",
                {"message": f"Error loading preset: {str(e)}"},
                to=request.sid,
            )