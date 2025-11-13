# tests/integration/test_routes.py

# T-030 — US-001: /create creates room and redirects to /room/<code>
def test_create_room_route(test_client, game_manager):
    res = test_client.post("/create", data={"name": "Host"})
    assert res.status_code == 302
    assert "/room/" in res.location


# T-031 — US-002: /join invalid code redirects back to index
def test_join_room_invalid(test_client, game_manager):
    res = test_client.post("/join", data={"code": "BAD123", "name": "Alice"})
    assert res.status_code == 302
    # Redirect to index
    assert res.location.endswith("/")


# T-032 — US-002: /join valid code redirects to /room/<code>
def test_join_room_valid(test_client, game_manager):
    code = game_manager.create_room()

    res = test_client.post("/join", data={"code": code, "name": "Bob"})
    assert res.status_code == 302
    assert f"/room/{code}" in res.location
