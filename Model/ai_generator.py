# Model/ai_generator.py
import os
import logging
import uuid
import time
import random
from google import genai
from typing import List, Optional

# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIGenerator:
    """Handles AI generation of truths and dares using Gemini API (with cache-busting)."""

    MODEL = "gemini-2.0-flash-lite"

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found - AI generation disabled")
            self.enabled = False
            self.client = None
            self.initialization_error = "API key not configured"
            return

        try:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            self.initialization_error = None
            logger.info(f"Gemini initialized (model={self.MODEL})")
        except Exception as e:
            self.enabled = False
            self.client = None
            self.initialization_error = str(e)
            logger.error(f"Gemini init failed: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_truth(self, existing_truths: List[str]) -> Optional[str]:
        """Generate a unique truth question."""
        if not self.enabled or not self.client:
            return None

        prompt = self._build_truth_prompt(existing_truths)

        # Random short delay between calls (avoid API echo)
        time.sleep(random.uniform(0.5, 1.5))

        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                generation_config={
                    "temperature": 0.9,
                    "top_p": 0.9,
                    "max_output_tokens": 256,
                },
            )

            generated_text = self._extract_text(response)
            if not generated_text:
                return None

            # Strip quotes, normalize punctuation
            generated_text = generated_text.strip().strip('"').strip("'")

            # Ensure it ends as a question
            if not generated_text.endswith("?"):
                generated_text += "?"

            logger.info(f"[AI GENERATED TRUTH] {generated_text}")
            return generated_text
        except Exception as e:
            logger.error(f"Error generating truth: {e}", exc_info=True)
            return None

    def generate_dare(self, existing_dares: List[str]) -> Optional[str]:
        """Generate a unique dare challenge."""
        if not self.enabled or not self.client:
            return None

        prompt = self._build_dare_prompt(existing_dares)
        time.sleep(random.uniform(0.5, 1.5))

        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                generation_config={
                    "temperature": 0.9,
                    "top_p": 0.9,
                    "max_output_tokens": 256,
                },
            )

            generated_text = self._extract_text(response)
            if not generated_text:
                return None

            generated_text = generated_text.strip().strip('"').strip("'")
            if not generated_text.endswith("."):
                generated_text += "."

            logger.info(f"[AI GENERATED DARE] {generated_text}")
            return generated_text
        except Exception as e:
            logger.error(f"Error generating dare: {e}", exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _extract_text(self, response) -> Optional[str]:
        """Extract plain text from Gemini API response."""
        if not response:
            return None
        if hasattr(response, "text"):
            return response.text.strip()
        if hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]
            if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                parts = cand.content.parts
                if parts and hasattr(parts[0], "text"):
                    return parts[0].text.strip()
        return None

    def _build_truth_prompt(self, existing_truths: List[str]) -> str:
        """Prompt template for truth generation with cache buster."""
        rand_tag = uuid.uuid4().hex[:8]
        prompt = (
            "You are generating ONE new unique Truth question for a Truth or Dare game.\n"
            "The question must be:\n"
            "- Fun, safe, and appropriate for ages 13–25\n"
            "- Unique and different from existing ones\n"
            "- Party-appropriate\n\n"
            "Existing Truth questions (avoid duplicating):\n"
        )

        for i, truth in enumerate(existing_truths[:30], 1):
            prompt += f"{i}. {truth}\n"

        prompt += (
            f"\nGenerate ONE new, unique Truth question now."
            f"\n[Random ID: {rand_tag}]"
        )
        return prompt

    def _build_dare_prompt(self, existing_dares: List[str]) -> str:
        """Prompt template for dare generation with cache buster."""
        rand_tag = uuid.uuid4().hex[:8]
        prompt = (
            "You are generating ONE new unique Dare for a Truth or Dare game.\n"
            "The dare must be:\n"
            "- Fun, silly, but safe\n"
            "- Suitable for a party with teens and young adults\n"
            "- Easy to perform without special equipment\n"
            "- Different from all existing ones\n\n"
            "Existing Dares (avoid duplicating):\n"
        )

        for i, dare in enumerate(existing_dares[:30], 1):
            prompt += f"{i}. {dare}\n"

        prompt += (
            f"\nGenerate ONE new, unique Dare now."
            f"\n[Random ID: {rand_tag}]"
        )
        return prompt

    # ------------------------------------------------------------------
    # Status utilities
    # ------------------------------------------------------------------
    def get_status(self) -> dict:
        return {
            "enabled": self.enabled,
            "model": self.MODEL,
            "initialization_error": self.initialization_error,
            "has_client": self.client is not None,
            "api_key_configured": os.environ.get("GEMINI_API_KEY") is not None,
        }

    def test_generation(self) -> dict:
        """Simple connectivity check."""
        if not self.enabled or not self.client:
            return {"success": False, "error": "AI not enabled"}

        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents="Generate one short truth question for a party.",
                generation_config={"temperature": 0.9, "max_output_tokens": 64},
            )
            txt = self._extract_text(response)
            return {"success": True, "sample_output": txt or "No text"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ----------------------------------------------------------------------
# Singleton accessor
# ----------------------------------------------------------------------
_ai_generator = None


def get_ai_generator():
    """Return singleton AI generator."""
    global _ai_generator
    if _ai_generator is None:
        _ai_generator = AIGenerator()
    return _ai_generator
