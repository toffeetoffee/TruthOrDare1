# Model/truth_dare_list.py
import json
import os
from Model.truth_dare import Truth, Dare


class TruthDareList:
    """Manages truths and dares for a player."""

    def __init__(self):
        self.truths = []
        self.dares = []
        self._load_defaults()

    # ------------------------------------------------------------------
    # Load and set defaults
    # ------------------------------------------------------------------
    def _load_defaults(self):
        """Load default truths and dares from file."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            file_path = os.path.join(parent_dir, "default_truths_dares.json")

            with open(file_path, "r") as f:
                data = json.load(f)

            for text in data.get("truths", []):
                self.truths.append(Truth(text, is_default=True, submitted_by=None))

            for text in data.get("dares", []):
                self.dares.append(Dare(text, is_default=True, submitted_by=None))
        except Exception as e:
            print(f"Warning: Could not load default truths/dares: {e}")

    def set_custom_defaults(self, default_truths_list, default_dares_list):
        """Set custom defaults instead of loading from file."""
        self.truths = []
        self.dares = []

        for text in default_truths_list:
            self.truths.append(Truth(text, is_default=True, submitted_by=None))

        for text in default_dares_list:
            self.dares.append(Dare(text, is_default=True, submitted_by=None))

    # ------------------------------------------------------------------
    # Add / remove items
    # ------------------------------------------------------------------
    def add_truth(self, text, submitted_by=None):
        """Add a custom truth."""
        self.truths.append(Truth(text, is_default=False, submitted_by=submitted_by))

    def add_dare(self, text, submitted_by=None):
        """Add a custom dare."""
        self.dares.append(Dare(text, is_default=False, submitted_by=submitted_by))

    def remove_truth_by_text(self, text):
        """Remove a truth by its text value."""
        before = len(self.truths)
        self.truths = [t for t in self.truths if t.text != text]
        after = len(self.truths)
        if before != after:
            print(f"[DEBUG] Removed truth: '{text}' -> Remaining: {after}")

    def remove_dare_by_text(self, text):
        """Remove a dare by its text value."""
        before = len(self.dares)
        self.dares = [d for d in self.dares if d.text != text]
        after = len(self.dares)
        if before != after:
            print(f"[DEBUG] Removed dare: '{text}' -> Remaining: {after}")

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    def get_truths(self):
        """Get all truths as list of dicts."""
        return [t.to_dict() for t in self.truths]

    def get_dares(self):
        """Get all dares as list of dicts."""
        return [d.to_dict() for d in self.dares]

    def get_count(self):
        """Get count of truths and dares."""
        return {"truths": len(self.truths), "dares": len(self.dares)}
