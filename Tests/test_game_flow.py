"""
Tests for Game Flow and Phases
Related User Stories: US-008 to US-017
"""
import pytest
from datetime import datetime, timedelta
from Model.game_state import GameState
from Model.round_record import RoundRecord


@pytest.fixture
def game_state():
    """Fixture to provide a fresh GameState instance"""
    return GameState()


class TestGameStateInitialization:
    """Tests for game state initialization"""
    
    def test_gf_001_initial_state_is_lobby(self, game_state):
        """
        Test ID: GF-001
        User Story: US-008
        Description: Verify that game starts in lobby phase
        Acceptance Criteria: Initial phase is 'lobby', not started
        """
        assert game_state.phase == GameState.PHASE_LOBBY
        assert not game_state.started
        assert game_state.current_round == 0
    
    def test_gf_002_initial_values(self, game_state):
        """
        Test ID: GF-002
        User Story: US-008
        Description: Verify that game state initializes with correct defaults
        Acceptance Criteria: All state variables have correct initial values
        """
        assert game_state.phase_end_time is None
        assert game_state.selected_player is None
        assert game_state.selected_choice is None
        assert game_state.current_truth_dare is None
        assert game_state.minigame is None
        assert len(game_state.skip_votes) == 0
        assert not game_state.skip_activated
        assert not game_state.list_empty
        assert game_state.max_rounds == 10


class TestCountdownPhase:
    """Tests for countdown phase (US-009)"""
    
    def test_gf_003_start_countdown(self, game_state):
        """
        Test ID: GF-003
        User Story: US-009
        Description: Verify that countdown phase can be started
        Acceptance Criteria: Phase changes to countdown, timer is set, game is started
        """
        game_state.start_countdown(duration=10)
        
        assert game_state.phase == GameState.PHASE_COUNTDOWN
        assert game_state.started
        assert game_state.phase_end_time is not None
    
    def test_gf_004_countdown_duration(self, game_state):
        """
        Test ID: GF-004
        User Story: US-009
        Description: Verify that countdown timer is set correctly
        Acceptance Criteria: Remaining time matches configured duration
        """
        game_state.start_countdown(duration=15)
        
        remaining = game_state.get_remaining_time()
        assert 14 <= remaining <= 15  # Allow for small timing variations
    
    def test_gf_005_countdown_custom_duration(self, game_state):
        """
        Test ID: GF-005
        User Story: US-046
        Description: Verify that countdown can use custom duration
        Acceptance Criteria: Custom duration is applied correctly
        """
        game_state.start_countdown(duration=5)
        
        remaining = game_state.get_remaining_time()
        assert 4 <= remaining <= 5


class TestPreparationPhase:
    """Tests for preparation phase (US-010)"""
    
    def test_gf_006_start_preparation(self, game_state):
        """
        Test ID: GF-006
        User Story: US-010
        Description: Verify that preparation phase can be started
        Acceptance Criteria: Phase changes to preparation, timer is set, round increments
        """
        initial_round = game_state.current_round
        
        game_state.start_preparation(duration=30)
        
        assert game_state.phase == GameState.PHASE_PREPARATION
        assert game_state.phase_end_time is not None
        assert game_state.current_round == initial_round + 1
    
    def test_gf_007_preparation_resets_round_data(self, game_state):
        """
        Test ID: GF-007
        User Story: US-010
        Description: Verify that preparation phase resets round-specific data
        Acceptance Criteria: Selected player, choice, minigame, and votes are cleared
        """
        # Set some data
        game_state.selected_player = "Alice"
        game_state.selected_choice = "truth"
        game_state.current_truth_dare = {"text": "test"}
        game_state.add_skip_vote("socket_1")
        
        game_state.start_preparation(duration=30)
        
        assert game_state.selected_player is None
        assert game_state.selected_choice is None
        assert game_state.current_truth_dare is None
        assert game_state.minigame is None
        assert len(game_state.skip_votes) == 0
    
    def test_gf_008_preparation_custom_duration(self, game_state):
        """
        Test ID: GF-008
        User Story: US-046
        Description: Verify that preparation can use custom duration
        Acceptance Criteria: Custom duration is applied correctly
        """
        game_state.start_preparation(duration=60)
        
        remaining = game_state.get_remaining_time()
        assert 59 <= remaining <= 60


class TestSelectionPhase:
    """Tests for selection phase (US-011, US-012, US-013)"""
    
    def test_gf_009_start_selection(self, game_state):
        """
        Test ID: GF-009
        User Story: US-011
        Description: Verify that selection phase can be started
        Acceptance Criteria: Phase changes to selection, timer is set
        """
        game_state.start_selection(duration=10)
        
        assert game_state.phase == GameState.PHASE_SELECTION
        assert game_state.phase_end_time is not None
    
    def test_gf_010_set_selected_player(self, game_state):
        """
        Test ID: GF-010
        User Story: US-011
        Description: Verify that selected player can be set
        Acceptance Criteria: selected_player is updated correctly
        """
        game_state.set_selected_player("Alice")
        
        assert game_state.selected_player == "Alice"
    
    def test_gf_011_set_selected_choice(self, game_state):
        """
        Test ID: GF-011
        User Story: US-012
        Description: Verify that player's choice can be recorded
        Acceptance Criteria: selected_choice is set to 'truth' or 'dare'
        """
        game_state.set_selected_choice("truth")
        assert game_state.selected_choice == "truth"
        
        game_state.set_selected_choice("dare")
        assert game_state.selected_choice == "dare"
    
    def test_gf_012_selection_clears_choice(self, game_state):
        """
        Test ID: GF-012
        User Story: US-011
        Description: Verify that starting selection clears previous choice
        Acceptance Criteria: selected_choice is None at start of selection
        """
        game_state.selected_choice = "truth"
        
        game_state.start_selection(duration=10)
        
        assert game_state.selected_choice is None


class TestTruthDarePhase:
    """Tests for truth/dare performance phase (US-014, US-015)"""
    
    def test_gf_013_start_truth_dare(self, game_state):
        """
        Test ID: GF-013
        User Story: US-014
        Description: Verify that truth/dare phase can be started
        Acceptance Criteria: Phase changes to truth_dare, timer is set, skip votes cleared
        """
        game_state.add_skip_vote("socket_1")
        
        game_state.start_truth_dare(duration=60)
        
        assert game_state.phase == GameState.PHASE_TRUTH_DARE
        assert game_state.phase_end_time is not None
        assert len(game_state.skip_votes) == 0
        assert not game_state.skip_activated
        assert not game_state.list_empty
    
    def test_gf_014_set_current_truth_dare(self, game_state):
        """
        Test ID: GF-014
        User Story: US-014
        Description: Verify that current truth/dare can be set
        Acceptance Criteria: current_truth_dare is updated with dict
        """
        truth_dare = {
            'text': 'What is your biggest fear?',
            'type': 'truth',
            'is_default': True,
            'submitted_by': None
        }
        
        game_state.set_current_truth_dare(truth_dare)
        
        assert game_state.current_truth_dare == truth_dare
    
    def test_gf_015_truth_dare_custom_duration(self, game_state):
        """
        Test ID: GF-015
        User Story: US-046
        Description: Verify that truth/dare can use custom duration
        Acceptance Criteria: Custom duration is applied correctly
        """
        game_state.start_truth_dare(duration=120)
        
        remaining = game_state.get_remaining_time()
        assert 119 <= remaining <= 120


class TestMinigamePhase:
    """Tests for minigame phase (US-018)"""
    
    def test_gf_016_start_minigame(self, game_state):
        """
        Test ID: GF-016
        User Story: US-018
        Description: Verify that minigame phase can be started
        Acceptance Criteria: Phase changes to minigame, no time limit
        """
        game_state.start_minigame()
        
        assert game_state.phase == GameState.PHASE_MINIGAME
        assert game_state.phase_end_time is None
    
    def test_gf_017_set_minigame(self, game_state):
        """
        Test ID: GF-017
        User Story: US-018
        Description: Verify that minigame object can be set
        Acceptance Criteria: minigame is stored in game state
        """
        from Model.minigame import StaringContest
        minigame = StaringContest()
        
        game_state.set_minigame(minigame)
        
        assert game_state.minigame is not None
        assert isinstance(game_state.minigame, StaringContest)


class TestEndGamePhase:
    """Tests for end game phase (US-016, US-017)"""
    
    def test_gf_018_start_end_game(self, game_state):
        """
        Test ID: GF-018
        User Story: US-016
        Description: Verify that end game phase can be started
        Acceptance Criteria: Phase changes to end_game, no time limit
        """
        game_state.start_end_game()
        
        assert game_state.phase == GameState.PHASE_END_GAME
        assert game_state.phase_end_time is None
    
    def test_gf_019_should_end_game_at_max_rounds(self, game_state):
        """
        Test ID: GF-019
        User Story: US-016
        Description: Verify that game ends after max rounds
        Acceptance Criteria: should_end_game() returns True at max_rounds
        """
        game_state.max_rounds = 10
        game_state.current_round = 9
        
        assert not game_state.should_end_game()
        
        game_state.current_round = 10
        assert game_state.should_end_game()
        
        game_state.current_round = 11
        assert game_state.should_end_game()
    
    def test_gf_020_custom_max_rounds(self, game_state):
        """
        Test ID: GF-020
        User Story: US-047
        Description: Verify that custom max rounds can be set
        Acceptance Criteria: Game ends after custom number of rounds
        """
        game_state.max_rounds = 5
        game_state.current_round = 5
        
        assert game_state.should_end_game()


class TestRoundProgression:
    """Tests for round progression (US-015)"""
    
    def test_gf_021_round_counter_increments(self, game_state):
        """
        Test ID: GF-021
        User Story: US-015
        Description: Verify that round counter increments each preparation phase
        Acceptance Criteria: current_round increases by 1 each time
        """
        assert game_state.current_round == 0
        
        game_state.start_preparation(duration=30)
        assert game_state.current_round == 1
        
        game_state.start_preparation(duration=30)
        assert game_state.current_round == 2
    
    def test_gf_022_phase_complete_check(self, game_state):
        """
        Test ID: GF-022
        User Story: US-015
        Description: Verify that phase completion can be checked
        Acceptance Criteria: is_phase_complete() returns correct boolean
        """
        # No end time set
        assert not game_state.is_phase_complete()
        
        # Set end time in the past
        game_state.phase_end_time = datetime.now() - timedelta(seconds=1)
        assert game_state.is_phase_complete()
        
        # Set end time in the future
        game_state.phase_end_time = datetime.now() + timedelta(seconds=10)
        assert not game_state.is_phase_complete()
    
    def test_gf_023_get_remaining_time(self, game_state):
        """
        Test ID: GF-023
        User Story: US-015
        Description: Verify that remaining time can be calculated
        Acceptance Criteria: get_remaining_time() returns seconds left
        """
        # No end time
        assert game_state.get_remaining_time() == 0
        
        # 10 seconds in future
        game_state.phase_end_time = datetime.now() + timedelta(seconds=10)
        remaining = game_state.get_remaining_time()
        assert 9 <= remaining <= 10
        
        # Past time should return 0
        game_state.phase_end_time = datetime.now() - timedelta(seconds=5)
        assert game_state.get_remaining_time() == 0


class TestGameRestart:
    """Tests for game restart (US-017)"""
    
    def test_gf_024_reset_for_new_game(self, game_state):
        """
        Test ID: GF-024
        User Story: US-017
        Description: Verify that game state can be reset for new game
        Acceptance Criteria: All state variables are reset to initial values
        """
        # Set up a game in progress
        game_state.start_countdown(duration=10)
        game_state.start_preparation(duration=30)
        game_state.current_round = 5
        game_state.set_selected_player("Alice")
        game_state.set_selected_choice("truth")
        game_state.add_skip_vote("socket_1")
        game_state.activate_skip()
        
        # Reset
        game_state.reset_for_new_game()
        
        assert game_state.phase == GameState.PHASE_COUNTDOWN
        assert game_state.phase_end_time is None
        assert not game_state.started
        assert game_state.selected_player is None
        assert game_state.selected_choice is None
        assert game_state.current_truth_dare is None
        assert game_state.minigame is None
        assert len(game_state.skip_votes) == 0
        assert game_state.current_round == 0
    
    def test_gf_025_reset_preserves_max_rounds(self, game_state):
        """
        Test ID: GF-025
        User Story: US-017
        Description: Verify that max_rounds setting is preserved on reset
        Acceptance Criteria: max_rounds remains the same after reset
        """
        game_state.max_rounds = 15
        
        game_state.reset_for_new_game()
        
        assert game_state.max_rounds == 15


class TestSkipMechanism:
    """Tests for skip voting within game state (US-053 to US-058)"""
    
    def test_gf_026_add_skip_vote(self, game_state):
        """
        Test ID: GF-026
        User Story: US-053
        Description: Verify that skip votes can be recorded
        Acceptance Criteria: Vote is added to skip_votes set
        """
        game_state.add_skip_vote("socket_1")
        
        assert "socket_1" in game_state.skip_votes
        assert game_state.get_skip_vote_count() == 1
    
    def test_gf_027_skip_vote_no_duplicates(self, game_state):
        """
        Test ID: GF-027
        User Story: US-055
        Description: Verify that same player cannot vote twice
        Acceptance Criteria: Duplicate votes are ignored (set behavior)
        """
        game_state.add_skip_vote("socket_1")
        game_state.add_skip_vote("socket_1")
        game_state.add_skip_vote("socket_1")
        
        assert game_state.get_skip_vote_count() == 1
    
    def test_gf_028_multiple_skip_votes(self, game_state):
        """
        Test ID: GF-028
        User Story: US-053
        Description: Verify that multiple players can vote to skip
        Acceptance Criteria: All unique votes are counted
        """
        game_state.add_skip_vote("socket_1")
        game_state.add_skip_vote("socket_2")
        game_state.add_skip_vote("socket_3")
        
        assert game_state.get_skip_vote_count() == 3
    
    def test_gf_029_activate_skip(self, game_state):
        """
        Test ID: GF-029
        User Story: US-056
        Description: Verify that skip can be activated
        Acceptance Criteria: skip_activated is set to True
        """
        assert not game_state.skip_activated
        
        game_state.activate_skip()
        
        assert game_state.skip_activated
    
    def test_gf_030_reduce_timer(self, game_state):
        """
        Test ID: GF-030
        User Story: US-056
        Description: Verify that timer can be reduced on skip activation
        Acceptance Criteria: Timer is reduced to specified seconds
        """
        game_state.start_truth_dare(duration=60)
        
        game_state.reduce_timer(seconds=5)
        
        remaining = game_state.get_remaining_time()
        assert 4 <= remaining <= 5
    
    def test_gf_031_skip_votes_cleared_each_round(self, game_state):
        """
        Test ID: GF-031
        User Story: US-053
        Description: Verify that skip votes are cleared when starting truth/dare
        Acceptance Criteria: skip_votes is empty at start of new truth/dare phase
        """
        game_state.add_skip_vote("socket_1")
        game_state.add_skip_vote("socket_2")
        
        game_state.start_truth_dare(duration=60)
        
        assert len(game_state.skip_votes) == 0
        assert not game_state.skip_activated


class TestEmptyListHandling:
    """Tests for empty list handling (US-037)"""
    
    def test_gf_032_list_empty_flag(self, game_state):
        """
        Test ID: GF-032
        User Story: US-037
        Description: Verify that list_empty flag can be set
        Acceptance Criteria: list_empty is accessible and modifiable
        """
        assert not game_state.list_empty
        
        game_state.list_empty = True
        
        assert game_state.list_empty
    
    def test_gf_033_list_empty_cleared_on_preparation(self, game_state):
        """
        Test ID: GF-033
        User Story: US-037
        Description: Verify that list_empty is cleared when starting preparation
        Acceptance Criteria: list_empty is False at start of preparation (implicitly tested in start_preparation)
        """
        game_state.list_empty = True
        
        game_state.start_preparation(duration=30)
        
        # list_empty should be cleared via reset round data
        assert not game_state.list_empty


class TestGameStateSerialization:
    """Tests for game state to dictionary conversion"""
    
    def test_gf_034_to_dict_basic(self, game_state):
        """
        Test ID: GF-034
        User Story: US-059
        Description: Verify that game state can be converted to dictionary
        Acceptance Criteria: to_dict() returns dict with all key fields
        """
        game_state.start_preparation(duration=30)
        game_state.set_selected_player("Alice")
        
        state_dict = game_state.to_dict()
        
        assert 'phase' in state_dict
        assert 'remaining_time' in state_dict
        assert 'started' in state_dict
        assert 'selected_player' in state_dict
        assert 'selected_choice' in state_dict
        assert 'current_truth_dare' in state_dict
        assert 'skip_vote_count' in state_dict
        assert 'skip_activated' in state_dict
        assert 'list_empty' in state_dict
        assert 'current_round' in state_dict
        assert 'max_rounds' in state_dict
    
    def test_gf_035_to_dict_with_minigame(self, game_state):
        """
        Test ID: GF-035
        User Story: US-059
        Description: Verify that game state dict includes minigame data
        Acceptance Criteria: minigame field is included when minigame is active
        """
        from Model.minigame import StaringContest
        minigame = StaringContest()
        game_state.set_minigame(minigame)
        
        state_dict = game_state.to_dict()
        
        assert 'minigame' in state_dict
        assert state_dict['minigame'] is not None


class TestRoundRecord:
    """Tests for round record keeping (US-044)"""
    
    def test_gf_036_round_record_creation(self):
        """
        Test ID: GF-036
        User Story: US-044
        Description: Verify that round records can be created
        Acceptance Criteria: RoundRecord stores all required information
        """
        record = RoundRecord(
            round_number=1,
            selected_player_name="Alice",
            truth_dare_text="What is your biggest fear?",
            truth_dare_type="truth",
            submitted_by="Bob"
        )
        
        assert record.round_number == 1
        assert record.selected_player_name == "Alice"
        assert record.truth_dare_text == "What is your biggest fear?"
        assert record.truth_dare_type == "truth"
        assert record.submitted_by == "Bob"
    
    def test_gf_037_round_record_default_submission(self):
        """
        Test ID: GF-037
        User Story: US-044
        Description: Verify that round records can mark default content
        Acceptance Criteria: submitted_by is None for default content
        """
        record = RoundRecord(
            round_number=2,
            selected_player_name="Charlie",
            truth_dare_text="Do 10 pushups",
            truth_dare_type="dare",
            submitted_by=None
        )
        
        assert record.submitted_by is None
    
    def test_gf_038_round_record_to_dict(self):
        """
        Test ID: GF-038
        User Story: US-044
        Description: Verify that round records can be converted to dict
        Acceptance Criteria: to_dict() returns properly formatted dictionary
        """
        record = RoundRecord(
            round_number=3,
            selected_player_name="Diana",
            truth_dare_text="Sing a song loudly",
            truth_dare_type="dare",
            submitted_by="Alice"
        )
        
        record_dict = record.to_dict()
        
        assert record_dict['round_number'] == 3
        assert record_dict['selected_player'] == "Diana"
        assert record_dict['truth_dare']['text'] == "Sing a song loudly"
        assert record_dict['truth_dare']['type'] == "dare"
        assert record_dict['submitted_by'] == "Alice"
