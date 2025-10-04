from datetime import datetime, timedelta

class GameState:
    """Tracks the current game state"""
    
    PHASE_LOBBY = 'lobby'
    PHASE_COUNTDOWN = 'countdown'
    PHASE_PREPARATION = 'preparation'
    PHASE_SELECTION = 'selection'
    
    def __init__(self):
        self.phase = self.PHASE_LOBBY
        self.phase_end_time = None
        self.started = False
        self.selected_player = None
        self.event_chance = 0.0  # 0% for now, will be configurable later
    
    def start_countdown(self, duration=10):
        """Start the countdown phase"""
        self.phase = self.PHASE_COUNTDOWN
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
        self.started = True
    
    def start_preparation(self, duration=30):
        """Start the preparation phase"""
        self.phase = self.PHASE_PREPARATION
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
    
    def start_selection(self, duration=10):
        """Start the selection phase"""
        self.phase = self.PHASE_SELECTION
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
    
    def set_selected_player(self, player_name):
        """Set the selected player for this round"""
        self.selected_player = player_name
    
    def get_remaining_time(self):
        """Get remaining time in current phase (in seconds)"""
        if self.phase_end_time is None:
            return 0
        
        remaining = (self.phase_end_time - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def is_phase_complete(self):
        """Check if current phase is complete"""
        if self.phase_end_time is None:
            return False
        return datetime.now() >= self.phase_end_time
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'phase': self.phase,
            'remaining_time': self.get_remaining_time(),
            'started': self.started,
            'selected_player': self.selected_player,
            'event_chance': self.event_chance
        }
