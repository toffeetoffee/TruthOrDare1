"""
Player entity class.
"""

from Model.content.truth_dare_list import TruthDareList


class Player:
    """Represents a player in the game"""
    
    def __init__(self, socket_id, name):
        self.socket_id = socket_id
        self.name = name
        self.truth_dare_list = TruthDareList()
        self.score = 0
        self.submissions_this_round = 0
    
    def add_score(self, points):
        """Add points to player's score"""
        self.score += points
    
    def reset_round_submissions(self):
        """Reset submission counter for new round"""
        self.submissions_this_round = 0
    
    def increment_submissions(self):
        """Increment submission counter"""
        self.submissions_this_round += 1
    
    def can_submit_more(self):
        """Check if player can submit more truths/dares this round"""
        from Model.systems.scoring_system import ScoringSystem
        return self.submissions_this_round < ScoringSystem.MAX_SUBMISSIONS_PER_ROUND
    
    def to_dict(self):
        """Convert player to dictionary format"""
        return {
            'sid': self.socket_id,
            'name': self.name,
            'score': self.score
        }
    
    @staticmethod
    def from_dict(data):
        """Create player from dictionary"""
        player = Player(data['sid'], data['name'])
        if 'score' in data:
            player.score = data['score']
        return player