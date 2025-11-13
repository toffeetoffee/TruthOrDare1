# tests/socket/test_socket_events.py

# T-040 — US-002 & US-003: "join" event adds player and emits correct update event
def test_socket_join_room(socket_client, game_manager):
    room_code = game_manager.create_room()

    socket_client.emit("join", {"room": room_code, "name": "Alice"})
    received = socket_client.get_received()

    event_names = [pkt["name"] for pkt in received]
    
    # Your backend emits "player_list" — not "room_state"
    assert "player_list" in event_names

    room = game_manager.get_room(room_code)
    assert room is not None
    assert any(p.name == "Alice" for p in room.players)



# T-041 — US-016: "update_settings" only works for host and updates room settings
def test_socket_update_settings(socket_client, game_manager):
    room_code = game_manager.create_room()

    # First, join as host via this socket
    socket_client.emit("join", {"room": room_code, "name": "Host"})
    socket_client.get_received()  # clear buffer

    # Now, emit update_settings as host
    socket_client.emit(
        "update_settings",
        {"room": room_code, "settings": {"countdown_duration": 15}},
    )

    room = game_manager.get_room(room_code)
    assert room.settings["countdown_duration"] == 15
