import threading
import time

from flask_socketio import emit
from flask import request

from .helpers import start_selection_or_minigame, start_truth_dare_phase_handler


def register_game_flow_events(socketio, game_manager):

    @socketio.on("start_game")
    def on_start_game(data):
        try:
            rc = data.get("room")

            if not rc:
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            cdur = room.settings["countdown_duration"]
            room.game_state.start_countdown(duration=cdur)

            emit("game_state_update", room.game_state.to_dict(), room=rc)

            # countdown -> prep -> then selection/minigame in background
            def start_prep():
                try:
                    time.sleep(cdur)
                    room_inner = game_manager.get_room(rc)
                    if room_inner:
                        pdur = room_inner.settings["preparation_duration"]
                        room_inner.game_state.start_preparation(duration=pdur)

                        room_inner.reset_player_round_submissions()

                        socketio.emit(
                            "game_state_update",
                            room_inner.game_state.to_dict(),
                            room=rc,
                            namespace="/",
                        )

                        def after_prep():
                            try:
                                time.sleep(pdur)
                                start_selection_or_minigame(rc)
                            except Exception as e:
                                print(f"[ERROR] after_prep: {e}")

                        t2 = threading.Thread(target=after_prep)
                        t2.daemon = True
                        t2.start()
                except Exception as e:
                    print(f"[ERROR] start_preparation: {e}")

            t = threading.Thread(target=start_prep)
            t.daemon = True
            t.start()
        except Exception as e:
            print(f"[ERROR] start_game: {e}")

    @socketio.on("restart_game")
    def on_restart_game(data):
        try:
            rc = data.get("room")

            if not rc:
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            if not room.is_host(request.sid):
                return

            room.reset_for_new_game()

            cdur = room.settings["countdown_duration"]
            room.game_state.start_countdown(duration=cdur)

            emit("game_state_update", room.game_state.to_dict(), room=rc)

            # just reuse start logic
            on_start_game({"room": rc})
        except Exception as e:
            print(f"[ERROR] restart_game: {e}")

    @socketio.on("select_truth_dare")
    def on_select_truth_dare(data):
        try:
            rc = data.get("room")
            choice = data.get("choice")

            if not rc or not choice:
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            if room.game_state.phase != "selection":
                return

            player = room.get_player_by_sid(request.sid)
            if not player or player.name != room.game_state.selected_player:
                return

            room.game_state.set_selected_choice(choice)

            emit("game_state_update", room.game_state.to_dict(), room=rc)
        except Exception as e:
            print(f"[ERROR] select_truth_dare: {e}")

    @socketio.on("minigame_vote")
    def on_minigame_vote(data):
        try:
            rc = data.get("room")
            voted_player = data.get("voted_player")

            if not rc or not voted_player:
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            if room.game_state.phase != "minigame":
                return

            mg = room.game_state.minigame
            if not mg:
                return

            player = room.get_player_by_sid(request.sid)
            if not player:
                return

            names = mg.get_participant_names()
            if player.name in names:
                return

            if request.sid in mg.votes:
                return

            mg.add_vote(request.sid, voted_player)

            loser = mg.check_immediate_winner()

            if loser:
                room.game_state.set_selected_player(loser.name)

                sel_dur = room.settings["selection_duration"]
                room.game_state.start_selection(duration=sel_dur)

                socketio.emit(
                    "game_state_update",
                    room.game_state.to_dict(),
                    room=rc,
                    namespace="/",
                )

                # delay then go into truth/dare
                def start_td():
                    try:
                        time.sleep(sel_dur)
                        start_truth_dare_phase_handler(rc)
                    except Exception as e:
                        print(f"[ERROR] start_td: {e}")

                td_thread = threading.Thread(target=start_td)
                td_thread.daemon = True
                td_thread.start()
            elif mg.check_all_voted():
                vote_counts = mg.get_vote_counts()

                if len(vote_counts) == 2:
                    counts = list(vote_counts.values())
                    if counts[0] == counts[1]:
                        loser = mg.handle_tie()
                    else:
                        loser = mg.determine_loser()
                else:
                    loser = mg.determine_loser()

                if loser:
                    room.game_state.set_selected_player(loser.name)

                    sel_dur = room.settings["selection_duration"]
                    room.game_state.start_selection(duration=sel_dur)

                    socketio.emit(
                        "game_state_update",
                        room.game_state.to_dict(),
                        room=rc,
                        namespace="/",
                    )

                    def start_td2():
                        try:
                            time.sleep(sel_dur)
                            start_truth_dare_phase_handler(rc)
                        except Exception as e:
                            print(f"[ERROR] start_td: {e}")

                    td_thread = threading.Thread(target=start_td2)
                    td_thread.daemon = True
                    td_thread.start()
            else:
                emit("game_state_update", room.game_state.to_dict(), room=rc)
        except Exception as e:
            print(f"[ERROR] minigame_vote: {e}")

    @socketio.on("vote_skip")
    def on_vote_skip(data):
        try:
            rc = data.get("room")

            if not rc:
                return

            room = game_manager.get_room(rc)
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

            others = len(room.players) - 1
            need = (others + 1) // 2   # half of the others

            if room.game_state.get_skip_vote_count() >= need:
                room.game_state.activate_skip()

                sk = room.settings["skip_duration"]
                room.game_state.reduce_timer(sk)

            emit("game_state_update", room.game_state.to_dict(), room=rc)
        except Exception as e:
            print(f"[ERROR] vote_skip: {e}")
