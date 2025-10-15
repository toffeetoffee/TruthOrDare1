from datetime import datetime, timedelta

class GameState:
    """Tracks the current game state"""
    
    PHASE_LOBBY = 'lobby'
    PHASE_COUNTDOWN = 'countdown'
    PHASE_PREPARATION = 'preparation'
    PHASE_MINIGAME = 'minigame'
    PHASE_SELECTION = 'selection'
    PHASE_TRUTH_DARE = 'truth_dare'
    PHASE_END_GAME = 'end_game'
    
    def __init__(self):
        self.phase = self.PHASE_LOBBY
        self.phase_end_time = None
        self.started = False
        self.selected_player = None
        self.selected_choice = None  # 'truth', 'dare', or None
        self.current_truth_dare = None  # The actual truth/dare being performed
        self.minigame = None  # Current minigame instance
        self.skip_votes = set()  # Set of player socket IDs who voted to skip
        self.skip_activated = False  # Whether skip has been activated this round
        
        # Round tracking
        self.current_round = 0
        self.max_rounds = 10  # Default, can be configured
    
    def start_countdown(self, duration=10):
        """Start the countdown phase"""
        self.phase = self.PHASE_COUNTDOWN
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
        self.started = True
    
    def start_preparation(self, duration=30):
        """Start the preparation phase"""
        self.phase = self.PHASE_PREPARATION
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
        # Reset round data
        self.selected_player = None
        self.selected_choice = None
        self.current_truth_dare = None
        self.minigame = None
        self.skip_votes.clear()
        # Increment round
        self.current_round += 1
    
    def start_minigame(self):
        """Start the minigame phase (no time limit)"""
        self.phase = self.PHASE_MINIGAME
        self.phase_end_time = None  # No time limit
    
    def start_selection(self, duration=10):
        """Start the selection phase"""
        self.phase = self.PHASE_SELECTION
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
        self.selected_choice = None
    
    def start_truth_dare(self, duration=60):
        """Start the truth or dare phase"""
        self.phase = self.PHASE_TRUTH_DARE
        self.phase_end_time = datetime.now() + timedelta(seconds=duration)
        self.skip_votes.clear()
        self.skip_activated = False
    
    def start_end_game(self):
        """Start the end game phase"""
        self.phase = self.PHASE_END_GAME
        self.phase_end_time = None
    
    def set_selected_player(self, player_name):
        """Set the selected player for this round"""
        self.selected_player = player_name
    
    def set_selected_choice(self, choice):
        """Set whether the player chose truth or dare"""
        self.selected_choice = choice
    
    def set_current_truth_dare(self, truth_dare_dict):
        """Set the current truth/dare being performed"""
        self.current_truth_dare = truth_dare_dict
    
    def set_minigame(self, minigame):
        """Set the current minigame"""
        self.minigame = minigame
    
    def add_skip_vote(self, player_sid):
        """Add a vote to skip the current truth/dare"""
        self.skip_votes.add(player_sid)
    
    def activate_skip(self):
        """Mark skip as activated"""
        self.skip_activated = True
    
    def get_skip_vote_count(self):
        """Get the number of skip votes"""
        return len(self.skip_votes)
    
    def reduce_timer(self, seconds=5):
        """Reduce the timer to a specific number of seconds"""
        self.phase_end_time = datetime.now() + timedelta(seconds=seconds)
    
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
    
    def should_end_game(self):
        """Check if game should end (max rounds reached)"""
        return self.current_round >= self.max_rounds
    
    def reset_for_new_game(self):
        """Reset state for a new game"""
        self.phase = self.PHASE_COUNTDOWN
        self.phase_end_time = None
        self.started = False
        self.selected_player = None
        self.selected_choice = None
        self.current_truth_dare = None
        self.minigame = None
        self.skip_votes.clear()
        self.current_round = 0
    
    def to_dict(self):
        """Convert to dictionary"""
        base_dict = {
            'phase': self.phase,
            'remaining_time': self.get_remaining_time(),
            'started': self.started,
            'selected_player': self.selected_player,
            'selected_choice': self.selected_choice,
            'current_truth_dare': self.current_truth_dare,
            'skip_vote_count': self.get_skip_vote_count(),
            'skip_activated': self.skip_activated,
            'current_round': self.current_round,
            'max_rounds': self.max_rounds
        }
        
        # Add minigame data if active
        if self.minigame:
            base_dict['minigame'] = self.minigame.to_dict()
        
        return base_dict