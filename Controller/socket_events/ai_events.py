# Controller/socket_events/ai_events.py

from flask_socketio import emit
from flask import request

from Model.ai_generator import get_ai_generator


def register_ai_events(socketio, game_manager):
    """Register events related to AI generator status and debugging."""

    @socketio.on("check_ai_status")
    def on_check_ai_status(data):
        """Check AI generator status and run a test (for debugging)."""
        room_code = data.get("room")

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can check AI status
        if not room.is_host(request.sid):
            return

        # Get AI generator status
        ai_gen = get_ai_generator()
        status = ai_gen.get_status()

        # Run test if requested
        test_result = None
        if data.get("run_test", False):
            test_result = ai_gen.test_generation()

        # Send status back to requester
        emit(
            "ai_status_result",
            {
                "status": status,
                "test_result": test_result,
                "room_ai_enabled": room.settings.get(
                    "ai_generation_enabled", False
                ),
            },
            to=request.sid,
        )
