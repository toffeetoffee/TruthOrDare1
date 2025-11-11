# Controller/socket_events/__init__.py
"""
Main entry point for all Socket.IO event registrations.
Ensures all submodules share the same socketio and game_manager instances.
"""

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
    Called once from app.py.
    Injects the shared socketio and game_manager into helper globals,
    then registers all event modules.
    """
    print(f"[SOCKET_INIT] Using shared GameManager id={id(game_manager)}")
    init_socket_helpers(socketio, game_manager)

    # Register all event groups
    register_lobby_events(socketio, game_manager)
    register_settings_events(socketio, game_manager)
    register_default_list_events(socketio, game_manager)
    register_game_flow_events(socketio, game_manager)
    register_submission_events(socketio, game_manager)
    register_ai_events(socketio, game_manager)
    register_disconnect_events(socketio, game_manager)


# Re-export helpers (for consistency with previous design)
__all__ = [
    "register_socket_events",
    "start_selection_or_minigame",
    "start_truth_dare_phase_handler",
    "_broadcast_room_state",
]
