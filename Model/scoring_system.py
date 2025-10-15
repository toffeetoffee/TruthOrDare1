class ScoringSystem:
    """Defines scoring rules and point values"""
    
    # Point values (highest to lowest)
    POINTS_PERFORM = 100  # Performing a truth/dare
    POINTS_MINIGAME_PARTICIPATION = 75  # Participating in a minigame
    POINTS_SUBMITTED_PERFORMED = 50  # Your submission gets performed
    POINTS_SUBMISSION = 10  # Submitting a truth/dare
    
    # Limits
    MAX_SUBMISSIONS_PER_ROUND = 3  # Max submissions per player per round
    
    @staticmethod
    def award_perform_points(player):
        """Award points for performing a truth/dare"""
        player.add_score(ScoringSystem.POINTS_PERFORM)
    
    @staticmethod
    def award_minigame_participation_points(player):
        """Award points for participating in a minigame"""
        player.add_score(ScoringSystem.POINTS_MINIGAME_PARTICIPATION)
    
    @staticmethod
    def award_submission_performed_points(player):
        """Award points when your submission is performed"""
        player.add_score(ScoringSystem.POINTS_SUBMITTED_PERFORMED)
    
    @staticmethod
    def award_submission_points(player):
        """Award points for submitting a truth/dare"""
        player.add_score(ScoringSystem.POINTS_SUBMISSION)