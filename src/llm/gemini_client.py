"""
Google Gemini API client for AI-LogGuard.

Provides log analysis using Google's Gemini 2.5 Flash model.
Free tier: 15 requests/minute, 1500 requests/day.
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum

import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiModel(Enum):
    """Available Gemini models."""
    FLASH = "gemini-2.5-flash"  # Fast, efficient, free tier (LATEST)
    PRO = "gemini-2.5-pro"  # More capable, slower


class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: GeminiModel = GeminiModel.FLASH,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (if None, reads from GEMINI_API_KEY env var)
            model: Gemini model to use
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key not provided. "
                "Set GEMINI_API_KEY environment variable or pass api_key parameter.\n"
                "Get free key: https://makersuite.google.com/app/apikey"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Model settings
        self.model_name = model.value if isinstance(model, GeminiModel) else model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        # Safety settings - Allow technical content (logs with ERROR, FAILED, etc.)
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Create model instance
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
            },
            safety_settings=self.safety_settings,
        )

        logger.info(f"Initialized Gemini client with model: {self.model_name}")

    def _sanitize_prompt(self, prompt: str) -> str:
        """
        Sanitize prompt to reduce safety filter triggers.
        
        Strategy: Replace alarming words with neutral equivalents
        while preserving technical meaning.
        """
        import re
        
        # Common CI/CD log words that might trigger safety filters
        # Use case-insensitive replacement
        replacements = {
            # Error-related (might be seen as violent/dangerous)
            r'\bkill\b': 'terminate',
            r'\bkilled\b': 'terminated',
            r'\bkilling\b': 'terminating',
            r'\babort\b': 'stop',
            r'\baborted\b': 'stopped',
            r'\baborting\b': 'stopping',
            r'\bfatal\b': 'critical',
            r'\bcrash\b': 'stop',
            r'\bcrashed\b': 'stopped',
            r'\bcrashing\b': 'stopping',
            r'\bpanic\b': 'critical_error',
            r'\battack\b': 'attempt',
            # Failure-related (soften language)
            r'\bfailure\b': 'issue',
            r'\bfailed\b': 'unsuccessful',
            r'\bfailing\b': 'not_working',
            r'\bfail\b': 'issue',
            r'\bdenied\b': 'rejected',
            r'\brefuse\b': 'reject',
            r'\brefused\b': 'rejected',
            # Violent/aggressive terms
            r'\bexploded\b': 'stopped_unexpectedly',
            r'\bblew up\b': 'stopped_unexpectedly',
            r'\bdied\b': 'stopped',
            r'\bdying\b': 'stopping',
        }
        
        sanitized = prompt
        for pattern, replacement in replacements.items():
            # Case-insensitive replacement preserving case of first letter
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # Also sanitize log content markers (case-sensitive to preserve format)
        sanitized = sanitized.replace('ERROR:', 'ISSUE:')
        sanitized = sanitized.replace('Error:', 'Issue:')
        sanitized = sanitized.replace('error:', 'issue:')
        sanitized = sanitized.replace('FATAL:', 'CRITICAL:')
        sanitized = sanitized.replace('Fatal:', 'Critical:')
        sanitized = sanitized.replace('fatal:', 'critical:')
        sanitized = sanitized.replace('FAILED:', 'UNSUCCESSFUL:')
        sanitized = sanitized.replace('Failed:', 'Unsuccessful:')
        sanitized = sanitized.replace('failed:', 'unsuccessful:')
        
        return sanitized

    def _create_ultra_safe_prompt(self, original_prompt: str) -> str:
        """
        Create ultra-safe prompt by removing all log content.
        Only keeps the question/instruction part.
        
        Last resort when even sanitized prompts are blocked.
        """
        # Extract error type from prompt if present
        error_type = "unknown"
        if "dependency" in original_prompt.lower():
            error_type = "dependency"
        elif "syntax" in original_prompt.lower():
            error_type = "code syntax"
        elif "test" in original_prompt.lower():
            error_type = "test"
        elif "timeout" in original_prompt.lower():
            error_type = "timeout"
        elif "environment" in original_prompt.lower() or "configuration" in original_prompt.lower():
            error_type = "environment configuration"
        elif "network" in original_prompt.lower():
            error_type = "network connectivity"
        
        # Generic safe prompt without log content
        safe_prompt = f"""Provide general troubleshooting guidance for a {error_type} issue in a CI/CD pipeline.

Please provide:
1. Common causes of {error_type} problems in CI/CD
2. Top 3 recommended solutions
3. Best practices to prevent this issue

Keep the response concise and actionable."""
        
        return safe_prompt

    # ✅ SIMPLIFIED: No automatic retry - single attempt only
    # If Flash fails/blocked → immediate fallback to ML (handled by caller)
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        sanitize: bool = True,
        retry_with_pro: bool = False,  # ✅ DEPRECATED: No longer used
    ) -> str:
        """
        Generate text using Gemini Flash (single attempt).

        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            sanitize: Apply prompt sanitization to reduce safety triggers
            retry_with_pro: (DEPRECATED) No longer used - single attempt only

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails/blocked (caller should fallback to ML immediately)
        """
        # Sanitize prompt to reduce safety filter triggers
        original_prompt = prompt
        if sanitize:
            prompt = self._sanitize_prompt(prompt)
            if prompt != original_prompt:
                logger.info("✨ Prompt sanitized to reduce safety filter triggers")
        
        # ✅ Single attempt - if blocked, let caller handle ML fallback
        return self._generate_internal(prompt, temperature, max_tokens)

    def _generate_internal(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Internal generate method without retry logic."""
        try:
            # Override settings if provided
            generation_config = {}
            if temperature is not None:
                generation_config["temperature"] = temperature
            if max_tokens is not None:
                generation_config["max_output_tokens"] = max_tokens

            # Generate response
            if generation_config:
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
            else:
                response = self.model.generate_content(prompt)

            # Debug: Print response structure
            logger.debug(f"Response candidates: {len(response.candidates) if response.candidates else 0}")
            if response.candidates:
                candidate = response.candidates[0]
                logger.debug(f"Finish reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'):
                    logger.debug(f"Safety ratings: {candidate.safety_ratings}")
            
            # Check if response was blocked
            if not response.candidates:
                error_msg = "No response candidates returned by Gemini"
                if hasattr(response, 'prompt_feedback'):
                    error_msg += f". Prompt feedback: {response.prompt_feedback}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                # Check finish reason (2 = SAFETY)
                finish_reason_value = candidate.finish_reason
                if finish_reason_value == 2:  # SAFETY
                    error_msg = f"Response blocked by safety filters (finish_reason=SAFETY)"
                    if hasattr(candidate, 'safety_ratings'):
                        error_msg += f"\nSafety ratings: {candidate.safety_ratings}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            # Extract text
            text = response.text
            logger.debug(f"Generated response: {len(text)} chars")
            return text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Gemini's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Fallback: rough estimate (1 token ≈ 4 chars)
            return len(text) // 4

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.

        Returns:
            Dict with model details
        """
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "provider": "Google Gemini",
            "free_tier": True,
            "rate_limit": "15 req/min, 1500 req/day",
        }


def test_gemini_client():
    """Test Gemini client with a simple prompt."""
    print("Testing Gemini Client...")
    print("-" * 50)

    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set!")
        print("Get free key: https://makersuite.google.com/app/apikey")
        print("Then: export GEMINI_API_KEY='your-key-here'")
        return

    try:
        # Create client
        client = GeminiClient()
        print(f"✅ Client created: {client.model_name}")

        # Test generation
        prompt = """Analyze this Jenkins build error:

ERROR: Build failed with exit code 1
npm ERR! code ELIFECYCLE
npm ERR! errno 1

Provide a brief summary (2-3 sentences)."""

        print("\n📝 Sending test prompt...")
        response = client.generate(prompt)

        print("\n✅ Response received:")
        print(response)

        # Test token counting
        token_count = client.count_tokens(prompt)
        print(f"\n📊 Prompt tokens: {token_count}")

        # Model info
        info = client.get_model_info()
        print(f"\n📋 Model Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    test_gemini_client()
