from Model.room import Room
from Model.player import Player


# T-014 — US-016: Room settings can be updated
def test_room_settings_update(room):
    original = room.settings["countdown_duration"]
    room.settings["countdown_duration"] = 15

    assert room.settings["countdown_duration"] == 15
    assert room.settings["countdown_duration"] != original


# T-024 — US-024: Host reassignment when host leaves
def test_host_reassignment():
    room = Room("XYZ123")

    p1 = Player("s1", "Alice")
    p2 = Player("s2", "Bob")

    room.add_player(p1)  # first join -> host
    room.add_player(p2)

    assert room.host_sid == "s1"

    room.remove_player("s1")
    # Host should be reassigned to the remaining player
    assert room.host_sid == "s2"
