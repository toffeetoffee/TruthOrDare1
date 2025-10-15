class Minigame:
    """Base class for minigames"""
    
    def __init__(self, contestants):
        """
        Args:
            contestants: List of Player objects participating
        """
        self.contestants = contestants
        self.votes = {}  # {voter_socket_id: voted_player_name}
        self.loser = None
        self.is_complete = False
    
    def add_vote(self, voter_sid, voted_player_name):
        """Add a vote for who lost/blinked"""
        self.votes[voter_sid] = voted_player_name
    
    def get_vote_count(self, player_name):
        """Get number of votes for a specific player"""
        return sum(1 for vote in self.votes.values() if vote == player_name)
    
    def get_vote_counts(self):
        """Get vote counts for all contestants"""
        return {
            contestant.name: self.get_vote_count(contestant.name)
            for contestant in self.contestants
        }
    
    def check_majority(self, total_voters):
        """Check if any player has majority votes"""
        required_votes = (total_voters + 1) // 2  # More than half
        
        for contestant in self.contestants:
            if self.get_vote_count(contestant.name) >= required_votes:
                self.loser = contestant.name
                self.is_complete = True
                return True
        
        return False
    
    def to_dict(self):
        """Convert to dictionary format"""
        return {
            'type': self.__class__.__name__,
            'contestants': [c.name for c in self.contestants],
            'votes': self.get_vote_counts(),
            'loser': self.loser,
            'is_complete': self.is_complete
        }


class StaringContest(Minigame):
    """Staring contest minigame - vote for who blinked first"""
    
    def __init__(self, contestant1, contestant2):
        """
        Args:
            contestant1: First Player object
            contestant2: Second Player object
        """
        super().__init__([contestant1, contestant2])
        self.contestant1 = contestant1
        self.contestant2 = contestant2
    
    def get_description(self):
        """Get description of the minigame"""
        return f"{self.contestant1.name} vs {self.contestant2.name} - Staring Contest!"
    
    def to_dict(self):
        """Convert to dictionary with staring contest specific info"""
        data = super().to_dict()
        data['description'] = self.get_description()
        data['contestant1'] = self.contestant1.name
        data['contestant2'] = self.contestant2.name
        return data