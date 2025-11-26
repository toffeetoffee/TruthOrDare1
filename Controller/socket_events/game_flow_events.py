import threading
import time

from flask_socketio import emit
from flask import request

from .helpers import start_selection_or_minigame, start_truth_dare_phase_handler


def register_game_flow_events(socketio, game_manager):
    """Register events for starting/restarting the game and in-round flow."""

    @socketio.on("start_game")
    def on_start_game(data):
        try:
            room_code = data.get("room")

            if not room_code:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            countdown_duration = room.settings["countdown_duration"]
            room.game_state.start_countdown(duration=countdown_duration)

            emit("game_state_update", room.game_state.to_dict(), room=room_code)

            def start_preparation():
                try:
                    time.sleep(countdown_duration)
                    room_inner = game_manager.get_room(room_code)
                    if room_inner:
                        prep_duration = room_inner.settings["preparation_duration"]
                        room_inner.game_state.start_preparation(duration=prep_duration)

                        room_inner.reset_player_round_submissions()

                        socketio.emit(
                            "game_state_update",
                            room_inner.game_state.to_dict(),
                            room=room_code,
                            namespace="/",
                        )

                        def after_prep():
                            try:
                                time.sleep(prep_duration)
                                start_selection_or_minigame(room_code)
                            except Exception as e:
                                print(f"[ERROR] after_prep: {e}")

                        prep_thread = threading.Thread(target=after_prep)
                        prep_thread.daemon = True
                        prep_thread.start()
                except Exception as e:
                    print(f"[ERROR] start_preparation: {e}")

            thread = threading.Thread(target=start_preparation)
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"[ERROR] start_game: {e}")

    @socketio.on("restart_game")
    def on_restart_game(data):
        try:
            room_code = data.get("room")

            if not room_code:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            room.reset_for_new_game()

            countdown_duration = room.settings["countdown_duration"]
            room.game_state.start_countdown(duration=countdown_duration)

            emit("game_state_update", room.game_state.to_dict(), room=room_code)

            on_start_game({"room": room_code})
        except Exception as e:
            print(f"[ERROR] restart_game: {e}")

    @socketio.on("select_truth_dare")
    def on_select_truth_dare(data):
        try:
            room_code = data.get("room")
            choice = data.get("choice")

            if not room_code or not choice:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if room.game_state.phase != "selection":
                return

            player = room.get_player_by_sid(request.sid)
            if not player or player.name != room.game_state.selected_player:
                return

            room.game_state.set_selected_choice(choice)

            emit("game_state_update", room.game_state.to_dict(), room=room_code)
        except Exception as e:
            print(f"[ERROR] select_truth_dare: {e}")

    @socketio.on("minigame_vote")
    def on_minigame_vote(data):
        try:
            room_code = data.get("room")
            voted_player = data.get("voted_player")

            if not room_code or not voted_player:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if room.game_state.phase != "minigame":
                return

            minigame = room.game_state.minigame
            if not minigame:
                return

            player = room.get_player_by_sid(request.sid)
            if not player:
                return

            participant_names = minigame.get_participant_names()
            if player.name in participant_names:
                return

            if request.sid in minigame.votes:
                return

            minigame.add_vote(request.sid, voted_player)

            loser = minigame.check_immediate_winner()

            if loser:
                room.game_state.set_selected_player(loser.name)

                selection_duration = room.settings["selection_duration"]
                room.game_state.start_selection(duration=selection_duration)

                socketio.emit(
                    "game_state_update",
                    room.game_state.to_dict(),
                    room=room_code,
                    namespace="/",
                )

                def start_td():
                    try:
                        time.sleep(selection_duration)
                        start_truth_dare_phase_handler(room_code)
                    except Exception as e:
                        print(f"[ERROR] start_td: {e}")

                td_thread = threading.Thread(target=start_td)
                td_thread.daemon = True
                td_thread.start()
            elif minigame.check_all_voted():
                vote_counts = minigame.get_vote_counts()

                if len(vote_counts) == 2:
                    counts = list(vote_counts.values())
                    if counts[0] == counts[1]:
                        loser = minigame.handle_tie()
                    else:
                        loser = minigame.determine_loser()
                else:
                    loser = minigame.determine_loser()

                if loser:
                    room.game_state.set_selected_player(loser.name)

                    selection_duration = room.settings["selection_duration"]
                    room.game_state.start_selection(duration=selection_duration)

                    socketio.emit(
                        "game_state_update",
                        room.game_state.to_dict(),
                        room=room_code,
                        namespace="/",
                    )

                    def start_td():
                        try:
                            time.sleep(selection_duration)
                            start_truth_dare_phase_handler(room_code)
                        except Exception as e:
                            print(f"[ERROR] start_td: {e}")

                    td_thread = threading.Thread(target=start_td)
                    td_thread.daemon = True
                    td_thread.start()
            else:
                emit("game_state_update", room.game_state.to_dict(), room=room_code)
        except Exception as e:
            print(f"[ERROR] minigame_vote: {e}")

    @socketio.on("vote_skip")
    def on_vote_skip(data):
        try:
            room_code = data.get("room")

            if not room_code:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if room.game_state.phase != "truth_dare":
                return

            if room.game_state.skip_activated:
                return

            player = room.get_player_by_sid(request.sid)
            if not player or player.name == room.game_state.selected_player:
                return

            room.game_state.add_skip_vote(request.sid)

            other_players_count = len(room.players) - 1
            required_votes = (other_players_count + 1) // 2

            if room.game_state.get_skip_vote_count() >= required_votes:
                room.game_state.activate_skip()

                skip_duration = room.settings["skip_duration"]
                room.game_state.reduce_timer(skip_duration)

            emit("game_state_update", room.game_state.to_dict(), room=room_code)
        except Exception as e:
            print(f"[ERROR] vote_skip: {e}")