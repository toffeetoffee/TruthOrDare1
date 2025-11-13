# tests/conftest.py
import pytest

from app import app, socketio, game_manager as global_game_manager
from Model.room import Room
from Model.player import Player
from Model.ai_generator import AIGenerator


# ----------------------------------------------------------------------
# Flask test client
# ----------------------------------------------------------------------
@pytest.fixture
def test_client():
    app.testing = True
    return app.test_client()


# ----------------------------------------------------------------------
# Socket.IO test client
# ----------------------------------------------------------------------
@pytest.fixture
def socket_client():
    # Attach to the same app/socketio used in app.py
    test_client = app.test_client()
    client = socketio.test_client(app, flask_test_client=test_client)
    return client


# ----------------------------------------------------------------------
# GameManager fixture (cleared state)
# ----------------------------------------------------------------------
@pytest.fixture
def game_manager():
    # Ensure we start with a clean rooms dict
    global_game_manager.rooms.clear()
    return global_game_manager


# ----------------------------------------------------------------------
# Room fixture (standalone room, not registered in GameManager)
# ----------------------------------------------------------------------
@pytest.fixture
def room():
    return Room("TEST01")


# ----------------------------------------------------------------------
# Player fixture
# ----------------------------------------------------------------------
@pytest.fixture
def player():
    return Player("socket123", "TestPlayer")


# ----------------------------------------------------------------------
# Mock AI generator (no real API calls)
# ----------------------------------------------------------------------
@pytest.fixture
def mock_ai_generator(monkeypatch):
    """
    Creates an AIGenerator instance but monkeypatches its generate_* methods
    to avoid real network calls.
    """
    # Fake env (in case your AIGenerator requires GEMINI_API_KEY)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    ai = AIGenerator()

    def fake_truth(existing):
        return "AI Generated Truth"

    def fake_dare(existing):
        return "AI Generated Dare"

    monkeypatch.setattr(ai, "generate_truth", fake_truth)
    monkeypatch.setattr(ai, "generate_dare", fake_dare)

    return ai
