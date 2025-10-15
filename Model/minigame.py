class Minigame:
    """Base class for minigames"""
    
    def __init__(self):
        self.participants = []  # List of Player objects
        self.votes = {}  # Dict[voter_sid: voted_player_name]
        self.winner = None
        self.loser = None
        self.is_complete = False
    
    def add_participant(self, player):
        """Add a participant to the minigame"""
        self.participants.append(player)
    
    def add_vote(self, voter_sid, voted_player_name):
        """Record a vote for who lost/blinked"""
        self.votes[voter_sid] = voted_player_name
    
    def check_voting_complete(self, total_non_participants):
        """Check if voting is complete (more than half voted)"""
        if total_non_participants == 0:
            return False
        
        required_votes = (total_non_participants // 2) + 1
        return len(self.votes) >= required_votes
    
    def determine_loser(self):
        """Determine who lost based on votes"""
        if not self.votes:
            return None
        
        # Count votes
        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1
        
        # Find player with most votes (they lost/blinked)
        loser_name = max(vote_counts, key=vote_counts.get)
        
        # Set winner and loser
        for participant in self.participants:
            if participant.name == loser_name:
                self.loser = participant
            else:
                self.winner = participant
        
        self.is_complete = True
        return self.loser
    
    def get_participant_names(self):
        """Get list of participant names"""
        return [p.name for p in self.participants]
    
    def to_dict(self):
        """Convert to dictionary format"""
        return {
            'type': 'staring_contest',
            'participants': self.get_participant_names(),
            'votes': self.votes,
            'vote_count': len(self.votes),
            'winner': self.winner.name if self.winner else None,
            'loser': self.loser.name if self.loser else None,
            'is_complete': self.is_complete
        }


class StaringContest(Minigame):
    """Staring contest minigame - vote for who blinked first"""
    
    def __init__(self):
        super().__init__()
        self.name = "Staring Contest"
        self.description = "Who will blink first?"