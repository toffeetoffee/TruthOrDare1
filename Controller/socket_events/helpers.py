# Controller/socket_events/helpers.py
"""
Shared helpers for Socket.IO events.
Enhanced duplicate-prevention and AI pacing.
"""

import threading
import time
import random
import logging
import re

from Model.scoring_system import ScoringSystem
from Model.round_record import RoundRecord
from Model.minigame import StaringContest
from Model.ai_generator import get_ai_generator
from Model.truth_dare import Truth, Dare

logger = logging.getLogger(__name__)
_socketio = None
_game_manager = None


# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
def init_socket_helpers(socketio, game_manager):
    global _socketio, _game_manager
    _socketio = socketio
    _game_manager = game_manager
    print(f"[HELPERS_INIT] SocketIO linked, GameManager id={id(game_manager)}")


# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------
def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.strip().lower())


def _broadcast_room_state(room_code, room):
    if not room:
        return
    _socketio.emit(
        "player_list",
        {"players": room.get_player_names(), "host_sid": room.host_sid},
        room=room_code,
    )


# ----------------------------------------------------------------------
# Game flow
# ----------------------------------------------------------------------
def start_selection_or_minigame(room_code):
    room = _game_manager.get_room(room_code)
    if not room or len(room.players) < 2:
        return

    if random.random() < room.settings.get("minigame_chance", 20) / 100.0:
        minigame = StaringContest()
        participants = random.sample(room.players, 2)
        for p in participants:
            minigame.add_participant(p)
            ScoringSystem.award_minigame_participate_points(p)
        minigame.set_total_voters(len(room.players) - 2)
        room.game_state.set_minigame(minigame)
        room.game_state.start_minigame()
        _socketio.emit("game_state_update", room.game_state.to_dict(), room=room_code)
    else:
        sel = random.choice(room.players)
        room.game_state.set_selected_player(sel.name)
        dur = room.settings["selection_duration"]
        room.game_state.start_selection(dur)
        _socketio.emit("game_state_update", room.game_state.to_dict(), room=room_code)
        threading.Thread(
            target=lambda: (time.sleep(dur), start_truth_dare_phase_handler(room_code)),
            daemon=True,
        ).start()


def start_truth_dare_phase_handler(room_code):
    room = _game_manager.get_room(room_code)
    if not room:
        return

    if room.game_state.selected_choice is None:
        room.game_state.set_selected_choice(random.choice(["truth", "dare"]))

    player = room.get_player_by_name(room.game_state.selected_player)
    list_empty = False

    if player:
        choice = room.game_state.selected_choice
        if choice == "truth":
            items = player.truth_dare_list.truths
            if items:
                item = random.choice(items)
                player.truth_dare_list.truths.remove(item)
                player.mark_truth_used(item.text)
                room.game_state.set_current_truth_dare(item.to_dict())
            else:
                list_empty = not _try_generate_ai_item(room, player, "truth")
        else:
            items = player.truth_dare_list.dares
            if items:
                item = random.choice(items)
                player.truth_dare_list.dares.remove(item)
                player.mark_dare_used(item.text)
                room.game_state.set_current_truth_dare(item.to_dict())
            else:
                list_empty = not _try_generate_ai_item(room, player, "dare")

    td_dur = room.settings["truth_dare_duration"]
    room.game_state.start_truth_dare(td_dur)
    if list_empty:
        room.game_state.list_empty = True
        room.game_state.activate_skip()
        room.game_state.reduce_timer(room.settings["skip_duration"])

    _socketio.emit("game_state_update", room.game_state.to_dict(), room=room_code)
    threading.Thread(target=lambda: _monitor_truth_dare(room_code), daemon=True).start()


# ----------------------------------------------------------------------
# AI generation with pacing & strict duplicate control
# ----------------------------------------------------------------------
def _try_generate_ai_item(room, player, item_type):
    """
    Generate a new truth/dare using AI while ensuring uniqueness
    and breaking Gemini's repetition pattern by discarding every even result.
    """
    ai_enabled = room.settings.get("ai_generation_enabled", False)
    if not ai_enabled:
        return False

    ai_gen = get_ai_generator()
    if not ai_gen.enabled:
        return False

    normalize = _normalize_text

    # Build context
    base_items = room.default_truths if item_type == "truth" else room.default_dares
    existing_norm = set(map(normalize, base_items))

    ai_items = (
        room.ai_generated_truths if item_type == "truth" else room.ai_generated_dares
    )
    existing_norm.update(map(normalize, ai_items))

    for p in room.players:
        if item_type == "truth":
            existing_norm.update(map(normalize, p.get_all_used_truths()))
            existing_norm.update(map(normalize, [t.text for t in p.truth_dare_list.truths]))
        else:
            existing_norm.update(map(normalize, p.get_all_used_dares()))
            existing_norm.update(map(normalize, [d.text for d in p.truth_dare_list.dares]))

    # Select the right counter
    if item_type == "truth":
        player.ai_generated_truth_count += 1
        generation_number = player.ai_generated_truth_count
    else:
        player.ai_generated_dare_count += 1
        generation_number = player.ai_generated_dare_count

    # ----------------- AI GENERATION -----------------
    # Random delay helps avoid API echo
    time.sleep(random.uniform(0.5, 1.5))
    first_gen = (
        ai_gen.generate_truth(list(existing_norm))
        if item_type == "truth"
        else ai_gen.generate_dare(list(existing_norm))
    )

    # CHEAT FIX: discard on every even-numbered generation
    if generation_number % 2 == 0:
        logger.info(f"[AI CHEAT] Discarding first {item_type} (#{generation_number}) to avoid repetition.")
        time.sleep(random.uniform(0.5, 1.0))
        second_gen = (
            ai_gen.generate_truth(list(existing_norm))
            if item_type == "truth"
            else ai_gen.generate_dare(list(existing_norm))
        )
        generated = second_gen or first_gen
    else:
        generated = first_gen
    # ------------------------------------------------

    if not generated:
        logger.warning(f"[AI FAILURE] No {item_type} generated after cheat attempt.")
        room.game_state.list_empty = True
        room.game_state.set_current_truth_dare({
            "text": f"{player.name} has no more {item_type}s available!",
            "type": item_type,
            "is_default": False,
            "submitted_by": None,
        })
        return False

    # Normalize and check duplicates just in case
    norm = normalize(generated)
    all_norm = set(map(normalize, room.ai_generated_truths if item_type == "truth" else room.ai_generated_dares))
    if norm in all_norm:
        logger.warning(f"[AI DUPLICATE AFTER CHEAT] {item_type}: {generated}")
        return False

    # Store and apply
    if item_type == "truth":
        room.add_ai_generated_truth(generated)
        new_item = Truth(generated, is_default=False, submitted_by="AI")
        player.truth_dare_list.truths.append(new_item)
        player.mark_truth_used(generated)
    else:
        room.add_ai_generated_dare(generated)
        new_item = Dare(generated, is_default=False, submitted_by="AI")
        player.truth_dare_list.dares.append(new_item)
        player.mark_dare_used(generated)

    room.game_state.set_current_truth_dare(new_item.to_dict())
    logger.info(f"[AI SUCCESS] {item_type.capitalize()} generated (#{generation_number}): {generated}")
    return True



# ----------------------------------------------------------------------
# Truth/dare phase monitoring
# ----------------------------------------------------------------------
def _monitor_truth_dare(room_code):
    while True:
        time.sleep(0.5)
        room = _game_manager.get_room(room_code)
        if not room:
            break
        if room.game_state.is_phase_complete():
            _handle_end_of_truth_dare(room, room_code)
            break


def _handle_end_of_truth_dare(room, room_code):
    performer = room.get_player_by_name(room.game_state.selected_player)
    if performer:
        ScoringSystem.award_perform_points(performer)

    if room.game_state.current_truth_dare:
        submitted_by = room.game_state.current_truth_dare.get("submitted_by")
        if submitted_by:
            sub = room.get_player_by_name(submitted_by)
            if sub:
                ScoringSystem.award_submission_performed_points(sub)
        rec = RoundRecord(
            round_number=room.game_state.current_round,
            selected_player_name=room.game_state.selected_player,
            truth_dare_text=room.game_state.current_truth_dare["text"],
            truth_dare_type=room.game_state.current_truth_dare.get(
                "type", room.game_state.selected_choice
            ),
            submitted_by=room.game_state.current_truth_dare.get("submitted_by"),
        )
        room.add_round_record(rec)

    if room.game_state.should_end_game():
        room.game_state.start_end_game()
        end_data = {
            "phase": "end_game",
            "round_history": room.get_round_history(),
            "top_players": room.get_top_players(5),
            "all_players": [{"name": p.name, "score": p.score} for p in room.players],
        }
        _socketio.emit("game_state_update", end_data, room=room_code)
    else:
        prep = room.settings["preparation_duration"]
        room.game_state.start_preparation(prep)
        room.reset_player_round_submissions()
        _socketio.emit("game_state_update", room.game_state.to_dict(), room=room_code)
        threading.Thread(
            target=lambda: (time.sleep(prep), start_selection_or_minigame(room_code)),
            daemon=True,
        ).start()
