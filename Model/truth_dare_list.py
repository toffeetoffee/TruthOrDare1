import json
import os
from Model.truth_dare import Truth, Dare


class TruthDareList:
    def __init__(self):
        self.truths = []
        self.dares = []
        self._load_defs()

    def _load_defs(self):
        # load from json file, warn if missing 
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            file_path = os.path.join(parent_dir, "default_truths_dares.json")

            with open(file_path, "r") as f:
                data = json.load(f)

            for txt in data.get("truths", []):
                self.truths.append(Truth(txt, is_default=True, submitted_by=None))

            for txt in data.get("dares", []):
                self.dares.append(Dare(txt, is_default=True, submitted_by=None))
        except Exception as e:
            print(f"Warning: Could not load default truths/dares: {e}")

    def set_custom_defaults(self, def_truths, def_dares):
        self.truths = []
        self.dares = []

        for txt in def_truths:
            self.truths.append(Truth(txt, is_default=True, submitted_by=None))

        for txt in def_dares:
            self.dares.append(Dare(txt, is_default=True, submitted_by=None))

    def add_truth(self, text, submitted_by=None):
        self.truths.append(Truth(text, is_default=False, submitted_by=submitted_by))

    def add_dare(self, text, submitted_by=None):
        self.dares.append(Dare(text, is_default=False, submitted_by=submitted_by))

    def remove_truth_by_text(self, text):
        before = len(self.truths)
        self.truths = [t for t in self.truths if t.text != text]
        after = len(self.truths)
        if before != after:
            print(f"[DEBUG] Removed truth: '{text}' -> Remaining: {after}")

    def remove_dare_by_text(self, text):
        before = len(self.dares)
        self.dares = [d for d in self.dares if d.text != text]
        after = len(self.dares)
        if before != after:
            print(f"[DEBUG] Removed dare: '{text}' -> Remaining: {after}")

    def get_truths(self):
        return [t.to_dict() for t in self.truths]

    def get_dares(self):
        return [d.to_dict() for d in self.dares]

    def get_count(self):
        return {"truths": len(self.truths), "dares": len(self.dares)}
