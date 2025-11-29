from flask_socketio import emit
from flask import request

from Model.ai_generator import get_ai_generator


def register_ai_events(socketio, game_manager):

    @socketio.on("check_ai_status")
    def on_check_ai_status(data):
        try:
            rc = data.get("room")

            if not rc:  # no room
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            if not room.is_host(request.sid):  # host only
                return

            ai_gen = get_ai_generator()
            status = ai_gen.get_status()

            test_res = None
            if data.get("run_test", False):
                test_res = ai_gen.test_generation()

            emit(
                "ai_status_result",
                {
                    "status": status,
                    "test_result": test_res,
                    "room_ai_enabled": room.settings.get(
                        "ai_generation_enabled", False
                    ),
                },
                to=request.sid,
            )
        except Exception as e:
            print(f"[ERROR] check_ai_status: {e}")
