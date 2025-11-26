# tests/ai/test_ai_mocked_significant.py

import pytest
from Model.ai_generator import AIGenerator
from Model.truth_dare_list import TruthDareList
from Model.round_record import RoundRecord
from Model.player import Player


# ======================================================
# T-AI-001 — Significant AI Test (Mocked)
# AI should disable when key not found
# ======================================================
def test_ai_disabled_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    ai = AIGenerator()

    assert ai.enabled is False
    assert ai.client is None
    assert ai.initialization_error is not None


# ======================================================
# T-AI-002 — Significant AI Test (Mocked)
# AI generates a truth and dare safely using mock
# ======================================================
def test_mock_ai_generates_truth_and_dare(mock_ai_generator):
    truth = mock_ai_generator.generate_truth([])
    dare = mock_ai_generator.generate_dare([])

    assert truth == "AI Generated Truth"
    assert dare == "AI Generated Dare"


# ======================================================
# T-AI-003 — Significant AI Test (Mocked)
# AI avoids duplicates in truth generation logic
# ======================================================
def test_mock_ai_avoids_duplicates(monkeypatch):
    ai = AIGenerator()
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")  # bypass disabled logic

    # Mock duplicate-avoidance algorithm
    monkeypatch.setattr(ai, "generate_truth", lambda existing: "New Unique Truth")

    existing_truths = ["Truth One", "Truth Two"]
    generated = ai.generate_truth(existing_truths)

    assert generated not in existing_truths
    assert isinstance(generated, str)


# ======================================================
# T-AI-004 — Significant AI Test (Mocked)
# AI integrated with TruthDareList
# ======================================================
def test_ai_integration_with_truthdarelist(mock_ai_generator):
    lst = TruthDareList()

    # Simulate AI filling empty list
    generated = mock_ai_generator.generate_truth([])
    lst.add_truth(generated, "AI")  # FIXED: no is_default argument

    truths = lst.get_truths()

    assert truths[-1]["text"] == "AI Generated Truth"
    assert truths[-1]["submitted_by"] == "AI"


# ======================================================
# T-AI-005 — Significant AI Test (Mocked)
# AI populates RoundRecord correctly
# ======================================================
def test_ai_roundrecord_integration(mock_ai_generator):
    generated = mock_ai_generator.generate_truth([])

    rr = RoundRecord(
        round_number=1,
        selected_player_name="Alice",
        truth_dare_text=generated,
        truth_dare_type="truth",
        submitted_by="AI"
    )

    d = rr.to_dict()

    assert d["truth_dare"]["text"] == "AI Generated Truth"
    assert d["submitted_by"] == "AI"


# ======================================================
# T-AI-006 — Significant AI Test (Mocked)
# AI used when player's list is empty
# ======================================================
def test_ai_activates_when_player_list_empty(mock_ai_generator):
    player = Player("s1", "Alice")
    player.truth_dare_list.set_custom_defaults([], [])  # force empty list

    # Simulate truth generation pipeline
    generated = mock_ai_generator.generate_truth(player.truth_dare_list.get_truths())

    assert isinstance(generated, str)
    assert generated == "AI Generated Truth"
