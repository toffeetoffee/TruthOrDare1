# Controller/socket_events/default_list_events.py

from flask_socketio import emit
from flask import request

import json


def register_default_list_events(socketio, game_manager):
    """Register events for managing default truth/dare lists and presets."""

    @socketio.on("get_default_lists")
    def on_get_default_lists(data):
        room_code = data.get("room")

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Send current default lists to requester
        emit(
            "default_lists_updated",
            {
                "truths": room.get_default_truths(),
                "dares": room.get_default_dares(),
            },
            to=request.sid,
        )

    @socketio.on("add_default_truth")
    def on_add_default_truth(data):
        room_code = data.get("room")
        text = data.get("text", "").strip()

        if not room_code or not text:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can modify defaults
        if not room.is_host(request.sid):
            return

        # Add the truth
        success = room.add_default_truth(text)

        if success:
            # Broadcast updated lists to all players
            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                room=room_code,
            )

    @socketio.on("add_default_dare")
    def on_add_default_dare(data):
        room_code = data.get("room")
        text = data.get("text", "").strip()

        if not room_code or not text:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can modify defaults
        if not room.is_host(request.sid):
            return

        # Add the dare
        success = room.add_default_dare(text)

        if success:
            # Broadcast updated lists to all players
            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                room=room_code,
            )

    @socketio.on("edit_default_truth")
    def on_edit_default_truth(data):
        room_code = data.get("room")
        old_text = data.get("old_text", "").strip()
        new_text = data.get("new_text", "").strip()

        if not room_code or not old_text or not new_text:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can modify defaults
        if not room.is_host(request.sid):
            return

        # Edit the truth
        success = room.edit_default_truth(old_text, new_text)

        if success:
            # Broadcast updated lists to all players
            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                room=room_code,
            )

    @socketio.on("edit_default_dare")
    def on_edit_default_dare(data):
        room_code = data.get("room")
        old_text = data.get("old_text", "").strip()
        new_text = data.get("new_text", "").strip()

        if not room_code or not old_text or not new_text:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can modify defaults
        if not room.is_host(request.sid):
            return

        # Edit the dare
        success = room.edit_default_dare(old_text, new_text)

        if success:
            # Broadcast updated lists to all players
            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                room=room_code,
            )

    @socketio.on("remove_default_truths")
    def on_remove_default_truths(data):
        room_code = data.get("room")
        texts_to_remove = data.get("texts", [])

        if not room_code or not texts_to_remove:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can modify defaults
        if not room.is_host(request.sid):
            return

        # Remove the truths
        room.remove_default_truths(texts_to_remove)

        # Broadcast updated lists to all players
        emit(
            "default_lists_updated",
            {
                "truths": room.get_default_truths(),
                "dares": room.get_default_dares(),
            },
            room=room_code,
        )

    @socketio.on("remove_default_dares")
    def on_remove_default_dares(data):
        room_code = data.get("room")
        texts_to_remove = data.get("texts", [])

        if not room_code or not texts_to_remove:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can modify defaults
        if not room.is_host(request.sid):
            return

        # Remove the dares
        room.remove_default_dares(texts_to_remove)

        # Broadcast updated lists to all players
        emit(
            "default_lists_updated",
            {
                "truths": room.get_default_truths(),
                "dares": room.get_default_dares(),
            },
            room=room_code,
        )

    @socketio.on("load_preset_file")
    def on_load_preset_file(data):
        room_code = data.get("room")
        file_data = data.get("file_data")  # JSON string

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

        # Only host can load presets
        if not room.is_host(request.sid):
            emit(
                "preset_error",
                {"message": "Only host can load presets"},
                to=request.sid,
            )
            return

        try:
            # Parse JSON
            preset = json.loads(file_data)

            # Validate structure
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

            # Validate all items are strings
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

            # Check for minimum requirements
            if len(preset["truths"]) == 0 and len(preset["dares"]) == 0:
                emit(
                    "preset_error",
                    {
                        "message": "Preset must contain at least one truth or dare",
                    },
                    to=request.sid,
                )
                return

            # Replace BOTH defaults
            room.default_truths = [
                t.strip() for t in preset["truths"] if t.strip()
            ]
            room.default_dares = [
                d.strip() for d in preset["dares"] if d.strip()
            ]

            # Update all existing players' truth/dare lists with the new defaults
            for player in room.players:
                player.truth_dare_list.set_custom_defaults(
                    room.default_truths.copy(),
                    room.default_dares.copy(),
                )

            # Broadcast updated lists to all players
            emit(
                "default_lists_updated",
                {
                    "truths": room.get_default_truths(),
                    "dares": room.get_default_dares(),
                },
                room=room_code,
            )

            # Send success message
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
        except Exception as e:  # noqa: BLE001
            emit(
                "preset_error",
                {"message": f"Error loading preset: {str(e)}"},
                to=request.sid,
            )
