"""
Socket event handler registration - combines all socket event modules.
"""

from Controller.socket_events.room_events import register_room_events
from Controller.socket_events.game_events import register_game_events
from Controller.socket_events.minigame_events import register_minigame_events


def register_socket_events(socketio, game_manager):
    """Register all socket event handlers"""
    
    # Register room events (join, leave, settings, etc.)
    register_room_events(socketio, game_manager)
    
    # Register game events (start, restart, submissions, etc.)
    register_game_events(socketio, game_manager)
    
    # Register minigame events (voting)
    # Pass the helper function from game_events
    register_minigame_events(
        socketio, 
        game_manager, 
        register_game_events.start_truth_dare_phase_handler
    )