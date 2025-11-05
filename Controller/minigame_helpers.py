# minigame_helpers.py
import threading
import time
from flask_socketio import emit

def handle_minigame_vote(socketio, game_manager, room_code, voted_player, request):
    """
    Handles a minigame vote. This function expects to be called from an
    event handler and will perform the same checks/behaviour as the original
    on_minigame_vote logic (emit updates, schedule selection->td, etc).
    """
    room = game_manager.get_room(room_code)
    if not room:
        return

    # Only during minigame phase
    if room.game_state.phase != 'minigame':
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
        selection_duration = room.settings['selection_duration']
        room.game_state.start_selection(duration=selection_duration)

        socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

        # Schedule truth/dare phase
        def start_td():
            time.sleep(selection_duration)
            # delegate to selection_helpers to keep flow consistent
            from selection_helpers import start_truth_dare_phase_handler
            start_truth_dare_phase_handler(socketio, game_manager, room_code)

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
            selection_duration = room.settings['selection_duration']
            room.game_state.start_selection(duration=selection_duration)

            socketio.emit('game_state_update', room.game_state.to_dict(), room=room_code, namespace='/')

            # Schedule truth/dare phase
            def start_td():
                time.sleep(selection_duration)
                from selection_helpers import start_truth_dare_phase_handler
                start_truth_dare_phase_handler(socketio, game_manager, room_code)

            td_thread = threading.Thread(target=start_td)
            td_thread.daemon = True
            td_thread.start()
    else:
        # Just broadcast updated vote count
        emit('game_state_update', room.game_state.to_dict(), room=room_code)
