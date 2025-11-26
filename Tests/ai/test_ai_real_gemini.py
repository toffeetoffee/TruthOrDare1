#disabling this because these tests require real API access

# import os
# import pytest
# from Model.ai_generator import AIGenerator

# API_KEY = ""


# @pytest.mark.realai
# def test_real_ai_initialization():
#     os.environ["GEMINI_API_KEY"] = API_KEY

#     ai = AIGenerator()
#     assert ai.enabled is True
#     assert ai.client is not None
#     assert ai.initialization_error is None


# @pytest.mark.realai
# def test_real_ai_generates_truth():
#     os.environ["GEMINI_API_KEY"] = API_KEY
#     ai = AIGenerator()

#     result = ai.generate_truth(["Do not duplicate this"])
#     assert isinstance(result, str)
#     assert len(result) > 3
#     assert "Do not duplicate this" not in result


# @pytest.mark.realai
# def test_real_ai_generates_dare():
#     os.environ["GEMINI_API_KEY"] = API_KEY
#     ai = AIGenerator()

#     result = ai.generate_dare([])
#     assert isinstance(result, str)
#     assert len(result) > 3


# @pytest.mark.realai
# def test_real_ai_multiple_generations_unique():
#     os.environ["GEMINI_API_KEY"] = API_KEY
#     ai = AIGenerator()

#     generated = set()
#     for _ in range(3):
#         text = ai.generate_truth([])
#         assert isinstance(text, str)
#         generated.add(text)

#     # Ensure nontrivial variety
#     assert len(generated) >= 2


# @pytest.mark.realai
# def test_real_ai_context_aware_generation():
#     os.environ["GEMINI_API_KEY"] = API_KEY
#     ai = AIGenerator()

#     existing = ["Reveal your biggest regret"]

#     response = ai.generate_truth(existing)
#     assert isinstance(response, str)
#     assert "regret" not in response.lower()
