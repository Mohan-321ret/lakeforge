"""LLM abstraction and factory."""

import os
from typing import Optional

from lakeforge.llm.base import BaseLLM, LLMResponse
from lakeforge.llm.cache import PromptCache
from lakeforge.llm.cost import CostTracker


def get_llm(
    provider: str = "groq",
    model: Optional[str] = None,
    cache: Optional[PromptCache] = None,
    cost_tracker: Optional[CostTracker] = None,
) -> BaseLLM:
    """
    Factory function to create an LLM client.

    Args:
        provider: Provider name - "groq" or "ollama"
        model: Model name (uses provider default if None)
        cache: Optional PromptCache for response caching
        cost_tracker: Optional CostTracker for cost logging

    Returns:
        LLM client instance

    Raises:
        ValueError: If provider not recognized
    """
    if provider == "groq":
        from lakeforge.llm.groq_ import GroqLLM

        model = model or os.getenv("GROQ_MODEL") or os.getenv("LLM_MODEL") or "openai/gpt-oss-120b"
        return GroqLLM(model=model)

    elif provider == "ollama":
        from lakeforge.llm.ollama_ import OllamaLLM

        model = model or "qwen2.5-coder:7b"
        return OllamaLLM(model=model)

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


__all__ = [
    "BaseLLM",
    "LLMResponse",
    "PromptCache",
    "CostTracker",
    "get_llm",
]
