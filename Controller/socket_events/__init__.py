from .lobby_events import register_lobby_events
from .game_flow_events import register_game_flow_events
from .content_events import register_content_events
from .ai_events import register_ai_events
from .scoring_events import register_scoring_events
from .minigame_events import register_minigame_events


def register_socket_events(socketio, game_manager):
    """
    Register all Socket.IO event handlers for the Truth or Dare app.
    This simply delegates registration to the specialized submodules.
    """
    register_lobby_events(socketio, game_manager)
    register_game_flow_events(socketio, game_manager)
    register_content_events(socketio, game_manager)
    register_ai_events(socketio, game_manager)
    register_scoring_events(socketio, game_manager)
    register_minigame_events(socketio, game_manager)
