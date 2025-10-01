import pytest
from app import app, socketio, rooms, gen_code

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
    rooms.clear()
    yield
    rooms.clear()

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
    # Verify room was created with correct structure
    assert len(rooms) == 1
    room_code = list(rooms.keys())[0]
    assert 'host_sid' in rooms[room_code]
    assert 'players' in rooms[room_code]
    assert rooms[room_code]['players'] == []

def test_create_room_without_name(client):
    """Test creating room without name redirects to home"""
    response = client.post('/create', data={'name': ''}, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/'
    assert len(rooms) == 0

def test_join_room_with_valid_code(client):
    """Test joining an existing room"""
    rooms['ABC123'] = {'host_sid': None, 'players': []}
    
    response = client.post('/join', data={'code': 'abc123', 'name': 'Bob'}, follow_redirects=False)
    assert response.status_code == 302
    assert '/room/ABC123' in response.location
    assert 'name=Bob' in response.location

def test_join_room_creates_if_missing(client):
    """Test joining a non-existent room creates it"""
    response = client.post('/join', data={'code': 'XYZ789', 'name': 'Charlie'}, follow_redirects=False)
    assert response.status_code == 302
    assert 'XYZ789' in rooms
    assert rooms['XYZ789']['players'] == []

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
    rooms['ROOM1'] = {'host_sid': None, 'players': []}
    
    socketio_client.emit('join', {'room': 'ROOM1', 'name': 'Alice'})
    received = socketio_client.get_received()
    
    # Should receive player_list event
    assert len(received) > 0
    player_list_event = received[0]
    assert player_list_event['name'] == 'player_list'
    assert 'Alice' in player_list_event['args'][0]['players']
    
    # Verify player was added to room
    assert len(rooms['ROOM1']['players']) == 1
    assert rooms['ROOM1']['players'][0]['name'] == 'Alice'

def test_first_player_becomes_host(socketio_client):
    """Test that the first player to join becomes host"""
    rooms['ROOM2'] = {'host_sid': None, 'players': []}
    
    socketio_client.emit('join', {'room': 'ROOM2', 'name': 'Alice'})
    
    # Host should be set (not None)
    assert rooms['ROOM2']['host_sid'] is not None
    # First player should be Alice
    assert len(rooms['ROOM2']['players']) == 1
    assert rooms['ROOM2']['players'][0]['name'] == 'Alice'

def test_multiple_players_join(socketio_client):
    """Test multiple players joining the same room"""
    rooms['ROOM3'] = {'host_sid': None, 'players': []}
    
    # First player joins
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': 'ROOM3', 'name': 'Alice'})
    
    # Second player joins
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': 'ROOM3', 'name': 'Bob'})
    
    # Both players should be in the room
    assert len(rooms['ROOM3']['players']) == 2
    names = [p['name'] for p in rooms['ROOM3']['players']]
    assert 'Alice' in names
    assert 'Bob' in names
    
    # First player should still be host (verify by checking it matches first player's sid)
    assert rooms['ROOM3']['host_sid'] == rooms['ROOM3']['players'][0]['sid']

def test_player_leave_room():
    """Test player leaving a room"""
    rooms['ROOM4'] = {'host_sid': None, 'players': []}
    
    # Two players join
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': 'ROOM4', 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': 'ROOM4', 'name': 'Bob'})
    
    assert len(rooms['ROOM4']['players']) == 2
    
    # Bob leaves
    client2.emit('leave', {'room': 'ROOM4'})
    
    # Only Alice should remain
    assert len(rooms['ROOM4']['players']) == 1
    assert rooms['ROOM4']['players'][0]['name'] == 'Alice'

def test_host_leaves_transfers_host():
    """Test that when host leaves, host is transferred to next player"""
    rooms['ROOM5'] = {'host_sid': None, 'players': []}
    
    # Two players join
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': 'ROOM5', 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': 'ROOM5', 'name': 'Bob'})
    
    # Store original host (should be first player)
    original_host = rooms['ROOM5']['host_sid']
    first_player_sid = rooms['ROOM5']['players'][0]['sid']
    assert original_host == first_player_sid
    
    # Alice (host) leaves
    client1.emit('leave', {'room': 'ROOM5'})
    
    # Bob should now be host (should match the remaining player's sid)
    assert len(rooms['ROOM5']['players']) == 1
    assert rooms['ROOM5']['players'][0]['name'] == 'Bob'
    assert rooms['ROOM5']['host_sid'] == rooms['ROOM5']['players'][0]['sid']

def test_last_player_leaves_deletes_room():
    """Test that room is deleted when last player leaves"""
    rooms['ROOM6'] = {'host_sid': None, 'players': []}
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': 'ROOM6', 'name': 'Alice'})
    
    assert 'ROOM6' in rooms
    
    # Alice leaves (she's the only player)
    client1.emit('leave', {'room': 'ROOM6'})
    
    # Room should be deleted
    assert 'ROOM6' not in rooms

def test_host_destroy_room():
    """Test host can destroy room"""
    rooms['ROOM7'] = {'host_sid': None, 'players': []}
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': 'ROOM7', 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': 'ROOM7', 'name': 'Bob'})
    
    assert 'ROOM7' in rooms
    assert len(rooms['ROOM7']['players']) == 2
    
    # Host destroys room
    client1.emit('destroy_room', {'room': 'ROOM7'})
    
    # Room should be deleted
    assert 'ROOM7' not in rooms

def test_non_host_cannot_destroy_room():
    """Test that non-host cannot destroy room"""
    rooms['ROOM8'] = {'host_sid': None, 'players': []}
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': 'ROOM8', 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': 'ROOM8', 'name': 'Bob'})
    
    # Bob (non-host) tries to destroy room
    client2.emit('destroy_room', {'room': 'ROOM8'})
    
    # Room should still exist
    assert 'ROOM8' in rooms
    assert len(rooms['ROOM8']['players']) == 2

def test_socket_disconnect_removes_player():
    """Test disconnecting removes player from room"""
    rooms['ROOM9'] = {'host_sid': None, 'players': []}
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': 'ROOM9', 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': 'ROOM9', 'name': 'Bob'})
    
    assert len(rooms['ROOM9']['players']) == 2
    
    # Bob disconnects
    client2.disconnect()
    
    # Only Alice should remain
    assert len(rooms['ROOM9']['players']) == 1
    assert rooms['ROOM9']['players'][0]['name'] == 'Alice'

def test_host_disconnect_transfers_host():
    """Test that when host disconnects, host is transferred"""
    rooms['ROOM10'] = {'host_sid': None, 'players': []}
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': 'ROOM10', 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': 'ROOM10', 'name': 'Bob'})
    
    # Verify Alice is host (first player)
    assert rooms['ROOM10']['host_sid'] == rooms['ROOM10']['players'][0]['sid']
    assert rooms['ROOM10']['players'][0]['name'] == 'Alice'
    
    # Alice disconnects
    client1.disconnect()
    
    # Bob should be the new host
    assert len(rooms['ROOM10']['players']) == 1
    assert rooms['ROOM10']['players'][0]['name'] == 'Bob'
    assert rooms['ROOM10']['host_sid'] == rooms['ROOM10']['players'][0]['sid']

# === Utility Tests ===

def test_gen_code_length():
    """Test room code generation length"""
    code = gen_code(6)
    assert len(code) == 6
    
def test_gen_code_format():
    """Test room code contains only uppercase letters and digits"""
    code = gen_code(8)
    assert code.isupper()
    assert code.isalnum()

def test_gen_code_uniqueness():
    """Test generated codes are different (probabilistically)"""
    codes = [gen_code(6) for _ in range(100)]
    assert len(set(codes)) > 90