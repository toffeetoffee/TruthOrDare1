"""
Truth question class.
"""

from Model.content.truth_dare import TruthDare


class Truth(TruthDare):
    """Represents a truth question"""
    
    def __init__(self, text, is_default=False, submitted_by=None):
        super().__init__(text, is_default, submitted_by)
        self.type = 'truth'