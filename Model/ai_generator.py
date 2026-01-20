import os
import logging
import threading
from typing import List, Optional

from google import genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIGenerator:
    MODEL = "gemini-1.5-flash"

    def __init__(self):
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in env -> AI off")
            self.enabled = False
            self.client = None
            self.initialization_error = "API key not configured"
            return

        try:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            self.initialization_error = None
            logger.info(f"Gemini AI init ok, model={self.MODEL}")
        except Exception as e:
            logger.error(f"Error initializing Gemini AI: {e}", exc_info=True)
            self.enabled = False
            self.client = None
            self.initialization_error = str(e)

    def generate_truth(self, existing_truths: List[str]) -> Optional[str]:
        if not self.enabled or not self.client:
            logger.warning(
                f"Cannot generate truth - AI off. Reason: {self.initialization_error}"
            )
            return None

        prompt = self._truth_prompt(existing_truths)
        logger.info(f"Generating truth with {len(existing_truths)} existing truths")

        try:
            resp = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config={"max_output_tokens": 256}
            )

            if not resp:
                logger.error("Empty response from Gemini API")
                return None

            txt = None
            if hasattr(resp, 'text'):
                txt = resp.text
            elif hasattr(resp, 'candidates') and resp.candidates:
                c = resp.candidates[0]
                if hasattr(c, 'content') and hasattr(c.content, 'parts'):
                    parts = c.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        txt = parts[0].text

            if not txt:
                logger.error(f"Could not extract text from response: {type(resp)} {resp}")
                return None

            txt = txt.strip()

            if not txt or len(txt) < 5:
                logger.error(f"Generated truth too short/empty: '{txt}'")
                return None

            if txt.startswith('"') and txt.endswith('"'):
                txt = txt[1:-1]
            if txt.startswith("'") and txt.endswith("'"):
                txt = txt[1:-1]

            if not txt.endswith('?') :
                txt += '?'

            logger.info(f"Generated truth ok: '{txt[:50]}...'")
            return txt

        except Exception as e:
            logger.error(f"Error generating truth: {e}", exc_info=True)
            return None

    def generate_dare(self, existing_dares: List[str]) -> Optional[str]:
        if not self.enabled or not self.client:
            logger.warning(
                f"Cannot generate dare - AI off. Reason: {self.initialization_error}"
            )
            return None

        prompt = self._dare_prompt(existing_dares)
        logger.info(f"Generating dare with {len(existing_dares)} existing dares")

        try:
            resp = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config={"max_output_tokens": 256}
            )

            if not resp:
                logger.error("Empty response from Gemini API")
                return None

            txt = None
            if hasattr(resp, 'text'):
                txt = resp.text
            elif hasattr(resp, 'candidates') and resp.candidates:
                c = resp.candidates[0]
                if hasattr(c, 'content') and hasattr(c.content, 'parts'):
                    parts = c.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        txt = parts[0].text

            if not txt:
                logger.error(f"Could not extract dare text from response: {type(resp)}")
                return None

            txt = txt.strip()

            if not txt or len(txt) < 5:
                logger.error(f"Generated dare too short/empty: '{txt}'")
                return None

            if txt.startswith('"') and txt.endswith('"'):
                txt = txt[1:-1]
            if txt.startswith("'") and txt.endswith("'"):
                txt = txt[1:-1]

            logger.info(f"Generated dare ok: '{txt[:50]}...'")
            return txt

        except Exception as e:
            logger.error(f"Error generating dare: {e}", exc_info=True)
            return None

    def _truth_prompt(self, existing_truths: List[str]) -> str:
        # bit long but easier to just keep it as one big string
        p = """You are helping generate questions for a Truth or Dare party game.

Generate ONE new truth question that is:
- Appropriate for teenagers and young adults (ages 13-25)
- Fun, interesting, and thought-provoking
- Not too personal or invasive
- Safe and appropriate for a party setting
- Different from all existing questions

IMPORTANT: Output ONLY the question itself, nothing else. No explanations, no prefixes, just the question.

"""
        if existing_truths:
            p += "Existing truth questions (DO NOT duplicate these):\n"
            for i, t in enumerate(existing_truths[:30], 1):
                p += f"{i}. {t}\n"
            p += "\n"

        p += "Generate ONE new, unique truth question now:"
        return p

    def _dare_prompt(self, existing_dares: List[str]) -> str:
        p = """You are helping generate dares for a Truth or Dare party game.

Generate ONE new dare that is:
- Appropriate for teenagers and young adults (ages 13-25)
- Fun, silly, and entertaining
- Safe and physically harmless
- Doable in a typical indoor setting
- Not embarrassing or humiliating
- Legal and ethical
- Different from all existing dares

IMPORTANT: Output ONLY the dare itself, nothing else. No explanations, no prefixes, just the dare action.

"""
        if existing_dares:
            p += "Existing dares (DO NOT duplicate these):\n"
            for i, d in enumerate(existing_dares[:30], 1):
                p += f"{i}. {d}\n"
            p += "\n"

        p += "Generate ONE new, unique dare now:"
        return p

    def get_status(self) -> dict:
        return {
            "enabled": self.enabled,
            "model": self.MODEL,
            "initialization_error": self.initialization_error,
            "has_client": self.client is not None,
            "api_key_configured": os.environ.get("GEMINI_API_KEY") is not None
        }

    def test_generation(self) -> dict:
        if not self.enabled or not self.client:
            return {
                "success": False,
                "error": f"AI generator not enabled: {self.initialization_error}"
            }

        try:
            logger.info("Running AI generation test...")
            resp = self.client.models.generate_content(
                model=self.MODEL,
                contents="Generate a simple truth question for a party game.",
                config={"max_output_tokens": 100}
            )

            txt = None
            if hasattr(resp, 'text'):
                txt = resp.text
            elif hasattr(resp, 'candidates') and resp.candidates:
                c = resp.candidates[0]
                if hasattr(c, 'content') and hasattr(c.content, 'parts'):
                    parts = c.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        txt = parts[0].text

            if txt:
                logger.info(f"AI test ok: '{txt[:50]}...'")
                return {"success": True, "sample_output": txt.strip()}
            else:
                logger.error("AI test failed - no text")
                return {"success": False, "error": "No text in API response"}

        except Exception as e:
            logger.error(f"AI test failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


_ai_generator = None
_ai_generator_lock = threading.Lock()


def get_ai_generator():
    global _ai_generator
    if _ai_generator is None:
        with _ai_generator_lock:
            if _ai_generator is None:
                _ai_generator = AIGenerator()
    return _ai_generator
