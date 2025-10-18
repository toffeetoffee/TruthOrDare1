"""Tests for Model classes"""
import pytest
from Model.game_manager import GameManager
from Model.room import Room
from Model.player import Player
from Model.game_state import GameState
from Model.truth_dare_list import TruthDareList
from Model.truth_dare import Truth, Dare
from Model.round_record import RoundRecord


class TestGameManager:
    """Tests for GameManager"""
    
    def test_create_room(self):
        """Test GameManager creates rooms correctly"""
        gm = GameManager()
        code = gm.create_room()
        assert code in gm.rooms
        assert len(code) == 6
    
    def test_get_room(self):
        """Test getting a room by code"""
        gm = GameManager()
        code = gm.create_room()
        room = gm.get_room(code)
        assert room is not None
        assert room.code == code
    
    def test_room_exists(self):
        """Test checking if room exists"""
        gm = GameManager()
        code = gm.create_room()
        assert gm.room_exists(code) == True
        assert gm.room_exists('INVALID') == False
    
    def test_delete_room(self):
        """Test deleting a room"""
        gm = GameManager()
        code = gm.create_room()
        gm.delete_room(code)
        assert code not in gm.rooms


class TestRoom:
    """Tests for Room"""
    
    def test_room_creation(self):
        """Test creating a room"""
        room = Room('TEST123')
        assert room.code == 'TEST123'
        assert len(room.players) == 0
        assert room.host_sid is None
    
    def test_add_player(self):
        """Test adding a player to room"""
        room = Room('TEST')
        player = Player('sid1', 'Alice')
        
        room.add_player(player)
        assert len(room.players) == 1
        assert room.host_sid == 'sid1'
    
    def test_add_duplicate_player(self):
        """Test adding same player twice doesn't duplicate"""
        room = Room('TEST')
        player = Player('sid1', 'Alice')
        
        room.add_player(player)
        room.add_player(player)
        assert len(room.players) == 1
    
    def test_remove_player(self):
        """Test removing a player"""
        room = Room('TEST')
        player1 = Player('sid1', 'Alice')
        player2 = Player('sid2', 'Bob')
        
        room.add_player(player1)
        room.add_player(player2)
        
        room.remove_player('sid1')
        assert len(room.players) == 1
        assert room.players[0].name == 'Bob'
        # Host should transfer
        assert room.host_sid == 'sid2'
    
    def test_get_player_by_sid(self):
        """Test getting player by socket ID"""
        room = Room('TEST')
        player = Player('sid1', 'Alice')
        room.add_player(player)
        
        found = room.get_player_by_sid('sid1')
        assert found is not None
        assert found.name == 'Alice'
    
    def test_get_player_by_name(self):
        """Test getting player by name"""
        room = Room('TEST')
        player = Player('sid1', 'Alice')
        room.add_player(player)
        
        found = room.get_player_by_name('Alice')
        assert found is not None
        assert found.socket_id == 'sid1'
    
    def test_is_host(self):
        """Test checking if player is host"""
        room = Room('TEST')
        player = Player('sid1', 'Alice')
        room.add_player(player)
        
        assert room.is_host('sid1') == True
        assert room.is_host('sid2') == False
    
    def test_default_settings(self):
        """Test room has default settings"""
        room = Room('TEST')
        
        assert 'countdown_duration' in room.settings
        assert 'preparation_duration' in room.settings
        assert 'selection_duration' in room.settings
        assert 'truth_dare_duration' in room.settings
        assert 'skip_duration' in room.settings
        assert 'max_rounds' in room.settings
        assert 'minigame_chance' in room.settings
    
    def test_update_settings(self):
        """Test updating room settings"""
        room = Room('TEST')
        
        new_settings = {
            'countdown_duration': 15,
            'preparation_duration': 45,
            'max_rounds': 20
        }
        
        room.update_settings(new_settings)
        
        assert room.settings['countdown_duration'] == 15
        assert room.settings['preparation_duration'] == 45
        assert room.settings['max_rounds'] == 20
    
    def test_round_history(self):
        """Test adding and getting round history"""
        room = Room('TEST')
        
        record1 = RoundRecord(1, 'Alice', 'Tell a secret', 'truth', None)
        record2 = RoundRecord(2, 'Bob', 'Dance', 'dare', 'Alice')
        
        room.add_round_record(record1)
        room.add_round_record(record2)
        
        assert len(room.round_history) == 2
        history = room.get_round_history()
        assert history[0]['round_number'] == 1
        assert history[1]['round_number'] == 2
    
    def test_top_players(self):
        """Test getting top players by score"""
        room = Room('TEST')
        
        alice = Player('sid1', 'Alice')
        alice.score = 150
        
        bob = Player('sid2', 'Bob')
        bob.score = 200
        
        charlie = Player('sid3', 'Charlie')
        charlie.score = 100
        
        room.add_player(alice)
        room.add_player(bob)
        room.add_player(charlie)
        
        top_players = room.get_top_players(5)
        
        assert len(top_players) == 3
        assert top_players[0]['name'] == 'Bob'
        assert top_players[0]['score'] == 200
        assert top_players[1]['name'] == 'Alice'
        assert top_players[2]['name'] == 'Charlie'


class TestPlayer:
    """Tests for Player"""
    
    def test_player_creation(self):
        """Test creating a player"""
        player = Player('sid1', 'Alice')
        assert player.socket_id == 'sid1'
        assert player.name == 'Alice'
        assert player.score == 0
        assert player.submissions_this_round == 0
    
    def test_add_score(self):
        """Test adding score to player"""
        player = Player('sid1', 'Alice')
        player.add_score(50)
        assert player.score == 50
        
        player.add_score(30)
        assert player.score == 80
    
    def test_submission_tracking(self):
        """Test submission counter"""
        player = Player('sid1', 'Alice')
        
        assert player.can_submit_more() == True
        
        player.increment_submissions()
        assert player.submissions_this_round == 1
        
        player.increment_submissions()
        player.increment_submissions()
        assert player.submissions_this_round == 3
        assert player.can_submit_more() == False
    
    def test_reset_submissions(self):
        """Test resetting submission counter"""
        player = Player('sid1', 'Alice')
        player.increment_submissions()
        player.increment_submissions()
        
        player.reset_round_submissions()
        assert player.submissions_this_round == 0


class TestGameState:
    """Tests for GameState"""
    
    def test_initial_state(self):
        """Test initial game state"""
        state = GameState()
        assert state.phase == GameState.PHASE_LOBBY
        assert state.started == False
        assert state.current_round == 0
    
    def test_phase_transitions(self):
        """Test phase transitions"""
        state = GameState()
        
        state.start_countdown(duration=10)
        assert state.phase == GameState.PHASE_COUNTDOWN
        assert state.started == True
        
        state.start_preparation(duration=30)
        assert state.phase == GameState.PHASE_PREPARATION
        assert state.current_round == 1
        
        state.start_selection(duration=10)
        assert state.phase == GameState.PHASE_SELECTION
        
        state.start_truth_dare(duration=60)
        assert state.phase == GameState.PHASE_TRUTH_DARE
    
    def test_selected_player(self):
        """Test setting selected player"""
        state = GameState()
        state.set_selected_player('Alice')
        assert state.selected_player == 'Alice'
    
    def test_skip_votes(self):
        """Test skip vote tracking"""
        state = GameState()
        
        state.add_skip_vote('sid1')
        state.add_skip_vote('sid2')
        
        assert state.get_skip_vote_count() == 2
        assert state.skip_activated == False
        
        state.activate_skip()
        assert state.skip_activated == True
    
    def test_round_tracking(self):
        """Test round tracking"""
        state = GameState()
        state.max_rounds = 5
        
        for i in range(5):
            state.start_preparation()
        
        assert state.current_round == 5
        assert state.should_end_game() == True
    
    def test_to_dict(self):
        """Test serialization to dictionary"""
        state = GameState()
        state.set_selected_player('Alice')
        state.set_selected_choice('dare')
        
        data = state.to_dict()
        assert data['phase'] == 'lobby'
        assert data['selected_player'] == 'Alice'
        assert data['selected_choice'] == 'dare'


class TestTruthDareList:
    """Tests for TruthDareList"""
    
    def test_loads_defaults(self):
        """Test that TruthDareList loads default truths and dares"""
        td_list = TruthDareList()
        
        truths = td_list.get_truths()
        dares = td_list.get_dares()
        
        assert len(truths) == 5
        assert len(dares) == 5
        
        # Check they're marked as defaults
        for truth in truths:
            assert truth['is_default'] == True
        for dare in dares:
            assert dare['is_default'] == True
    
    def test_add_custom_items(self):
        """Test adding custom truths and dares"""
        td_list = TruthDareList()
        
        td_list.add_truth('Custom truth?', submitted_by='Alice')
        td_list.add_dare('Custom dare', submitted_by='Bob')
        
        truths = td_list.get_truths()
        dares = td_list.get_dares()
        
        assert len(truths) == 6
        assert len(dares) == 6
        
        # Check custom items
        assert truths[-1]['is_default'] == False
        assert truths[-1]['submitted_by'] == 'Alice'
        assert dares[-1]['is_default'] == False
        assert dares[-1]['submitted_by'] == 'Bob'


class TestTruthDare:
    """Tests for Truth and Dare classes"""
    
    def test_truth_creation(self):
        """Test creating a truth"""
        truth = Truth('What is your secret?', is_default=False, submitted_by='Alice')
        assert truth.text == 'What is your secret?'
        assert truth.type == 'truth'
        assert truth.submitted_by == 'Alice'
    
    def test_dare_creation(self):
        """Test creating a dare"""
        dare = Dare('Do 10 pushups', is_default=False, submitted_by='Bob')
        assert dare.text == 'Do 10 pushups'
        assert dare.type == 'dare'
        assert dare.submitted_by == 'Bob'
    
    def test_to_dict(self):
        """Test serialization"""
        truth = Truth('Question?', is_default=True)
        data = truth.to_dict()
        
        assert data['text'] == 'Question?'
        assert data['is_default'] == True


class TestRoundRecord:
    """Tests for RoundRecord"""
    
    def test_creation(self):
        """Test creating a round record"""
        record = RoundRecord(
            round_number=1,
            selected_player_name='Alice',
            truth_dare_text='Do 10 pushups',
            truth_dare_type='dare',
            submitted_by='Bob'
        )
        
        assert record.round_number == 1
        assert record.selected_player_name == 'Alice'
        assert record.truth_dare_text == 'Do 10 pushups'
        assert record.truth_dare_type == 'dare'
        assert record.submitted_by == 'Bob'
    
    def test_to_dict(self):
        """Test serialization"""
        record = RoundRecord(1, 'Alice', 'Question?', 'truth', None)
        data = record.to_dict()
        
        assert data['round_number'] == 1
        assert data['selected_player'] == 'Alice'
        assert data['truth_dare']['text'] == 'Question?'
        assert data['truth_dare']['type'] == 'truth'
        assert data['submitted_by'] is None