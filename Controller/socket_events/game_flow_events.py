from flask_socketio import emit
import threading
import time
import random

from Model.round_record import RoundRecord
from Model.scoring_system import ScoringSystem
from Model.ai_generator import get_ai_generator
from Model.truth_dare import Truth, Dare


def register_game_flow_events(socketio, game_manager):
    """Handles the full game flow events like start_game and phase transitions."""

    @socketio.on("start_game")
    def handle_start_game(data):
        room_code = data.get("room")
        room = game_manager.get_room(room_code)
        if not room:
            emit("error", {"message": "Room not found."})
            return

        # Start game and broadcast state
        room.state.start_countdown()
        emit("game_started", {"phase": "countdown"}, to=room_code)

        # Background phase control thread
        threading.Thread(
            target=_run_game_phases,
            args=(socketio, room_code, game_manager),
            daemon=True
        ).start()


def _run_game_phases(socketio, room_code, game_manager):
    """Internal thread loop to move through game phases automatically."""
    room = game_manager.get_room(room_code)
    if not room:
        return

    while not room.state.should_end_game():
        # Broadcast current state periodically
        socketio.emit("game_state_update", room.state.to_dict(), to=room_code)

        # Phase check
        if room.state.is_phase_complete():
            _next_phase(socketio, room, game_manager)
        time.sleep(1)

    # End game summary
    socketio.emit("game_over", {
        "top_players": room.get_top_players(),
        "round_history": [r.to_dict() for r in room.round_records]
    }, to=room_code)


def _next_phase(socketio, room, game_manager):
    """Move to the next logical phase."""
    state = room.state
    socketio.emit("phase_ended", {"phase": state.phase}, to=room.code)

    if state.phase == "countdown":
        state.start_preparation()
    elif state.phase == "preparation":
        # maybe start a minigame
        if random.random() < room.settings.get("minigame_chance", 0.25):
            state.start_minigame()
        else:
            state.start_selection()
    elif state.phase == "minigame":
        state.start_selection()
    elif state.phase == "selection":
        state.start_truth_dare()
    elif state.phase == "truth_dare":
        state.start_preparation()
    elif state.phase == "end_game":
        return

    socketio.emit("phase_started", {"phase": state.phase}, to=room.code)