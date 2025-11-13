from Model.minigame import Minigame, StaringContest
from Model.player import Player


# T-013 — US-015: Minigame voting and winner resolution
def test_minigame_winner():
    mg = Minigame()
    p1 = Player("s1", "Alice")
    p2 = Player("s2", "Bob")

    mg.add_participant(p1)
    mg.add_participant(p2)
    mg.set_total_voters(2)

    # Both voters vote that Bob lost
    mg.add_vote("voter1", "Bob")
    mg.add_vote("voter2", "Bob")

    loser = mg.check_immediate_winner()

    assert loser is not None
    assert mg.is_complete
    assert loser.name == "Bob"
    assert mg.loser.name == "Bob"
    assert mg.winner.name == "Alice"


# T-013b — US-015: StaringContest sets descriptive fields
def test_staring_contest_metadata():
    sc = StaringContest()

    assert sc.type == "staring_contest"
    assert "Staring Contest" in sc.name
    assert "blinked" in sc.description_voter
