from flask_socketio import emit
from flask import request


def register_minigame_events(socketio, game_manager):
    """Events for handling minigame votes and results."""

    @socketio.on("minigame_vote")
    def handle_minigame_vote(data):
        room_code = data.get("room")
        voted_name = data.get("vote")
        room = game_manager.get_room(room_code)
        if not room or not room.state.minigame:
            return

        minigame = room.state.minigame
        voter = room.get_player_by_sid(request.sid)
        if not voter or not voted_name:
            return

        minigame.record_vote(voter, voted_name)
        emit("minigame_vote_update", minigame.get_vote_status(), to=room_code)

        if minigame.is_finished():
            loser = minigame.get_loser()
            room.state.selected_player = loser
            emit("minigame_ended", {"loser": loser.name}, to=room_code)
            room.state.start_selection()
            emit("phase_started", {"phase": "selection"}, to=room_code)