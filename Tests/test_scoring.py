from Model.player import Player
from Model.scoring_system import ScoringSystem


# T-022 — US-022: ScoringSystem awards correct points for actions
def test_scoring_values():
    p = Player("s1", "Alice")

    ScoringSystem.award_submission_points(p)
    assert p.score == ScoringSystem.POINTS_SUBMISSION

    ScoringSystem.award_submission_performed_points(p)
    assert p.score == ScoringSystem.POINTS_SUBMISSION + ScoringSystem.POINTS_SUBMITTED_PERFORMED

    ScoringSystem.award_minigame_participate_points(p)
    assert p.score == (
        ScoringSystem.POINTS_SUBMISSION
        + ScoringSystem.POINTS_SUBMITTED_PERFORMED
        + ScoringSystem.POINTS_MINIGAME_PARTICIPATE
    )

    ScoringSystem.award_perform_points(p)
    assert p.score == (
        ScoringSystem.POINTS_SUBMISSION
        + ScoringSystem.POINTS_SUBMITTED_PERFORMED
        + ScoringSystem.POINTS_MINIGAME_PARTICIPATE
        + ScoringSystem.POINTS_PERFORM
    )
