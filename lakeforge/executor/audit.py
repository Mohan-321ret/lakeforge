"""Audit logging for SQL execution.

Logs all SQL executions to a JSON Lines file for audit trail,
cost tracking, and performance analysis.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dataclasses import asdict
from lakeforge.executor.base import ExecutionResult


class AuditLogger:
    """Log SQL executions to audit trail.

    Features:
    - JSON Lines format (one execution per line)
    - Timestamp, SQL, provider, result metrics
    - Cost tracking (if applicable)
    - Append-only (immutable audit trail)
    """

    def __init__(self, log_file: Optional[str] = None):
        """Initialize audit logger.

        Args:
            log_file: Path to audit log file (default ~/.lakeforge/audit.log.jsonl)
        """
        if log_file is None:
            home = Path.home()
            log_file = home / ".lakeforge" / "audit.log.jsonl"

        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_execution(
        self,
        sql: str,
        result: ExecutionResult,
        provider: str = "duckdb",
        model: Optional[str] = None,
        cost: float = 0.0,
        prompt_preview: Optional[str] = None,
    ) -> None:
        """Log a SQL execution.

        Args:
            sql: SQL query that was executed
            result: ExecutionResult from execution
            provider: Data provider/executor name
            model: LLM model used to generate SQL (if applicable)
            cost: Cost of execution (in dollars)
            prompt_preview: Preview of the prompt used (for LLM)
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "sql": sql[:500],  # Truncate very long SQL
            "status": result.status.value,
            "rows": result.rows,
            "total_rows": result.total_rows,
            "columns": result.columns,
            "duration_ms": result.duration_ms,
            "error_message": result.error_message,
            "warning": result.warning,
            "model": model,
            "cost": cost,
            "prompt_preview": prompt_preview,
        }

        # Write to file (append mode)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_total_cost(self) -> float:
        """Get total cost of all logged executions.

        Returns:
            Total cost in dollars
        """
        if not self.log_file.exists():
            return 0.0

        total = 0.0
        with open(self.log_file) as f:
            for line in f:
                entry = json.loads(line)
                if "cost" in entry:
                    total += entry["cost"]

        return total

    def get_stats(self) -> dict:
        """Get statistics from audit log.

        Returns:
            Dict with execution stats (count, total rows, total cost, etc.)
        """
        if not self.log_file.exists():
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_rows": 0,
                "total_cost": 0.0,
                "total_duration_ms": 0.0,
                "providers": {},
            }

        stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "error_executions": 0,
            "timeout_executions": 0,
            "total_rows": 0,
            "total_cost": 0.0,
            "total_duration_ms": 0.0,
            "providers": {},
        }

        with open(self.log_file) as f:
            for line in f:
                entry = json.loads(line)
                stats["total_executions"] += 1

                # Status counts
                status = entry.get("status")
                if status == "success":
                    stats["successful_executions"] += 1
                elif status == "error":
                    stats["error_executions"] += 1
                elif status == "timeout":
                    stats["timeout_executions"] += 1

                # Row counts
                if entry.get("rows"):
                    stats["total_rows"] += entry["rows"]

                # Cost
                if entry.get("cost"):
                    stats["total_cost"] += entry["cost"]

                # Duration
                if entry.get("duration_ms"):
                    stats["total_duration_ms"] += entry["duration_ms"]

                # Provider breakdown
                provider = entry.get("provider", "unknown")
                if provider not in stats["providers"]:
                    stats["providers"][provider] = {
                        "count": 0,
                        "cost": 0.0,
                        "rows": 0,
                    }
                stats["providers"][provider]["count"] += 1
                if entry.get("cost"):
                    stats["providers"][provider]["cost"] += entry["cost"]
                if entry.get("rows"):
                    stats["providers"][provider]["rows"] += entry["rows"]

        return stats

    def clear(self) -> None:
        """Clear audit log file."""
        if self.log_file.exists():
            self.log_file.unlink()

    def read_entries(self, limit: Optional[int] = None) -> list:
        """Read audit log entries.

        Args:
            limit: Maximum number of entries to read (default: all)

        Returns:
            List of audit log entries (dicts)
        """
        if not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file) as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                entries.append(json.loads(line))

        return entries
