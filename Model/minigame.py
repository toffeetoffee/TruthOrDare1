class Minigame:
    """Base class for minigames"""
    
    def __init__(self):
        self.participants = []  # List of Player objects
        self.votes = {}  # Dict[voter_sid: voted_player_name]
        self.winner = None
        self.loser = None
        self.is_complete = False
        self.total_voters = 0  # Total number of non-participants who can vote
    
    def add_participant(self, player):
        """Add a participant to the minigame"""
        self.participants.append(player)
    
    def set_total_voters(self, total):
        """Set the total number of voters (non-participants)"""
        self.total_voters = total
    
    def add_vote(self, voter_sid, voted_player_name):
        """Record a vote for who lost/blinked"""
        self.votes[voter_sid] = voted_player_name
    
    def check_immediate_winner(self):
        """
        Check if one player has reached winning threshold (at least half of total votes).
        Returns the loser (player with winning votes) or None if no winner yet.
        """
        if self.total_voters == 0:
            return None
        
        # Count votes for each participant
        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1
        
        # Calculate threshold: at least half (rounding up)
        winning_threshold = (self.total_voters + 1) // 2
        
        # Check if anyone reached the threshold
        for player_name, count in vote_counts.items():
            if count >= winning_threshold:
                # This player has enough votes to lose
                for participant in self.participants:
                    if participant.name == player_name:
                        self.loser = participant
                    else:
                        self.winner = participant
                
                self.is_complete = True
                return self.loser
        
        return None
    
    def check_all_voted(self):
        """Check if all voters have voted"""
        return len(self.votes) >= self.total_voters
    
    def handle_tie(self):
        """Handle tie situation - randomly pick loser"""
        if len(self.participants) != 2:
            return None
        
        import random
        self.loser = random.choice(self.participants)
        self.winner = self.participants[0] if self.loser == self.participants[1] else self.participants[1]
        self.is_complete = True
        return self.loser
    
    def determine_loser(self):
        """Determine who lost based on votes (legacy method for compatibility)"""
        if not self.votes:
            return None
        
        # Count votes
        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1
        
        # Check if it's a tie
        if len(vote_counts) == 2:
            counts = list(vote_counts.values())
            if counts[0] == counts[1]:
                # It's a tie - randomly pick
                return self.handle_tie()
        
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
    
    def get_vote_counts(self):
        """Get vote counts for each participant"""
        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1
        return vote_counts
    
    def to_dict(self):
        """Convert to dictionary format"""
        return {
            'type': 'staring_contest',
            'participants': self.get_participant_names(),
            'votes': self.votes,
            'vote_count': len(self.votes),
            'vote_counts': self.get_vote_counts(),
            'total_voters': self.total_voters,
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