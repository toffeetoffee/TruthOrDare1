import time
from Model.game_state import GameState


# T-005 — US-005: Game phases transition correctly
def test_phase_transitions():
    gs = GameState()

    gs.start_countdown(10)
    assert gs.phase == GameState.PHASE_COUNTDOWN

    gs.start_preparation(30)
    assert gs.phase == GameState.PHASE_PREPARATION


# T-006 — US-006: Remaining time is non-negative and within expected range
def test_get_remaining_time():
    gs = GameState()
    gs.start_countdown(2)

    time.sleep(1)
    remaining = gs.get_remaining_time()

    assert 0 <= remaining <= 2


# T-012 — US-015 / US-015 & US-015 (skip voting): skip vote tracking
def test_skip_vote_logic():
    gs = GameState()
    assert gs.get_skip_vote_count() == 0
    assert not gs.skip_activated

    gs.add_skip_vote("sid1")
    gs.add_skip_vote("sid2")

    assert gs.get_skip_vote_count() == 2

    gs.activate_skip()
    assert gs.skip_activated
