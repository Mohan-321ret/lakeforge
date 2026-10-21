"""LLM abstraction layer for multi-provider support."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Response from LLM completion."""

    text: str
    """Generated text."""
    prompt_tokens: int
    """Number of input tokens."""
    completion_tokens: int
    """Number of output tokens."""
    total_tokens: int
    """Total tokens (input + output)."""
    model: str
    """Model used for completion."""
    cost: float = 0.0
    """Cost in USD for this completion."""


class BaseLLM(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model: str = "default"):
        """
        Initialize LLM client.

        Args:
            model: Model name to use
        """
        self.model = model

    @abstractmethod
    def complete(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> LLMResponse:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-2.0)
            top_p: Nucleus sampling parameter (0.0-1.0)

        Returns:
            LLMResponse with generated text and token counts
        """
        pass

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text (simple heuristic).

        Uses: ~1.3 tokens per word on average.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        words = len(text.split())
        return max(1, int(words * 1.3))

    def calculate_cost(
        self, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """
        Calculate cost for LLM call.

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Override in subclasses with actual pricing
        return 0.0
