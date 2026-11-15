"""Base executor interface for query execution.

Defines the abstract interface that all query executors must implement.
Handles result normalization, error handling, and audit logging.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Dict, Optional
import time
from enum import Enum


class ExecutionStatus(str, Enum):
    """Status of query execution."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


@dataclass
class ExecutionResult:
    """Result of query execution.

    Attributes:
        status: Execution status (success, error, timeout, partial)
        data: Result data (list of dicts or None if error)
        rows: Number of rows returned
        columns: Column names in result
        duration_ms: Query execution time in milliseconds
        error_message: Error message if status is error
        warning: Warning message if truncated or timeout
        total_rows: Total rows before truncation (if applicable)
    """

    status: ExecutionStatus
    data: Optional[List[Dict[str, Any]]]
    rows: int
    columns: List[str]
    duration_ms: float
    error_message: Optional[str] = None
    warning: Optional[str] = None
    total_rows: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert result to dict for serialization."""
        return {
            "status": self.status.value,
            "data": self.data,
            "rows": self.rows,
            "columns": self.columns,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "warning": self.warning,
            "total_rows": self.total_rows,
        }


class ExecutionError(Exception):
    """Raised when query execution fails."""

    pass


class BaseExecutor(ABC):
    """Abstract base class for query executors.

    All executors must implement the execute() method and handle:
    - SQL execution against a data source
    - Timeout enforcement
    - Result normalization (to JSON-serializable dict format)
    - Error handling and recovery
    - Audit logging
    """

    def __init__(self, max_result_rows: int = 10000):
        """Initialize executor.

        Args:
            max_result_rows: Maximum rows to return in result (default 10000)
        """
        self.max_result_rows = max_result_rows

    @abstractmethod
    def execute(
        self, sql: str, timeout_sec: int = 30
    ) -> ExecutionResult:
        """Execute SQL query.

        Args:
            sql: SQL query string
            timeout_sec: Query timeout in seconds

        Returns:
            ExecutionResult with status, data, and metadata

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def _execute_impl(self, sql: str, timeout_sec: int) -> tuple:
        """Internal implementation of query execution.

        Subclasses override this to provide actual execution logic.

        Args:
            sql: SQL query string
            timeout_sec: Query timeout in seconds

        Returns:
            Tuple of (data, columns, duration_ms) where:
                - data: List of dicts (one dict per row)
                - columns: List of column names
                - duration_ms: Execution time in milliseconds

        Raises:
            ExecutionError: If execution fails
            TimeoutError: If execution exceeds timeout
        """
        raise NotImplementedError("Subclasses must implement _execute_impl()")

    def _normalize_result(self, data: Any, columns: List[str]) -> tuple:
        """Normalize result to JSON-serializable format.

        Converts various formats (DataFrame, tuples, etc.) to list of dicts.

        Args:
            data: Raw result data
            columns: Column names

        Returns:
            Tuple of (normalized_data, columns) where normalized_data is list of dicts
        """
        if isinstance(data, list):
            # Already a list, convert each row to dict if needed
            if data and isinstance(data[0], dict):
                return data, columns
            elif data and isinstance(data[0], (tuple, list)):
                return [dict(zip(columns, row)) for row in data], columns
            else:
                return data, columns
        else:
            # Try to convert to list of dicts
            raise ExecutionError(f"Cannot normalize result type: {type(data)}")

    def _handle_error(self, error: Exception, sql: str) -> ExecutionResult:
        """Handle query execution error.

        Args:
            error: Exception that occurred
            sql: SQL query that failed

        Returns:
            ExecutionResult with error status and message
        """
        error_msg = str(error)
        if isinstance(error, TimeoutError):
            status = ExecutionStatus.TIMEOUT
            error_msg = "Query execution exceeded timeout limit"
        else:
            status = ExecutionStatus.ERROR

        return ExecutionResult(
            status=status,
            data=None,
            rows=0,
            columns=[],
            duration_ms=0.0,
            error_message=error_msg,
        )

    def _limit_results(
        self, data: List[Dict], columns: List[str], duration_ms: float
    ) -> ExecutionResult:
        """Limit results and create ExecutionResult.

        Args:
            data: List of result dicts
            columns: Column names
            duration_ms: Execution duration

        Returns:
            ExecutionResult, potentially with warning if truncated
        """
        total_rows = len(data)
        warning = None
        truncated_data = data

        if total_rows > self.max_result_rows:
            warning = f"Result truncated to {self.max_result_rows} rows (total: {total_rows})"
            truncated_data = data[: self.max_result_rows]

        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            data=truncated_data,
            rows=len(truncated_data),
            columns=columns,
            duration_ms=duration_ms,
            warning=warning,
            total_rows=total_rows if total_rows > self.max_result_rows else None,
        )
