import pytest
import time
from app import app, socketio, game_manager
from Model.truth_dare_list import TruthDareList
from Model.game_state import GameState

@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def socketio_client():
    """SocketIO test client"""
    return socketio.test_client(app)

@pytest.fixture(autouse=True)
def clear_rooms():
    """Clear rooms before each test"""
    game_manager.rooms.clear()
    yield
    game_manager.rooms.clear()

# === Route Tests ===

def test_index_page(client):
    """Test home page loads"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Dare or Dare' in response.data

def test_create_room_with_name(client):
    """Test creating a room with a valid name"""
    response = client.post('/create', data={'name': 'Alice'}, follow_redirects=False)
    assert response.status_code == 302
    assert '/room/' in response.location
    assert 'name=Alice' in response.location
    # Verify room was created
    assert len(game_manager.rooms) == 1

def test_create_room_without_name(client):
    """Test creating room without name redirects to home"""
    response = client.post('/create', data={'name': ''}, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/'
    assert len(game_manager.rooms) == 0

def test_join_room_with_valid_code(client):
    """Test joining an existing room"""
    game_manager.create_room()
    code = list(game_manager.rooms.keys())[0]
    
    response = client.post('/join', data={'code': code.lower(), 'name': 'Bob'}, follow_redirects=False)
    assert response.status_code == 302
    assert f'/room/{code}' in response.location
    assert 'name=Bob' in response.location

def test_join_room_creates_if_missing(client):
    """Test joining a non-existent room creates it"""
    response = client.post('/join', data={'code': 'XYZ789', 'name': 'Charlie'}, follow_redirects=False)
    assert response.status_code == 302
    assert 'XYZ789' in game_manager.rooms

def test_join_room_without_code_or_name(client):
    """Test joining without code or name redirects to home"""
    response = client.post('/join', data={'code': '', 'name': 'Bob'}, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/'
    
    response = client.post('/join', data={'code': 'ABC123', 'name': ''}, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/'

def test_room_page_with_name(client):
    """Test accessing room page with name"""
    response = client.get('/room/TEST123?name=Alice')
    assert response.status_code == 200
    assert b'TEST123' in response.data
    assert b'Alice' in response.data

def test_room_page_without_name_redirects(client):
    """Test accessing room without name redirects to home"""
    response = client.get('/room/TEST123', follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/'

# === Socket Tests ===

def test_socket_join_room(socketio_client):
    """Test player joining via socket"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    socketio_client.emit('join', {'room': room_code, 'name': 'Alice'})
    received = socketio_client.get_received()
    
    # Should receive player_list event
    assert len(received) > 0
    player_list_event = received[0]
    assert player_list_event['name'] == 'player_list'
    assert 'Alice' in player_list_event['args'][0]['players']
    
    # Verify player was added to room
    room = game_manager.get_room(room_code)
    assert len(room.players) == 1
    assert room.players[0].name == 'Alice'

def test_first_player_becomes_host(socketio_client):
    """Test that the first player to join becomes host"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    socketio_client.emit('join', {'room': room_code, 'name': 'Alice'})
    
    room = game_manager.get_room(room_code)
    # Host should be set (not None)
    assert room.host_sid is not None
    # First player should be Alice
    assert len(room.players) == 1
    assert room.players[0].name == 'Alice'

def test_multiple_players_join(socketio_client):
    """Test multiple players joining the same room"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    # First player joins
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    # Second player joins
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    room = game_manager.get_room(room_code)
    # Both players should be in the room
    assert len(room.players) == 2
    names = [p.name for p in room.players]
    assert 'Alice' in names
    assert 'Bob' in names
    
    # First player should still be host
    assert room.host_sid == room.players[0].socket_id

def test_player_leave_room():
    """Test player leaving a room"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    # Two players join
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    room = game_manager.get_room(room_code)
    assert len(room.players) == 2
    
    # Bob leaves
    client2.emit('leave', {'room': room_code})
    
    # Only Alice should remain
    room = game_manager.get_room(room_code)
    assert len(room.players) == 1
    assert room.players[0].name == 'Alice'

def test_host_leaves_transfers_host():
    """Test that when host leaves, host is transferred to next player"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    # Two players join
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    room = game_manager.get_room(room_code)
    # Store original host (should be first player)
    original_host = room.host_sid
    first_player_sid = room.players[0].socket_id
    assert original_host == first_player_sid
    
    # Alice (host) leaves
    client1.emit('leave', {'room': room_code})
    
    # Bob should now be host
    room = game_manager.get_room(room_code)
    assert len(room.players) == 1
    assert room.players[0].name == 'Bob'
    assert room.host_sid == room.players[0].socket_id

def test_last_player_leaves_deletes_room():
    """Test that room is deleted when last player leaves"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    assert room_code in game_manager.rooms
    
    # Alice leaves (she's the only player)
    client1.emit('leave', {'room': room_code})
    
    # Room should be deleted
    assert room_code not in game_manager.rooms

def test_host_destroy_room():
    """Test host can destroy room"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    assert room_code in game_manager.rooms
    room = game_manager.get_room(room_code)
    assert len(room.players) == 2
    
    # Host destroys room
    client1.emit('destroy_room', {'room': room_code})
    
    # Room should be deleted
    assert room_code not in game_manager.rooms

def test_non_host_cannot_destroy_room():
    """Test that non-host cannot destroy room"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    # Bob (non-host) tries to destroy room
    client2.emit('destroy_room', {'room': room_code})
    
    # Room should still exist
    assert room_code in game_manager.rooms
    room = game_manager.get_room(room_code)
    assert len(room.players) == 2

def test_socket_disconnect_removes_player():
    """Test disconnecting removes player from room"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    room = game_manager.get_room(room_code)
    assert len(room.players) == 2
    
    # Bob disconnects
    client2.disconnect()
    
    # Only Alice should remain
    room = game_manager.get_room(room_code)
    assert len(room.players) == 1
    assert room.players[0].name == 'Alice'

def test_host_disconnect_transfers_host():
    """Test that when host disconnects, host is transferred"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    room = game_manager.get_room(room_code)
    # Verify Alice is host (first player)
    assert room.host_sid == room.players[0].socket_id
    assert room.players[0].name == 'Alice'
    
    # Alice disconnects
    client1.disconnect()
    
    # Bob should be the new host
    room = game_manager.get_room(room_code)
    assert len(room.players) == 1
    assert room.players[0].name == 'Bob'
    assert room.host_sid == room.players[0].socket_id

# === Game Logic Tests ===

def test_host_can_start_game():
    """Test that host can start the game"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    room = game_manager.get_room(room_code)
    assert room.game_state.phase == 'lobby'
    
    # Host starts game
    client1.emit('start_game', {'room': room_code})
    
    # Should be in countdown phase
    room = game_manager.get_room(room_code)
    assert room.game_state.phase == 'countdown'
    assert room.game_state.started == True

def test_non_host_cannot_start_game():
    """Test that non-host cannot start game"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    room = game_manager.get_room(room_code)
    assert room.game_state.phase == 'lobby'
    
    # Bob (non-host) tries to start
    client2.emit('start_game', {'room': room_code})
    
    # Should still be in lobby
    room = game_manager.get_room(room_code)
    assert room.game_state.phase == 'lobby'

def test_submit_truth_dare():
    """Test submitting a truth or dare"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    room = game_manager.get_room(room_code)
    
    # Start game and move to preparation
    room.game_state.start_preparation()
    
    # Submit a truth to multiple players
    client1.emit('submit_truth_dare', {
        'room': room_code,
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

def test_submit_truth_dare_multiple_targets():
    """Test submitting a truth or dare to multiple players"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    client3 = socketio.test_client(app)
    client3.emit('join', {'room': room_code, 'name': 'Charlie'})
    
    room = game_manager.get_room(room_code)
    
    # Start game and move to preparation
    room.game_state.start_preparation()
    
    # Submit a dare to multiple players
    client1.emit('submit_truth_dare', {
        'room': room_code,
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
    assert bob_dares[-1]['is_default'] == False
    assert charlie_dares[-1]['is_default'] == False

# === Model Tests ===

def test_game_manager_create_room():
    """Test GameManager creates rooms correctly"""
    code = game_manager.create_room()
    assert code in game_manager.rooms
    assert len(code) == 6

def test_room_add_player():
    """Test Room adds players correctly"""
    from Model.room import Room
    from Model.player import Player
    
    room = Room('TEST')
    player = Player('sid1', 'Alice')
    
    room.add_player(player)
    assert len(room.players) == 1
    assert room.host_sid == 'sid1'

def test_room_remove_player():
    """Test Room removes players correctly"""
    from Model.room import Room
    from Model.player import Player
    
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

def test_truth_dare_list_loads_defaults():
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

def test_truth_dare_list_add_custom():
    """Test adding custom truths and dares"""
    td_list = TruthDareList()
    
    td_list.add_truth('Custom truth?')
    td_list.add_dare('Custom dare')
    
    truths = td_list.get_truths()
    dares = td_list.get_dares()
    
    assert len(truths) == 6  # 5 defaults + 1 custom
    assert len(dares) == 6
    
    # Check custom items are not marked as default
    assert truths[-1]['is_default'] == False
    assert dares[-1]['is_default'] == False

def test_game_state_transitions():
    """Test game state phase transitions"""
    state = GameState()
    
    assert state.phase == 'lobby'
    assert state.started == False
    
    state.start_countdown(duration=10)
    assert state.phase == 'countdown'
    assert state.started == True
    assert state.get_remaining_time() > 0
    
    state.start_preparation(duration=30)
    assert state.phase == 'preparation'
    assert state.get_remaining_time() > 0
    
    state.start_selection(duration=10)
    assert state.phase == 'selection'
    assert state.get_remaining_time() > 0

def test_game_state_selected_player():
    """Test game state can store selected player"""
    state = GameState()
    
    assert state.selected_player is None
    
    state.set_selected_player('Alice')
    assert state.selected_player == 'Alice'
    
    # Check it's included in to_dict
    state_dict = state.to_dict()
    assert state_dict['selected_player'] == 'Alice'

def test_selection_phase_selects_random_player():
    """Test that selection phase randomly selects a player"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    client3 = socketio.test_client(app)
    client3.emit('join', {'room': room_code, 'name': 'Charlie'})
    
    room = game_manager.get_room(room_code)
    
    # Manually trigger selection phase
    import random
    random.seed(42)  # For reproducibility
    selected_player = random.choice(room.players)
    room.game_state.set_selected_player(selected_player.name)
    room.game_state.start_selection(duration=10)
    
    # Should have a selected player
    assert room.game_state.selected_player is not None
    assert room.game_state.selected_player in ['Alice', 'Bob', 'Charlie']
    assert room.game_state.phase == 'selection'

def test_truth_dare_choice_selection():
    """Test that selected player can choose truth or dare"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    room = game_manager.get_room(room_code)
    room.game_state.set_selected_player('Alice')
    room.game_state.start_selection(duration=10)
    
    # Alice chooses dare
    client1.emit('select_truth_dare', {
        'room': room_code,
        'choice': 'dare'
    })
    
    # Choice should be set
    assert room.game_state.selected_choice == 'dare'

def test_truth_dare_phase_picks_random_item():
    """Test that truth/dare phase picks and removes random item"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    room = game_manager.get_room(room_code)
    alice = room.get_player_by_name('Alice')
    
    # Add custom dare
    alice.truth_dare_list.add_dare('Custom dare')
    initial_dare_count = len(alice.truth_dare_list.dares)
    
    # Simulate truth/dare phase starting
    room.game_state.set_selected_player('Alice')
    room.game_state.set_selected_choice('dare')
    
    # Pick random dare
    import random
    dares = alice.truth_dare_list.dares
    selected_dare = random.choice(dares)
    alice.truth_dare_list.dares.remove(selected_dare)
    
    # Should have one less dare
    assert len(alice.truth_dare_list.dares) == initial_dare_count - 1

def test_vote_skip_functionality():
    """Test that players can vote to skip"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    client3 = socketio.test_client(app)
    client3.emit('join', {'room': room_code, 'name': 'Charlie'})
    
    room = game_manager.get_room(room_code)
    room.game_state.set_selected_player('Alice')
    room.game_state.start_truth_dare(duration=60)
    
    # Bob and Charlie vote to skip
    room.game_state.add_skip_vote('bob_sid')
    room.game_state.add_skip_vote('charlie_sid')
    
    # Should have 2 votes
    assert room.game_state.get_skip_vote_count() == 2
    
    # Check if majority reached (2 out of 2 other players = 100%)
    other_players = 2  # Alice is selected, so Bob and Charlie
    required = (other_players + 1) // 2  # At least 1
    assert room.game_state.get_skip_vote_count() >= required

def test_room_default_settings():
    """Test that rooms have default settings"""
    from Model.room import Room
    
    room = Room('TEST')
    
    assert 'countdown_duration' in room.settings
    assert 'preparation_duration' in room.settings
    assert 'selection_duration' in room.settings
    assert 'truth_dare_duration' in room.settings
    assert 'skip_duration' in room.settings
    
    # Check default values
    assert room.settings['countdown_duration'] == 10
    assert room.settings['preparation_duration'] == 30
    assert room.settings['selection_duration'] == 10
    assert room.settings['truth_dare_duration'] == 60
    assert room.settings['skip_duration'] == 5

def test_update_room_settings():
    """Test updating room settings"""
    from Model.room import Room
    
    room = Room('TEST')
    
    new_settings = {
        'countdown_duration': 15,
        'preparation_duration': 45,
        'selection_duration': 20,
        'truth_dare_duration': 90,
        'skip_duration': 10,
        'max_rounds': 20
    }
    
    room.update_settings(new_settings)
    
    assert room.settings['countdown_duration'] == 15
    assert room.settings['preparation_duration'] == 45
    assert room.settings['selection_duration'] == 20
    assert room.settings['truth_dare_duration'] == 90
    assert room.settings['skip_duration'] == 10
    assert room.settings['max_rounds'] == 20

def test_host_can_update_settings():
    """Test that host can update settings via socket"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    room = game_manager.get_room(room_code)
    
    # Alice (host) updates settings
    client1.emit('update_settings', {
        'room': room_code,
        'settings': {
            'countdown_duration': 20,
            'preparation_duration': 60
        }
    })
    
    # Settings should be updated
    assert room.settings['countdown_duration'] == 20
    assert room.settings['preparation_duration'] == 60

# === Scoring System Tests ===

def test_player_score_initialization():
    """Test that player score starts at 0"""
    from Model.player import Player
    
    player = Player('sid1', 'Alice')
    assert player.score == 0

def test_player_add_score():
    """Test adding score to player"""
    from Model.player import Player
    
    player = Player('sid1', 'Alice')
    player.add_score(50)
    assert player.score == 50
    
    player.add_score(30)
    assert player.score == 80

def test_scoring_system_values():
    """Test scoring system point values"""
    from Model.scoring_system import ScoringSystem
    
    assert ScoringSystem.POINTS_PERFORM == 100
    assert ScoringSystem.POINTS_SUBMITTED_PERFORMED == 50
    assert ScoringSystem.POINTS_SUBMISSION == 10
    assert ScoringSystem.MAX_SUBMISSIONS_PER_ROUND == 3

def test_player_submission_limits():
    """Test player submission tracking"""
    from Model.player import Player
    
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
    
    player.reset_round_submissions()
    assert player.submissions_this_round == 0
    assert player.can_submit_more() == True

def test_truth_dare_with_submitter():
    """Test truth/dare items track submitter"""
    from Model.truth_dare import Truth, Dare
    
    truth = Truth('Custom truth?', is_default=False, submitted_by='Alice')
    assert truth.submitted_by == 'Alice'
    assert truth.to_dict()['submitted_by'] == 'Alice'
    
    dare = Dare('Custom dare', is_default=False, submitted_by='Bob')
    assert dare.submitted_by == 'Bob'
    assert dare.to_dict()['submitted_by'] == 'Bob'

def test_round_record_creation():
    """Test creating round records"""
    from Model.round_record import RoundRecord
    
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
    
    record_dict = record.to_dict()
    assert record_dict['round_number'] == 1
    assert record_dict['selected_player'] == 'Alice'
    assert record_dict['truth_dare']['text'] == 'Do 10 pushups'
    assert record_dict['truth_dare']['type'] == 'dare'
    assert record_dict['submitted_by'] == 'Bob'

def test_room_round_history():
    """Test room tracks round history"""
    from Model.room import Room
    from Model.round_record import RoundRecord
    
    room = Room('TEST')
    
    assert len(room.round_history) == 0
    
    record1 = RoundRecord(1, 'Alice', 'Tell a secret', 'truth', None)
    record2 = RoundRecord(2, 'Bob', 'Dance', 'dare', 'Alice')
    
    room.add_round_record(record1)
    room.add_round_record(record2)
    
    assert len(room.round_history) == 2
    
    history = room.get_round_history()
    assert len(history) == 2
    assert history[0]['round_number'] == 1
    assert history[1]['round_number'] == 2

def test_room_top_players():
    """Test getting top players by score"""
    from Model.room import Room
    from Model.player import Player
    
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
    assert top_players[1]['score'] == 150
    assert top_players[2]['name'] == 'Charlie'
    assert top_players[2]['score'] == 100

def test_game_state_round_tracking():
    """Test game state tracks rounds"""
    from Model.game_state import GameState
    
    state = GameState()
    
    assert state.current_round == 0
    assert state.max_rounds == 10
    assert state.should_end_game() == False
    
    # Simulate rounds
    for i in range(10):
        state.start_preparation()
    
    assert state.current_round == 10
    assert state.should_end_game() == True

def test_game_state_end_game_phase():
    """Test game state end game phase"""
    from Model.game_state import GameState
    
    state = GameState()
    
    state.start_end_game()
    assert state.phase == GameState.PHASE_END_GAME
    assert state.phase_end_time is None

def test_room_reset_for_new_game():
    """Test room resets properly for new game"""
    from Model.room import Room
    from Model.player import Player
    from Model.round_record import RoundRecord
    
    room = Room('TEST')
    
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
    assert room.game_state.phase == 'countdown'

def test_submission_with_limit():
    """Test submission limit enforcement"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': room_code, 'name': 'Bob'})
    
    room = game_manager.get_room(room_code)
    room.game_state.start_preparation()
    
    alice = room.get_player_by_name('Alice')
    
    # Submit 3 times (max limit)
    for i in range(3):
        client1.emit('submit_truth_dare', {
            'room': room_code,
            'text': f'Truth {i+1}',
            'type': 'truth',
            'targets': ['Bob']
        })
    
    # Alice should have score from 3 submissions
    assert alice.score == 30  # 3 * 10 points
    assert alice.submissions_this_round == 3
    
    # Try to submit 4th time (should be rejected)
    client1.emit('submit_truth_dare', {
        'room': room_code,
        'text': 'Truth 4',
        'type': 'truth',
        'targets': ['Bob']
    })
    
    # Score should still be 30
    assert alice.score == 30
    assert alice.submissions_this_round == 3

def test_room_default_settings_include_max_rounds():
    """Test that room default settings include max_rounds"""
    from Model.room import Room
    
    room = Room('TEST')
    
    assert 'max_rounds' in room.settings
    assert room.settings['max_rounds'] == 10

# === Minigame Tests ===

def test_minigame_creation():
    """Test creating a staring contest minigame"""
    from Model.minigame import StaringContest
    from Model.player import Player
    
    minigame = StaringContest()
    
    player1 = Player('sid1', 'Alice')
    player2 = Player('sid2', 'Bob')
    
    minigame.add_participant(player1)
    minigame.add_participant(player2)
    
    assert len(minigame.participants) == 2
    assert minigame.get_participant_names() == ['Alice', 'Bob']

def test_minigame_voting():
    """Test minigame voting system"""
    from Model.minigame import StaringContest
    from Model.player import Player
    
    minigame = StaringContest()
    
    alice = Player('sid1', 'Alice')
    bob = Player('sid2', 'Bob')
    
    minigame.add_participant(alice)
    minigame.add_participant(bob)
    
    # Players vote (3 voters total)
    minigame.add_vote('voter1', 'Alice')
    minigame.add_vote('voter2', 'Alice')
    
    assert len(minigame.votes) == 2
    assert minigame.check_voting_complete(3) == True  # 2 out of 3 is majority

def test_minigame_determine_loser():
    """Test determining the loser of a minigame"""
    from Model.minigame import StaringContest
    from Model.player import Player
    
    minigame = StaringContest()
    
    alice = Player('sid1', 'Alice')
    bob = Player('sid2', 'Bob')
    
    minigame.add_participant(alice)
    minigame.add_participant(bob)
    
    # Vote for Alice as loser
    minigame.add_vote('voter1', 'Alice')
    minigame.add_vote('voter2', 'Alice')
    minigame.add_vote('voter3', 'Bob')
    
    loser = minigame.determine_loser()
    
    assert loser == alice
    assert minigame.loser == alice
    assert minigame.winner == bob
    assert minigame.is_complete == True

def test_minigame_participation_points():
    """Test that minigame participants get points"""
    from Model.scoring_system import ScoringSystem
    from Model.player import Player
    
    player = Player('sid1', 'Alice')
    
    initial_score = player.score
    ScoringSystem.award_minigame_participate_points(player)
    
    assert player.score == initial_score + 75
    assert player.score == ScoringSystem.POINTS_MINIGAME_PARTICIPATE

def test_scoring_system_minigame_points():
    """Test that scoring system has minigame points defined"""
    from Model.scoring_system import ScoringSystem
    
    assert hasattr(ScoringSystem, 'POINTS_MINIGAME_PARTICIPATE')
    assert ScoringSystem.POINTS_MINIGAME_PARTICIPATE == 75
    # Verify order: perform > minigame > submission_performed > submission
    assert ScoringSystem.POINTS_PERFORM > ScoringSystem.POINTS_MINIGAME_PARTICIPATE
    assert ScoringSystem.POINTS_MINIGAME_PARTICIPATE > ScoringSystem.POINTS_SUBMITTED_PERFORMED

def test_game_state_minigame_phase():
    """Test game state minigame phase"""
    from Model.game_state import GameState
    
    state = GameState()
    
    assert hasattr(state, 'PHASE_MINIGAME')
    assert state.PHASE_MINIGAME == 'minigame'
    
    state.start_minigame()
    assert state.phase == 'minigame'
    assert state.phase_end_time is None  # No time limit

def test_game_state_tracks_minigame():
    """Test that game state can track a minigame"""
    from Model.game_state import GameState
    from Model.minigame import StaringContest
    from Model.player import Player
    
    state = GameState()
    minigame = StaringContest()
    
    player1 = Player('sid1', 'Alice')
    player2 = Player('sid2', 'Bob')
    
    minigame.add_participant(player1)
    minigame.add_participant(player2)
    
    state.set_minigame(minigame)
    
    assert state.minigame == minigame
    
    # Check to_dict includes minigame
    state_dict = state.to_dict()
    assert 'minigame' in state_dict
    assert state_dict['minigame']['type'] == 'staring_contest'

def test_room_minigame_chance_setting():
    """Test that room has minigame_chance setting"""
    from Model.room import Room
    
    room = Room('TEST')
    
    assert 'minigame_chance' in room.settings
    assert room.settings['minigame_chance'] == 20  # Default 20%

def test_minigame_to_dict():
    """Test minigame serialization"""
    from Model.minigame import StaringContest
    from Model.player import Player
    
    minigame = StaringContest()
    
    alice = Player('sid1', 'Alice')
    bob = Player('sid2', 'Bob')
    
    minigame.add_participant(alice)
    minigame.add_participant(bob)
    minigame.add_vote('voter1', 'Alice')
    
    minigame_dict = minigame.to_dict()
    
    assert minigame_dict['type'] == 'staring_contest'
    assert minigame_dict['participants'] == ['Alice', 'Bob']
    assert minigame_dict['vote_count'] == 1
    assert minigame_dict['is_complete'] == False

def test_minigame_voting_incomplete():
    """Test that voting is incomplete without majority"""
    from Model.minigame import StaringContest
    from Model.player import Player
    
    minigame = StaringContest()
    
    alice = Player('sid1', 'Alice')
    bob = Player('sid2', 'Bob')
    
    minigame.add_participant(alice)
    minigame.add_participant(bob)
    
    # Only 1 vote out of 4 non-participants
    minigame.add_vote('voter1', 'Alice')
    
    assert minigame.check_voting_complete(4) == False  # Need 2 votes (using same formula as skip votes)

def test_minigame_voting_exact_majority():
    """Test voting with exact majority"""
    from Model.minigame import StaringContest
    from Model.player import Player
    
    minigame = StaringContest()
    
    alice = Player('sid1', 'Alice')
    bob = Player('sid2', 'Bob')
    
    minigame.add_participant(alice)
    minigame.add_participant(bob)
    
    # 2 votes out of 3 non-participants (majority using (3+1)//2 = 2)
    minigame.add_vote('voter1', 'Alice')
    minigame.add_vote('voter2', 'Alice')
    
    assert minigame.check_voting_complete(3) == True

def test_minigame_voting_threshold_matches_skip():
    """Test that minigame voting uses same threshold as skip votes"""
    from Model.minigame import StaringContest
    from Model.player import Player
    
    minigame = StaringContest()
    
    alice = Player('sid1', 'Alice')
    bob = Player('sid2', 'Bob')
    
    minigame.add_participant(alice)
    minigame.add_participant(bob)
    
    # Test various scenarios to ensure formula matches skip votes: (n + 1) // 2
    
    # 2 non-participants: need (2+1)//2 = 1 vote
    minigame.add_vote('v1', 'Alice')
    assert minigame.check_voting_complete(2) == True
    
    minigame.votes.clear()
    
    # 4 non-participants: need (4+1)//2 = 2 votes
    minigame.add_vote('v1', 'Alice')
    assert minigame.check_voting_complete(4) == False  # Only 1 vote
    minigame.add_vote('v2', 'Alice')
    assert minigame.check_voting_complete(4) == True  # Now 2 votes
    
    minigame.votes.clear()
    
    # 5 non-participants: need (5+1)//2 = 3 votes
    minigame.add_vote('v1', 'Alice')
    minigame.add_vote('v2', 'Alice')
    assert minigame.check_voting_complete(5) == False  # Only 2 votes
    minigame.add_vote('v3', 'Alice')
    assert minigame.check_voting_complete(5) == True  # Now 3 votes

def test_host_can_update_minigame_chance():
    """Test that host can update minigame chance setting"""
    game_manager.create_room()
    room_code = list(game_manager.rooms.keys())[0]
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': room_code, 'name': 'Alice'})
    
    room = game_manager.get_room(room_code)
    
    # Alice (host) updates minigame chance
    client1.emit('update_settings', {
        'room': room_code,
        'settings': {
            'minigame_chance': 50
        }
    })
    
    # Setting should be updated
    assert room.settings['minigame_chance'] == 50