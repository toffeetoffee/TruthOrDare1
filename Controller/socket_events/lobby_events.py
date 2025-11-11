from flask_socketio import join_room, leave_room, emit
from flask import request


def register_lobby_events(socketio, game_manager):
    """Socket events related to lobby and player connections."""

    @socketio.on("join")
    def handle_join(data):
        name = data.get("name", "Anonymous")
        room_code = data.get("room")

        room = game_manager.get_room(room_code)
        if not room:
            emit("error", {"message": "Room not found."})
            return

        player = room.add_player(request.sid, name)
        join_room(room_code)

        # Create the payload structure JS expects
        payload = {
            "players": [p.name for p in room.players],
            "host_sid": room.host_sid,
        }

        emit("player_list", payload, to=room_code)
        emit("joined_room", {"name": name, "room": room_code})

    @socketio.on("leave")
    def handle_leave(data):
        room_code = data.get("room")
        room = game_manager.get_room(room_code)
        if not room:
            return

        player = room.get_player_by_sid(request.sid)
        if player:
            room.remove_player(player)
            leave_room(room_code)

            payload = {
                "players": [p.name for p in room.players],
                "host_sid": room.host_sid,
            }
            emit("player_list", payload, to=room_code)
            emit("left_room", {"name": player.name}, to=room_code)

        if room.is_empty():
            game_manager.remove_room(room_code)

    @socketio.on("disconnect")
    def handle_disconnect():
        for room in list(game_manager.rooms.values()):
            player = room.get_player_by_sid(request.sid)
            if player:
                room.remove_player(player)

                payload = {
                    "players": [p.name for p in room.players],
                    "host_sid": room.host_sid,
                }
                emit("player_list", payload, to=room.code)

                if room.is_empty():
                    game_manager.remove_room(room.code)