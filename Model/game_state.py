from datetime import datetime, timedelta
import threading


class GameState:
    PHASE_LOBBY = 'lobby'
    PHASE_COUNTDOWN = 'countdown'
    PHASE_PREPARATION = 'preparation'
    PHASE_MINIGAME = 'minigame'
    PHASE_SELECTION = 'selection'
    PHASE_TRUTH_DARE = 'truth_dare'
    PHASE_END_GAME = 'end_game'

    def __init__(self):
        self.phase = self.PHASE_LOBBY
        self.phase_end_time = None
        self.started = False
        self.selected_player = None
        self.selected_choice = None
        self.current_truth_dare = None
        self.minigame = None
        self.skip_votes = set()
        self.skip_activated = False
        self.list_empty = False
        self.current_round = 0
        self.max_rounds = 10
        self._lock = threading.RLock()

    def start_countdown(self, duration=10):
        with self._lock:
            self.phase = self.PHASE_COUNTDOWN
            self.phase_end_time = datetime.now() + timedelta(seconds=duration)
            self.started = True

    def start_preparation(self, duration=30):
        with self._lock:
            self.phase = self.PHASE_PREPARATION
            self.phase_end_time = datetime.now() + timedelta(seconds=duration)
            self.selected_player = None
            self.selected_choice = None
            self.current_truth_dare = None
            self.minigame = None
            self.list_empty = False
            self.skip_votes.clear()
            self.current_round += 1

    def start_minigame(self):
        with self._lock:
            self.phase = self.PHASE_MINIGAME
            self.phase_end_time = None

    def start_selection(self, duration=10):
        with self._lock:
            self.phase = self.PHASE_SELECTION
            self.phase_end_time = datetime.now() + timedelta(seconds=duration)
            self.selected_choice = None

    def start_truth_dare(self, duration=60):
        with self._lock:
            self.phase = self.PHASE_TRUTH_DARE
            self.phase_end_time = datetime.now() + timedelta(seconds=duration)
            self.skip_votes.clear()
            self.skip_activated = False
            self.list_empty = False

    def start_end_game(self):
        with self._lock:
            self.phase = self.PHASE_END_GAME
            self.phase_end_time = None

    def set_selected_player(self, player_name):
        with self._lock:
            self.selected_player = player_name

    def set_selected_choice(self, choice):
        with self._lock:
            self.selected_choice = choice

    def set_current_truth_dare(self, truth_dare_dict):
        with self._lock:
            self.current_truth_dare = truth_dare_dict

    def set_minigame(self, minigame):
        with self._lock:
            self.minigame = minigame

    def add_skip_vote(self, player_sid):
        with self._lock:
            self.skip_votes.add(player_sid)

    def activate_skip(self):
        with self._lock:
            self.skip_activated = True

    def get_skip_vote_count(self):
        with self._lock:
            return len(self.skip_votes)

    def reduce_timer(self, seconds=5):
        with self._lock:
            self.phase_end_time = datetime.now() + timedelta(seconds=seconds)

    def get_remaining_time(self):
        with self._lock:
            if self.phase_end_time is None:
                return 0

            rem = (self.phase_end_time - datetime.now()).total_seconds()
            return max(0, int(rem))

    def is_phase_complete(self):
        with self._lock:
            if self.phase_end_time is None:
                return False
            return datetime.now() >= self.phase_end_time

    def should_end_game(self):
        with self._lock:
            return self.current_round >= self.max_rounds

    def reset_for_new_game(self):
        with self._lock:
            self.phase = self.PHASE_COUNTDOWN
            self.phase_end_time = None
            self.started = False
            self.selected_player = None
            self.selected_choice = None
            self.current_truth_dare = None
            self.minigame = None
            self.skip_votes.clear()
            self.current_round = 0

    def to_dict(self):
        with self._lock:
            base = {
                'phase': self.phase,
                'remaining_time': self.get_remaining_time(),
                'started': self.started,
                'selected_player': self.selected_player,
                'selected_choice': self.selected_choice,
                'current_truth_dare': self.current_truth_dare,
                'skip_vote_count': self.get_skip_vote_count(),
                'skip_activated': self.skip_activated,
                'list_empty': self.list_empty,
                'current_round': self.current_round,
                'max_rounds': self.max_rounds
            }

            if self.minigame:
                base['minigame'] = self.minigame.to_dict()

            return base
