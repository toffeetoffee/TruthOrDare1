class RoundRecord:
    def __init__(self, round_number, selected_player_name,
                 truth_dare_text, truth_dare_type, submitted_by=None):
        # storing what happened in one round
        self.round_number = round_number
        self.selected_player_name = selected_player_name
        self.truth_dare_text = truth_dare_text
        self.truth_dare_type = truth_dare_type   # 'truth' or 'dare'
        self.submitted_by = submitted_by  # None if from defaults

    def to_dict(self):
        return {
            "round_number": self.round_number,
            "selected_player": self.selected_player_name,
            "truth_dare": {
                "text": self.truth_dare_text,
                "type": self.truth_dare_type
            },
            "submitted_by": self.submitted_by
        }
