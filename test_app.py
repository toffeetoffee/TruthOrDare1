import pytest
from app import app, socketio, game_manager

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
