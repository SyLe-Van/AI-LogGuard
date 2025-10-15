"""
OpenAI client for AI-LogGuard
Handles communication with OpenAI API with retry logic and rate limiting
"""
import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Client for OpenAI API with retry logic and error handling
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (defaults to env var)
            model: Model to use (gpt-3.5-turbo, gpt-4, etc.)
            max_retries: Maximum number of retries
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, timeout=timeout)
        except ImportError:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            )
        
        # Track usage
        self.total_tokens = 0
        self.request_count = 0
        self.error_count = 0
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request with retry logic
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            **kwargs: Additional arguments for API
            
        Returns:
            Response dict with 'content', 'tokens', 'model'
        """
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Extract response
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
                
                # Update stats
                self.total_tokens += tokens_used
                self.request_count += 1
                
                logger.info(
                    f"OpenAI API call successful: {tokens_used} tokens, "
                    f"model={response.model}"
                )
                
                return {
                    "content": content,
                    "tokens": tokens_used,
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason,
                }
            
            except Exception as e:
                attempt += 1
                last_error = e
                self.error_count += 1
                
                logger.warning(
                    f"OpenAI API call failed (attempt {attempt}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"OpenAI API call failed after {self.max_retries} attempts")
                    raise last_error
        
        raise last_error
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Simplified generate method for single prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional arguments
            
        Returns:
            Generated text content
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response["content"]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics
        
        Returns:
            Dict with usage stats
        """
        # Approximate cost (GPT-3.5-turbo: $0.002 per 1K tokens)
        cost_per_1k = 0.002 if "gpt-3.5" in self.model else 0.03  # GPT-4 higher
        estimated_cost = (self.total_tokens / 1000) * cost_per_1k
        
        return {
            "model": self.model,
            "requests": self.request_count,
            "errors": self.error_count,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(estimated_cost, 4),
            "success_rate": (
                round((self.request_count / (self.request_count + self.error_count)) * 100, 2)
                if (self.request_count + self.error_count) > 0
                else 0
            )
        }
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.total_tokens = 0
        self.request_count = 0
        self.error_count = 0


# Singleton instance
_client: Optional[OpenAIClient] = None


def get_openai_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    force_new: bool = False
) -> OpenAIClient:
    """
    Get or create OpenAI client singleton
    
    Args:
        api_key: Optional API key override
        model: Optional model override
        force_new: Force creation of new client
        
    Returns:
        OpenAIClient instance
    """
    global _client
    
    if _client is None or force_new:
        _client = OpenAIClient(
            api_key=api_key,
            model=model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        )
    
    return _client
