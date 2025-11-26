from flask_socketio import emit
from flask import request

from Model.scoring_system import ScoringSystem


def register_submission_events(socketio, game_manager):
    """Register events related to player submissions of truths/dares."""

    @socketio.on("submit_truth_dare")
    def on_submit_truth_dare(data):
        try:
            room_code = data.get("room")
            text = data.get("text", "").strip()
            item_type = data.get("type")
            target_names = data.get("targets", [])

            if not room_code or not text or not item_type or not target_names:
                return

            room = game_manager.get_room(room_code)
            if not room:
                return

            if room.game_state.phase != "preparation":
                return

            submitter = room.get_player_by_sid(request.sid)
            if not submitter:
                return

            # Atomic check and increment
            if not submitter.try_submit():
                emit(
                    "submission_error",
                    {
                        "message": (
                            "You can only submit "
                            f"{ScoringSystem.MAX_SUBMISSIONS_PER_ROUND} "
                            "truths/dares per round"
                        )
                    },
                    to=request.sid,
                )
                return

            successfully_added = []
            for target_name in target_names:
                target_player = room.get_player_by_name(target_name)
                if target_player:
                    if item_type == "truth":
                        target_player.truth_dare_list.add_truth(
                            text, submitted_by=submitter.name
                        )
                    elif item_type == "dare":
                        target_player.truth_dare_list.add_dare(
                            text, submitted_by=submitter.name
                        )
                    successfully_added.append(target_name)

            if successfully_added:
                ScoringSystem.award_submission_points(submitter)

                emit(
                    "submission_success",
                    {
                        "text": text,
                        "type": item_type,
                        "targets": successfully_added,
                    },
                    to=request.sid,
                )
        except Exception as e:
            print(f"[ERROR] submit_truth_dare: {e}")
            emit("submission_error", {"message": "An error occurred"}, to=request.sid)