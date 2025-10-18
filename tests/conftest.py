"""
Shared pytest fixtures for all tests.
"""

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
    """Create a sample room with a code"""
    code = game_manager.create_room()
    return code, game_manager.get_room(code)