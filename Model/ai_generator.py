import os
import logging
from google import genai
from typing import List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIGenerator:
    """Handles AI generation of truths and dares using Gemini API"""
    
    # Model optimized for free tier (30 RPM)
    MODEL = "gemini-2.0-flash-lite"
    
    def __init__(self):
        """Initialize Gemini API client with API key from environment"""
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables - AI generation will be disabled")
            self.enabled = False
            self.client = None
            self.initialization_error = "API key not configured"
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            self.initialization_error = None
            logger.info(f"Gemini AI initialized successfully with model: {self.MODEL}")
        except Exception as e:
            logger.error(f"Error initializing Gemini AI: {e}", exc_info=True)
            self.enabled = False
            self.client = None
            self.initialization_error = str(e)
    
    def generate_truth(self, existing_truths: List[str]) -> Optional[str]:
        """
        Generate a new truth question using Gemini API
        
        Args:
            existing_truths: List of existing truth questions to avoid duplicates
            
        Returns:
            Generated truth question or None if generation fails
        """
        if not self.enabled or not self.client:
            logger.warning(f"Cannot generate truth - AI generator not enabled. Reason: {self.initialization_error}")
            return None
        
        prompt = self._build_truth_prompt(existing_truths)
        logger.info(f"Generating truth with {len(existing_truths)} existing truths as context")
        
        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config={"max_output_tokens": 256}
            )
            
            # Validate response object
            if not response:
                logger.error("Received empty response from Gemini API")
                return None
            
            # Try to get text from response - handle different response formats
            generated_text = None
            if hasattr(response, 'text'):
                generated_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to get text from first candidate
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts = candidate.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        generated_text = parts[0].text
            
            if not generated_text:
                logger.error(f"Could not extract text from response. Response type: {type(response)}, Response: {response}")
                return None
            
            generated_text = generated_text.strip()
            
            # Validate that we actually got content
            if not generated_text or len(generated_text) < 5:
                logger.error(f"Generated text is too short or empty: '{generated_text}'")
                return None
            
            # Remove quotes if present
            if generated_text.startswith('"') and generated_text.endswith('"'):
                generated_text = generated_text[1:-1]
            if generated_text.startswith("'") and generated_text.endswith("'"):
                generated_text = generated_text[1:-1]
            
            # Ensure it ends with a question mark
            if not generated_text.endswith('?'):
                generated_text += '?'
            
            logger.info(f"Successfully generated truth: '{generated_text[:50]}...'")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating truth: {e}", exc_info=True)
            return None
    
    def generate_dare(self, existing_dares: List[str]) -> Optional[str]:
        """
        Generate a new dare challenge using Gemini API
        
        Args:
            existing_dares: List of existing dare challenges to avoid duplicates
            
        Returns:
            Generated dare challenge or None if generation fails
        """
        if not self.enabled or not self.client:
            logger.warning(f"Cannot generate dare - AI generator not enabled. Reason: {self.initialization_error}")
            return None
        
        prompt = self._build_dare_prompt(existing_dares)
        logger.info(f"Generating dare with {len(existing_dares)} existing dares as context")
        
        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config={"max_output_tokens": 256}
            )
            
            # Validate response object
            if not response:
                logger.error("Received empty response from Gemini API")
                return None
            
            # Try to get text from response - handle different response formats
            generated_text = None
            if hasattr(response, 'text'):
                generated_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to get text from first candidate
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts = candidate.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        generated_text = parts[0].text
            
            if not generated_text:
                logger.error(f"Could not extract text from response. Response type: {type(response)}, Response: {response}")
                return None
            
            generated_text = generated_text.strip()
            
            # Validate that we actually got content
            if not generated_text or len(generated_text) < 5:
                logger.error(f"Generated text is too short or empty: '{generated_text}'")
                return None
            
            # Remove quotes if present
            if generated_text.startswith('"') and generated_text.endswith('"'):
                generated_text = generated_text[1:-1]
            if generated_text.startswith("'") and generated_text.endswith("'"):
                generated_text = generated_text[1:-1]
            
            logger.info(f"Successfully generated dare: '{generated_text[:50]}...'")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating dare: {e}", exc_info=True)
            return None
    
    def _build_truth_prompt(self, existing_truths: List[str]) -> str:
        """Build prompt for truth generation"""
        prompt = """You are helping generate questions for a Truth or Dare party game.

Generate ONE new truth question that is:
- Appropriate for teenagers and young adults (ages 13-25)
- Fun, interesting, and thought-provoking
- Not too personal or invasive
- Safe and appropriate for a party setting
- Different from all existing questions

IMPORTANT: Output ONLY the question itself, nothing else. No explanations, no prefixes, just the question.

"""
        
        if existing_truths:
            prompt += "Existing truth questions (DO NOT duplicate these):\n"
            for i, truth in enumerate(existing_truths[:30], 1):  # Limit to 30 to avoid token limits
                prompt += f"{i}. {truth}\n"
            prompt += "\n"
        
        prompt += "Generate ONE new, unique truth question now:"
        
        return prompt
    
    def _build_dare_prompt(self, existing_dares: List[str]) -> str:
        """Build prompt for dare generation"""
        prompt = """You are helping generate dares for a Truth or Dare party game.

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
            prompt += "Existing dares (DO NOT duplicate these):\n"
            for i, dare in enumerate(existing_dares[:30], 1):  # Limit to 30 to avoid token limits
                prompt += f"{i}. {dare}\n"
            prompt += "\n"
        
        prompt += "Generate ONE new, unique dare now:"
        
        return prompt
    
    def get_status(self) -> dict:
        """Get the current status of the AI generator"""
        return {
            'enabled': self.enabled,
            'model': self.MODEL,
            'initialization_error': self.initialization_error,
            'has_client': self.client is not None,
            'api_key_configured': os.environ.get('GEMINI_API_KEY') is not None
        }
    
    def test_generation(self) -> dict:
        """Test the AI generation with a simple request"""
        if not self.enabled or not self.client:
            return {
                'success': False,
                'error': f'AI generator not enabled: {self.initialization_error}'
            }
        
        try:
            logger.info("Running AI generation test...")
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents="Generate a simple truth question for a party game.",
                config={"max_output_tokens": 100}
            )
            
            # Try to extract text
            generated_text = None
            if hasattr(response, 'text'):
                generated_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts = candidate.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        generated_text = parts[0].text
            
            if generated_text:
                logger.info(f"AI generation test successful: '{generated_text[:50]}...'")
                return {
                    'success': True,
                    'sample_output': generated_text.strip()
                }
            else:
                logger.error(f"AI generation test failed - no text in response")
                return {
                    'success': False,
                    'error': 'No text in API response'
                }
        except Exception as e:
            logger.error(f"AI generation test failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
_ai_generator = None

def get_ai_generator():
    """Get or create the AI generator singleton"""
    global _ai_generator
    if _ai_generator is None:
        _ai_generator = AIGenerator()
    return _ai_generator
