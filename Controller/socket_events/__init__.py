# Controller/socket_events/__init__.py

from .helpers import (
    init_socket_helpers,
    start_selection_or_minigame,
    start_truth_dare_phase_handler,
    _broadcast_room_state,
)
from .lobby_events import register_lobby_events
from .settings_events import register_settings_events
from .default_list_events import register_default_list_events
from .game_flow_events import register_game_flow_events
from .submission_events import register_submission_events
from .ai_events import register_ai_events
from .disconnect_events import register_disconnect_events


def register_socket_events(socketio, game_manager):
    """
    Public entry point used by app.py.
    Sets up helpers and registers all Socket.IO event handlers.
    """
    # Configure helper module with the current socketio and game_manager
    init_socket_helpers(socketio, game_manager)

    # Register groups of events
    register_lobby_events(socketio, game_manager)
    register_settings_events(socketio, game_manager)
    register_default_list_events(socketio, game_manager)
    register_game_flow_events(socketio, game_manager)
    register_submission_events(socketio, game_manager)
    register_ai_events(socketio, game_manager)
    register_disconnect_events(socketio, game_manager)


# Re-export helpers so names stay available if other files import them
__all__ = [
    "register_socket_events",
    "start_selection_or_minigame",
    "start_truth_dare_phase_handler",
    "_broadcast_room_state",
]
