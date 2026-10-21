"""Groq LLM client implementation."""

import os
from typing import Optional

from lakeforge.llm.base import BaseLLM, LLMResponse

# Import Groq at module level for mocking
try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore


class GroqLLM(BaseLLM):
    """Groq LLM client using groq-python library."""

    # Groq pricing (as of 2024)
    PRICING = {
        "llama-3.1-70b-versatile": {
            "input": 0.59 / 1_000_000,  # per token
            "output": 0.79 / 1_000_000,
        },
        "llama-3.1-8b-instant": {
            "input": 0.05 / 1_000_000,
            "output": 0.08 / 1_000_000,
        },
        "mixtral-8x7b-32768": {
            "input": 0.24 / 1_000_000,
            "output": 0.24 / 1_000_000,
        },
    }

    def __init__(
        self, model: str = "llama-3.1-70b-versatile", api_key: Optional[str] = None
    ):
        """
        Initialize Groq LLM client.

        Args:
            model: Model name (default: Llama 3.1 70B)
            api_key: Groq API key (default: from GROQ_API_KEY env var)
        """
        super().__init__(model)
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Groq API key not found. Set GROQ_API_KEY environment variable."
            )

        if Groq is None:
            raise ImportError(
                "groq-python is required. Install with: pip install groq"
            )

        self.client = Groq(api_key=self.api_key)

    def complete(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> LLMResponse:
        """
        Generate completion using Groq API.

        Args:
            prompt: Input prompt
            max_tokens: Max tokens in response
            temperature: Sampling temperature
            top_p: Nucleus sampling

        Returns:
            LLMResponse with generated text and token counts
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            text = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Calculate cost
            cost = self.calculate_cost(prompt_tokens, completion_tokens)

            return LLMResponse(
                text=text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=self.model,
                cost=cost,
            )

        except Exception as e:
            # Handle rate limits and other errors
            if "rate_limit" in str(e).lower():
                raise RuntimeError(f"Groq rate limit exceeded: {e}")
            raise RuntimeError(f"Groq API error: {e}")

    def calculate_cost(
        self, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Calculate cost for this model."""
        pricing = self.PRICING.get(
            self.model,
            {"input": 0.0, "output": 0.0},
        )
        return (
            prompt_tokens * pricing["input"]
            + completion_tokens * pricing["output"]
        )
