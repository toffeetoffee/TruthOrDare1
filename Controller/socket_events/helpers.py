# Controller/socket_events/helpers.py

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

_socketio = None
_game_manager = None


def init_socket_helpers(socketio, game_manager):
    """
    Must be called once from register_socket_events so helpers
    can access socketio and game_manager without changing their
    public signatures.
    """
    global _socketio, _game_manager
    _socketio = socketio
    _game_manager = game_manager


def _broadcast_room_state(room_code, room):
    """Helper to broadcast room state to all players."""
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


def start_selection_or_minigame(room_code):
    """Helper to decide between minigame or normal selection."""
    room = _game_manager.get_room(room_code)
    if not room or len(room.players) < 2:
        return

    # Check for minigame chance
    minigame_chance = room.settings.get("minigame_chance", 20) / 100.0
    trigger_minigame = random.random() < minigame_chance

    if trigger_minigame and len(room.players) >= 2:
        # Start minigame (staring contest)
        minigame = StaringContest()

        # Randomly select 2 players
        participants = random.sample(room.players, 2)
        for participant in participants:
            minigame.add_participant(participant)

        # Set total voters (all players except the 2 participants)
        total_voters = len(room.players) - 2
        minigame.set_total_voters(total_voters)

        # Award participation points
        for participant in participants:
            ScoringSystem.award_minigame_participate_points(participant)

        # Set minigame in game state
        room.game_state.set_minigame(minigame)
        room.game_state.start_minigame()

        _socketio.emit(
            "game_state_update",
            room.game_state.to_dict(),
            room=room_code,
            namespace="/",
        )

        # Minigame continues until voting completes (handled by minigame_vote)
    else:
        # No minigame - proceed to normal selection
        selected_player = random.choice(room.players)
        room.game_state.set_selected_player(selected_player.name)

        selection_duration = room.settings["selection_duration"]
        room.game_state.start_selection(duration=selection_duration)

        _socketio.emit(
            "game_state_update",
            room.game_state.to_dict(),
            room=room_code,
            namespace="/",
        )

        # Schedule truth/dare phase after selection
        def start_truth_dare_phase():
            time.sleep(selection_duration)
            start_truth_dare_phase_handler(room_code)

        td_thread = threading.Thread(target=start_truth_dare_phase)
        td_thread.daemon = True
        td_thread.start()


def start_truth_dare_phase_handler(room_code):
    """Helper to start truth/dare phase."""
    room = _game_manager.get_room(room_code)
    if not room:
        return

    # If no choice was made, randomize
    if room.game_state.selected_choice is None:
        room.game_state.set_selected_choice(random.choice(["truth", "dare"]))

    # Get the selected player
    selected_player = room.get_player_by_name(room.game_state.selected_player)
    list_was_empty = False

    if selected_player:
        # Pick random truth or dare based on choice
        choice = room.game_state.selected_choice
        if choice == "truth":
            truths = selected_player.truth_dare_list.truths
            if truths:
                selected_item = random.choice(truths)
                selected_player.truth_dare_list.truths.remove(selected_item)
                # Mark as used to prevent AI duplicates
                selected_player.mark_truth_used(selected_item.text)
                room.game_state.set_current_truth_dare(selected_item.to_dict())
            else:
                # List is empty! Try AI generation if enabled
                ai_enabled = room.settings.get("ai_generation_enabled", False)
                logger.info(
                    f"Player {selected_player.name}'s truth list is empty. "
                    f"AI generation enabled: {ai_enabled}"
                )

                generated_text = None

                if ai_enabled:
                    # Get AI generator and try to generate a new truth
                    ai_gen = get_ai_generator()
                    logger.info(
                        "AI generator status - Enabled: %s, Has client: %s",
                        ai_gen.enabled,
                        ai_gen.client is not None,
                    )

                    if ai_gen.enabled:
                        # Get context from room defaults
                        existing_truths = room.default_truths.copy()

                        # Add this player's current and used truths
                        existing_truths.extend(
                            [t.text for t in selected_player.truth_dare_list.truths]
                        )
                        existing_truths.extend(
                            selected_player.get_all_used_truths()
                        )

                        # Also add truths from other players' current lists and used lists
                        for other_player in room.players:
                            if other_player.socket_id != selected_player.socket_id:
                                existing_truths.extend(
                                    [
                                        t.text
                                        for t in other_player.truth_dare_list.truths
                                    ]
                                )
                                existing_truths.extend(
                                    other_player.get_all_used_truths()
                                )

                        logger.info(
                            "Attempting to generate truth with %d existing truths "
                            "as context (including %d used by this player)",
                            len(existing_truths),
                            len(selected_player.get_all_used_truths()),
                        )
                        generated_text = ai_gen.generate_truth(existing_truths)

                        if generated_text:
                            # Successfully generated! Add to player's list and mark as used
                            logger.info(
                                "Successfully generated truth for %s: '%.50s...'",
                                selected_player.name,
                                generated_text,
                            )
                            new_truth = Truth(
                                generated_text, is_default=False, submitted_by="AI"
                            )
                            selected_player.truth_dare_list.truths.append(new_truth)
                            # Mark as used immediately since it will be performed
                            selected_player.mark_truth_used(generated_text)
                            room.game_state.set_current_truth_dare(
                                new_truth.to_dict()
                            )
                            list_was_empty = False
                        else:
                            logger.error(
                                "AI generation returned None for truth - "
                                "falling back to empty message"
                            )
                    else:
                        logger.warning(
                            "AI generator is not enabled - Initialization error: %s",
                            ai_gen.initialization_error,
                        )

                # If AI didn't generate (disabled or failed), use fallback message
                if generated_text is None:
                    logger.warning(
                        "Using fallback message for %s - no truths available",
                        selected_player.name,
                    )
                    list_was_empty = True
                    room.game_state.list_empty = True
                    room.game_state.set_current_truth_dare(
                        {
                            "text": f"{selected_player.name} has no more truths available!",
                            "type": "truth",
                            "is_default": False,
                            "submitted_by": None,
                        }
                    )
        else:  # dare
            dares = selected_player.truth_dare_list.dares
            if dares:
                selected_item = random.choice(dares)
                selected_player.truth_dare_list.dares.remove(selected_item)
                # Mark as used to prevent AI duplicates
                selected_player.mark_dare_used(selected_item.text)
                room.game_state.set_current_truth_dare(selected_item.to_dict())
            else:
                # List is empty! Try AI generation if enabled
                ai_enabled = room.settings.get("ai_generation_enabled", False)
                logger.info(
                    "Player %s's dare list is empty. AI generation enabled: %s",
                    selected_player.name,
                    ai_enabled,
                )

                generated_text = None

                if ai_enabled:
                    # Get AI generator and try to generate a new dare
                    ai_gen = get_ai_generator()
                    logger.info(
                        "AI generator status - Enabled: %s, Has client: %s",
                        ai_gen.enabled,
                        ai_gen.client is not None,
                    )

                    if ai_gen.enabled:
                        # Get context from room defaults
                        existing_dares = room.default_dares.copy()

                        # Add this player's current and used dares
                        existing_dares.extend(
                            [d.text for d in selected_player.truth_dare_list.dares]
                        )
                        existing_dares.extend(selected_player.get_all_used_dares())

                        # Also add dares from other players' current lists and used lists
                        for other_player in room.players:
                            if other_player.socket_id != selected_player.socket_id:
                                existing_dares.extend(
                                    [
                                        d.text
                                        for d in other_player.truth_dare_list.dares
                                    ]
                                )
                                existing_dares.extend(
                                    other_player.get_all_used_dares()
                                )

                        logger.info(
                            "Attempting to generate dare with %d existing dares as "
                            "context (including %d used by this player)",
                            len(existing_dares),
                            len(selected_player.get_all_used_dares()),
                        )
                        generated_text = ai_gen.generate_dare(existing_dares)

                        if generated_text:
                            # Successfully generated! Add to player's list and mark as used
                            logger.info(
                                "Successfully generated dare for %s: '%.50s...'",
                                selected_player.name,
                                generated_text,
                            )
                            new_dare = Dare(
                                generated_text, is_default=False, submitted_by="AI"
                            )
                            selected_player.truth_dare_list.dares.append(new_dare)
                            # Mark as used immediately since it will be performed
                            selected_player.mark_dare_used(generated_text)
                            room.game_state.set_current_truth_dare(
                                new_dare.to_dict()
                            )
                            list_was_empty = False
                        else:
                            logger.error(
                                "AI generation returned None for dare - "
                                "falling back to empty message"
                            )
                    else:
                        logger.warning(
                            "AI generator is not enabled - Initialization error: %s",
                            ai_gen.initialization_error,
                        )

                # If AI didn't generate (disabled or failed), use fallback message
                if generated_text is None:
                    logger.warning(
                        "Using fallback message for %s - no dares available",
                        selected_player.name,
                    )
                    list_was_empty = True
                    room.game_state.list_empty = True
                    room.game_state.set_current_truth_dare(
                        {
                            "text": f"{selected_player.name} has no more dares available!",
                            "type": "dare",
                            "is_default": False,
                            "submitted_by": None,
                        }
                    )

    # Start truth/dare phase with configurable duration
    td_duration = room.settings["truth_dare_duration"]
    room.game_state.start_truth_dare(duration=td_duration)

    # If list was empty, automatically activate skip
    if list_was_empty:
        room.game_state.list_empty = True
        room.game_state.activate_skip()
        skip_duration = room.settings["skip_duration"]
        room.game_state.reduce_timer(skip_duration)

    _socketio.emit(
        "game_state_update",
        room.game_state.to_dict(),
        room=room_code,
        namespace="/",
    )

    # Schedule end of truth/dare phase
    def end_truth_dare_phase():
        # Check timer dynamically
        while True:
            time.sleep(0.5)
            room_inner = _game_manager.get_room(room_code)
            if not room_inner:
                break

            # Check if phase is complete
            if room_inner.game_state.is_phase_complete():
                # Award points for performing
                performer = room_inner.get_player_by_name(
                    room_inner.game_state.selected_player
                )
                if performer:
                    ScoringSystem.award_perform_points(performer)

                # Award points to submitter if custom truth/dare
                if room_inner.game_state.current_truth_dare:
                    submitted_by = room_inner.game_state.current_truth_dare.get(
                        "submitted_by"
                    )
                    if submitted_by:
                        submitter = room_inner.get_player_by_name(submitted_by)
                        if submitter:
                            ScoringSystem.award_submission_performed_points(submitter)

                # Record round history
                if room_inner.game_state.current_truth_dare:
                    round_record = RoundRecord(
                        round_number=room_inner.game_state.current_round,
                        selected_player_name=room_inner.game_state.selected_player,
                        truth_dare_text=room_inner.game_state.current_truth_dare["text"],
                        truth_dare_type=room_inner.game_state.current_truth_dare.get(
                            "type", room_inner.game_state.selected_choice
                        ),
                        submitted_by=room_inner.game_state.current_truth_dare.get(
                            "submitted_by"
                        ),
                    )
                    room_inner.add_round_record(round_record)

                # Check if game should end
                if room_inner.game_state.should_end_game():
                    room_inner.game_state.start_end_game()

                    # Broadcast end game state with statistics
                    end_game_data = {
                        "phase": "end_game",
                        "round_history": room_inner.get_round_history(),
                        "top_players": room_inner.get_top_players(5),
                        "all_players": [
                            {"name": p.name, "score": p.score}
                            for p in room_inner.players
                        ],
                    }
                    _socketio.emit(
                        "game_state_update",
                        end_game_data,
                        room=room_code,
                        namespace="/",
                    )
                else:
                    # Continue to next round
                    prep_duration = room_inner.settings["preparation_duration"]
                    room_inner.game_state.start_preparation(duration=prep_duration)

                    # Reset player submission counters
                    room_inner.reset_player_round_submissions()

                    _socketio.emit(
                        "game_state_update",
                        room_inner.game_state.to_dict(),
                        room=room_code,
                        namespace="/",
                    )

                    # Continue the loop - start next round
                    def next_round():
                        time.sleep(prep_duration)
                        start_selection_or_minigame(room_code)

                    next_round_thread = threading.Thread(target=next_round)
                    next_round_thread.daemon = True
                    next_round_thread.start()
                break

    td_end_thread = threading.Thread(target=end_truth_dare_phase)
    td_end_thread.daemon = True
    td_end_thread.start()
