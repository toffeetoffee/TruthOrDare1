# Model/minigame.py
import random


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
        """Check if one player reached the majority of votes."""
        if self.total_voters == 0:
            return None
        
        # Count votes
        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1
        
        # Winning threshold = ceil(total_voters / 2)
        winning_threshold = (self.total_voters + 1) // 2
        
        # Check if anyone reached threshold
        for player_name, count in vote_counts.items():
            if count >= winning_threshold:
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
        self.loser = random.choice(self.participants)
        self.winner = self.participants[0] if self.loser == self.participants[1] else self.participants[1]
        self.is_complete = True
        return self.loser
    
    def determine_loser(self):
        """Determine who lost based on votes (legacy compatibility)"""
        if not self.votes:
            return None
        
        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1
        
        # Tie check
        if len(vote_counts) == 2:
            counts = list(vote_counts.values())
            if counts[0] == counts[1]:
                return self.handle_tie()
        
        # Most votes = loser
        loser_name = max(vote_counts, key=vote_counts.get)
        for participant in self.participants:
            if participant.name == loser_name:
                self.loser = participant
            else:
                self.winner = participant
        self.is_complete = True
        return self.loser
    
    def get_participant_names(self):
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
            "type": "staring_contest",  # default fallback
            "participants": self.get_participant_names(),
            "votes": self.votes,
            "vote_count": len(self.votes),
            "vote_counts": self.get_vote_counts(),
            "total_voters": self.total_voters,
            "winner": self.winner.name if self.winner else None,
            "loser": self.loser.name if self.loser else None,
            "is_complete": self.is_complete,
        }


class StaringContest(Minigame):
    """Staring contest minigame - vote for who blinked first"""
    
    def __init__(self):
        super().__init__()
        self.name = "Staring Contest"
        self.description = "Who will blink first?"
    
    def to_dict(self):
        base = super().to_dict()
        base["type"] = "staring_contest"
        base["name"] = self.name
        base["description"] = self.description
        return base


class ArmWrestlingContest(Minigame):
    """Arm wrestling minigame - vote for who lost the match"""
    
    def __init__(self):
        super().__init__()
        self.name = "Arm Wrestling Contest"
        self.description = "Vote for who lost the arm wrestling match!"
    
    def to_dict(self):
        base = super().to_dict()
        base["type"] = "arm_wrestling"
        base["name"] = self.name
        base["description"] = self.description
        return base
