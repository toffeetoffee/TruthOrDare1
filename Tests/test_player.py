"""
Tests for Player functionality
Related User Stories: US-003, US-023, US-024, US-025, US-026, US-027, US-028, US-039-US-044
"""
import pytest
from Model.player import Player
from Model.truth_dare import Truth, Dare
from Model.scoring_system import ScoringSystem


@pytest.fixture
def player():
    """Fixture to provide a player instance"""
    return Player('socket_123', 'TestPlayer')


@pytest.fixture
def player_with_content(player):
    """Fixture to provide a player with some content"""
    player.truth_dare_list.add_truth("What's your favorite color?", submitted_by="Alice")
    player.truth_dare_list.add_truth("Have you ever lied to your best friend?", submitted_by="Bob")
    player.truth_dare_list.add_dare("Do 10 jumping jacks", submitted_by="Alice")
    player.truth_dare_list.add_dare("Sing a song", submitted_by="Charlie")
    return player


class TestPlayerInitialization:
    """Tests for player initialization"""
    
    def test_pl_001_player_creation(self):
        """
        Test ID: PL-001
        User Story: US-002
        Description: Verify that a player can be created with socket ID and name
        Acceptance Criteria: Player has correct socket_id, name, and initial values
        """
        player = Player('socket_123', 'Alice')
        
        assert player.socket_id == 'socket_123'
        assert player.name == 'Alice'
        assert player.score == 0
        assert player.submissions_this_round == 0
    
    def test_pl_002_player_has_truth_dare_list(self, player):
        """
        Test ID: PL-002
        User Story: US-007, US-028
        Description: Verify that player has a truth/dare list upon creation
        Acceptance Criteria: Player has truth_dare_list with default content
        """
        assert player.truth_dare_list is not None
        
        truths = player.truth_dare_list.get_truths()
        dares = player.truth_dare_list.get_dares()
        
        assert len(truths) > 0
        assert len(dares) > 0


class TestPlayerScoring:
    """Tests for player scoring system (US-039 to US-044)"""
    
    def test_pl_003_add_score(self, player):
        """
        Test ID: PL-003
        User Story: US-039, US-040, US-041, US-042
        Description: Verify that scores can be added to player
        Acceptance Criteria: Player's score increases by the added amount
        """
        initial_score = player.score
        
        player.add_score(100)
        assert player.score == initial_score + 100
        
        player.add_score(50)
        assert player.score == initial_score + 150
    
    def test_pl_004_perform_points(self, player):
        """
        Test ID: PL-004
        User Story: US-039
        Description: Verify that performing truth/dare awards 100 points
        Acceptance Criteria: Player receives 100 points for performing
        """
        ScoringSystem.award_perform_points(player)
        
        assert player.score == 100
    
    def test_pl_005_minigame_participate_points(self, player):
        """
        Test ID: PL-005
        User Story: US-040
        Description: Verify that minigame participation awards 75 points
        Acceptance Criteria: Player receives 75 points for participating
        """
        ScoringSystem.award_minigame_participate_points(player)
        
        assert player.score == 75
    
    def test_pl_006_submission_performed_points(self, player):
        """
        Test ID: PL-006
        User Story: US-041
        Description: Verify that having submission performed awards 50 points
        Acceptance Criteria: Player receives 50 points when their submission is performed
        """
        ScoringSystem.award_submission_performed_points(player)
        
        assert player.score == 50
    
    def test_pl_007_submission_points(self, player):
        """
        Test ID: PL-007
        User Story: US-042
        Description: Verify that submitting content awards 10 points
        Acceptance Criteria: Player receives 10 points for each submission
        """
        ScoringSystem.award_submission_points(player)
        
        assert player.score == 10
    
    def test_pl_008_cumulative_scoring(self, player):
        """
        Test ID: PL-008
        User Story: US-042, US-043
        Description: Verify that scores accumulate correctly
        Acceptance Criteria: Multiple point awards accumulate properly
        """
        ScoringSystem.award_submission_points(player)  # +10
        ScoringSystem.award_submission_points(player)  # +10
        ScoringSystem.award_perform_points(player)     # +100
        ScoringSystem.award_submission_performed_points(player)  # +50
        
        assert player.score == 170


class TestSubmissionManagement:
    """Tests for submission tracking (US-023, US-024, US-025)"""
    
    def test_pl_009_reset_round_submissions(self, player):
        """
        Test ID: PL-009
        User Story: US-010, US-023
        Description: Verify that submission counter resets for new rounds
        Acceptance Criteria: submissions_this_round is set to 0
        """
        player.submissions_this_round = 3
        
        player.reset_round_submissions()
        
        assert player.submissions_this_round == 0
    
    def test_pl_010_increment_submissions(self, player):
        """
        Test ID: PL-010
        User Story: US-023, US-024
        Description: Verify that submission counter increments
        Acceptance Criteria: submissions_this_round increases by 1
        """
        assert player.submissions_this_round == 0
        
        player.increment_submissions()
        assert player.submissions_this_round == 1
        
        player.increment_submissions()
        assert player.submissions_this_round == 2
    
    def test_pl_011_can_submit_more_within_limit(self, player):
        """
        Test ID: PL-011
        User Story: US-025
        Description: Verify that player can submit when under limit
        Acceptance Criteria: can_submit_more() returns True when < 3 submissions
        """
        assert player.can_submit_more()
        
        player.increment_submissions()
        assert player.can_submit_more()
        
        player.increment_submissions()
        assert player.can_submit_more()
    
    def test_pl_012_cannot_submit_at_limit(self, player):
        """
        Test ID: PL-012
        User Story: US-025
        Description: Verify that player cannot submit after reaching limit
        Acceptance Criteria: can_submit_more() returns False at 3 submissions
        """
        player.submissions_this_round = 3
        
        assert not player.can_submit_more()
    
    def test_pl_013_submission_limit_constant(self):
        """
        Test ID: PL-013
        User Story: US-025
        Description: Verify that submission limit is set to 3
        Acceptance Criteria: MAX_SUBMISSIONS_PER_ROUND is 3
        """
        assert ScoringSystem.MAX_SUBMISSIONS_PER_ROUND == 3


class TestTruthDareList:
    """Tests for player's truth/dare list management (US-007, US-023, US-024, US-026, US-027)"""
    
    def test_pl_014_add_custom_truth(self, player):
        """
        Test ID: PL-014
        User Story: US-023
        Description: Verify that custom truths can be added to player's list
        Acceptance Criteria: Truth is added with correct attributes
        """
        initial_count = len(player.truth_dare_list.truths)
        
        player.truth_dare_list.add_truth("What's your biggest secret?", submitted_by="Alice")
        
        truths = player.truth_dare_list.get_truths()
        assert len(truths) == initial_count + 1
        
        # Find the added truth
        added_truth = next(t for t in truths if t['text'] == "What's your biggest secret?")
        assert added_truth['is_default'] == False
        assert added_truth['submitted_by'] == "Alice"
    
    def test_pl_015_add_custom_dare(self, player):
        """
        Test ID: PL-015
        User Story: US-024
        Description: Verify that custom dares can be added to player's list
        Acceptance Criteria: Dare is added with correct attributes
        """
        initial_count = len(player.truth_dare_list.dares)
        
        player.truth_dare_list.add_dare("Do a handstand", submitted_by="Bob")
        
        dares = player.truth_dare_list.get_dares()
        assert len(dares) == initial_count + 1
        
        # Find the added dare
        added_dare = next(d for d in dares if d['text'] == "Do a handstand")
        assert added_dare['is_default'] == False
        assert added_dare['submitted_by'] == "Bob"
    
    def test_pl_016_get_truths_as_dicts(self, player_with_content):
        """
        Test ID: PL-016
        User Story: US-026
        Description: Verify that truths can be retrieved as dictionaries
        Acceptance Criteria: get_truths() returns list of truth dictionaries
        """
        truths = player_with_content.truth_dare_list.get_truths()
        
        assert isinstance(truths, list)
        assert len(truths) > 0
        
        for truth in truths:
            assert 'text' in truth
            assert 'is_default' in truth
            assert 'submitted_by' in truth
    
    def test_pl_017_get_dares_as_dicts(self, player_with_content):
        """
        Test ID: PL-017
        User Story: US-026
        Description: Verify that dares can be retrieved as dictionaries
        Acceptance Criteria: get_dares() returns list of dare dictionaries
        """
        dares = player_with_content.truth_dare_list.get_dares()
        
        assert isinstance(dares, list)
        assert len(dares) > 0
        
        for dare in dares:
            assert 'text' in dare
            assert 'is_default' in dare
            assert 'submitted_by' in dare
    
    def test_pl_018_get_count(self, player_with_content):
        """
        Test ID: PL-018
        User Story: US-007
        Description: Verify that truth/dare counts can be retrieved
        Acceptance Criteria: get_count() returns dict with truths and dares counts
        """
        count = player_with_content.truth_dare_list.get_count()
        
        assert 'truths' in count
        assert 'dares' in count
        assert count['truths'] > 0
        assert count['dares'] > 0
    
    def test_pl_019_item_removed_after_use(self, player_with_content):
        """
        Test ID: PL-019
        User Story: US-027
        Description: Verify that truth/dare items can be removed from list
        Acceptance Criteria: Item is removed from the appropriate list
        """
        truths = player_with_content.truth_dare_list.truths
        initial_count = len(truths)
        
        # Remove first truth
        removed_truth = truths[0]
        truths.remove(removed_truth)
        
        assert len(player_with_content.truth_dare_list.truths) == initial_count - 1
        assert removed_truth not in player_with_content.truth_dare_list.truths
    
    def test_pl_020_set_custom_defaults(self, player):
        """
        Test ID: PL-020
        User Story: US-028
        Description: Verify that custom defaults can be set for player
        Acceptance Criteria: Player's lists are replaced with custom defaults
        """
        custom_truths = ["Custom truth 1", "Custom truth 2"]
        custom_dares = ["Custom dare 1", "Custom dare 2", "Custom dare 3"]
        
        player.truth_dare_list.set_custom_defaults(custom_truths, custom_dares)
        
        truths = player.truth_dare_list.get_truths()
        dares = player.truth_dare_list.get_dares()
        
        assert len(truths) == 2
        assert len(dares) == 3
        
        # All should be marked as defaults
        assert all(t['is_default'] for t in truths)
        assert all(d['is_default'] for d in dares)


class TestPlayerSerialization:
    """Tests for player data conversion"""
    
    def test_pl_021_to_dict(self, player):
        """
        Test ID: PL-021
        User Story: US-003
        Description: Verify that player can be converted to dictionary
        Acceptance Criteria: to_dict() returns dict with sid, name, and score
        """
        player.score = 150
        
        player_dict = player.to_dict()
        
        assert player_dict['sid'] == 'socket_123'
        assert player_dict['name'] == 'TestPlayer'
        assert player_dict['score'] == 150
    
    def test_pl_022_from_dict(self):
        """
        Test ID: PL-022
        User Story: US-003
        Description: Verify that player can be created from dictionary
        Acceptance Criteria: from_dict() creates player with correct attributes
        """
        data = {
            'sid': 'socket_456',
            'name': 'Alice',
            'score': 200
        }
        
        player = Player.from_dict(data)
        
        assert player.socket_id == 'socket_456'
        assert player.name == 'Alice'
        assert player.score == 200
    
    def test_pl_023_from_dict_without_score(self):
        """
        Test ID: PL-023
        User Story: US-003
        Description: Verify that player can be created from dict without score
        Acceptance Criteria: from_dict() sets score to 0 if not provided
        """
        data = {
            'sid': 'socket_789',
            'name': 'Bob'
        }
        
        player = Player.from_dict(data)
        
        assert player.socket_id == 'socket_789'
        assert player.name == 'Bob'
        assert player.score == 0


class TestTruthDareObjects:
    """Tests for Truth and Dare objects"""
    
    def test_pl_024_truth_creation(self):
        """
        Test ID: PL-024
        User Story: US-023
        Description: Verify that Truth objects can be created
        Acceptance Criteria: Truth has text, type, is_default, and submitted_by
        """
        truth = Truth("What's your favorite food?", is_default=False, submitted_by="Alice")
        
        assert truth.text == "What's your favorite food?"
        assert truth.type == 'truth'
        assert truth.is_default == False
        assert truth.submitted_by == "Alice"
    
    def test_pl_025_truth_default_creation(self):
        """
        Test ID: PL-025
        User Story: US-009, US-028
        Description: Verify that default Truth objects can be created
        Acceptance Criteria: Truth marked as default has no submitter
        """
        truth = Truth("Default truth question", is_default=True, submitted_by=None)
        
        assert truth.is_default == True
        assert truth.submitted_by is None
    
    def test_pl_026_dare_creation(self):
        """
        Test ID: PL-026
        User Story: US-024
        Description: Verify that Dare objects can be created
        Acceptance Criteria: Dare has text, type, is_default, and submitted_by
        """
        dare = Dare("Do 20 pushups", is_default=False, submitted_by="Bob")
        
        assert dare.text == "Do 20 pushups"
        assert dare.type == 'dare'
        assert dare.is_default == False
        assert dare.submitted_by == "Bob"
    
    def test_pl_027_dare_default_creation(self):
        """
        Test ID: PL-027
        User Story: US-009, US-028
        Description: Verify that default Dare objects can be created
        Acceptance Criteria: Dare marked as default has no submitter
        """
        dare = Dare("Default dare challenge", is_default=True, submitted_by=None)
        
        assert dare.is_default == True
        assert dare.submitted_by is None
    
    def test_pl_028_truth_to_dict(self):
        """
        Test ID: PL-028
        User Story: US-026
        Description: Verify that Truth can be converted to dictionary
        Acceptance Criteria: to_dict() returns dict with all attributes
        """
        truth = Truth("Test truth?", is_default=False, submitted_by="Alice")
        
        truth_dict = truth.to_dict()
        
        assert truth_dict['text'] == "Test truth?"
        assert truth_dict['is_default'] == False
        assert truth_dict['submitted_by'] == "Alice"
    
    def test_pl_029_dare_to_dict(self):
        """
        Test ID: PL-029
        User Story: US-026
        Description: Verify that Dare can be converted to dictionary
        Acceptance Criteria: to_dict() returns dict with all attributes
        """
        dare = Dare("Test dare", is_default=False, submitted_by="Bob")
        
        dare_dict = dare.to_dict()
        
        assert dare_dict['text'] == "Test dare"
        assert dare_dict['is_default'] == False
        assert dare_dict['submitted_by'] == "Bob"
