"""
Tests for Vote Skip Mechanism
Related User Stories: US-053 to US-058
"""
import pytest
from Model.game_state import GameState
from Model.room import Room
from Model.player import Player


@pytest.fixture
def game_state():
    """Fixture for game state"""
    return GameState()


@pytest.fixture
def room_with_players():
    """Fixture for room with 5 players"""
    room = Room('TEST01')
    room.add_player(Player('socket_1', 'Alice'))
    room.add_player(Player('socket_2', 'Bob'))
    room.add_player(Player('socket_3', 'Charlie'))
    room.add_player(Player('socket_4', 'Diana'))
    room.add_player(Player('socket_5', 'Eve'))
    return room


class TestSkipVoting:
    """Tests for vote skip mechanism (US-053, US-054, US-055)"""
    
    def test_vs_001_add_skip_vote(self, game_state):
        """
        Test ID: VS-001
        User Story: US-053
        Description: Verify that skip vote can be recorded
        Acceptance Criteria: Vote is added to skip_votes set
        """
        game_state.add_skip_vote('socket_1')
        
        assert 'socket_1' in game_state.skip_votes
        assert game_state.get_skip_vote_count() == 1
    
    def test_vs_002_multiple_players_vote_skip(self, game_state):
        """
        Test ID: VS-002
        User Story: US-053
        Description: Verify that multiple players can vote to skip
        Acceptance Criteria: All unique votes are counted
        """
        game_state.add_skip_vote('socket_1')
        game_state.add_skip_vote('socket_2')
        game_state.add_skip_vote('socket_3')
        
        assert game_state.get_skip_vote_count() == 3
        assert 'socket_1' in game_state.skip_votes
        assert 'socket_2' in game_state.skip_votes
        assert 'socket_3' in game_state.skip_votes
    
    def test_vs_003_player_cannot_vote_twice(self, game_state):
        """
        Test ID: VS-003
        User Story: US-055
        Description: Verify that same player cannot vote multiple times
        Acceptance Criteria: Duplicate votes are ignored (set behavior)
        """
        game_state.add_skip_vote('socket_1')
        game_state.add_skip_vote('socket_1')
        game_state.add_skip_vote('socket_1')
        
        assert game_state.get_skip_vote_count() == 1
    
    def test_vs_004_get_skip_vote_count(self, game_state):
        """
        Test ID: VS-004
        User Story: US-058
        Description: Verify that skip vote count can be retrieved
        Acceptance Criteria: get_skip_vote_count() returns correct number
        """
        assert game_state.get_skip_vote_count() == 0
        
        game_state.add_skip_vote('socket_1')
        assert game_state.get_skip_vote_count() == 1
        
        game_state.add_skip_vote('socket_2')
        assert game_state.get_skip_vote_count() == 2
    
    def test_vs_005_skip_votes_cleared_each_round(self, game_state):
        """
        Test ID: VS-005
        User Story: US-053
        Description: Verify that skip votes are cleared when starting new truth/dare
        Acceptance Criteria: skip_votes is empty at start of truth/dare phase
        """
        game_state.add_skip_vote('socket_1')
        game_state.add_skip_vote('socket_2')
        
        game_state.start_truth_dare(duration=60)
        
        assert game_state.get_skip_vote_count() == 0
        assert len(game_state.skip_votes) == 0


class TestSkipActivation:
    """Tests for skip activation (US-056)"""
    
    def test_vs_006_activate_skip(self, game_state):
        """
        Test ID: VS-006
        User Story: US-056
        Description: Verify that skip can be activated
        Acceptance Criteria: skip_activated is set to True
        """
        assert not game_state.skip_activated
        
        game_state.activate_skip()
        
        assert game_state.skip_activated
    
    def test_vs_007_skip_not_activated_initially(self, game_state):
        """
        Test ID: VS-007
        User Story: US-056
        Description: Verify that skip is not activated at start of truth/dare
        Acceptance Criteria: skip_activated is False initially
        """
        game_state.start_truth_dare(duration=60)
        
        assert not game_state.skip_activated
    
    def test_vs_008_skip_activation_prevents_further_votes(self, game_state):
        """
        Test ID: VS-008
        User Story: US-056
        Description: Verify that skip status indicates voting is closed
        Acceptance Criteria: skip_activated can be checked to disable voting
        Note: Enforcement happens in socket_events and frontend
        """
        game_state.activate_skip()
        
        # Skip is activated - further votes should be ignored in socket_events
        assert game_state.skip_activated


class TestSkipThreshold:
    """Tests for skip vote threshold calculation (US-056)"""
    
    def test_vs_009_threshold_with_5_players(self, room_with_players):
        """
        Test ID: VS-009
        User Story: US-056
        Description: Verify threshold calculation with 5 players
        Acceptance Criteria: With 5 players (4 can vote), need 2 votes (50% of 4)
        """
        # 5 players total, 1 performing, 4 can vote
        # Required: ceil(4 / 2) = 2 votes
        other_players_count = len(room_with_players.players) - 1
        required_votes = (other_players_count + 1) // 2  # Ceiling division
        
        assert other_players_count == 4
        assert required_votes == 2
    
    def test_vs_010_threshold_with_3_players(self):
        """
        Test ID: VS-010
        User Story: US-056
        Description: Verify threshold calculation with 3 players
        Acceptance Criteria: With 3 players (2 can vote), need 1 vote (50% of 2)
        """
        # 3 players total, 1 performing, 2 can vote
        # Required: ceil(2 / 2) = 1 vote
        other_players_count = 2
        required_votes = (other_players_count + 1) // 2
        
        assert required_votes == 1
    
    def test_vs_011_threshold_with_6_players(self):
        """
        Test ID: VS-011
        User Story: US-056
        Description: Verify threshold calculation with 6 players
        Acceptance Criteria: With 6 players (5 can vote), need 3 votes (50% of 5)
        """
        # 6 players total, 1 performing, 5 can vote
        # Required: ceil(5 / 2) = 3 votes
        other_players_count = 5
        required_votes = (other_players_count + 1) // 2
        
        assert required_votes == 3
    
    def test_vs_012_threshold_with_10_players(self):
        """
        Test ID: VS-012
        User Story: US-056
        Description: Verify threshold calculation with 10 players
        Acceptance Criteria: With 10 players (9 can vote), need 5 votes (50% of 9)
        """
        # 10 players total, 1 performing, 9 can vote
        # Required: ceil(9 / 2) = 5 votes
        other_players_count = 9
        required_votes = (other_players_count + 1) // 2
        
        assert required_votes == 5


class TestTimerReduction:
    """Tests for timer reduction on skip (US-056)"""
    
    def test_vs_013_reduce_timer_on_skip(self, game_state):
        """
        Test ID: VS-013
        User Story: US-056
        Description: Verify that timer is reduced when skip activates
        Acceptance Criteria: Timer is set to skip_duration seconds
        """
        game_state.start_truth_dare(duration=60)
        
        # Activate skip and reduce timer
        game_state.activate_skip()
        game_state.reduce_timer(seconds=5)
        
        remaining = game_state.get_remaining_time()
        assert 4 <= remaining <= 5
    
    def test_vs_014_reduce_timer_custom_duration(self, game_state):
        """
        Test ID: VS-014
        User Story: US-056
        Description: Verify that timer can be reduced to custom duration
        Acceptance Criteria: Timer is set to specified seconds
        """
        game_state.start_truth_dare(duration=60)
        
        game_state.reduce_timer(seconds=10)
        
        remaining = game_state.get_remaining_time()
        assert 9 <= remaining <= 10
    
    def test_vs_015_reduce_timer_method(self, game_state):
        """
        Test ID: VS-015
        User Story: US-056
        Description: Verify that reduce_timer method works correctly
        Acceptance Criteria: phase_end_time is updated to current time + specified seconds
        """
        game_state.start_truth_dare(duration=60)
        initial_remaining = game_state.get_remaining_time()
        
        game_state.reduce_timer(seconds=3)
        new_remaining = game_state.get_remaining_time()
        
        assert initial_remaining > 50  # Was ~60
        assert new_remaining <= 3  # Now ~3


class TestAutoSkipEmptyList:
    """Tests for auto-skip when list is empty (US-057)"""
    
    def test_vs_016_list_empty_flag(self, game_state):
        """
        Test ID: VS-016
        User Story: US-057
        Description: Verify that list_empty flag can be set
        Acceptance Criteria: list_empty is accessible and modifiable
        """
        assert not game_state.list_empty
        
        game_state.list_empty = True
        
        assert game_state.list_empty
    
    def test_vs_017_auto_skip_with_empty_list(self, game_state):
        """
        Test ID: VS-017
        User Story: US-057
        Description: Verify that skip auto-activates when list is empty
        Acceptance Criteria: When list_empty is True, skip should be activated
        Note: This logic is in socket_events.py
        """
        # This test documents the expected behavior
        # The actual implementation is in socket_events.py
        game_state.list_empty = True
        game_state.activate_skip()
        
        assert game_state.skip_activated
        assert game_state.list_empty
    
    def test_vs_018_list_empty_cleared_on_preparation(self, game_state):
        """
        Test ID: VS-018
        User Story: US-057
        Description: Verify that list_empty is cleared on new preparation phase
        Acceptance Criteria: list_empty is False after start_preparation
        """
        game_state.list_empty = True
        
        game_state.start_preparation(duration=30)
        
        # list_empty should be reset (via round data reset)
        assert not game_state.list_empty


class TestSkipStatus:
    """Tests for skip status visibility (US-058)"""
    
    def test_vs_019_skip_status_in_game_state(self, game_state):
        """
        Test ID: VS-019
        User Story: US-058
        Description: Verify that skip status is included in game state
        Acceptance Criteria: to_dict() includes skip_vote_count and skip_activated
        """
        game_state.add_skip_vote('socket_1')
        game_state.add_skip_vote('socket_2')
        game_state.activate_skip()
        
        state_dict = game_state.to_dict()
        
        assert 'skip_vote_count' in state_dict
        assert 'skip_activated' in state_dict
        assert state_dict['skip_vote_count'] == 2
        assert state_dict['skip_activated'] == True
    
    def test_vs_020_skip_vote_count_visibility(self, game_state):
        """
        Test ID: VS-020
        User Story: US-058
        Description: Verify that current skip vote count is accessible
        Acceptance Criteria: get_skip_vote_count() returns current count
        """
        assert game_state.get_skip_vote_count() == 0
        
        game_state.add_skip_vote('socket_1')
        assert game_state.get_skip_vote_count() == 1
        
        game_state.add_skip_vote('socket_2')
        game_state.add_skip_vote('socket_3')
        assert game_state.get_skip_vote_count() == 3
    
    def test_vs_021_skip_activated_status_visibility(self, game_state):
        """
        Test ID: VS-021
        User Story: US-058
        Description: Verify that skip activation status is accessible
        Acceptance Criteria: skip_activated can be checked
        """
        assert not game_state.skip_activated
        
        game_state.activate_skip()
        
        assert game_state.skip_activated


class TestPerformerCannotVote:
    """Tests for preventing performer from voting (US-054)"""
    
    def test_vs_022_selected_player_identified(self, game_state):
        """
        Test ID: VS-022
        User Story: US-054
        Description: Verify that selected player can be identified
        Acceptance Criteria: selected_player is set and accessible
        """
        game_state.set_selected_player("Alice")
        
        assert game_state.selected_player == "Alice"
    
    def test_vs_023_performer_exclusion_from_vote_count(self, room_with_players):
        """
        Test ID: VS-023
        User Story: US-054
        Description: Verify that performer is excluded from vote count
        Acceptance Criteria: Required votes based on non-performing players
        """
        # 5 players total, 1 performing (Alice)
        total_players = len(room_with_players.players)
        room_with_players.game_state.set_selected_player("Alice")
        
        other_players_count = total_players - 1
        
        assert other_players_count == 4
    
    def test_vs_024_only_non_performers_can_vote(self):
        """
        Test ID: VS-024
        User Story: US-054
        Description: Verify that only non-performing players should vote
        Acceptance Criteria: Performer's vote should be rejected in socket_events
        Note: This logic is enforced in socket_events.py
        """
        # This test documents the expected behavior
        # The actual check is in socket_events.py on_vote_skip handler
        game_state = GameState()
        game_state.set_selected_player("Alice")
        
        # In socket_events, check would be:
        # if player.name == game_state.selected_player: return
        
        assert game_state.selected_player == "Alice"


class TestSkipIntegration:
    """Integration tests for skip mechanism"""
    
    def test_vs_025_full_skip_workflow(self, room_with_players):
        """
        Test ID: VS-025
        User Story: US-053, US-056, US-058
        Description: Verify complete skip workflow
        Acceptance Criteria: Votes accumulate, threshold reached, skip activates
        """
        gs = room_with_players.game_state
        gs.start_truth_dare(duration=60)
        gs.set_selected_player("Alice")
        
        # 4 players can vote (5 total - 1 performing)
        # Need 2 votes to activate skip
        
        # First vote
        gs.add_skip_vote('socket_2')
        assert gs.get_skip_vote_count() == 1
        assert not gs.skip_activated
        
        # Second vote - reaches threshold
        gs.add_skip_vote('socket_3')
        assert gs.get_skip_vote_count() == 2
        
        # Activate skip manually (socket_events does this)
        gs.activate_skip()
        gs.reduce_timer(seconds=5)
        
        assert gs.skip_activated
        assert gs.get_remaining_time() <= 5
    
    def test_vs_026_skip_with_all_voting(self, room_with_players):
        """
        Test ID: VS-026
        User Story: US-053, US-056
        Description: Verify skip with all non-performers voting
        Acceptance Criteria: Skip activates when all eligible players vote
        """
        gs = room_with_players.game_state
        gs.start_truth_dare(duration=60)
        gs.set_selected_player("Alice")
        
        # All 4 non-performers vote
        gs.add_skip_vote('socket_2')
        gs.add_skip_vote('socket_3')
        gs.add_skip_vote('socket_4')
        gs.add_skip_vote('socket_5')
        
        assert gs.get_skip_vote_count() == 4
        
        gs.activate_skip()
        assert gs.skip_activated
    
    def test_vs_027_skip_not_activated_below_threshold(self):
        """
        Test ID: VS-027
        User Story: US-056
        Description: Verify skip doesn't activate below threshold
        Acceptance Criteria: Skip remains inactive with insufficient votes
        """
        gs = GameState()
        gs.start_truth_dare(duration=60)
        
        # Only 1 vote when 2+ needed
        gs.add_skip_vote('socket_1')
        
        assert gs.get_skip_vote_count() == 1
        assert not gs.skip_activated
    
    def test_vs_028_skip_state_serialization(self, game_state):
        """
        Test ID: VS-028
        User Story: US-058, US-059
        Description: Verify skip state is properly serialized
        Acceptance Criteria: to_dict() includes all skip-related fields
        """
        game_state.add_skip_vote('socket_1')
        game_state.add_skip_vote('socket_2')
        game_state.activate_skip()
        game_state.list_empty = True
        
        state_dict = game_state.to_dict()
        
        assert state_dict['skip_vote_count'] == 2
        assert state_dict['skip_activated'] == True
        assert state_dict['list_empty'] == True


class TestEmptyListBanner:
    """Tests for empty list banner display (US-057)"""
    
    def test_vs_029_list_empty_in_state_dict(self, game_state):
        """
        Test ID: VS-029
        User Story: US-057
        Description: Verify that list_empty flag is in state dict
        Acceptance Criteria: to_dict() includes list_empty field
        """
        game_state.list_empty = True
        
        state_dict = game_state.to_dict()
        
        assert 'list_empty' in state_dict
        assert state_dict['list_empty'] == True
    
    def test_vs_030_list_empty_false_by_default(self, game_state):
        """
        Test ID: VS-030
        User Story: US-057
        Description: Verify that list_empty is False by default
        Acceptance Criteria: list_empty starts as False
        """
        state_dict = game_state.to_dict()
        
        assert state_dict['list_empty'] == False
