class TruthDare:
    """Base class for truth or dare items"""
    
    def __init__(self, text, is_default=False):
        self.text = text
        self.is_default = is_default
    
    def to_dict(self):
        return {
            'text': self.text,
            'is_default': self.is_default
        }


class Truth(TruthDare):
    """Represents a truth question"""
    
    def __init__(self, text, is_default=False):
        super().__init__(text, is_default)
        self.type = 'truth'


class Dare(TruthDare):
    """Represents a dare challenge"""
    
    def __init__(self, text, is_default=False):
        super().__init__(text, is_default)
        self.type = 'dare'
