"""Tests for game logic and flow"""
import pytest
from app import socketio, game_manager


def test_host_can_start_game(sample_room):
    """Test that host can start the game"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    room = game_manager.get_room(sample_room)
    assert room.game_state.phase == 'lobby'
    
    # Host starts game
    client1.emit('start_game', {'room': sample_room})
    
    # Should be in countdown phase
    room = game_manager.get_room(sample_room)
    assert room.game_state.phase == 'countdown'
    assert room.game_state.started == True


def test_non_host_cannot_start_game(sample_room):
    """Test that non-host cannot start game"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    assert room.game_state.phase == 'lobby'
    
    # Bob (non-host) tries to start
    client2.emit('start_game', {'room': sample_room})
    
    # Should still be in lobby
    room = game_manager.get_room(sample_room)
    assert room.game_state.phase == 'lobby'


def test_submit_truth_dare(sample_room):
    """Test submitting a truth or dare"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    
    # Start game and move to preparation
    room.game_state.start_preparation()
    
    # Submit a truth to Bob
    client1.emit('submit_truth_dare', {
        'room': sample_room,
        'text': 'What is your favorite color?',
        'type': 'truth',
        'targets': ['Bob']
    })
    
    # Bob should have the new truth
    bob = room.get_player_by_name('Bob')
    truths = bob.truth_dare_list.get_truths()
    assert len(truths) == 6  # 5 defaults + 1 custom
    assert truths[-1]['text'] == 'What is your favorite color?'
    assert truths[-1]['is_default'] == False


def test_submit_truth_dare_multiple_targets(sample_room):
    """Test submitting a truth or dare to multiple players"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    client3 = socketio.test_client(app)
    client3.emit('join', {'room': sample_room, 'name': 'Charlie'})
    
    room = game_manager.get_room(sample_room)
    room.game_state.start_preparation()
    
    # Submit a dare to multiple players
    client1.emit('submit_truth_dare', {
        'room': sample_room,
        'text': 'Do 20 jumping jacks',
        'type': 'dare',
        'targets': ['Bob', 'Charlie']
    })
    
    # Both Bob and Charlie should have the new dare
    bob = room.get_player_by_name('Bob')
    charlie = room.get_player_by_name('Charlie')
    
    bob_dares = bob.truth_dare_list.get_dares()
    charlie_dares = charlie.truth_dare_list.get_dares()
    
    assert len(bob_dares) == 6  # 5 defaults + 1 custom
    assert len(charlie_dares) == 6
    
    assert bob_dares[-1]['text'] == 'Do 20 jumping jacks'
    assert charlie_dares[-1]['text'] == 'Do 20 jumping jacks'


def test_submission_only_in_preparation_phase(sample_room):
    """Test that submissions only work in preparation phase"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    
    # Try to submit in lobby phase
    client1.emit('submit_truth_dare', {
        'room': sample_room,
        'text': 'Test',
        'type': 'truth',
        'targets': ['Bob']
    })
    
    bob = room.get_player_by_name('Bob')
    truths = bob.truth_dare_list.get_truths()
    # Should still have only defaults
    assert len(truths) == 5


def test_selected_player_can_choose_truth_dare(sample_room):
    """Test that selected player can choose truth or dare"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    room = game_manager.get_room(sample_room)
    room.game_state.set_selected_player('Alice')
    room.game_state.start_selection(duration=10)
    
    # Alice chooses dare
    client1.emit('select_truth_dare', {
        'room': sample_room,
        'choice': 'dare'
    })
    
    # Choice should be set
    assert room.game_state.selected_choice == 'dare'


def test_only_selected_player_can_choose(sample_room):
    """Test that only selected player can choose"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    room.game_state.set_selected_player('Alice')
    room.game_state.start_selection(duration=10)
    
    # Bob (not selected) tries to choose
    client2.emit('select_truth_dare', {
        'room': sample_room,
        'choice': 'dare'
    })
    
    # Choice should not be set
    assert room.game_state.selected_choice is None


def test_vote_skip_functionality(sample_room):
    """Test that players can vote to skip"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    client3 = socketio.test_client(app)
    client3.emit('join', {'room': sample_room, 'name': 'Charlie'})
    
    room = game_manager.get_room(sample_room)
    room.game_state.set_selected_player('Alice')
    room.game_state.start_truth_dare(duration=60)
    
    # Bob votes to skip
    client2.emit('vote_skip', {'room': sample_room})
    
    room = game_manager.get_room(sample_room)
    assert room.game_state.get_skip_vote_count() >= 1


def test_selected_player_cannot_vote_skip(sample_room):
    """Test that selected player cannot vote to skip"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    room.game_state.set_selected_player('Alice')
    room.game_state.start_truth_dare(duration=60)
    
    # Alice (selected player) tries to vote skip
    client1.emit('vote_skip', {'room': sample_room})
    
    # Vote should not be counted
    assert room.game_state.get_skip_vote_count() == 0


def test_skip_only_in_truth_dare_phase(sample_room):
    """Test that skip votes only work in truth_dare phase"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    
    # Try to vote in lobby
    client2.emit('vote_skip', {'room': sample_room})
    
    # Vote should not be counted
    assert room.game_state.get_skip_vote_count() == 0


def test_submission_with_limit(sample_room):
    """Test submission limit enforcement"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    room.game_state.start_preparation()
    
    alice = room.get_player_by_name('Alice')
    
    # Submit 3 times (max limit)
    for i in range(3):
        client1.emit('submit_truth_dare', {
            'room': sample_room,
            'text': f'Truth {i+1}',
            'type': 'truth',
            'targets': ['Bob']
        })
    
    # Alice should have reached limit
    assert alice.submissions_this_round == 3
    assert alice.can_submit_more() == False


def test_room_reset_for_new_game(sample_room):
    """Test room resets properly when restarting game"""
    from Model.player import Player
    from Model.round_record import RoundRecord
    
    room = game_manager.get_room(sample_room)
    
    alice = Player('sid1', 'Alice')
    alice.score = 150
    alice.submissions_this_round = 2
    
    bob = Player('sid2', 'Bob')
    bob.score = 200
    bob.submissions_this_round = 3
    
    room.add_player(alice)
    room.add_player(bob)
    
    # Add some round history
    record = RoundRecord(1, 'Alice', 'Test', 'dare', None)
    room.add_round_record(record)
    
    # Start game
    room.game_state.start_countdown()
    room.game_state.current_round = 5
    
    # Reset
    room.reset_for_new_game()
    
    # Check everything is reset
    assert alice.score == 0
    assert bob.score == 0
    assert alice.submissions_this_round == 0
    assert bob.submissions_this_round == 0
    assert len(room.round_history) == 0
    assert room.game_state.current_round == 0


def test_host_can_restart_game(sample_room):
    """Test that host can restart the game"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    room = game_manager.get_room(sample_room)
    
    # Simulate game in progress
    room.game_state.current_round = 5
    room.game_state.start_truth_dare()
    
    # Host restarts game
    client1.emit('restart_game', {'room': sample_room})
    
    # Game should reset to countdown
    room = game_manager.get_room(sample_room)
    assert room.game_state.phase == 'countdown'
    assert room.game_state.current_round == 0


def test_non_host_cannot_restart_game(sample_room):
    """Test that non-host cannot restart game"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    room.game_state.current_round = 5
    original_round = room.game_state.current_round
    
    # Bob tries to restart
    client2.emit('restart_game', {'room': sample_room})
    
    # Round should not change
    room = game_manager.get_room(sample_room)
    assert room.game_state.current_round == original_round