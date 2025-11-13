from Model.player import Player
from Model.scoring_system import ScoringSystem


# T-022 — US-022: Player score increments correctly
def test_player_score_addition(player):
    player.add_score(50)
    assert player.score == 50


# T-007 — US-007: Submission counters work with ScoringSystem constraints
def test_submission_counter_increments_and_limit(player):
    # Initially 0
    assert player.submissions_this_round == 0

    for _ in range(ScoringSystem.MAX_SUBMISSIONS_PER_ROUND):
        assert player.can_submit_more()
        player.increment_submissions()

    assert player.submissions_this_round == ScoringSystem.MAX_SUBMISSIONS_PER_ROUND
    assert not player.can_submit_more()

    player.reset_round_submissions()
    assert player.submissions_this_round == 0


# T-010 — US-012: Used truth tracking with normalization and uniqueness
def test_used_items_tracking():
    p = Player("s1", "Alice")

    p.mark_truth_used("Sample Truth")
    p.mark_truth_used("sample truth")  # duplicate in different case

    # Only one stored, but normalized set remembers it
    assert p.get_all_used_truths() == ["Sample Truth"]
    assert p.has_used_truth("SAMPLE TRUTH")
