class Player:
    """Represents a player in the game"""
    
    def __init__(self, socket_id, name):
        self.socket_id = socket_id
        self.name = name
    
    def to_dict(self):
        """Convert player to dictionary format"""
        return {
            'sid': self.socket_id,
            'name': self.name
        }
    
    @staticmethod
    def from_dict(data):
        """Create player from dictionary"""
        return Player(data['sid'], data['name'])
