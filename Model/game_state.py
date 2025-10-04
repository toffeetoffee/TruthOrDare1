from datetime import datetime, timedelta

class GameState:
    """Tracks the current game state"""
    
    PHASE_LOBBY = 'lobby'
    PHASE_COUNTDOWN = 'countdown'
    PHASE_PREPARATION = 'preparation'
    
    def __init__(self):
        self.phase = self.PHASE_LOBBY
        self.phase_end_time = None
        self.started = False
    
    def start_countdown(self, duration=10):
        """Start the countdown phase"""
        self.phase = self.PHASE_COUNTDOWN
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
        self.started = True
    
    def start_preparation(self, duration=30):
        """Start the preparation phase"""
        self.phase = self.PHASE_PREPARATION
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
    
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
            'started': self.started
        }
