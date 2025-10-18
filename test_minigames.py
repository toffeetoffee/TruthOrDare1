"""Tests for minigame system"""
import pytest
from Model.minigame import Minigame, StaringContest
from Model.player import Player
from Model.game_state import GameState


class TestMinigameBase:
    """Tests for base Minigame class"""
    
    def test_minigame_initialization(self):
        """Test minigame starts with empty state"""
        minigame = Minigame()
        
        assert len(minigame.participants) == 0
        assert len(minigame.votes) == 0
        assert minigame.winner is None
        assert minigame.loser is None
        assert minigame.is_complete == False
        assert minigame.total_voters == 0
    
    def test_add_participants(self):
        """Test adding participants to minigame"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        
        assert len(minigame.participants) == 2
        assert minigame.participants[0] == alice
        assert minigame.participants[1] == bob
    
    def test_set_total_voters(self):
        """Test setting total number of voters"""
        minigame = Minigame()
        minigame.set_total_voters(5)
        
        assert minigame.total_voters == 5
    
    def test_add_vote(self):
        """Test adding votes"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        
        minigame.add_vote('voter1', 'Alice')
        minigame.add_vote('voter2', 'Bob')
        
        assert len(minigame.votes) == 2
        assert minigame.votes['voter1'] == 'Alice'
        assert minigame.votes['voter2'] == 'Bob'
    
    def test_get_participant_names(self):
        """Test getting participant names"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        
        names = minigame.get_participant_names()
        assert names == ['Alice', 'Bob']
    
    def test_get_vote_counts(self):
        """Test getting vote counts"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        
        minigame.add_vote('v1', 'Alice')
        minigame.add_vote('v2', 'Alice')
        minigame.add_vote('v3', 'Bob')
        
        counts = minigame.get_vote_counts()
        assert counts['Alice'] == 2
        assert counts['Bob'] == 1


class TestMinigameVoting:
    """Tests for minigame voting mechanics"""
    
    def test_check_immediate_winner_simple_majority(self):
        """Test immediate winner with simple majority"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        minigame.set_total_voters(3)
        
        # Add 2 votes for Alice (2/3 is majority)
        minigame.add_vote('v1', 'Alice')
        minigame.add_vote('v2', 'Alice')
        
        loser = minigame.check_immediate_winner()
        
        assert loser == alice
        assert minigame.winner == bob
        assert minigame.is_complete == True
    
    def test_check_immediate_winner_not_yet(self):
        """Test no immediate winner when threshold not reached"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        minigame.set_total_voters(5)
        
        # Add 2 votes for Alice (need 3 out of 5)
        minigame.add_vote('v1', 'Alice')
        minigame.add_vote('v2', 'Alice')
        
        loser = minigame.check_immediate_winner()
        
        assert loser is None
        assert minigame.is_complete == False
    
    def test_check_all_voted(self):
        """Test checking if all voters have voted"""
        minigame = Minigame()
        minigame.set_total_voters(3)
        
        assert minigame.check_all_voted() == False
        
        minigame.add_vote('v1', 'Alice')
        minigame.add_vote('v2', 'Bob')
        assert minigame.check_all_voted() == False
        
        minigame.add_vote('v3', 'Alice')
        assert minigame.check_all_voted() == True
    
    def test_determine_loser_by_votes(self):
        """Test determining loser when all have voted"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        
        # Alice gets 3 votes, Bob gets 1
        minigame.add_vote('v1', 'Alice')
        minigame.add_vote('v2', 'Alice')
        minigame.add_vote('v3', 'Alice')
        minigame.add_vote('v4', 'Bob')
        
        loser = minigame.determine_loser()
        
        assert loser == alice
        assert minigame.winner == bob
        assert minigame.is_complete == True
    
    def test_handle_tie(self):
        """Test handling tied votes"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        
        # Tied votes
        minigame.add_vote('v1', 'Alice')
        minigame.add_vote('v2', 'Alice')
        minigame.add_vote('v3', 'Bob')
        minigame.add_vote('v4', 'Bob')
        
        loser = minigame.handle_tie()
        
        # Should randomly pick one
        assert loser in [alice, bob]
        assert minigame.winner in [alice, bob]
        assert minigame.winner != minigame.loser
        assert minigame.is_complete == True
    
    def test_voting_threshold_matches_skip_formula(self):
        """Test that voting threshold uses same formula as skip votes: (n+1)//2"""
        minigame = Minigame()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        minigame.add_participant(alice)
        minigame.add_participant(bob)
        
        # Test with 2 voters: need (2+1)//2 = 1 vote
        minigame.set_total_voters(2)
        minigame.add_vote('v1', 'Alice')
        assert minigame.check_immediate_winner() == alice
        
        # Reset
        minigame.votes.clear()
        minigame.is_complete = False
        minigame.winner = None
        minigame.loser = None
        
        # Test with 4 voters: need (4+1)//2 = 2 votes
        minigame.set_total_voters(4)
        minigame.add_vote('v1', 'Alice')
        assert minigame.check_immediate_winner() is None
        minigame.add_vote('v2', 'Alice')
        assert minigame.check_immediate_winner() == alice
        
        # Reset
        minigame.votes.clear()
        minigame.is_complete = False
        minigame.winner = None
        minigame.loser = None
        
        # Test with 5 voters: need (5+1)//2 = 3 votes
        minigame.set_total_voters(5)
        minigame.add_vote('v1', 'Alice')
        minigame.add_vote('v2', 'Alice')
        assert minigame.check_immediate_winner() is None
        minigame.add_vote('v3', 'Alice')
        assert minigame.check_immediate_winner() == alice


class TestStaringContest:
    """Tests for StaringContest minigame"""
    
    def test_staring_contest_creation(self):
        """Test creating a staring contest"""
        contest = StaringContest()
        
        assert contest.name == "Staring Contest"
        assert contest.description == "Who will blink first?"
        assert len(contest.participants) == 0
    
    def test_staring_contest_full_flow(self):
        """Test complete staring contest flow"""
        contest = StaringContest()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        contest.add_participant(alice)
        contest.add_participant(bob)
        contest.set_total_voters(3)
        
        # Voting
        contest.add_vote('v1', 'Alice')
        contest.add_vote('v2', 'Alice')
        
        # Determine winner
        loser = contest.check_immediate_winner()
        
        assert loser == alice
        assert contest.winner == bob
        assert contest.is_complete == True
    
    def test_staring_contest_to_dict(self):
        """Test serialization of staring contest"""
        contest = StaringContest()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        contest.add_participant(alice)
        contest.add_participant(bob)
        contest.set_total_voters(3)
        contest.add_vote('v1', 'Alice')
        
        data = contest.to_dict()
        
        assert data['type'] == 'staring_contest'
        assert data['participants'] == ['Alice', 'Bob']
        assert data['vote_count'] == 1
        assert data['total_voters'] == 3
        assert data['is_complete'] == False


class TestGameStateMinigame:
    """Tests for GameState minigame integration"""
    
    def test_game_state_has_minigame_phase(self):
        """Test that game state has minigame phase constant"""
        assert hasattr(GameState, 'PHASE_MINIGAME')
        assert GameState.PHASE_MINIGAME == 'minigame'
    
    def test_start_minigame_phase(self):
        """Test starting minigame phase"""
        state = GameState()
        
        state.start_minigame()
        
        assert state.phase == 'minigame'
        assert state.phase_end_time is None  # No time limit
    
    def test_set_minigame(self):
        """Test setting current minigame"""
        state = GameState()
        contest = StaringContest()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        contest.add_participant(alice)
        contest.add_participant(bob)
        
        state.set_minigame(contest)
        
        assert state.minigame == contest
    
    def test_game_state_to_dict_includes_minigame(self):
        """Test that to_dict includes minigame data"""
        state = GameState()
        contest = StaringContest()
        
        alice = Player('sid1', 'Alice')
        bob = Player('sid2', 'Bob')
        
        contest.add_participant(alice)
        contest.add_participant(bob)
        
        state.set_minigame(contest)
        state.start_minigame()
        
        data = state.to_dict()
        
        assert 'minigame' in data
        assert data['minigame']['type'] == 'staring_contest'
        assert data['minigame']['participants'] == ['Alice', 'Bob']


class TestMinigameSettings:
    """Tests for minigame-related settings"""
    
    def test_room_has_minigame_chance_setting(self):
        """Test that room has minigame_chance setting"""
        from Model.room import Room
        
        room = Room('TEST')
        
        assert 'minigame_chance' in room.settings
        assert room.settings['minigame_chance'] == 20  # Default 20%
    
    def test_update_minigame_chance(self):
        """Test updating minigame chance setting"""
        from Model.room import Room
        
        room = Room('TEST')
        
        room.update_settings({'minigame_chance': 50})
        
        assert room.settings['minigame_chance'] == 50
    
    def test_minigame_chance_validation(self):
        """Test that minigame chance accepts valid range"""
        from Model.room import Room
        
        room = Room('TEST')
        
        # Valid values
        room.update_settings({'minigame_chance': 0})
        assert room.settings['minigame_chance'] == 0
        
        room.update_settings({'minigame_chance': 100})
        assert room.settings['minigame_chance'] == 100
        
        room.update_settings({'minigame_chance': 50})
        assert room.settings['minigame_chance'] == 50


class TestMinigameScoring:
    """Tests for minigame scoring integration"""
    
    def test_minigame_participate_points(self):
        """Test that participants get points"""
        from Model.scoring_system import ScoringSystem
        
        player = Player('sid1', 'Alice')
        initial_score = player.score
        
        ScoringSystem.award_minigame_participate_points(player)
        
        assert player.score == initial_score + 75
    
    def test_minigame_points_value(self):
        """Test minigame points are between performance and submission"""
        from Model.scoring_system import ScoringSystem
        
        assert ScoringSystem.POINTS_MINIGAME_PARTICIPATE == 75
        assert ScoringSystem.POINTS_PERFORM > ScoringSystem.POINTS_MINIGAME_PARTICIPATE
        assert ScoringSystem.POINTS_MINIGAME_PARTICIPATE > ScoringSystem.POINTS_SUBMITTED_PERFORMED