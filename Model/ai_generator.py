import os
from google import genai
from typing import List, Optional

class AIGenerator:
    """Handles AI generation of truths and dares using Gemini API"""
    
    # Model optimized for free tier (30 RPM)
    MODEL = "gemini-2.0-flash-lite"
    
    def __init__(self):
        """Initialize Gemini API client with API key from environment"""
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")
            self.enabled = False
            self.client = None
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            print("Gemini AI initialized successfully")
        except Exception as e:
            print(f"Error initializing Gemini AI: {e}")
            self.enabled = False
            self.client = None
    
    def generate_truth(self, existing_truths: List[str]) -> Optional[str]:
        """
        Generate a new truth question using Gemini API
        
        Args:
            existing_truths: List of existing truth questions to avoid duplicates
            
        Returns:
            Generated truth question or None if generation fails
        """
        if not self.enabled or not self.client:
            return None
        
        prompt = self._build_truth_prompt(existing_truths)
        
        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config={"max_output_tokens": 256}
            )
            
            # Get text from response
            generated_text = getattr(response, "text", str(response)).strip()
            
            # Remove quotes if present
            if generated_text.startswith('"') and generated_text.endswith('"'):
                generated_text = generated_text[1:-1]
            if generated_text.startswith("'") and generated_text.endswith("'"):
                generated_text = generated_text[1:-1]
            
            # Ensure it ends with a question mark
            if not generated_text.endswith('?'):
                generated_text += '?'
            
            return generated_text
        except Exception as e:
            print(f"Error generating truth: {e}")
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
            return None
        
        prompt = self._build_dare_prompt(existing_dares)
        
        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config={"max_output_tokens": 256}
            )
            
            # Get text from response
            generated_text = getattr(response, "text", str(response)).strip()
            
            # Remove quotes if present
            if generated_text.startswith('"') and generated_text.endswith('"'):
                generated_text = generated_text[1:-1]
            if generated_text.startswith("'") and generated_text.endswith("'"):
                generated_text = generated_text[1:-1]
            
            return generated_text
        except Exception as e:
            print(f"Error generating dare: {e}")
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


# Singleton instance
_ai_generator = None

def get_ai_generator():
    """Get or create the AI generator singleton"""
    global _ai_generator
    if _ai_generator is None:
        _ai_generator = AIGenerator()
    return _ai_generator
