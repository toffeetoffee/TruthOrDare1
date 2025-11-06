from Model.truth_dare_list import TruthDareList
from Model.scoring_system import ScoringSystem

class Player:
    """Represents a player in the game"""
    
    def __init__(self, socket_id, name):
        self.socket_id = socket_id
        self.name = name
        self.truth_dare_list = TruthDareList()
        self.score = 0
        self.submissions_this_round = 0
        
        # Track used truths/dares to prevent AI from generating duplicates
        self.used_truths = []  # List of truth texts that have been performed
        self.used_dares = []   # List of dare texts that have been performed
    
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
        
        return self.submissions_this_round < ScoringSystem.MAX_SUBMISSIONS_PER_ROUND
    
    def mark_truth_used(self, truth_text):
        """Mark a truth as used (performed) to prevent AI duplicates"""
        if truth_text and truth_text not in self.used_truths:
            self.used_truths.append(truth_text)
    
    def mark_dare_used(self, dare_text):
        """Mark a dare as used (performed) to prevent AI duplicates"""
        if dare_text and dare_text not in self.used_dares:
            self.used_dares.append(dare_text)
    
    def get_all_used_truths(self):
        """Get all truths this player has used (for AI context)"""
        return self.used_truths.copy()
    
    def get_all_used_dares(self):
        """Get all dares this player has used (for AI context)"""
        return self.used_dares.copy()
    
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