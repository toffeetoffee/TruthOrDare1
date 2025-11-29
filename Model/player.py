import re
import threading
from Model.truth_dare_list import TruthDareList
from Model.scoring_system import ScoringSystem


def _norm_txt(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', text.strip().lower())


class Player:
    def __init__(self, socket_id, name):
        self.socket_id = socket_id
        self.name = name
        self.truth_dare_list = TruthDareList()
        self.score = 0
        self.submissions_this_round=0
        self._lock = threading.RLock()

        # keep track so AI doesn't repeat stuff
        self.used_truths = []
        self.used_dares = []
        self._used_truths_norm = set()
        self._used_dares_norm = set()

    def add_score(self, points):
        with self._lock:
            self.score += points

    def reset_round_submissions(self):
        with self._lock:
            self.submissions_this_round = 0

    def increment_submissions(self):
        with self._lock:
            self.submissions_this_round += 1

    def can_submit_more(self):
        with self._lock:
            return self.submissions_this_round < ScoringSystem.MAX_SUBMISSIONS_PER_ROUND

    def try_submit(self):
        # check+increase in one go so it's safe with threads
        with self._lock:
            if self.submissions_this_round < ScoringSystem.MAX_SUBMISSIONS_PER_ROUND:
                self.submissions_this_round += 1
                return True
            return False

    def mark_truth_used(self, txt):
        with self._lock:
            if not txt: return
            n = _norm_txt(txt)
            if n not in self._used_truths_norm:
                self.used_truths.append(txt)
                self._used_truths_norm.add(n)

    def mark_dare_used(self, txt):
        with self._lock:
            if not txt:
                return
            n = _norm_txt(txt)
            if n not in self._used_dares_norm:
                self.used_dares.append(txt)
                self._used_dares_norm.add(n)

    def has_used_truth(self, txt):
        with self._lock:
            return _norm_txt(txt) in self._used_truths_norm

    def has_used_dare(self, txt):
        with self._lock:
            return _norm_txt(txt) in self._used_dares_norm

    def get_all_used_truths(self):
        with self._lock:
            return self.used_truths.copy()

    def get_all_used_dares(self):
        with self._lock:
            return self.used_dares.copy()

    def to_dict(self):
        with self._lock:
            return {
                "sid": self.socket_id,
                "name": self.name,
                "score": self.score,
            }

    @staticmethod
    def from_dict(data):
        p = Player(data["sid"], data["name"])
        if "score" in data:
            p.score = data["score"]
        return p
