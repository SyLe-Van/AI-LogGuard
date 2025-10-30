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
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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

        # Create model instance
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
            },
        )

        logger.info(f"Initialized Gemini client with model: {self.model_name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails after retries
        """
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
