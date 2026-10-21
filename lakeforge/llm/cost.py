"""Cost tracking for LLM calls."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class CostTracker:
    """Track costs of LLM calls with budget enforcement."""

    def __init__(
        self,
        log_file: Optional[str | Path] = None,
        max_cost_per_run: Optional[float] = None,
    ):
        """
        Initialize cost tracker.

        Args:
            log_file: Path to JSONL log file
                     (default: ~/.lakeforge/qa.log.jsonl)
            max_cost_per_run: Maximum cost allowed per run (default: None = unlimited)
        """
        if log_file is None:
            log_file = Path.home() / ".lakeforge" / "qa.log.jsonl"
        else:
            log_file = Path(log_file)

        log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file
        self.max_cost_per_run = max_cost_per_run
        self.total_cost = 0.0

    def log_call(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        prompt_preview: str = "",
    ) -> None:
        """
        Log an LLM call.

        Args:
            provider: LLM provider (groq, ollama, etc.)
            model: Model name
            prompt_tokens: Input token count
            completion_tokens: Output token count
            cost: Cost in USD
            prompt_preview: First 100 chars of prompt (for debugging)

        Raises:
            RuntimeError: If cost exceeds max_cost_per_run
        """
        self.total_cost += cost

        # Check budget
        if self.max_cost_per_run and self.total_cost > self.max_cost_per_run:
            raise RuntimeError(
                f"Cost limit exceeded: ${self.total_cost:.4f} > "
                f"${self.max_cost_per_run:.4f}"
            )

        # Log to file
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": cost,
            "prompt_preview": prompt_preview[:100],
            "total_cost_so_far": self.total_cost,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_total_cost(self) -> float:
        """Get total cost for this run."""
        return self.total_cost

    def reset(self) -> None:
        """Reset total cost counter."""
        self.total_cost = 0.0

    def get_run_stats(self) -> dict:
        """Get statistics about LLM usage."""
        stats = {
            "total_cost": self.total_cost,
            "max_cost_per_run": self.max_cost_per_run,
            "budget_remaining": None,
        }

        if self.max_cost_per_run:
            stats["budget_remaining"] = (
                self.max_cost_per_run - self.total_cost
            )

        return stats
