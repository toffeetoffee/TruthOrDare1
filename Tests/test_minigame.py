"""
Tests for Minigame functionality
Related User Stories: US-018 to US-022
"""
import pytest
from Model.minigame import Minigame, StaringContest
from Model.player import Player


@pytest.fixture
def player1():
    """Fixture for first test player"""
    return Player('socket_1', 'Alice')


@pytest.fixture
def player2():
    """Fixture for second test player"""
    return Player('socket_2', 'Bob')


@pytest.fixture
def minigame():
    """Fixture for basic minigame"""
    return Minigame()


@pytest.fixture
def staring_contest():
    """Fixture for staring contest minigame"""
    return StaringContest()


@pytest.fixture
def minigame_with_participants(player1, player2):
    """Fixture for minigame with two participants"""
    mg = StaringContest()
    mg.add_participant(player1)
    mg.add_participant(player2)
    mg.set_total_voters(3)  # 3 other players can vote
    return mg


class TestMinigameInitialization:
    """Tests for minigame initialization"""
    
    def test_mg_001_minigame_creation(self, minigame):
        """
        Test ID: MG-001
        User Story: US-018
        Description: Verify that minigame can be created
        Acceptance Criteria: Minigame has empty participants and votes
        """
        assert minigame.participants == []
        assert minigame.votes == {}
        assert minigame.winner is None
        assert minigame.loser is None
        assert not minigame.is_complete
        assert minigame.total_voters == 0
    
    def test_mg_002_staring_contest_creation(self, staring_contest):
        """
        Test ID: MG-002
        User Story: US-018, US-019
        Description: Verify that staring contest minigame can be created
        Acceptance Criteria: StaringContest has name and description
        """
        assert staring_contest.name == "Staring Contest"
        assert staring_contest.description == "Who will blink first?"
        assert staring_contest.participants == []


class TestParticipantManagement:
    """Tests for adding and managing participants (US-019)"""
    
    def test_mg_003_add_participant(self, minigame, player1):
        """
        Test ID: MG-003
        User Story: US-019
        Description: Verify that participants can be added to minigame
        Acceptance Criteria: Player is added to participants list
        """
        minigame.add_participant(player1)
        
        assert len(minigame.participants) == 1
        assert minigame.participants[0] == player1
    
    def test_mg_004_add_two_participants(self, minigame, player1, player2):
        """
        Test ID: MG-004
        User Story: US-018, US-019
        Description: Verify that two participants can be added
        Acceptance Criteria: Both players are in participants list
        """
        minigame.add_participant(player1)
        minigame.add_participant(player2)
        
        assert len(minigame.participants) == 2
        assert player1 in minigame.participants
        assert player2 in minigame.participants
    
    def test_mg_005_get_participant_names(self, minigame_with_participants):
        """
        Test ID: MG-005
        User Story: US-019
        Description: Verify that participant names can be retrieved
        Acceptance Criteria: get_participant_names() returns list of names
        """
        names = minigame_with_participants.get_participant_names()
        
        assert len(names) == 2
        assert 'Alice' in names
        assert 'Bob' in names
    
    def test_mg_006_set_total_voters(self, minigame):
        """
        Test ID: MG-006
        User Story: US-020
        Description: Verify that total voter count can be set
        Acceptance Criteria: total_voters is set to specified value
        """
        minigame.set_total_voters(5)
        
        assert minigame.total_voters == 5


class TestVoting:
    """Tests for minigame voting (US-020, US-021)"""
    
    def test_mg_007_add_vote(self, minigame_with_participants):
        """
        Test ID: MG-007
        User Story: US-020
        Description: Verify that votes can be recorded
        Acceptance Criteria: Vote is stored with voter and voted player
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        
        assert 'socket_3' in minigame_with_participants.votes
        assert minigame_with_participants.votes['socket_3'] == 'Alice'
    
    def test_mg_008_multiple_votes(self, minigame_with_participants):
        """
        Test ID: MG-008
        User Story: US-020
        Description: Verify that multiple players can vote
        Acceptance Criteria: All votes are recorded separately
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Bob')
        minigame_with_participants.add_vote('socket_5', 'Alice')
        
        assert len(minigame_with_participants.votes) == 3
        assert minigame_with_participants.votes['socket_3'] == 'Alice'
        assert minigame_with_participants.votes['socket_4'] == 'Bob'
        assert minigame_with_participants.votes['socket_5'] == 'Alice'
    
    def test_mg_009_get_vote_counts(self, minigame_with_participants):
        """
        Test ID: MG-009
        User Story: US-020
        Description: Verify that vote counts can be tallied
        Acceptance Criteria: get_vote_counts() returns dict with counts per player
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Bob')
        minigame_with_participants.add_vote('socket_5', 'Alice')
        
        vote_counts = minigame_with_participants.get_vote_counts()
        
        assert vote_counts['Alice'] == 2
        assert vote_counts['Bob'] == 1
    
    def test_mg_010_check_all_voted(self, minigame_with_participants):
        """
        Test ID: MG-010
        User Story: US-021
        Description: Verify that we can check if all players voted
        Acceptance Criteria: check_all_voted() returns True when vote count equals total_voters
        """
        assert not minigame_with_participants.check_all_voted()
        
        minigame_with_participants.add_vote('socket_3', 'Alice')
        assert not minigame_with_participants.check_all_voted()
        
        minigame_with_participants.add_vote('socket_4', 'Bob')
        assert not minigame_with_participants.check_all_voted()
        
        minigame_with_participants.add_vote('socket_5', 'Alice')
        assert minigame_with_participants.check_all_voted()


class TestImmediateWinner:
    """Tests for immediate winner detection (US-021)"""
    
    def test_mg_011_immediate_winner_at_threshold(self, minigame_with_participants):
        """
        Test ID: MG-011
        User Story: US-021
        Description: Verify that winner is detected when threshold is reached
        Acceptance Criteria: check_immediate_winner() returns loser when at least half vote
        """
        # With 3 total voters, need 2 votes (ceiling of 3/2)
        minigame_with_participants.add_vote('socket_3', 'Alice')
        
        loser = minigame_with_participants.check_immediate_winner()
        assert loser is None  # Not enough votes yet
        
        minigame_with_participants.add_vote('socket_4', 'Alice')
        
        loser = minigame_with_participants.check_immediate_winner()
        assert loser is not None
        assert loser.name == 'Alice'
        assert minigame_with_participants.winner.name == 'Bob'
        assert minigame_with_participants.is_complete
    
    def test_mg_012_immediate_winner_exact_half(self):
        """
        Test ID: MG-012
        User Story: US-021
        Description: Verify threshold calculation with even number of voters
        Acceptance Criteria: With 4 voters, need 2 votes to win immediately
        """
        mg = Minigame()
        p1 = Player('s1', 'Alice')
        p2 = Player('s2', 'Bob')
        mg.add_participant(p1)
        mg.add_participant(p2)
        mg.set_total_voters(4)  # Need 2 votes (4/2 = 2)
        
        mg.add_vote('s3', 'Alice')
        loser = mg.check_immediate_winner()
        assert loser is None
        
        mg.add_vote('s4', 'Alice')
        loser = mg.check_immediate_winner()
        assert loser is not None
        assert loser.name == 'Alice'
    
    def test_mg_013_no_immediate_winner_with_split(self, minigame_with_participants):
        """
        Test ID: MG-013
        User Story: US-021
        Description: Verify no immediate winner when votes are split
        Acceptance Criteria: check_immediate_winner() returns None when split
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Bob')
        
        loser = minigame_with_participants.check_immediate_winner()
        
        assert loser is None
        assert not minigame_with_participants.is_complete


class TestDetermineLoser:
    """Tests for determining loser after all votes (US-021, US-022)"""
    
    def test_mg_014_determine_loser_clear_winner(self, minigame_with_participants):
        """
        Test ID: MG-014
        User Story: US-021
        Description: Verify loser is determined correctly with clear majority
        Acceptance Criteria: Player with most votes is declared loser
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Alice')
        minigame_with_participants.add_vote('socket_5', 'Bob')
        
        loser = minigame_with_participants.determine_loser()
        
        assert loser is not None
        assert loser.name == 'Alice'
        assert minigame_with_participants.winner.name == 'Bob'
        assert minigame_with_participants.is_complete
    
    def test_mg_015_determine_loser_unanimous(self, minigame_with_participants):
        """
        Test ID: MG-015
        User Story: US-021
        Description: Verify loser determination with unanimous votes
        Acceptance Criteria: Player with all votes is declared loser
        """
        minigame_with_participants.add_vote('socket_3', 'Bob')
        minigame_with_participants.add_vote('socket_4', 'Bob')
        minigame_with_participants.add_vote('socket_5', 'Bob')
        
        loser = minigame_with_participants.determine_loser()
        
        assert loser.name == 'Bob'
        assert minigame_with_participants.winner.name == 'Alice'
    
    def test_mg_016_no_loser_without_votes(self, minigame_with_participants):
        """
        Test ID: MG-016
        User Story: US-021
        Description: Verify that loser cannot be determined without votes
        Acceptance Criteria: determine_loser() returns None when no votes
        """
        loser = minigame_with_participants.determine_loser()
        
        assert loser is None
        assert not minigame_with_participants.is_complete


class TestTieHandling:
    """Tests for tie resolution (US-022)"""
    
    def test_mg_017_handle_tie_random_selection(self, minigame_with_participants):
        """
        Test ID: MG-017
        User Story: US-022
        Description: Verify that ties are resolved randomly
        Acceptance Criteria: One participant is randomly selected as loser
        """
        # Create a tie scenario
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Bob')
        
        loser = minigame_with_participants.handle_tie()
        
        assert loser is not None
        assert loser.name in ['Alice', 'Bob']
        assert minigame_with_participants.winner is not None
        assert minigame_with_participants.winner != loser
        assert minigame_with_participants.is_complete
    
    def test_mg_018_determine_loser_handles_tie(self, minigame_with_participants):
        """
        Test ID: MG-018
        User Story: US-022
        Description: Verify that determine_loser() automatically handles ties
        Acceptance Criteria: Tie is detected and handle_tie() is called
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Bob')
        minigame_with_participants.add_vote('socket_5', 'Alice')
        minigame_with_participants.add_vote('socket_6', 'Bob')
        
        # This should be a 2-2 tie
        loser = minigame_with_participants.determine_loser()
        
        assert loser is not None
        assert loser.name in ['Alice', 'Bob']
        assert minigame_with_participants.is_complete
    
    def test_mg_019_handle_tie_requires_two_participants(self, minigame):
        """
        Test ID: MG-019
        User Story: US-022
        Description: Verify that tie handling requires exactly 2 participants
        Acceptance Criteria: handle_tie() returns None if not 2 participants
        """
        # Only 1 participant
        p1 = Player('s1', 'Alice')
        minigame.add_participant(p1)
        
        loser = minigame.handle_tie()
        
        assert loser is None


class TestMinigameCompletion:
    """Tests for minigame completion state"""
    
    def test_mg_020_is_complete_initially_false(self, minigame_with_participants):
        """
        Test ID: MG-020
        User Story: US-021
        Description: Verify that minigame starts as not complete
        Acceptance Criteria: is_complete is False initially
        """
        assert not minigame_with_participants.is_complete
    
    def test_mg_021_is_complete_after_immediate_winner(self, minigame_with_participants):
        """
        Test ID: MG-021
        User Story: US-021
        Description: Verify that minigame completes with immediate winner
        Acceptance Criteria: is_complete is True after immediate winner
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Alice')
        
        minigame_with_participants.check_immediate_winner()
        
        assert minigame_with_participants.is_complete
    
    def test_mg_022_is_complete_after_determine_loser(self, minigame_with_participants):
        """
        Test ID: MG-022
        User Story: US-021
        Description: Verify that minigame completes after determining loser
        Acceptance Criteria: is_complete is True after determine_loser()
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Alice')
        minigame_with_participants.add_vote('socket_5', 'Bob')
        
        minigame_with_participants.determine_loser()
        
        assert minigame_with_participants.is_complete


class TestMinigameSerialization:
    """Tests for minigame to dictionary conversion (US-059)"""
    
    def test_mg_023_to_dict_basic(self, minigame_with_participants):
        """
        Test ID: MG-023
        User Story: US-059
        Description: Verify that minigame can be converted to dictionary
        Acceptance Criteria: to_dict() returns dict with all key fields
        """
        mg_dict = minigame_with_participants.to_dict()
        
        assert 'type' in mg_dict
        assert 'participants' in mg_dict
        assert 'votes' in mg_dict
        assert 'vote_count' in mg_dict
        assert 'vote_counts' in mg_dict
        assert 'total_voters' in mg_dict
        assert 'winner' in mg_dict
        assert 'loser' in mg_dict
        assert 'is_complete' in mg_dict
    
    def test_mg_024_to_dict_with_votes(self, minigame_with_participants):
        """
        Test ID: MG-024
        User Story: US-059
        Description: Verify that minigame dict includes vote data
        Acceptance Criteria: votes and vote_counts are properly serialized
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Bob')
        
        mg_dict = minigame_with_participants.to_dict()
        
        assert mg_dict['vote_count'] == 2
        assert mg_dict['total_voters'] == 3
        assert 'Alice' in mg_dict['vote_counts']
        assert 'Bob' in mg_dict['vote_counts']
    
    def test_mg_025_to_dict_with_winner_loser(self, minigame_with_participants):
        """
        Test ID: MG-025
        User Story: US-059
        Description: Verify that minigame dict includes winner/loser
        Acceptance Criteria: winner and loser names are included when set
        """
        minigame_with_participants.add_vote('socket_3', 'Alice')
        minigame_with_participants.add_vote('socket_4', 'Alice')
        minigame_with_participants.check_immediate_winner()
        
        mg_dict = minigame_with_participants.to_dict()
        
        assert mg_dict['loser'] == 'Alice'
        assert mg_dict['winner'] == 'Bob'
        assert mg_dict['is_complete'] == True
    
    def test_mg_026_to_dict_no_winner_yet(self, minigame_with_participants):
        """
        Test ID: MG-026
        User Story: US-059
        Description: Verify that minigame dict handles no winner scenario
        Acceptance Criteria: winner and loser are None when not determined
        """
        mg_dict = minigame_with_participants.to_dict()
        
        assert mg_dict['winner'] is None
        assert mg_dict['loser'] is None
        assert mg_dict['is_complete'] == False
    
    def test_mg_027_to_dict_participant_names(self, minigame_with_participants):
        """
        Test ID: MG-027
        User Story: US-019, US-059
        Description: Verify that participant names are included in dict
        Acceptance Criteria: participants field contains list of names
        """
        mg_dict = minigame_with_participants.to_dict()
        
        assert mg_dict['participants'] == ['Alice', 'Bob']


class TestStaringContestSpecific:
    """Tests specific to staring contest minigame"""
    
    def test_mg_028_staring_contest_type(self, staring_contest):
        """
        Test ID: MG-028
        User Story: US-018, US-019
        Description: Verify that staring contest has correct type in dict
        Acceptance Criteria: type field is 'staring_contest'
        """
        sc_dict = staring_contest.to_dict()
        
        assert sc_dict['type'] == 'staring_contest'
    
    def test_mg_029_staring_contest_inherits_minigame(self, staring_contest):
        """
        Test ID: MG-029
        User Story: US-018
        Description: Verify that StaringContest inherits from Minigame
        Acceptance Criteria: StaringContest is instance of Minigame
        """
        assert isinstance(staring_contest, Minigame)
    
    def test_mg_030_staring_contest_full_workflow(self):
        """
        Test ID: MG-030
        User Story: US-018, US-019, US-020, US-021
        Description: Verify complete staring contest workflow
        Acceptance Criteria: Full game flow works correctly
        """
        # Create staring contest
        sc = StaringContest()
        p1 = Player('s1', 'Alice')
        p2 = Player('s2', 'Bob')
        
        # Add participants
        sc.add_participant(p1)
        sc.add_participant(p2)
        sc.set_total_voters(3)
        
        # Add votes
        sc.add_vote('s3', 'Alice')
        sc.add_vote('s4', 'Bob')
        sc.add_vote('s5', 'Alice')
        
        # Determine loser
        loser = sc.determine_loser()
        
        assert loser.name == 'Alice'
        assert sc.winner.name == 'Bob'
        assert sc.is_complete
        assert sc.get_vote_counts()['Alice'] == 2
        assert sc.get_vote_counts()['Bob'] == 1
