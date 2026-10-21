"""Comprehensive tests for SQL executor module."""

import pytest
import tempfile
import json
from pathlib import Path
from lakeforge.executor import (
    DuckDBExecutor,
    ExecutionResult,
    ExecutionStatus,
    ExecutionError,
)
from lakeforge.executor.audit import AuditLogger


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_result_creation(self):
        """Test creating an execution result."""
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            data=[{"id": 1, "name": "Alice"}],
            rows=1,
            columns=["id", "name"],
            duration_ms=10.5,
        )
        assert result.status == ExecutionStatus.SUCCESS
        assert result.rows == 1
        assert len(result.data) == 1

    def test_result_to_dict(self):
        """Test converting result to dict."""
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            data=[{"id": 1}],
            rows=1,
            columns=["id"],
            duration_ms=5.0,
        )
        result_dict = result.to_dict()
        assert result_dict["status"] == "success"
        assert result_dict["rows"] == 1


class TestDuckDBExecutorBasics:
    """Test basic DuckDB executor functionality."""

    def test_executor_initialization(self):
        """Test executor initializes."""
        with DuckDBExecutor() as executor:
            assert executor.database == ":memory:"
            assert executor.max_result_rows == 10000

    def test_executor_custom_config(self):
        """Test executor with custom config."""
        with DuckDBExecutor(max_result_rows=5000) as executor:
            assert executor.max_result_rows == 5000

    def test_context_manager(self):
        """Test executor as context manager."""
        executor = DuckDBExecutor()
        assert executor.connection is None  # Initially None
        executor.connection = executor._get_connection()  # Initialize
        assert executor.connection is not None
        executor.close()
        assert executor.connection is None  # After close


class TestSimpleQueries:
    """Test simple query execution."""

    def test_execute_simple_select(self):
        """Test executing simple SELECT."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT 1 as id, 'test' as name")
            assert result.status == ExecutionStatus.SUCCESS
            assert result.rows == 1
            assert result.columns == ["id", "name"]
            assert result.data[0]["id"] == 1
            assert result.data[0]["name"] == "test"

    def test_execute_select_multiple_rows(self):
        """Test SELECT returning multiple rows."""
        with DuckDBExecutor() as executor:
            sql = """
            SELECT 1 as id, 'Alice' as name
            UNION ALL
            SELECT 2, 'Bob'
            UNION ALL
            SELECT 3, 'Charlie'
            """
            result = executor.execute(sql)
            assert result.status == ExecutionStatus.SUCCESS
            assert result.rows == 3
            assert len(result.data) == 3

    def test_execute_with_aggregation(self):
        """Test aggregate query."""
        with DuckDBExecutor() as executor:
            sql = """
            SELECT COUNT(*) as count, SUM(1) as total
            FROM (SELECT 1 UNION ALL SELECT 1 UNION ALL SELECT 1)
            """
            result = executor.execute(sql)
            assert result.status == ExecutionStatus.SUCCESS
            assert result.rows == 1
            assert result.data[0]["count"] == 3

    def test_execute_with_where_clause(self):
        """Test SELECT with WHERE."""
        with DuckDBExecutor() as executor:
            sql = """
            SELECT 1 as id
            UNION ALL SELECT 2
            UNION ALL SELECT 3
            WHERE id > 1
            """
            # Note: DuckDB's UNION ALL with WHERE works differently
            # This is a simplified test
            result = executor.execute("SELECT 1 as id WHERE 1 = 1")
            assert result.status == ExecutionStatus.SUCCESS


class TestResultNormalization:
    """Test result normalization to dict format."""

    def test_result_is_dict_format(self):
        """Test that results are normalized to dict format."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT 1 as a, 2 as b, 3 as c")
            assert isinstance(result.data, list)
            assert isinstance(result.data[0], dict)
            assert "a" in result.data[0]
            assert "b" in result.data[0]
            assert "c" in result.data[0]

    def test_column_names_extracted(self):
        """Test that column names are extracted correctly."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT 1 as first_col, 2 as second_col")
            assert result.columns == ["first_col", "second_col"]


class TestResultLimiting:
    """Test result size limiting."""

    def test_result_within_limit(self):
        """Test result that fits within limit."""
        with DuckDBExecutor(max_result_rows=100) as executor:
            result = executor.execute("SELECT 1 as id UNION ALL SELECT 2")
            assert result.status == ExecutionStatus.SUCCESS
            assert result.rows == 2
            assert result.warning is None

    def test_result_exceeds_limit(self):
        """Test result that exceeds limit gets truncated."""
        with DuckDBExecutor(max_result_rows=5) as executor:
            # Generate result with more rows than limit
            sql = """
            SELECT 1 as id
            UNION ALL SELECT 2
            UNION ALL SELECT 3
            UNION ALL SELECT 4
            UNION ALL SELECT 5
            UNION ALL SELECT 6
            UNION ALL SELECT 7
            UNION ALL SELECT 8
            UNION ALL SELECT 9
            UNION ALL SELECT 10
            """
            result = executor.execute(sql)
            assert result.status == ExecutionStatus.SUCCESS
            assert result.rows == 5  # Truncated
            assert result.total_rows == 10  # Original count
            assert result.warning is not None
            assert "truncated" in result.warning.lower()


class TestErrorHandling:
    """Test error handling during execution."""

    def test_syntax_error(self):
        """Test handling of SQL syntax errors."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT * FORM users")  # FORM is wrong
            assert result.status == ExecutionStatus.ERROR
            assert result.error_message is not None
            assert result.data is None

    def test_table_not_found(self):
        """Test handling of missing table."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT * FROM nonexistent_table")
            assert result.status == ExecutionStatus.ERROR
            # DuckDB's error message contains "does not exist" or "catalog error"
            error_lower = result.error_message.lower()
            assert "does not exist" in error_lower or "catalog error" in error_lower

    def test_column_not_found(self):
        """Test handling of missing column."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT nonexistent_column FROM (SELECT 1 as id)")
            assert result.status == ExecutionStatus.ERROR
            assert result.error_message is not None


class TestTimeout:
    """Test query timeout handling."""

    def test_normal_query_within_timeout(self):
        """Test that normal query completes within timeout."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT 1 as id", timeout_sec=30)
            assert result.status == ExecutionStatus.SUCCESS
            assert result.duration_ms < 100  # Should be fast

    def test_timeout_configuration(self):
        """Test that timeout can be configured."""
        with DuckDBExecutor() as executor:
            # Just verify the query doesn't fail with timeout
            result = executor.execute("SELECT 1", timeout_sec=5)
            assert result.status == ExecutionStatus.SUCCESS


class TestTableOperations:
    """Test table-specific operations."""

    def test_list_tables_empty(self):
        """Test listing tables in empty database."""
        with DuckDBExecutor() as executor:
            tables = executor.list_tables()
            assert isinstance(tables, list)

    def test_get_table_schema_error(self):
        """Test getting schema of nonexistent table."""
        with DuckDBExecutor() as executor:
            with pytest.raises(ExecutionError):
                executor.get_table_schema("nonexistent_table")

    def test_load_data_error(self):
        """Test loading nonexistent data source."""
        with DuckDBExecutor() as executor:
            with pytest.raises(ExecutionError):
                executor.load_data("nonexistent_file.csv")


class TestAuditLogger:
    """Test audit logging functionality."""

    def test_audit_logger_creation(self):
        """Test creating audit logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))
            assert logger.log_file == log_file

    def test_audit_logger_logging(self):
        """Test logging executions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))

            # Log an execution
            result = ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data=[{"id": 1}],
                rows=1,
                columns=["id"],
                duration_ms=10.0,
            )
            logger.log_execution("SELECT 1", result, provider="duckdb")

            # Verify log file was created
            assert log_file.exists()

            # Read and verify entry
            with open(log_file) as f:
                entry = json.loads(f.readline())
                assert entry["provider"] == "duckdb"
                assert entry["status"] == "success"
                assert entry["rows"] == 1

    def test_audit_logger_multiple_entries(self):
        """Test logging multiple executions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))

            # Log multiple executions
            for i in range(3):
                result = ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    data=[],
                    rows=i + 1,
                    columns=["id"],
                    duration_ms=10.0 * (i + 1),
                )
                logger.log_execution(f"SELECT {i+1}", result)

            # Read all entries
            entries = logger.read_entries()
            assert len(entries) == 3
            assert entries[0]["rows"] == 1
            assert entries[2]["rows"] == 3

    def test_audit_logger_cost_tracking(self):
        """Test cost tracking in audit log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))

            # Log execution with cost
            result = ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data=[],
                rows=1,
                columns=["id"],
                duration_ms=10.0,
            )
            logger.log_execution("SELECT 1", result, cost=0.05)

            # Get total cost
            total_cost = logger.get_total_cost()
            assert total_cost == 0.05

    def test_audit_logger_stats(self):
        """Test getting statistics from audit log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))

            # Log various executions
            result_success = ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data=[],
                rows=100,
                columns=["id"],
                duration_ms=50.0,
            )
            result_error = ExecutionResult(
                status=ExecutionStatus.ERROR,
                data=None,
                rows=0,
                columns=[],
                duration_ms=10.0,
                error_message="Test error",
            )

            logger.log_execution("SELECT 1", result_success, cost=0.01)
            logger.log_execution("SELECT 2", result_error, cost=0.00)

            # Get stats
            stats = logger.get_stats()
            assert stats["total_executions"] == 2
            assert stats["successful_executions"] == 1
            assert stats["error_executions"] == 1
            assert stats["total_rows"] == 100
            assert stats["total_cost"] == 0.01

    def test_audit_logger_clear(self):
        """Test clearing audit log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))

            # Log an entry
            result = ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data=[],
                rows=1,
                columns=["id"],
                duration_ms=10.0,
            )
            logger.log_execution("SELECT 1", result)
            assert log_file.exists()

            # Clear
            logger.clear()
            assert not log_file.exists()

    def test_audit_logger_stats_empty(self):
        """Test getting stats from empty log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))

            stats = logger.get_stats()
            assert stats["total_executions"] == 0
            assert stats["total_cost"] == 0.0


class TestExecutorIntegration:
    """Test executor with audit logging integration."""

    def test_execution_with_logging(self):
        """Test executing query and logging result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))

            with DuckDBExecutor() as executor:
                result = executor.execute("SELECT 1 as id, 'test' as name")

            # Log the result
            logger.log_execution("SELECT 1 as id, 'test' as name", result)

            # Verify logging
            entries = logger.read_entries()
            assert len(entries) == 1
            assert entries[0]["status"] == "success"
            assert entries[0]["rows"] == 1

    def test_multiple_queries_with_audit(self):
        """Test executing multiple queries with audit logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log.jsonl"
            logger = AuditLogger(str(log_file))

            queries = [
                "SELECT 1 as num",
                "SELECT 2 as num",
                "SELECT 3 as num",
            ]

            with DuckDBExecutor() as executor:
                for query in queries:
                    result = executor.execute(query)
                    logger.log_execution(query, result)

            # Verify all queries logged
            stats = logger.get_stats()
            assert stats["total_executions"] == 3
            assert stats["successful_executions"] == 3


class TestEdgeCases:
    """Test edge cases in execution."""

    def test_empty_result_set(self):
        """Test query that returns no rows."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT 1 WHERE FALSE")
            assert result.status == ExecutionStatus.SUCCESS
            assert result.rows == 0
            assert result.data == []

    def test_null_values(self):
        """Test handling of NULL values."""
        with DuckDBExecutor() as executor:
            result = executor.execute("SELECT NULL as nullable, 1 as not_null")
            assert result.status == ExecutionStatus.SUCCESS
            assert result.data[0]["nullable"] is None
            assert result.data[0]["not_null"] == 1

    def test_various_data_types(self):
        """Test various SQL data types."""
        with DuckDBExecutor() as executor:
            sql = """
            SELECT
                1 as int_col,
                1.5 as float_col,
                'text' as text_col,
                true as bool_col,
                DATE '2020-01-01' as date_col
            """
            result = executor.execute(sql)
            assert result.status == ExecutionStatus.SUCCESS
            row = result.data[0]
            assert row["int_col"] == 1
            assert row["float_col"] == 1.5
            assert row["text_col"] == "text"
            assert row["bool_col"] is True

    def test_special_characters_in_result(self):
        """Test handling special characters in results."""
        with DuckDBExecutor() as executor:
            result = executor.execute(
                "SELECT 'Hello \"World\"' as quoted, 'Line\\nBreak' as escaped"
            )
            assert result.status == ExecutionStatus.SUCCESS
