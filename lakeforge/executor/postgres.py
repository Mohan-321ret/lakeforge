"""Postgres SQL executor using SQLAlchemy."""

import time
from typing import Any, List, Dict, Optional

from lakeforge.executor.base import BaseExecutor, ExecutionResult, ExecutionStatus


class PostgresExecutor(BaseExecutor):
    """Executor for Postgres SQL queries."""

    def __init__(
        self,
        connection_string: str = "",
        max_result_rows: int = 10000,
    ):
        """Initialize Postgres executor.

        Args:
            connection_string: SQLAlchemy connection string
                             (e.g., postgresql+psycopg2://user:pass@host/db)
            max_result_rows: Maximum rows to return

        Raises:
            ImportError: If sqlalchemy or psycopg2 is not installed.
            ValueError: If connection string is missing.
        """
        super().__init__(max_result_rows=max_result_rows)

        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError(
                "Postgres executor requires: pip install sqlalchemy psycopg2-binary"
            )

        import os

        self.connection_string = connection_string or os.getenv(
            "POSTGRES_CONNECTION_STRING", ""
        )

        if not self.connection_string:
            raise ValueError(
                "Postgres connection string missing. "
                "Set connection_string or POSTGRES_CONNECTION_STRING environment variable."
            )

        from sqlalchemy import create_engine

        self.engine = create_engine(self.connection_string, echo=False)
        self.connection: Any = None

    def _get_connection(self) -> Any:
        """Get or create connection."""
        if self.connection is None:
            self.connection = self.engine.connect()
        return self.connection

    def _execute_impl(self, sql: str, timeout_sec: int) -> tuple:
        """Internal execution implementation."""
        from sqlalchemy import text
        start_time = time.time()
        connection = self._get_connection()

        # Execute query
        query_obj = text(sql)
        result = connection.execute(query_obj)

        # Fetch column names
        if result.keys():
            columns = list(result.keys())
        else:
            columns = []

        # Fetch results
        rows_list = result.fetchall()

        # Convert to dicts
        data = []
        for row in rows_list:
            row_dict = {columns[i]: row[i] for i in range(len(columns))}
            data.append(row_dict)

        duration_ms = (time.time() - start_time) * 1000
        return data, columns, duration_ms

    def execute(self, sql: str, timeout_sec: int = 30) -> ExecutionResult:
        """Execute SQL query on Postgres.

        Args:
            sql: SQL query string
            timeout_sec: Query timeout in seconds

        Returns:
            ExecutionResult with status and data
        """
        start_time = time.time()

        try:
            data, columns, duration_ms = self._execute_impl(sql, timeout_sec)
            # Apply row limiting
            result_obj = self._limit_results(data, columns, duration_ms / 1000.0)
            return result_obj

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                data=None,
                rows=0,
                columns=[],
                duration_ms=duration_ms,
                error_message=str(e),
            )

    def _limit_results(
        self, data: List[Dict[str, Any]], columns: List[str], duration_sec: float
    ) -> ExecutionResult:
        """Apply row limit to results.

        Args:
            data: List of result dicts
            columns: Column names
            duration_sec: Query duration in seconds

        Returns:
            ExecutionResult with possible truncation warning
        """
        duration_ms = duration_sec * 1000
        total_rows = len(data)

        if total_rows > self.max_result_rows:
            truncated_data = data[: self.max_result_rows]
            warning = f"Results truncated from {total_rows} to {self.max_result_rows} rows"

            return ExecutionResult(
                status=ExecutionStatus.PARTIAL,
                data=truncated_data,
                rows=len(truncated_data),
                columns=columns,
                duration_ms=duration_ms,
                warning=warning,
                total_rows=total_rows,
            )
        else:
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data=data,
                rows=total_rows,
                columns=columns,
                duration_ms=duration_ms,
            )

    def close(self) -> None:
        """Close Postgres connection."""
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

        if self.engine is not None:
            try:
                self.engine.dispose()
            except Exception:
                pass

    def __enter__(self):
        """Context manager entry."""
        self._get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
