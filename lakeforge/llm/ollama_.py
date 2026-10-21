"""Ollama LLM client for local inference."""

import requests
from typing import Optional

from lakeforge.llm.base import BaseLLM, LLMResponse


class OllamaLLM(BaseLLM):
    """Ollama LLM client for local model inference."""

    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        base_url: str = "http://localhost:11434",
    ):
        """
        Initialize Ollama LLM client.

        Args:
            model: Model name (default: qwen2.5-coder:7b)
            base_url: Ollama server URL (default: localhost:11434)
        """
        super().__init__(model)
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"

        # Check if Ollama is running
        try:
            self._health_check()
        except Exception as e:
            raise RuntimeError(
                f"Ollama not running at {base_url}. "
                "Start Ollama with: ollama serve"
            ) from e

    def _health_check(self) -> None:
        """Check if Ollama server is running."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2,
            )
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Cannot connect to Ollama: {e}")

    def complete(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> LLMResponse:
        """
        Generate completion using local Ollama model.

        Args:
            prompt: Input prompt
            max_tokens: Max tokens in response
            temperature: Sampling temperature
            top_p: Nucleus sampling

        Returns:
            LLMResponse with generated text and token counts
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens,
                },
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=300,  # Long timeout for large models
            )
            response.raise_for_status()

            data = response.json()

            text = data.get("response", "")
            # Ollama provides token count
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            total_tokens = prompt_tokens + completion_tokens

            # No cost for local models
            cost = 0.0

            return LLMResponse(
                text=text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=self.model,
                cost=cost,
            )

        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}: {e}"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def calculate_cost(
        self, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Local models are free."""
        return 0.0
