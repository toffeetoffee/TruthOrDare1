# Model/player.py
import re
from Model.truth_dare_list import TruthDareList
from Model.scoring_system import ScoringSystem


def _normalize_text(text: str) -> str:
    """Normalize text for consistent duplicate checking."""
    return re.sub(r'[^a-z0-9]+', '', text.strip().lower())


class Player:
    """Represents a player in the game."""

    def __init__(self, socket_id, name):
        self.socket_id = socket_id
        self.name = name
        self.truth_dare_list = TruthDareList()
        self.score = 0
        self.submissions_this_round = 0

        # Track used truths/dares to prevent AI from generating duplicates
        self.used_truths = []
        self.used_dares = []
        self._used_truths_normalized = set()
        self._used_dares_normalized = set()

    # ------------------------------------------------------------------
    # Score and submission management
    # ------------------------------------------------------------------
    def add_score(self, points):
        self.score += points

    def reset_round_submissions(self):
        self.submissions_this_round = 0

    def increment_submissions(self):
        self.submissions_this_round += 1

    def can_submit_more(self):
        return self.submissions_this_round < ScoringSystem.MAX_SUBMISSIONS_PER_ROUND

    # ------------------------------------------------------------------
    # Truth/Dare tracking for AI duplicate prevention
    # ------------------------------------------------------------------
    def mark_truth_used(self, truth_text):
        if not truth_text:
            return
        norm = _normalize_text(truth_text)
        if norm not in self._used_truths_normalized:
            self.used_truths.append(truth_text)
            self._used_truths_normalized.add(norm)

    def mark_dare_used(self, dare_text):
        if not dare_text:
            return
        norm = _normalize_text(dare_text)
        if norm not in self._used_dares_normalized:
            self.used_dares.append(dare_text)
            self._used_dares_normalized.add(norm)

    def has_used_truth(self, text):
        return _normalize_text(text) in self._used_truths_normalized

    def has_used_dare(self, text):
        return _normalize_text(text) in self._used_dares_normalized

    def get_all_used_truths(self):
        return self.used_truths.copy()

    def get_all_used_dares(self):
        return self.used_dares.copy()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self):
        return {
            "sid": self.socket_id,
            "name": self.name,
            "score": self.score,
        }

    @staticmethod
    def from_dict(data):
        player = Player(data["sid"], data["name"])
        if "score" in data:
            player.score = data["score"]
        return player
