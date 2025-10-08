from Model.player import Player
from Model.game_state import GameState

class Room:
    """Represents a game room"""
    
    def __init__(self, code):
        self.code = code
        self.host_sid = None
        self.players = []
        self.game_state = GameState()
        # Game settings (configurable by host)
        self.settings = {
            'countdown_duration': 10,
            'preparation_duration': 30,
            'selection_duration': 10,
            'truth_dare_duration': 60,
            'skip_duration': 5
        }
    
    def update_settings(self, new_settings):
        """Update room settings"""
        for key, value in new_settings.items():
            if key in self.settings:
                self.settings[key] = int(value)
    
    def add_player(self, player):
        """Add a player to the room"""
        # Check if player already exists
        if not any(p.socket_id == player.socket_id for p in self.players):
            self.players.append(player)
        
        # Set host if this is the first player
        if self.host_sid is None:
            self.host_sid = player.socket_id
    
    def remove_player(self, socket_id):
        """Remove a player by socket ID"""
        self.players = [p for p in self.players if p.socket_id != socket_id]
        
        # Transfer host if needed
        if self.host_sid == socket_id:
            if len(self.players) > 0:
                self.host_sid = self.players[0].socket_id
            else:
                self.host_sid = None
    
    def get_player_names(self):
        """Get list of player names"""
        return [p.name for p in self.players]
    
    def get_player_by_sid(self, socket_id):
        """Get player by socket ID"""
        for player in self.players:
            if player.socket_id == socket_id:
                return player
        return None
    
    def get_player_by_name(self, name):
        """Get player by name"""
        for player in self.players:
            if player.name == name:
                return player
        return None
    
    def is_empty(self):
        """Check if room has no players"""
        return len(self.players) == 0
    
    def is_host(self, socket_id):
        """Check if socket ID is the host"""
        return self.host_sid == socket_id
    
    def to_dict(self):
        """Convert room to dictionary format (for backward compatibility)"""
        return {
            'host_sid': self.host_sid,
            'players': [p.to_dict() for p in self.players]
        }