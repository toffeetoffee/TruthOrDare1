class TruthDare:
    def __init__(self, text, is_default=False, submitted_by=None):
        self.text = text
        self.is_default = is_default
        self.submitted_by = submitted_by   # who added it (None = default)

    def to_dict(self):
        return {
            "text": self.text,
            "is_default": self.is_default,
            "submitted_by": self.submitted_by
        }


class Truth(TruthDare):
    def __init__(self, text, is_default=False, submitted_by=None):
        super().__init__(text, is_default, submitted_by)
        self.type = "truth"


class Dare(TruthDare):
    def __init__(self, text, is_default=False, submitted_by=None):
        super().__init__(text, is_default, submitted_by)
        self.type = "dare"
