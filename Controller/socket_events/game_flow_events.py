# Controller/socket_events/game_flow_events.py

import threading
import time

from flask_socketio import emit
from flask import request

from .helpers import start_selection_or_minigame, start_truth_dare_phase_handler


def register_game_flow_events(socketio, game_manager):
    """Register events for starting/restarting the game and in-round flow."""

    @socketio.on("start_game")
    def on_start_game(data):
        room_code = data.get("room")

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can start
        if not room.is_host(request.sid):
            return

        # Start countdown with configurable duration
        countdown_duration = room.settings["countdown_duration"]
        room.game_state.start_countdown(duration=countdown_duration)

        # Broadcast game state
        emit("game_state_update", room.game_state.to_dict(), room=room_code)

        # Schedule preparation phase after countdown
        def start_preparation():
            time.sleep(countdown_duration)
            room_inner = game_manager.get_room(room_code)
            if room_inner:
                prep_duration = room_inner.settings["preparation_duration"]
                room_inner.game_state.start_preparation(duration=prep_duration)

                # Reset player submission counters for new round
                room_inner.reset_player_round_submissions()

                socketio.emit(
                    "game_state_update",
                    room_inner.game_state.to_dict(),
                    room=room_code,
                    namespace="/",
                )

                # Schedule selection or minigame after preparation
                def after_prep():
                    time.sleep(prep_duration)
                    start_selection_or_minigame(room_code)

                prep_thread = threading.Thread(target=after_prep)
                prep_thread.daemon = True
                prep_thread.start()

        thread = threading.Thread(target=start_preparation)
        thread.daemon = True
        thread.start()

    @socketio.on("restart_game")
    def on_restart_game(data):
        room_code = data.get("room")

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only host can restart
        if not room.is_host(request.sid):
            return

        # Reset room for new game
        room.reset_for_new_game()

        # Start countdown immediately
        countdown_duration = room.settings["countdown_duration"]
        room.game_state.start_countdown(duration=countdown_duration)

        # Broadcast reset state
        emit("game_state_update", room.game_state.to_dict(), room=room_code)

        # Trigger start_game logic (same behavior as original)
        on_start_game({"room": room_code})

    @socketio.on("select_truth_dare")
    def on_select_truth_dare(data):
        room_code = data.get("room")
        choice = data.get("choice")  # 'truth' or 'dare'

        if not room_code or not choice:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only during selection phase
        if room.game_state.phase != "selection":
            return

        # Only the selected player can choose
        player = room.get_player_by_sid(request.sid)
        if not player or player.name != room.game_state.selected_player:
            return

        # Set the choice
        room.game_state.set_selected_choice(choice)

        # Broadcast updated state
        emit("game_state_update", room.game_state.to_dict(), room=room_code)

    @socketio.on("minigame_vote")
    def on_minigame_vote(data):
        room_code = data.get("room")
        voted_player = data.get("voted_player")  # Name of player who blinked

        if not room_code or not voted_player:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only during minigame phase
        if room.game_state.phase != "minigame":
            return

        minigame = room.game_state.minigame
        if not minigame:
            return

        # Only non-participants can vote
        player = room.get_player_by_sid(request.sid)
        if not player:
            return

        participant_names = minigame.get_participant_names()
        if player.name in participant_names:
            return  # Participants can't vote

        # Check if player already voted
        if request.sid in minigame.votes:
            return  # Already voted

        # Add vote
        minigame.add_vote(request.sid, voted_player)

        # Check for immediate winner (one player reached at least half of total votes)
        loser = minigame.check_immediate_winner()

        if loser:
            # Someone reached the threshold - proceed immediately
            room.game_state.set_selected_player(loser.name)

            # Move to selection phase
            selection_duration = room.settings["selection_duration"]
            room.game_state.start_selection(duration=selection_duration)

            socketio.emit(
                "game_state_update",
                room.game_state.to_dict(),
                room=room_code,
                namespace="/",
            )

            # Schedule truth/dare phase
            def start_td():
                time.sleep(selection_duration)
                start_truth_dare_phase_handler(room_code)

            td_thread = threading.Thread(target=start_td)
            td_thread.daemon = True
            td_thread.start()
        elif minigame.check_all_voted():
            # All voters have voted - check for tie
            vote_counts = minigame.get_vote_counts()

            if len(vote_counts) == 2:
                counts = list(vote_counts.values())
                if counts[0] == counts[1]:
                    # It's a tie - randomly pick loser
                    loser = minigame.handle_tie()
                else:
                    # Someone has more votes
                    loser = minigame.determine_loser()
            else:
                # One player has all or most votes
                loser = minigame.determine_loser()

            if loser:
                # Set loser as selected player
                room.game_state.set_selected_player(loser.name)

                # Move to selection phase
                selection_duration = room.settings["selection_duration"]
                room.game_state.start_selection(duration=selection_duration)

                socketio.emit(
                    "game_state_update",
                    room.game_state.to_dict(),
                    room=room_code,
                    namespace="/",
                )

                # Schedule truth/dare phase
                def start_td():
                    time.sleep(selection_duration)
                    start_truth_dare_phase_handler(room_code)

                td_thread = threading.Thread(target=start_td)
                td_thread.daemon = True
                td_thread.start()
        else:
            # Just broadcast updated vote count
            emit("game_state_update", room.game_state.to_dict(), room=room_code)

    @socketio.on("vote_skip")
    def on_vote_skip(data):
        room_code = data.get("room")

        if not room_code:
            return

        room = game_manager.get_room(room_code)
        if not room:
            return

        # Only during truth_dare phase
        if room.game_state.phase != "truth_dare":
            return

        # Can't vote if skip already activated
        if room.game_state.skip_activated:
            return

        # Only non-selected players can vote
        player = room.get_player_by_sid(request.sid)
        if not player or player.name == room.game_state.selected_player:
            return

        # Add vote
        room.game_state.add_skip_vote(request.sid)

        # Check if at least half of other players voted
        other_players_count = len(room.players) - 1  # Exclude selected player
        required_votes = (other_players_count + 1) // 2  # At least half (ceiling)

        if room.game_state.get_skip_vote_count() >= required_votes:
            # Activate skip
            room.game_state.activate_skip()

            # Reduce timer to configured skip duration
            skip_duration = room.settings["skip_duration"]
            room.game_state.reduce_timer(skip_duration)

        # Broadcast updated state
        emit("game_state_update", room.game_state.to_dict(), room=room_code)
