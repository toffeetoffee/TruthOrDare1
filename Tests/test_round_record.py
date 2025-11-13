from Model.round_record import RoundRecord


# T-017 — US-019: RoundRecord stores and serializes round info
def test_round_record_creation():
    rr = RoundRecord(
        round_number=1,
        selected_player_name="Alice",
        truth_dare_text="Sample Truth",
        truth_dare_type="truth",
        submitted_by="Bob",
    )

    d = rr.to_dict()

    assert d["round_number"] == 1
    assert d["selected_player"] == "Alice"
    assert d["truth_dare"]["text"] == "Sample Truth"
    assert d["truth_dare"]["type"] == "truth"
    assert d["submitted_by"] == "Bob"
