"""
Base class for truth or dare items.
"""

class TruthDare:
    """Base class for truth or dare items"""
    
    def __init__(self, text, is_default=False, submitted_by=None):
        """
        Args:
            text: The truth/dare text
            is_default: Whether this is a default truth/dare
            submitted_by: Name of player who submitted (None for defaults)
        """
        self.text = text
        self.is_default = is_default
        self.submitted_by = submitted_by
        self.type = None  # Will be set by subclasses
    
    def to_dict(self):
        """Convert to dictionary format"""
        return {
            'text': self.text,
            'is_default': self.is_default,
            'submitted_by': self.submitted_by,
            'type': self.type
        }