# Controller/socket_events/helpers.py
"""
Holds shared helper functions and global references for the socket event system.
All Socket.IO event modules import helpers to access the same socketio and game_manager.
"""

import threading
import time
import random
import logging

from Model.scoring_system import ScoringSystem
from Model.round_record import RoundRecord
from Model.minigame import StaringContest
from Model.ai_generator import get_ai_generator
from Model.truth_dare import Truth, Dare

logger = logging.getLogger(__name__)

# These are initialized by init_socket_helpers() when app starts
_socketio = None
_game_manager = None


# ----------------------------------------------------------------------
# Initialization
# ----------------------------------------------------------------------
def init_socket_helpers(socketio, game_manager):
    """
    Must be called from register_socket_events() in __init__.py
    to share the same SocketIO and GameManager instances.
    """
    global _socketio, _game_manager
    _socketio = socketio
    _game_manager = game_manager

    print(f"[HELPERS_INIT] SocketIO bound. Shared GameManager id={id(game_manager)}")


# ----------------------------------------------------------------------
# Shared helper functions
# ----------------------------------------------------------------------
def _broadcast_room_state(room_code, room):
    """Broadcasts the player list and host ID to everyone in the room."""
    if not room:
        return

    _socketio.emit(
        "player_list",
        {
            "players": room.get_player_names(),
            "host_sid": room.host_sid,
        },
        room=room_code,
    )


# ----------------------------------------------------------------------
# Game phase helpers (unchanged logic)
# ----------------------------------------------------------------------
def start_selection_or_minigame(room_code):
    """Helper to decide between minigame or normal selection."""
    room = _game_manager.get_room(room_code)
    if not room or len(room.players) < 2:
        return

    minigame_chance = room.settings.get("minigame_chance", 20) / 100.0
    trigger_minigame = random.random() < minigame_chance

    if trigger_minigame and len(room.players) >= 2:
        # Start minigame (staring contest)
        minigame = StaringContest()
        participants = random.sample(room.players, 2)
        for participant in participants:
            minigame.add_participant(participant)

        total_voters = len(room.players) - 2
        minigame.set_total_voters(total_voters)

        for participant in participants:
            ScoringSystem.award_minigame_participate_points(participant)

        room.game_state.set_minigame(minigame)
        room.game_state.start_minigame()

        _socketio.emit(
            "game_state_update", room.game_state.to_dict(), room=room_code, namespace="/"
        )
    else:
        # Normal selection
        selected_player = random.choice(room.players)
        room.game_state.set_selected_player(selected_player.name)
        selection_duration = room.settings["selection_duration"]
        room.game_state.start_selection(duration=selection_duration)

        _socketio.emit(
            "game_state_update", room.game_state.to_dict(), room=room_code, namespace="/"
        )

        def start_td_phase():
            time.sleep(selection_duration)
            start_truth_dare_phase_handler(room_code)

        thread = threading.Thread(target=start_td_phase, daemon=True)
        thread.start()


def start_truth_dare_phase_handler(room_code):
    """Handles beginning of the Truth/Dare phase."""
    room = _game_manager.get_room(room_code)
    if not room:
        return

    if room.game_state.selected_choice is None:
        room.game_state.set_selected_choice(random.choice(["truth", "dare"]))

    selected_player = room.get_player_by_name(room.game_state.selected_player)
    list_was_empty = False

    if selected_player:
        choice = room.game_state.selected_choice
        if choice == "truth":
            truths = selected_player.truth_dare_list.truths
            if truths:
                item = random.choice(truths)
                selected_player.truth_dare_list.truths.remove(item)
                selected_player.mark_truth_used(item.text)
                room.game_state.set_current_truth_dare(item.to_dict())
            else:
                list_was_empty = not _try_generate_ai_item(
                    room, selected_player, "truth"
                )
        else:
            dares = selected_player.truth_dare_list.dares
            if dares:
                item = random.choice(dares)
                selected_player.truth_dare_list.dares.remove(item)
                selected_player.mark_dare_used(item.text)
                room.game_state.set_current_truth_dare(item.to_dict())
            else:
                list_was_empty = not _try_generate_ai_item(room, selected_player, "dare")

    # Start truth/dare phase timer
    td_duration = room.settings["truth_dare_duration"]
    room.game_state.start_truth_dare(duration=td_duration)

    if list_was_empty:
        room.game_state.list_empty = True
        room.game_state.activate_skip()
        room.game_state.reduce_timer(room.settings["skip_duration"])

    _socketio.emit(
        "game_state_update", room.game_state.to_dict(), room=room_code, namespace="/"
    )

    def end_td_phase():
        while True:
            time.sleep(0.5)
            r = _game_manager.get_room(room_code)
            if not r:
                break
            if r.game_state.is_phase_complete():
                _handle_end_of_truth_dare(r, room_code)
                break

    thread = threading.Thread(target=end_td_phase, daemon=True)
    thread.start()


# ----------------------------------------------------------------------
# Internal helpers (AI generation + round end)
# ----------------------------------------------------------------------
def _try_generate_ai_item(room, player, item_type):
    """Attempt AI generation for empty list. Returns True if successful."""
    ai_enabled = room.settings.get("ai_generation_enabled", False)
    if not ai_enabled:
        return False

    ai_gen = get_ai_generator()
    if not ai_gen.enabled:
        return False

    existing = room.default_truths.copy() if item_type == "truth" else room.default_dares.copy()
    if item_type == "truth":
        existing.extend([t.text for t in player.truth_dare_list.truths])
        existing.extend(player.get_all_used_truths())
    else:
        existing.extend([d.text for d in player.truth_dare_list.dares])
        existing.extend(player.get_all_used_dares())

    for other in room.players:
        if other.socket_id != player.socket_id:
            if item_type == "truth":
                existing.extend([t.text for t in other.truth_dare_list.truths])
                existing.extend(other.get_all_used_truths())
            else:
                existing.extend([d.text for d in other.truth_dare_list.dares])
                existing.extend(other.get_all_used_dares())

    generated_text = (
        ai_gen.generate_truth(existing)
        if item_type == "truth"
        else ai_gen.generate_dare(existing)
    )
    if not generated_text:
        room.game_state.list_empty = True
        room.game_state.set_current_truth_dare(
            {
                "text": f"{player.name} has no more {item_type}s available!",
                "type": item_type,
                "is_default": False,
                "submitted_by": None,
            }
        )
        return False

    if item_type == "truth":
        new_item = Truth(generated_text, is_default=False, submitted_by="AI")
        player.truth_dare_list.truths.append(new_item)
        player.mark_truth_used(generated_text)
    else:
        new_item = Dare(generated_text, is_default=False, submitted_by="AI")
        player.truth_dare_list.dares.append(new_item)
        player.mark_dare_used(generated_text)

    room.game_state.set_current_truth_dare(new_item.to_dict())
    return True


def _handle_end_of_truth_dare(room, room_code):
    """Handles scoring, round record, and moving to next round."""
    performer = room.get_player_by_name(room.game_state.selected_player)
    if performer:
        ScoringSystem.award_perform_points(performer)

    if room.game_state.current_truth_dare:
        submitted_by = room.game_state.current_truth_dare.get("submitted_by")
        if submitted_by:
            submitter = room.get_player_by_name(submitted_by)
            if submitter:
                ScoringSystem.award_submission_performed_points(submitter)

        round_record = RoundRecord(
            round_number=room.game_state.current_round,
            selected_player_name=room.game_state.selected_player,
            truth_dare_text=room.game_state.current_truth_dare["text"],
            truth_dare_type=room.game_state.current_truth_dare.get(
                "type", room.game_state.selected_choice
            ),
            submitted_by=room.game_state.current_truth_dare.get("submitted_by"),
        )
        room.add_round_record(round_record)

    if room.game_state.should_end_game():
        room.game_state.start_end_game()
        end_data = {
            "phase": "end_game",
            "round_history": room.get_round_history(),
            "top_players": room.get_top_players(5),
            "all_players": [{"name": p.name, "score": p.score} for p in room.players],
        }
        _socketio.emit("game_state_update", end_data, room=room_code, namespace="/")
    else:
        prep_duration = room.settings["preparation_duration"]
        room.game_state.start_preparation(duration=prep_duration)
        room.reset_player_round_submissions()
        _socketio.emit(
            "game_state_update", room.game_state.to_dict(), room=room_code, namespace="/"
        )

        def next_round():
            time.sleep(prep_duration)
            start_selection_or_minigame(room_code)

        threading.Thread(target=next_round, daemon=True).start()
