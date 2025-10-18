"""
Dare challenge class.
"""

from Model.content.truth_dare import TruthDare


class Dare(TruthDare):
    """Represents a dare challenge"""
    
    def __init__(self, text, is_default=False, submitted_by=None):
        super().__init__(text, is_default, submitted_by)
        self.type = 'dare'