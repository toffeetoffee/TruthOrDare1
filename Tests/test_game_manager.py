import pytest
from Model.game_manager import GameManager


# T-001 — US-001: Create a game room and get a unique 6-char alphanumeric code
def test_create_room_unique_code(game_manager):
    code1 = game_manager.create_room()
    code2 = game_manager.create_room()

    assert code1 != code2
    assert len(code1) == 6
    assert code1.isalnum()


# T-002 — US-021: Room is deleted when last player leaves
def test_delete_empty_room(game_manager):
    code = game_manager.create_room()
    game_manager.add_player_to_room(code, "s1", "Alice")

    # Now remove the last player
    game_manager.remove_player_from_room(code, "s1")

    assert code not in game_manager.rooms


# T-003 — US-002: Add/remove players from room via GameManager
def test_add_and_remove_player(game_manager):
    code = game_manager.create_room()

    game_manager.add_player_to_room(code, "socket1", "Alice")
    room = game_manager.get_room(code)
    assert len(room.players) == 1

    game_manager.remove_player_from_room(code, "socket1")
    room = game_manager.get_room(code)
    # After removal, room should be deleted because it is empty
    assert room is None
