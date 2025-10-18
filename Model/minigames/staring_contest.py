"""
Staring contest minigame implementation.
"""

from Model.minigames.minigame import Minigame


class StaringContest(Minigame):
    """Staring contest minigame - vote for who blinked first"""
    
    def __init__(self):
        super().__init__()
        self.name = "Staring Contest"
        self.description = "Who will blink first?"
    
    def to_dict(self):
        """Convert to dictionary format"""
        result = super().to_dict()
        result['type'] = 'staring_contest'
        return result