"""
Round record class for tracking game history.
"""


class RoundRecord:
    """Records information about a completed round"""
    
    def __init__(self, round_number, selected_player_name, truth_dare_text, truth_dare_type, submitted_by=None):
        """
        Args:
            round_number: The round number
            selected_player_name: Name of player who performed
            truth_dare_text: The actual truth/dare text
            truth_dare_type: 'truth' or 'dare'
            submitted_by: Name of player who submitted it (None if default)
        """
        self.round_number = round_number
        self.selected_player_name = selected_player_name
        self.truth_dare_text = truth_dare_text
        self.truth_dare_type = truth_dare_type
        self.submitted_by = submitted_by
    
    def to_dict(self):
        """Convert to dictionary format"""
        return {
            'round_number': self.round_number,
            'selected_player': self.selected_player_name,
            'truth_dare': {
                'text': self.truth_dare_text,
                'type': self.truth_dare_type
            },
            'submitted_by': self.submitted_by
        }