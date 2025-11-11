from flask_socketio import emit
from Model.ai_generator import get_ai_generator


def register_ai_events(socketio, game_manager):
    """AI-related socket events for generation and diagnostics."""

    @socketio.on("check_ai_status")
    def handle_check_ai_status(data):
        ai_gen = get_ai_generator()
        emit("ai_status", {
            "enabled": ai_gen.enabled,
            "has_client": ai_gen.client is not None
        }, to=data.get("room"))

    @socketio.on("test_ai_generation")
    def handle_test_ai_generation(data):
        ai_gen = get_ai_generator()
        result = ai_gen.test_generation()
        emit("ai_test_result", {"result": result}, to=data.get("room"))