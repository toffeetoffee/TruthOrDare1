from flask import request
from flask_socketio import emit


def register_scoring_events(socketio, game_manager):
    """Scoreboard and round record events."""

    @socketio.on("get_scores")
    def handle_get_scores(data):
        room_code = data.get("room")
        room = game_manager.get_room(room_code)
        if not room:
            return
        emit("scores", {"players": room.get_player_scores()}, to=request.sid)

    @socketio.on("get_round_history")
    def handle_get_round_history(data):
        room_code = data.get("room")
        room = game_manager.get_room(room_code)
        if not room:
            return
        emit(
            "round_history",
            {"records": [r.to_dict() for r in room.round_records]},
            to=request.sid,
        )