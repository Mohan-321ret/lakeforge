"""SQL Executor module.

Provides query execution against various data sources with
result normalization, timeout handling, and audit logging.
"""

from lakeforge.executor.base import (
    BaseExecutor,
    ExecutionResult,
    ExecutionStatus,
    ExecutionError,
)
from lakeforge.executor.duckdb_ import DuckDBExecutor
from lakeforge.executor.audit import AuditLogger

__all__ = [
    "BaseExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    "ExecutionError",
    "DuckDBExecutor",
    "AuditLogger",
]
