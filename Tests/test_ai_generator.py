import os
from Model.ai_generator import AIGenerator


# T-015 — US-018: AI is disabled when GEMINI_API_KEY is missing
def test_ai_disabled_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    ai = AIGenerator()

    assert ai.enabled is False
    assert ai.client is None
    assert ai.initialization_error is not None


# T-015b — US-018: Using mock_ai_generator fixture to ensure AI outputs strings
def test_ai_generation_mock_fixture(mock_ai_generator):
    truth = mock_ai_generator.generate_truth([])
    dare = mock_ai_generator.generate_dare([])

    assert truth == "AI Generated Truth"
    assert dare == "AI Generated Dare"
