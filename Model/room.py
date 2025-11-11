# Model/room.py
import json
import os
import re
from Model.player import Player
from Model.game_state import GameState


# ----------------------------------------------------------------------
# Normalization helper
# ----------------------------------------------------------------------
def _normalize_text(text: str) -> str:
    """Normalize text for strict duplicate comparison."""
    return re.sub(r"[^a-z0-9]+", "", text.strip().lower())


# ----------------------------------------------------------------------
# Room class
# ----------------------------------------------------------------------
class Room:
    """Represents a game room"""

    def __init__(self, code):
        self.code = code
        self.host_sid = None
        self.players = []
        self.game_state = GameState()
        self.round_history = []

        # Default truths/dares for this room
        self.default_truths = []
        self.default_dares = []
        self._load_default_lists()

        # AI-generated tracking
        self.ai_generated_truths = []
        self.ai_generated_dares = []
        self._ai_generated_truths_normalized = set()
        self._ai_generated_dares_normalized = set()

        # Configurable game settings
        self.settings = {
            "countdown_duration": 10,
            "preparation_duration": 30,
            "selection_duration": 10,
            "truth_dare_duration": 60,
            "skip_duration": 5,
            "max_rounds": 10,
            "minigame_chance": 20,
            "ai_generation_enabled": True,
        }

    # ------------------------------------------------------------------
    # Load defaults
    # ------------------------------------------------------------------
    def _load_default_lists(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            file_path = os.path.join(parent_dir, "default_truths_dares.json")
            with open(file_path, "r") as f:
                data = json.load(f)
            self.default_truths = data.get("truths", [])
            self.default_dares = data.get("dares", [])
        except Exception as e:
            print(f"Warning: Could not load default truths/dares: {e}")
            self.default_truths = [
                "What is your biggest fear?",
                "What is the most embarrassing thing you've ever done?",
            ]
            self.default_dares = ["Do 10 pushups", "Sing a song loudly"]

    # ------------------------------------------------------------------
    # Default list operations
    # ------------------------------------------------------------------
    def get_default_truths(self):
        return self.default_truths.copy()

    def get_default_dares(self):
        return self.default_dares.copy()

    def add_default_truth(self, text):
        if text and text not in self.default_truths:
            self.default_truths.append(text)
            return True
        return False

    def add_default_dare(self, text):
        if text and text not in self.default_dares:
            self.default_dares.append(text)
            return True
        return False

    def edit_default_truth(self, old_text, new_text):
        try:
            idx = self.default_truths.index(old_text)
            if new_text and new_text not in self.default_truths:
                self.default_truths[idx] = new_text
                return True
        except ValueError:
            pass
        return False

    def edit_default_dare(self, old_text, new_text):
        try:
            idx = self.default_dares.index(old_text)
            if new_text and new_text not in self.default_dares:
                self.default_dares[idx] = new_text
                return True
        except ValueError:
            pass
        return False

    def remove_default_truths(self, texts_to_remove):
        for t in texts_to_remove:
            if t in self.default_truths:
                self.default_truths.remove(t)

    def remove_default_dares(self, texts_to_remove):
        for t in texts_to_remove:
            if t in self.default_dares:
                self.default_dares.remove(t)

    # ------------------------------------------------------------------
    # AI duplicate tracking helpers
    # ------------------------------------------------------------------
    def add_ai_generated_truth(self, text):
        norm = _normalize_text(text)
        if norm not in self._ai_generated_truths_normalized:
            self._ai_generated_truths_normalized.add(norm)
            self.ai_generated_truths.append(text)
            return True
        return False

    def add_ai_generated_dare(self, text):
        norm = _normalize_text(text)
        if norm not in self._ai_generated_dares_normalized:
            self._ai_generated_dares_normalized.add(norm)
            self.ai_generated_dares.append(text)
            return True
        return False

    def get_all_used_truths(self):
        all_truths = self.default_truths.copy()
        all_truths.extend(self.ai_generated_truths)
        for p in self.players:
            all_truths.extend([t.text for t in p.truth_dare_list.truths])
        return all_truths

    def get_all_used_dares(self):
        all_dares = self.default_dares.copy()
        all_dares.extend(self.ai_generated_dares)
        for p in self.players:
            all_dares.extend([d.text for d in p.truth_dare_list.dares])
        return all_dares

    # ------------------------------------------------------------------
    # Settings, players, and scoring
    # ------------------------------------------------------------------
    def update_settings(self, new_settings):
        for k, v in new_settings.items():
            if k in self.settings:
                self.settings[k] = int(v)
        if "max_rounds" in new_settings:
            self.game_state.max_rounds = int(new_settings["max_rounds"])

    def add_player(self, player):
        if not any(p.socket_id == player.socket_id for p in self.players):
            player.truth_dare_list.set_custom_defaults(
                self.default_truths.copy(), self.default_dares.copy()
            )
            self.players.append(player)
        if self.host_sid is None:
            self.host_sid = player.socket_id

    def remove_player(self, socket_id):
        self.players = [p for p in self.players if p.socket_id != socket_id]
        if self.host_sid == socket_id:
            self.host_sid = self.players[0].socket_id if self.players else None

    def get_player_names(self):
        return [p.name for p in self.players]

    def get_player_by_sid(self, socket_id):
        return next((p for p in self.players if p.socket_id == socket_id), None)

    def get_player_by_name(self, name):
        return next((p for p in self.players if p.name == name), None)

    def is_empty(self):
        return not self.players

    def is_host(self, socket_id):
        return self.host_sid == socket_id

    # ------------------------------------------------------------------
    # Round and game resets
    # ------------------------------------------------------------------
    def add_round_record(self, record):
        self.round_history.append(record)

    def get_round_history(self):
        return [r.to_dict() for r in self.round_history]

    def get_top_players(self, n=5):
        sorted_players = sorted(self.players, key=lambda p: p.score, reverse=True)
        return [{"name": p.name, "score": p.score} for p in sorted_players[:n]]

    def reset_for_new_game(self):
        for p in self.players:
            p.score = 0
            p.submissions_this_round = 0
            p.used_truths = []
            p.used_dares = []
            p.truth_dare_list.set_custom_defaults(
                self.default_truths.copy(), self.default_dares.copy()
            )
        self.round_history = []
        self.game_state.reset_for_new_game()
        # Note: AI lists persist to prevent duplicates

    def reset_player_round_submissions(self):
        for p in self.players:
            p.reset_round_submissions()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self):
        return {
            "host_sid": self.host_sid,
            "players": [p.to_dict() for p in self.players],
        }
