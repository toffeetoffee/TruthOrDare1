from Model.player import Player
from Model.game_state import GameState

class Room:
    """Represents a game room"""
    
    def __init__(self, code):
        self.code = code
        self.host_sid = None
        self.players = []
        self.game_state = GameState()
        self.round_history = []  # List of RoundRecord objects
        
        # Game settings (configurable by host)
        self.settings = {
            'countdown_duration': 10,
            'preparation_duration': 30,
            'minigame_duration': 30,
            'selection_duration': 10,
            'truth_dare_duration': 60,
            'skip_duration': 5,
            'max_rounds': 10,
            'minigame_chance': 20  # Percentage (0-100)
        }
    
    def update_settings(self, new_settings):
        """Update room settings"""
        for key, value in new_settings.items():
            if key in self.settings:
                self.settings[key] = int(value)
        
        # Update game state max_rounds if changed
        if 'max_rounds' in new_settings:
            self.game_state.max_rounds = int(new_settings['max_rounds'])
        
        # Update game state minigame_chance if changed
        if 'minigame_chance' in new_settings:
            self.game_state.minigame_chance = int(new_settings['minigame_chance']) / 100.0
    
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
    
    def add_round_record(self, round_record):
        """Add a round record to history"""
        self.round_history.append(round_record)
    
    def get_round_history(self):
        """Get all round records as dictionaries"""
        return [record.to_dict() for record in self.round_history]
    
    def get_top_players(self, n=5):
        """Get top N players by score"""
        sorted_players = sorted(self.players, key=lambda p: p.score, reverse=True)
        return [{'name': p.name, 'score': p.score} for p in sorted_players[:n]]
    
    def reset_for_new_game(self):
        """Reset room for a new game"""
        # Reset all player scores and submissions
        for player in self.players:
            player.score = 0
            player.submissions_this_round = 0
        
        # Clear round history
        self.round_history = []
        
        # Reset game state
        self.game_state.reset_for_new_game()
    
    def reset_player_round_submissions(self):
        """Reset submission counters for all players at start of new round"""
        for player in self.players:
            player.reset_round_submissions()
    
    def to_dict(self):
        """Convert room to dictionary format (for backward compatibility)"""
        return {
            'host_sid': self.host_sid,
            'players': [p.to_dict() for p in self.players]
        }