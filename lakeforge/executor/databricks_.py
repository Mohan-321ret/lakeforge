"""Databricks SQL executor using databricks-sql-connector."""

import time
from typing import Any, List, Dict, Optional

from lakeforge.executor.base import BaseExecutor, ExecutionResult, ExecutionStatus


class DatabricksExecutor(BaseExecutor):
    """Executor for Databricks SQL queries."""

    def __init__(
        self,
        host: str = "",
        token: str = "",
        warehouse_id: str = "default",
        max_result_rows: int = 10000,
    ):
        """Initialize Databricks executor.

        Args:
            host: Databricks host (e.g., workspace.cloud.databricks.com)
            token: Databricks API token
            warehouse_id: SQL warehouse ID
            max_result_rows: Maximum rows to return

        Raises:
            ImportError: If databricks-sql-connector is not installed.
            ValueError: If credentials are missing.
        """
        super().__init__(max_result_rows=max_result_rows)

        try:
            import databricks.sql
        except ImportError:
            raise ImportError(
                "Databricks executor requires: pip install databricks-sql-connector"
            )

        import os

        self.host = host or os.getenv("DATABRICKS_HOST", "")
        self.token = token or os.getenv("DATABRICKS_TOKEN", "")
        self.warehouse_id = warehouse_id or "default"

        if not self.host or not self.token:
            raise ValueError(
                "Databricks credentials missing. Set DATABRICKS_HOST and DATABRICKS_TOKEN."
            )

        self.connection: Any = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Databricks."""
        import databricks.sql

        try:
            self.connection = databricks.sql.connect(
                host=self.host,
                http_path=f"/sql/1.0/warehouses/{self.warehouse_id}",
                token=self.token,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Databricks: {e}")

    def _execute_impl(self, sql: str, timeout_sec: int) -> tuple:
        """Internal execution implementation."""
        start_time = time.time()
        if self.connection is None:
            self._connect()

        cursor = self.connection.cursor()
        cursor.execute(sql)

        # Fetch column names
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
        else:
            columns = []

        # Fetch results
        rows_list = cursor.fetchall()

        # Convert to dicts
        data = []
        for row in rows_list:
            row_dict = {columns[i]: row[i] for i in range(len(columns))}
            data.append(row_dict)

        duration_ms = (time.time() - start_time) * 1000
        return data, columns, duration_ms

    def execute(self, sql: str, timeout_sec: int = 30) -> ExecutionResult:
        """Execute SQL query on Databricks.

        Args:
            sql: SQL query string
            timeout_sec: Query timeout in seconds (Databricks may not enforce per-query)

        Returns:
            ExecutionResult with status and data
        """
        start_time = time.time()

        try:
            data, columns, duration_ms = self._execute_impl(sql, timeout_sec)
            # Apply row limiting
            result = self._limit_results(data, columns, duration_ms / 1000.0)
            return result

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
        """Close Databricks connection."""
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
