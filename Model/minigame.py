import random


class Minigame:
    def __init__(self):
        self.participants = []          # Player objects
        self.votes = {}                 # voter_sid -> player_name
        self.winner = None
        self.loser = None
        self.is_complete = False
        self.total_voters = 0

        self.name = "Generic Minigame"
        self.description_voter = "Vote for the loser!"
        self.description_participant = "You're playing in this minigame!"
        self.vote_instruction = "Vote for the loser!"

    def add_participant(self, player):
        self.participants.append(player)

    def set_total_voters(self, total):
        self.total_voters = total

    def add_vote(self, voter_sid, voted_player_name):
        self.votes[voter_sid] = voted_player_name

    def check_immediate_winner(self):
        if self.total_voters == 0:
            return None

        vc = {}
        for voted_player in self.votes.values():
            vc[voted_player] = vc.get(voted_player, 0) + 1

        threshold = (self.total_voters + 1) // 2

        for player_name, count in vc.items():
            if count >= threshold:
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
        self.winner = (
            self.participants[0]
            if self.loser == self.participants[1]
            else self.participants[1]
        )
        self.is_complete = True
        return self.loser

    def determine_loser(self):
        if not self.votes:
            return None

        vc = {}
        for voted_player in self.votes.values():
            vc[voted_player] = vc.get(voted_player, 0) + 1

        if len(vc) == 2:
            counts = list(vc.values())
            if counts[0] == counts[1]:
                return self.handle_tie()

        loser_name = max(vc, key=vc.get)
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
        vc = {}
        for voted_player in self.votes.values():
            vc[voted_player] = vc.get(voted_player, 0) + 1
        return vc

    def to_dict(self):
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


class StaringContest(Minigame):
    def __init__(self):
        super().__init__()
        self.type = "staring_contest"
        self.name = "🎮 Staring Contest"
        self.description_voter = "Vote for the player who blinked first."
        self.description_participant = "You are competing! Don't blink! 👀"
        self.vote_instruction = "Vote for the loser (the one who blinked first)!"


class ArmWrestlingContest(Minigame):
    def __init__(self):
        super().__init__()
        self.type = "arm_wrestling"
        self.name = "💪 Arm Wrestling Contest"
        self.description_voter = "Vote for the player who lost the arm wrestling match."
        self.description_participant = "You are arm wrestling! Show your strength! 💪"
        self.vote_instruction = "Vote for the loser of the arm wrestling match!"
