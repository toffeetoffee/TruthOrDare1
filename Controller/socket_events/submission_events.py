from flask_socketio import emit
from flask import request

from Model.scoring_system import ScoringSystem


def register_submission_events(socketio, game_manager):

    @socketio.on("submit_truth_dare")
    def on_submit_truth_dare(data):
        try:
            rc = data.get("room")
            text = data.get("text", "").strip()
            item_type = data.get("type")
            targets = data.get("targets", [])

            if not rc or not text or not item_type or not targets:
                return

            room = game_manager.get_room(rc)
            if not room:
                return

            if room.game_state.phase != "preparation":
                return

            submitter = room.get_player_by_sid(request.sid)
            if not submitter:
                return

            # per-round limit, done atomically
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

            ok_targets = []
            for name in targets:
                target = room.get_player_by_name(name)
                if target:
                    if item_type == "truth":
                        target.truth_dare_list.add_truth(
                            text, submitted_by=submitter.name
                        )
                    elif item_type == "dare":
                        target.truth_dare_list.add_dare(
                            text, submitted_by=submitter.name
                        )
                    ok_targets.append(name)

            if ok_targets:
                ScoringSystem.award_submission_points(submitter)

                emit(
                    "submission_success",
                    {
                        "text": text,
                        "type": item_type,
                        "targets": ok_targets,
                    },
                    to=request.sid,
                )
        except Exception as e:
            print(f"[ERROR] submit_truth_dare: {e}")
            emit("submission_error", {"message": "An error occurred"}, to=request.sid)
