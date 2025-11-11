# Model/minigame.py
import random


class Minigame:
    """Base class for all minigames."""

    def __init__(self):
        self.participants = []  # List of Player objects
        self.votes = {}  # Dict[voter_sid: voted_player_name]
        self.winner = None
        self.loser = None
        self.is_complete = False
        self.total_voters = 0

        # Descriptive fields for UI
        self.name = "Generic Minigame"
        self.description_voter = "Vote for the loser!"
        self.description_participant = "You're playing in this minigame!"
        self.vote_instruction = "Vote for the loser!"

    # --- Core mechanics ---
    def add_participant(self, player):
        self.participants.append(player)

    def set_total_voters(self, total):
        self.total_voters = total

    def add_vote(self, voter_sid, voted_player_name):
        self.votes[voter_sid] = voted_player_name

    def check_immediate_winner(self):
        if self.total_voters == 0:
            return None

        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1

        winning_threshold = (self.total_voters + 1) // 2

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
        return len(self.votes) >= self.total_voters

    def handle_tie(self):
        if len(self.participants) != 2:
            return None
        self.loser = random.choice(self.participants)
        self.winner = self.participants[0] if self.loser == self.participants[1] else self.participants[1]
        self.is_complete = True
        return self.loser

    def determine_loser(self):
        if not self.votes:
            return None

        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1

        # Tie handling
        if len(vote_counts) == 2:
            counts = list(vote_counts.values())
            if counts[0] == counts[1]:
                return self.handle_tie()

        loser_name = max(vote_counts, key=vote_counts.get)
        for participant in self.participants:
            if participant.name == loser_name:
                self.loser = participant
            else:
                self.winner = participant
        self.is_complete = True
        return self.loser

    # --- Utility ---
    def get_participant_names(self):
        return [p.name for p in self.participants]

    def get_vote_counts(self):
        vote_counts = {}
        for voted_player in self.votes.values():
            vote_counts[voted_player] = vote_counts.get(voted_player, 0) + 1
        return vote_counts

    def to_dict(self):
        """Convert to dictionary for frontend rendering."""
        return {
            "type": getattr(self, "type", "minigame"),
            "name": self.name,
            "description_voter": self.description_voter,
            "description_participant": self.description_participant,
            "vote_instruction": self.vote_instruction,
            "participants": self.get_participant_names(),
            "vote_counts": self.get_vote_counts(),
            "vote_count": len(self.votes),
            "total_voters": self.total_voters,
            "winner": self.winner.name if self.winner else None,
            "loser": self.loser.name if self.loser else None,
            "is_complete": self.is_complete,
        }


# ------------------------------------------------------------
# Specific Minigames
# ------------------------------------------------------------

class StaringContest(Minigame):
    """Vote for who blinked first."""
    def __init__(self):
        super().__init__()
        self.type = "staring_contest"
        self.name = "🎮 Staring Contest"
        self.description_voter = "Vote for the player who blinked first."
        self.description_participant = "You are competing! Don't blink! 👀"
        self.vote_instruction = "Vote for the loser (the one who blinked first)!"


class ArmWrestlingContest(Minigame):
    """Vote for who lost the arm wrestling match."""
    def __init__(self):
        super().__init__()
        self.type = "arm_wrestling"
        self.name = "💪 Arm Wrestling Contest"
        self.description_voter = "Vote for the player who lost the arm wrestling match."
        self.description_participant = "You are arm wrestling! Show your strength! 💪"
        self.vote_instruction = "Vote for the loser of the arm wrestling match!"
