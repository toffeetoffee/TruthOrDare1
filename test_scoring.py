"""Tests for scoring system"""
import pytest
from Model.player import Player
from Model.scoring_system import ScoringSystem


class TestScoringSystem:
    """Tests for ScoringSystem"""
    
    def test_point_values(self):
        """Test scoring system point values are defined"""
        assert ScoringSystem.POINTS_PERFORM == 100
        assert ScoringSystem.POINTS_MINIGAME_PARTICIPATE == 75
        assert ScoringSystem.POINTS_SUBMITTED_PERFORMED == 50
        assert ScoringSystem.POINTS_SUBMISSION == 10
    
    def test_point_hierarchy(self):
        """Test that points are in correct hierarchy"""
        assert ScoringSystem.POINTS_PERFORM > ScoringSystem.POINTS_MINIGAME_PARTICIPATE
        assert ScoringSystem.POINTS_MINIGAME_PARTICIPATE > ScoringSystem.POINTS_SUBMITTED_PERFORMED
        assert ScoringSystem.POINTS_SUBMITTED_PERFORMED > ScoringSystem.POINTS_SUBMISSION
    
    def test_submission_limit(self):
        """Test submission limit is defined"""
        assert ScoringSystem.MAX_SUBMISSIONS_PER_ROUND == 3
    
    def test_award_perform_points(self):
        """Test awarding perform points"""
        player = Player('sid1', 'Alice')
        initial_score = player.score
        
        ScoringSystem.award_perform_points(player)
        
        assert player.score == initial_score + ScoringSystem.POINTS_PERFORM
        assert player.score == 100
    
    def test_award_minigame_participate_points(self):
        """Test awarding minigame participation points"""
        player = Player('sid1', 'Alice')
        initial_score = player.score
        
        ScoringSystem.award_minigame_participate_points(player)
        
        assert player.score == initial_score + ScoringSystem.POINTS_MINIGAME_PARTICIPATE
        assert player.score == 75
    
    def test_award_submission_performed_points(self):
        """Test awarding points when submission is performed"""
        player = Player('sid1', 'Alice')
        initial_score = player.score
        
        ScoringSystem.award_submission_performed_points(player)
        
        assert player.score == initial_score + ScoringSystem.POINTS_SUBMITTED_PERFORMED
        assert player.score == 50
    
    def test_award_submission_points(self):
        """Test awarding submission points"""
        player = Player('sid1', 'Alice')
        initial_score = player.score
        
        ScoringSystem.award_submission_points(player)
        
        assert player.score == initial_score + ScoringSystem.POINTS_SUBMISSION
        assert player.score == 10
    
    def test_multiple_score_awards(self):
        """Test awarding multiple types of points"""
        player = Player('sid1', 'Alice')
        
        # Submit 3 truths/dares
        for _ in range(3):
            ScoringSystem.award_submission_points(player)
        
        # One gets performed
        ScoringSystem.award_submission_performed_points(player)
        
        # Player also performs
        ScoringSystem.award_perform_points(player)
        
        expected = (3 * 10) + 50 + 100
        assert player.score == expected
        assert player.score == 180


class TestPlayerScoring:
    """Tests for player scoring features"""
    
    def test_initial_score(self):
        """Test player starts with 0 score"""
        player = Player('sid1', 'Alice')
        assert player.score == 0
    
    def test_add_score(self):
        """Test adding score directly"""
        player = Player('sid1', 'Alice')
        player.add_score(50)
        assert player.score == 50
        
        player.add_score(30)
        assert player.score == 80
    
    def test_negative_score_handling(self):
        """Test that score can go negative (if needed)"""
        player = Player('sid1', 'Alice')
        player.add_score(-10)
        assert player.score == -10
    
    def test_submission_counter(self):
        """Test submission counter tracking"""
        player = Player('sid1', 'Alice')
        
        assert player.submissions_this_round == 0
        assert player.can_submit_more() == True
        
        player.increment_submissions()
        assert player.submissions_this_round == 1
        assert player.can_submit_more() == True
        
        player.increment_submissions()
        player.increment_submissions()
        assert player.submissions_this_round == 3
        assert player.can_submit_more() == False
        
        # Try to increment beyond limit
        player.increment_submissions()
        assert player.submissions_this_round == 4  # Counter increases but can_submit_more returns False
        assert player.can_submit_more() == False
    
    def test_reset_submissions(self):
        """Test resetting submission counter for new round"""
        player = Player('sid1', 'Alice')
        
        player.increment_submissions()
        player.increment_submissions()
        player.increment_submissions()
        
        player.reset_round_submissions()
        
        assert player.submissions_this_round == 0
        assert player.can_submit_more() == True


class TestRoomScoring:
    """Tests for room-level scoring features"""
    
    def test_room_top_players(self):
        """Test getting top players sorted by score"""
        from Model.room import Room
        
        room = Room('TEST')
        
        alice = Player('sid1', 'Alice')
        alice.score = 150
        
        bob = Player('sid2', 'Bob')
        bob.score = 200
        
        charlie = Player('sid3', 'Charlie')
        charlie.score = 100
        
        david = Player('sid4', 'David')
        david.score = 175
        
        room.add_player(alice)
        room.add_player(bob)
        room.add_player(charlie)
        room.add_player(david)
        
        # Get top 3 players
        top_players = room.get_top_players(3)
        
        assert len(top_players) == 3
        assert top_players[0]['name'] == 'Bob'
        assert top_players[0]['score'] == 200
        assert top_players[1]['name'] == 'David'
        assert top_players[1]['score'] == 175
        assert top_players[2]['name'] == 'Alice'
        assert top_players[2]['score'] == 150
    
    def test_room_top_players_with_ties(self):
        """Test top players with tied scores"""
        from Model.room import Room
        
        room = Room('TEST')
        
        alice = Player('sid1', 'Alice')
        alice.score = 100
        
        bob = Player('sid2', 'Bob')
        bob.score = 100
        
        charlie = Player('sid3', 'Charlie')
        charlie.score = 100
        
        room.add_player(alice)
        room.add_player(bob)
        room.add_player(charlie)
        
        top_players = room.get_top_players(5)
        
        # All should be returned
        assert len(top_players) == 3
        # All have same score
        for player in top_players:
            assert player['score'] == 100
    
    def test_room_reset_clears_scores(self):
        """Test that room reset clears all player scores"""
        from Model.room import Room
        
        room = Room('TEST')
        
        alice = Player('sid1', 'Alice')
        alice.score = 150
        
        bob = Player('sid2', 'Bob')
        bob.score = 200
        
        room.add_player(alice)
        room.add_player(bob)
        
        # Reset room
        room.reset_for_new_game()
        
        assert alice.score == 0
        assert bob.score == 0


class TestEndGameScoring:
    """Tests for end game scoring and statistics"""
    
    def test_round_record_tracks_submitter(self):
        """Test that round records track who submitted"""
        from Model.round_record import RoundRecord
        
        record = RoundRecord(
            round_number=1,
            selected_player_name='Alice',
            truth_dare_text='Do 10 pushups',
            truth_dare_type='dare',
            submitted_by='Bob'
        )
        
        assert record.submitted_by == 'Bob'
        
        data = record.to_dict()
        assert data['submitted_by'] == 'Bob'
    
    def test_round_record_default_submission(self):
        """Test round record with default truth/dare (no submitter)"""
        from Model.round_record import RoundRecord
        
        record = RoundRecord(
            round_number=1,
            selected_player_name='Alice',
            truth_dare_text='Tell a secret',
            truth_dare_type='truth',
            submitted_by=None
        )
        
        assert record.submitted_by is None
        
        data = record.to_dict()
        assert data['submitted_by'] is None