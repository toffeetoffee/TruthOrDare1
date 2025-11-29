import threading
import time
import random
import logging
import re

from Model.scoring_system import ScoringSystem
from Model.round_record import RoundRecord
from Model.minigame import StaringContest, ArmWrestlingContest
from Model.ai_generator import get_ai_generator
from Model.truth_dare import Truth, Dare

logger = logging.getLogger(__name__)
_socketio = None
_game_mgr = None

_ai_lock = threading.Lock()


def init_socket_helpers(socketio, game_manager):
    global _socketio, _game_mgr
    _socketio = socketio
    _game_mgr = game_manager
    print(f"[HELPERS_INIT] SocketIO linked, GameManager id={id(game_manager)}")


def _clean_text(txt):
    return re.sub(r"[^a-z0-9]+", "", txt.strip().lower())


def _emit_room_state(code, room_obj):
    if not _socketio:
        logger.error("SocketIO isn't set - can't send player list.")
        return
    if not room_obj:
        return
    _socketio.emit(
        "player_list",
        {"players": room_obj.get_player_names(), "host_sid": room_obj.host_sid},
        room=code,
    )


def _broadcast_room_state(code, room_obj):
    _emit_room_state(code, room_obj)


def start_selection_or_minigame(room_code):
    if not _game_mgr:
        logger.warning("Game manager not available — skipping selection/minigame.")
        return
    if not _socketio:
        logger.warning("SocketIO not linked — cannot emit game state.")
        return

    try:
        room = _game_mgr.get_room(room_code)
        if not room or len(room.players) < 2:
            return

        # decide if we do minigame or just pick someone
        chance = room.settings.get("minigame_chance", 20)
        roll = random.random()
        threshold = chance / 100.0

        if roll < threshold:
            random.seed(time.time() + hash(room_code) + random.randint(0, 9999))

            MiniGameClass = random.choice([StaringContest, ArmWrestlingContest])
            mg = MiniGameClass()

            contenders = random.sample(room.players, 2)
            for p in contenders:
                mg.add_participant(p)
                ScoringSystem.award_minigame_participate_points(p)

            mg.set_total_voters(len(room.players) - 2)
            room.game_state.set_minigame(mg)
            room.game_state.start_minigame()

            _socketio.emit("game_state_update", room.game_state.to_dict(), room=room_code)
        else:
            chosen = random.choice(room.players)
            room.game_state.set_selected_player(chosen.name)

            sel_t = room.settings["selection_duration"]
            room.game_state.start_selection(sel_t)

            _socketio.emit("game_state_update", room.game_state.to_dict(), room=room_code)

            # delay then go to truth or dare
            def later():
                time.sleep(sel_t)
                start_truth_dare_phase_handler(room_code)

            threading.Thread(target=later, daemon=True).start()

    except Exception as ex:
        logger.exception(f"start_selection_or_minigame() blew up: {ex}")


def start_truth_dare_phase_handler(room_code):
    if not _game_mgr or not _socketio:
        logger.warning("Missing game manager or socket instance.")
        return

    try:
        room = _game_mgr.get_room(room_code)
        if not room:
            return

        if room.game_state.selected_choice is None:
            room.game_state.set_selected_choice(random.choice(["truth", "dare"]))

        selected = room.get_player_by_name(room.game_state.selected_player)
        no_more = False

        if selected:
            kind = room.game_state.selected_choice
            if kind == "truth":
                truths = selected.truth_dare_list.truths
                if truths:
                    ch = random.choice(truths)
                    selected.truth_dare_list.remove_truth_by_text(ch.text)
                    selected.mark_truth_used(ch.text)
                    room.game_state.set_current_truth_dare(ch.to_dict())
                else:
                    no_more = not _try_generate_ai_item(room, selected, "truth")
            else:
                dares = selected.truth_dare_list.dares
                if dares:
                    ch = random.choice(dares)
                    selected.truth_dare_list.remove_dare_by_text(ch.text)
                    selected.mark_dare_used(ch.text)
                    room.game_state.set_current_truth_dare(ch.to_dict())
                else:
                    no_more = not _try_generate_ai_item(room, selected, "dare")

        td_time = room.settings["truth_dare_duration"]
        room.game_state.start_truth_dare(td_time)

        if no_more:
            room.game_state.list_empty = True
            room.game_state.activate_skip()
            room.game_state.reduce_timer(room.settings["skip_duration"])

        _socketio.emit("game_state_update", room.game_state.to_dict(), room=room_code)

        # watch the timer in a cheap while loop
        threading.Thread(
            target=lambda: _monitor_truth_dare(room_code),
            daemon=True
        ).start()

    except Exception as err:
        logger.exception(f"Exception in start_truth_dare_phase_handler: {err}")


def _try_generate_ai_item(room, player, item_type):
    try:
        if not room.settings.get("ai_generation_enabled", False):
            return False

        ai_gen = get_ai_generator()
        if not ai_gen.enabled:
            return False

        norm = _clean_text
        if item_type == "truth":
            existing = set(map(norm, room.default_truths))
            existing.update(map(norm, room.ai_generated_truths))
        else:
            existing = set(map(norm, room.default_dares))
            existing.update(map(norm, room.ai_generated_dares))

        # also include any extra normalized stuff
        if hasattr(room, "_ai_generated_truths_normalized") and item_type == "truth":
            existing.update(room._ai_generated_truths_normalized)
        if hasattr(room, "_ai_generated_dares_normalized") and item_type == "dare":
            existing.update(room._ai_generated_dares_normalized)

        for p in room.players:
            if item_type == "truth":
                existing.update(map(norm, p.get_all_used_truths()))
                existing.update(map(norm, [t.text for t in p.truth_dare_list.truths]))
            else:
                existing.update(map(norm, p.get_all_used_dares()))
                existing.update(map(norm, [d.text for d in p.truth_dare_list.dares]))

        # try a few times to get something unique from AI
        for _ in range(5):
            time.sleep(random.uniform(0.5, 1.5))

            seed_tag = f"SEED:{random.randint(1000,9999)}"
            try:
                with _ai_lock:
                    if item_type == "truth":
                        res = ai_gen.generate_truth(list(existing) + [seed_tag])
                    else:
                        res = ai_gen.generate_dare(list(existing) + [seed_tag])
            except Exception as gen_err:
                logger.error(f"AI generation error: {gen_err}")
                continue

            if not res or _clean_text(res) in existing:
                continue

            if item_type == "truth":
                if not room.add_ai_generated_truth(res):
                    continue
                player.truth_dare_list.add_truth(res, submitted_by="AI")
                player.truth_dare_list.remove_truth_by_text(res)
                player.mark_truth_used(res)
                td = Truth(res, False, "AI")
            else:
                if not room.add_ai_generated_dare(res):
                    continue
                player.truth_dare_list.add_dare(res, submitted_by="AI")
                player.truth_dare_list.remove_dare_by_text(res)
                player.mark_dare_used(res)
                td = Dare(res, False, "AI")

            room.game_state.set_current_truth_dare(td.to_dict())
            logger.info(f"Generated new {item_type}: {res}")
            return True

        logger.warning(f"AI failed to generate unique {item_type}")
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
    except Exception as e:
        logger.exception(f"_try_generate_ai_item bombed: {e}")
        return False


def _monitor_truth_dare(room_code):
    if not _game_mgr:
        logger.error("Game manager missing in _monitor_truth_dare")
        return

    try:
        while True:
            time.sleep(0.5)
            room = _game_mgr.get_room(room_code)
            if not room:
                break
            if room.game_state.is_phase_complete():
                _handle_end_of_truth_dare(room, room_code)
                break
    except Exception as e:
        logger.exception(f"Error in _monitor_truth_dare: {e}")


def _handle_end_of_truth_dare(room, code):
    if not _socketio:
        logger.error("SocketIO missing during end of truth/dare")
        return

    try:
        performer = room.get_player_by_name(room.game_state.selected_player)
        if performer:
            ScoringSystem.award_perform_points(performer)

        curr = room.game_state.current_truth_dare
        if curr:
            submitter = (
                room.get_player_by_name(curr.get("submitted_by"))
                if curr.get("submitted_by") else None
            )
            if submitter:
                ScoringSystem.award_submission_performed_points(submitter)

            rec = RoundRecord(
                round_number=room.game_state.current_round,
                selected_player_name=room.game_state.selected_player,
                truth_dare_text=curr["text"],
                truth_dare_type=curr.get("type", room.game_state.selected_choice),
                submitted_by=curr.get("submitted_by"),
            )
            room.add_round_record(rec)

        if room.game_state.should_end_game():
            room.game_state.start_end_game()
            final_data = {
                "phase": "end_game",
                "round_history": room.get_round_history(),
                "top_players": room.get_top_players(5),
                "all_players": [{"name": p.name, "score": p.score} for p in room.players],
            }
            _socketio.emit("game_state_update", final_data, room=code)
        else:
            prep_t = room.settings["preparation_duration"]
            room.game_state.start_preparation(prep_t)
            room.reset_player_round_submissions()
            _socketio.emit("game_state_update", room.game_state.to_dict(), room=code)

            threading.Thread(
                target=lambda: (time.sleep(prep_t), start_selection_or_minigame(code)),
                daemon=True,
            ).start()
    except Exception as e:
        logger.exception(f"Exception in _handle_end_of_truth_dare: {e}")
