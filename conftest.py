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
    """Clear rooms before and after each test"""
    game_manager.rooms.clear()
    yield
    game_manager.rooms.clear()

@pytest.fixture
def sample_room():
    """Create a sample room for testing"""
    code = game_manager.create_room()
    return code

@pytest.fixture
def room_with_players(sample_room):
    """Create a room with two players"""
    from Model.player import Player
    room = game_manager.get_room(sample_room)
    
    alice = Player('alice_sid', 'Alice')
    bob = Player('bob_sid', 'Bob')
    
    room.add_player(alice)
    room.add_player(bob)
    
    return sample_room, room