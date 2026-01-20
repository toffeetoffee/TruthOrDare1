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
    """Normalize text for duplicate comparison"""
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
        logger.warning("Game manager not available – skipping selection/minigame.")
        return
    if not _socketio:
        logger.warning("SocketIO not linked – cannot emit game state.")
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
    """
    Try to generate AI item with proper duplicate prevention.
    
    CRITICAL FIX: Keep original text separate from normalized text.
    - Pass ORIGINAL text to AI for context
    - Use NORMALIZED text for duplicate checking
    """
    try:
        # Debug logging
        logger.info(f"🚨 AI GENERATION TRIGGERED - Player: {player.name}, Type: {item_type}, Round: {room.game_state.current_round}")
        
        # Track AI calls per game
        if not hasattr(room, '_ai_call_count'):
            room._ai_call_count = 0
        room._ai_call_count += 1
        logger.info(f"🚨 TOTAL AI CALLS THIS GAME: {room._ai_call_count}")
        
        if not room.settings.get("ai_generation_enabled", False):
            logger.info("AI generation is disabled in room settings")
            return False

        ai_gen = get_ai_generator()
        if not ai_gen.enabled:
            logger.warning("AI generator not enabled")
            return False

        # ===== FIX #1: Separate ORIGINAL text from NORMALIZED text =====
        
        # Collect ORIGINAL text for AI context
        if item_type == "truth":
            original_texts = list(room.default_truths)
            original_texts.extend(room.ai_generated_truths)
        else:
            original_texts = list(room.default_dares)
            original_texts.extend(room.ai_generated_dares)
        
        # Collect from all players (original text)
        for p in room.players:
            if item_type == "truth":
                original_texts.extend(p.get_all_used_truths())
                original_texts.extend([t.text for t in p.truth_dare_list.truths])
            else:
                original_texts.extend(p.get_all_used_dares())
                original_texts.extend([d.text for d in p.truth_dare_list.dares])
        
        # Build NORMALIZED set for duplicate checking (separate from originals)
        existing_normalized = set(_clean_text(txt) for txt in original_texts)
        
        # Debug logging
        logger.info(f"🔍 Total original items collected: {len(original_texts)}")
        logger.info(f"🔍 First 3 originals: {original_texts[:3]}")
        logger.info(f"🔍 Normalized set size: {len(existing_normalized)}")
        logger.info(f"🔍 First 3 normalized: {list(existing_normalized)[:3]}")

        # ===== FIX #2: Reduce retry attempts from 5 to 3 =====
        for attempt in range(3):  # Reduced from 5 to 3
            logger.info(f"🔄 AI generation attempt {attempt + 1}/3")
            
            # ===== FIX #3: Exponential backoff instead of random delay =====
            if attempt > 0:
                # Exponential backoff: 2^attempt + small random jitter
                delay = min(10, (2 ** attempt) + random.uniform(0, 1))
                logger.info(f"⏱️ Waiting {delay:.2f}s before retry...")
                time.sleep(delay)
            else:
                # Small initial delay to avoid hitting rate limits
                time.sleep(random.uniform(0.3, 0.7))

            # Random seed to prevent cache collisions
            unique_tag = f"SEED:{random.randint(1000, 9999)}"

            try:
                with _ai_lock:
                    logger.info(f"📡 Making API call to Gemini (attempt {attempt + 1}/3)...")
                    
                    # ===== CRITICAL: Pass ORIGINAL text to AI (limit to 30 for token management) =====
                    context_items = original_texts[:30]
                    
                    if item_type == "truth":
                        generated = ai_gen.generate_truth(context_items + [unique_tag])
                    else:
                        generated = ai_gen.generate_dare(context_items + [unique_tag])
                    
                    logger.info(f"✅ API call completed successfully")
                    
            except Exception as e:
                logger.error(f"❌ AI generation API error on attempt {attempt + 1}: {e}", exc_info=True)
                continue

            if not generated:
                logger.warning(f"⚠️ AI returned empty result on attempt {attempt + 1}")
                continue

            logger.info(f"📝 Generated text: '{generated[:50]}...'")

            # ===== Check for duplicate using NORMALIZED comparison =====
            normalized_generated = _clean_text(generated)
            
            if normalized_generated in existing_normalized:
                logger.warning(f"🔁 Duplicate detected (normalized): '{normalized_generated}' - attempt {attempt + 1}/3")
                continue

            # ===== Success - add to appropriate lists =====
            logger.info(f"✨ SUCCESS - Unique {item_type} generated: '{generated}'")
            
            if item_type == "truth":
                if not room.add_ai_generated_truth(generated):
                    logger.warning("⚠️ Room rejected AI truth (possible race condition)")
                    continue
                    
                new_item = Truth(generated, False, "AI")
                player.truth_dare_list.add_truth(generated, submitted_by="AI")
                player.truth_dare_list.remove_truth_by_text(generated)
                player.mark_truth_used(generated)
            else:
                if not room.add_ai_generated_dare(generated):
                    logger.warning("⚠️ Room rejected AI dare (possible race condition)")
                    continue
                    
                new_item = Dare(generated, False, "AI")
                player.truth_dare_list.add_dare(generated, submitted_by="AI")
                player.truth_dare_list.remove_dare_by_text(generated)
                player.mark_dare_used(generated)

            room.game_state.set_current_truth_dare(new_item.to_dict())
            logger.info(f"🎉 AI {item_type} successfully integrated into game")
            return True

        # ===== All retries failed =====
        logger.error(f"❌ AI GENERATION FAILED - No unique {item_type} after 3 attempts")
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
        logger.exception(f"💥 CRITICAL ERROR in _try_generate_ai_item: {e}")
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
