# selection_helpers.py
import random
import threading
import time
import logging

from Model.scoring_system import ScoringSystem
from Model.round_record import RoundRecord
from Model.minigame import StaringContest
from Model.ai_generator import get_ai_generator
from Model.truth_dare import Truth, Dare

logger = logging.getLogger(__name__)

def start_selection_or_minigame(socketio, game_manager, room_code):
    """Decide between starting a minigame or doing a normal selection."""
    room = game_manager.get_room(room_code)
    if not room or len(room.players) < 2:
        return

    # Check for minigame chance
    minigame_chance = room.settings.get('minigame_chance', 20) / 100.0
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

        socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

        # Minigame continues until voting completes (handled by minigame vote handler)
    else:
        # No minigame - proceed to normal selection
        selected_player = random.choice(room.players)
        room.game_state.set_selected_player(selected_player.name)

        selection_duration = room.settings['selection_duration']
        room.game_state.start_selection(duration=selection_duration)

        socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

        # Schedule truth/dare phase after selection
        def start_truth_dare_phase():
            time.sleep(selection_duration)
            start_truth_dare_phase_handler(socketio, game_manager, room_code)

        td_thread = threading.Thread(target=start_truth_dare_phase)
        td_thread.daemon = True
        td_thread.start()


def start_truth_dare_phase_handler(socketio, game_manager, room_code):
    """Helper to start truth/dare phase"""
    room = game_manager.get_room(room_code)
    if not room:
        return

    # If no choice was made, randomize
    if room.game_state.selected_choice is None:
        room.game_state.set_selected_choice(random.choice(['truth', 'dare']))

    # Get the selected player
    selected_player = room.get_player_by_name(room.game_state.selected_player)
    list_was_empty = False

    if selected_player:
        # Pick random truth or dare based on choice
        choice = room.game_state.selected_choice
        if choice == 'truth':
            truths = selected_player.truth_dare_list.truths
            if truths:
                selected_item = random.choice(truths)
                selected_player.truth_dare_list.truths.remove(selected_item)
                room.game_state.set_current_truth_dare(selected_item.to_dict())
            else:
                # List is empty! Try AI generation if enabled
                ai_enabled = room.settings.get('ai_generation_enabled', False)
                logger.info(f"Player {selected_player.name}'s truth list is empty. AI generation enabled: {ai_enabled}")

                generated_text = None

                if ai_enabled:
                    # Get AI generator and try to generate a new truth
                    ai_gen = get_ai_generator()
                    logger.info(f"AI generator status - Enabled: {ai_gen.enabled}, Has client: {ai_gen.client is not None}")

                    if ai_gen.enabled:
                        # Get context from room defaults (since player's list is empty)
                        existing_truths = room.default_truths.copy()

                        # Also add truths from other players for more variety
                        for other_player in room.players:
                            if other_player.socket_id != selected_player.socket_id:
                                existing_truths.extend([t.text for t in other_player.truth_dare_list.truths])

                        logger.info(f"Attempting to generate truth with {len(existing_truths)} existing truths as context")
                        generated_text = ai_gen.generate_truth(existing_truths)

                        if generated_text:
                            # Successfully generated! Add it to the player's list and use it
                            logger.info(f"Successfully generated truth for {selected_player.name}: '{generated_text[:50]}...'")
                            new_truth = Truth(generated_text, is_default=False, submitted_by='AI')
                            selected_player.truth_dare_list.truths.append(new_truth)
                            room.game_state.set_current_truth_dare(new_truth.to_dict())
                            list_was_empty = False  # Successfully generated, so list wasn't really empty
                        else:
                            logger.error(f"AI generation returned None for truth - falling back to empty message")
                    else:
                        logger.warning(f"AI generator is not enabled - Initialization error: {ai_gen.initialization_error}")

                # If AI didn't generate (disabled or failed), use fallback message
                if generated_text is None:
                    logger.warning(f"Using fallback message for {selected_player.name} - no truths available")
                    list_was_empty = True
                    room.game_state.list_empty = True
                    room.game_state.set_current_truth_dare({
                        'text': f'{selected_player.name} has no more truths available!',
                        'type': 'truth',
                        'is_default': False,
                        'submitted_by': None
                    })
        else:  # dare
            dares = selected_player.truth_dare_list.dares
            if dares:
                selected_item = random.choice(dares)
                selected_player.truth_dare_list.dares.remove(selected_item)
                room.game_state.set_current_truth_dare(selected_item.to_dict())
            else:
                # List is empty! Try AI generation if enabled
                ai_enabled = room.settings.get('ai_generation_enabled', False)
                logger.info(f"Player {selected_player.name}'s dare list is empty. AI generation enabled: {ai_enabled}")

                generated_text = None

                if ai_enabled:
                    # Get AI generator and try to generate a new dare
                    ai_gen = get_ai_generator()
                    logger.info(f"AI generator status - Enabled: {ai_gen.enabled}, Has client: {ai_gen.client is not None}")

                    if ai_gen.enabled:
                        # Get context from room defaults (since player's list is empty)
                        existing_dares = room.default_dares.copy()

                        # Also add dares from other players for more variety
                        for other_player in room.players:
                            if other_player.socket_id != selected_player.socket_id:
                                existing_dares.extend([d.text for d in other_player.truth_dare_list.dares])

                        logger.info(f"Attempting to generate dare with {len(existing_dares)} existing dares as context")
                        generated_text = ai_gen.generate_dare(existing_dares)

                        if generated_text:
                            # Successfully generated! Add it to the player's list and use it
                            logger.info(f"Successfully generated dare for {selected_player.name}: '{generated_text[:50]}...'")
                            new_dare = Dare(generated_text, is_default=False, submitted_by='AI')
                            selected_player.truth_dare_list.dares.append(new_dare)
                            room.game_state.set_current_truth_dare(new_dare.to_dict())
                            list_was_empty = False  # Successfully generated, so list wasn't really empty
                        else:
                            logger.error(f"AI generation returned None for dare - falling back to empty message")
                    else:
                        logger.warning(f"AI generator is not enabled - Initialization error: {ai_gen.initialization_error}")

                # If AI didn't generate (disabled or failed), use fallback message
                if generated_text is None:
                    logger.warning(f"Using fallback message for {selected_player.name} - no dares available")
                    list_was_empty = True
                    room.game_state.list_empty = True
                    room.game_state.set_current_truth_dare({
                        'text': f'{selected_player.name} has no more dares available!',
                        'type': 'dare',
                        'is_default': False,
                        'submitted_by': None
                    })

    # Start truth/dare phase with configurable duration
    td_duration = room.settings['truth_dare_duration']
    room.game_state.start_truth_dare(duration=td_duration)

    # If list was empty, automatically activate skip
    if list_was_empty:
        room.game_state.list_empty = True
        room.game_state.activate_skip()
        skip_duration = room.settings['skip_duration']
        room.game_state.reduce_timer(skip_duration)

    socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

    # Schedule end of truth/dare phase
    def end_truth_dare_phase():
        # Check timer dynamically
        while True:
            time.sleep(0.5)
            room = game_manager.get_room(room_code)
            if not room:
                break

            # Check if phase is complete
            if room.game_state.is_phase_complete():
                # Award points for performing
                performer = room.get_player_by_name(room.game_state.selected_player)
                if performer:
                    ScoringSystem.award_perform_points(performer)

                # Award points to submitter if custom truth/dare
                if room.game_state.current_truth_dare:
                    submitted_by = room.game_state.current_truth_dare.get('submitted_by')
                    if submitted_by:
                        submitter = room.get_player_by_name(submitted_by)
                        if submitter:
                            ScoringSystem.award_submission_performed_points(submitter)

                # Record round history
                if room.game_state.current_truth_dare:
                    round_record = RoundRecord(
                        round_number=room.game_state.current_round,
                        selected_player_name=room.game_state.selected_player,
                        truth_dare_text=room.game_state.current_truth_dare['text'],
                        truth_dare_type=room.game_state.current_truth_dare.get('type', room.game_state.selected_choice),
                        submitted_by=room.game_state.current_truth_dare.get('submitted_by')
                    )
                    room.add_round_record(round_record)

                # Check if game should end
                if room.game_state.should_end_game():
                    room.game_state.start_end_game()

                    # Broadcast end game state with statistics
                    end_game_data = {
                        'phase': 'end_game',
                        'round_history': room.get_round_history(),
                        'top_players': room.get_top_players(5),
                        'all_players': [{'name': p.name, 'score': p.score} for p in room.players]
                    }
                    socketio.emit('game_state_update', end_game_data, room=room_code, namespace='/')
                else:
                    # Continue to next round
                    prep_duration = room.settings['preparation_duration']
                    room.game_state.start_preparation(duration=prep_duration)

                    # Reset player submission counters
                    room.reset_player_round_submissions()

                    socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

                    # Continue the loop - start next round
                    def next_round():
                        time.sleep(prep_duration)
                        start_selection_or_minigame(socketio, game_manager, room_code)

                    next_round_thread = threading.Thread(target=next_round)
                    next_round_thread.daemon = True
                    next_round_thread.start()
                break

    td_end_thread = threading.Thread(target=end_truth_dare_phase)
    td_end_thread.daemon = True
    td_end_thread.start()
