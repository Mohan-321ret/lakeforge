"""Tests for Phase 12.1: Error handling and UX improvements."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lakeforge.errors import (
    LakeforgeException,
    SourceNotFoundError,
    InvalidSourceURIError,
    ConnectorNotAvailableError,
    AuthenticationError,
    ValidationError,
    ExecutionError,
    TimeoutError,
    get_error_suggestion,
)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_lakeforge_exception_basic(self):
        """Test basic exception initialization."""
        exc = LakeforgeException("Test error")
        assert exc.message == "Test error"
        assert exc.suggestion is None
        assert str(exc) == "Test error"

    def test_lakeforge_exception_with_suggestion(self):
        """Test exception with suggestion."""
        exc = LakeforgeException("Test error", "Try this instead")
        assert exc.message == "Test error"
        assert exc.suggestion == "Try this instead"
        assert "Test error" in str(exc)
        assert "Try this instead" in str(exc)
        assert "💡 Suggestion:" in str(exc)

    def test_source_not_found_error(self):
        """Test SourceNotFoundError."""
        exc = SourceNotFoundError("File not found")
        assert isinstance(exc, LakeforgeException)
        assert exc.message == "File not found"

    def test_invalid_source_uri_error(self):
        """Test InvalidSourceURIError."""
        exc = InvalidSourceURIError("Bad URI format")
        assert isinstance(exc, LakeforgeException)
        assert exc.message == "Bad URI format"

    def test_connector_not_available_error(self):
        """Test ConnectorNotAvailableError."""
        exc = ConnectorNotAvailableError("Databricks not installed")
        assert isinstance(exc, LakeforgeException)
        assert exc.message == "Databricks not installed"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError("Invalid token")
        assert isinstance(exc, LakeforgeException)
        assert exc.message == "Invalid token"

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError("Invalid SQL")
        assert isinstance(exc, LakeforgeException)
        assert exc.message == "Invalid SQL"

    def test_execution_error(self):
        """Test ExecutionError."""
        exc = ExecutionError("Query failed")
        assert isinstance(exc, LakeforgeException)
        assert exc.message == "Query failed"

    def test_timeout_error(self):
        """Test TimeoutError."""
        exc = TimeoutError("Query timeout")
        assert isinstance(exc, ExecutionError)
        assert exc.message == "Query timeout"


class TestErrorSuggestions:
    """Test error suggestion generation."""

    def test_file_not_found_suggestion(self):
        """Test suggestion for file not found."""
        error = Exception("No such file or directory")
        suggestion = get_error_suggestion(error)
        assert suggestion is not None
        assert "file path" in suggestion.lower()

    def test_permission_denied_suggestion(self):
        """Test suggestion for permission denied."""
        error = Exception("Permission denied")
        suggestion = get_error_suggestion(error)
        assert suggestion is not None
        assert "permission" in suggestion.lower()

    def test_connection_refused_suggestion(self):
        """Test suggestion for connection refused."""
        error = Exception("Connection refused to host")
        suggestion = get_error_suggestion(error)
        assert suggestion is not None
        assert "connect" in suggestion.lower()

    def test_authentication_failure_suggestion(self):
        """Test suggestion for authentication failure."""
        error = Exception("Unauthorized: Invalid token")
        suggestion = get_error_suggestion(error)
        assert suggestion is not None
        assert "authentication" in suggestion.lower() or "credentials" in suggestion.lower()

    def test_sql_syntax_error_suggestion(self):
        """Test suggestion for SQL syntax error."""
        error = Exception("Syntax error in SQL")
        suggestion = get_error_suggestion(error)
        assert suggestion is not None
        assert "sql" in suggestion.lower()

    def test_table_not_found_suggestion(self):
        """Test suggestion for table not found."""
        error = Exception("Table users does not exist")
        suggestion = get_error_suggestion(error)
        assert suggestion is not None
        assert "table" in suggestion.lower()

    def test_module_not_found_suggestion(self):
        """Test suggestion for module not found."""
        error = Exception("No module named databricks")
        suggestion = get_error_suggestion(error)
        assert suggestion is not None
        assert ("library" in suggestion.lower() or "pip install" in suggestion.lower())

    def test_timeout_suggestion(self):
        """Test suggestion for timeout."""
        error = Exception("Query execution timed out")
        suggestion = get_error_suggestion(error)
        assert suggestion is not None
        assert "timeout" in suggestion.lower() or "long" in suggestion.lower()

    def test_unknown_error_no_suggestion(self):
        """Test that unknown errors return no suggestion."""
        error = Exception("Some random error message")
        suggestion = get_error_suggestion(error)
        assert suggestion is None


class TestCLIErrorHandling:
    """Test CLI error handling functions."""

    def test_validate_source_local_file_exists(self):
        """Test validation of existing local file."""
        from lakeforge.cli import _validate_source
        import tempfile

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            fname = f.name

        try:
            result = _validate_source(fname)
            assert result["valid"] is True
            assert "accessible" in result["message"].lower()
        finally:
            Path(fname).unlink()

    def test_validate_source_local_file_not_exists(self):
        """Test validation of non-existent local file."""
        from lakeforge.cli import _validate_source

        result = _validate_source("/nonexistent/path/file.csv")
        assert result["valid"] is False
        assert "not found" in result["message"].lower()
        assert "suggestion" in result

    def test_validate_source_s3(self):
        """Test validation of S3 path."""
        from lakeforge.cli import _validate_source

        result = _validate_source("s3://my-bucket/data/file.csv")
        assert result["valid"] is True
        assert "s3" in result["message"].lower()

    def test_validate_source_databricks_valid(self):
        """Test validation of valid Databricks URI."""
        from lakeforge.cli import _validate_source

        result = _validate_source("databricks://workspace/catalog/schema/table")
        assert result["valid"] is True
        assert "databricks" in result["message"].lower()

    def test_validate_source_databricks_invalid(self):
        """Test validation of invalid Databricks URI."""
        from lakeforge.cli import _validate_source

        result = _validate_source("databricks://incomplete")
        assert result["valid"] is False
        assert "invalid" in result["message"].lower()

    def test_validate_source_postgres_valid(self):
        """Test validation of valid Postgres URI."""
        from lakeforge.cli import _validate_source

        result = _validate_source("postgres://user@localhost/mydb/public")
        assert result["valid"] is True
        assert "postgres" in result["message"].lower()

    def test_validate_source_unknown_scheme(self):
        """Test validation of unknown URI scheme."""
        from lakeforge.cli import _validate_source

        result = _validate_source("unknown://path/to/source")
        assert result["valid"] is False
        assert "unknown" in result["message"].lower()

    def test_print_error_basic(self):
        """Test error printing function."""
        from lakeforge.cli import _print_error
        from io import StringIO
        import sys

        # Capture console output
        captured_output = StringIO()
        
        # This would normally print to console, we just verify it doesn't raise
        _print_error("Test error message")

    def test_print_error_with_suggestion(self):
        """Test error printing with suggestion."""
        from lakeforge.cli import _print_error

        # Verify it doesn't raise an exception
        _print_error("Test error", "Try this fix", verbose=True)


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_exception_chain_source_not_found(self):
        """Test exception chain for source not found."""
        exc = SourceNotFoundError(
            "File not found: data.csv",
            "Check the file path exists"
        )
        assert "data.csv" in str(exc)
        assert "file path" in str(exc).lower()

    def test_exception_chain_authentication(self):
        """Test exception chain for authentication."""
        exc = AuthenticationError(
            "DATABRICKS_TOKEN env var not set",
            "Export DATABRICKS_TOKEN before running"
        )
        assert "DATABRICKS_TOKEN" in str(exc)
        assert "Export" in str(exc)

    def test_exception_chain_connector_unavailable(self):
        """Test exception chain for unavailable connector."""
        exc = ConnectorNotAvailableError(
            "databricks-sql-connector not installed",
            "Install with: pip install databricks-sql-connector"
        )
        assert "databricks-sql-connector" in str(exc)
        assert "pip install" in str(exc)


class TestValidationMessages:
    """Test validation error messages."""

    def test_validation_error_formatting(self):
        """Test validation error message formatting."""
        error_msg = "Column 'age' has invalid type: should be numeric"
        exc = ValidationError(error_msg, "Ensure all numeric columns are cast properly")
        result_str = str(exc)
        assert "age" in result_str
        assert "numeric" in result_str

    def test_execution_error_formatting(self):
        """Test execution error message formatting."""
        error_msg = "Query exceeded 30 second timeout"
        exc = ExecutionError(error_msg, "Reduce query complexity or increase timeout")
        result_str = str(exc)
        assert "exceeded" in result_str or "timeout" in result_str


class TestErrorPropagation:
    """Test error propagation through the stack."""

    def test_source_error_propagates(self):
        """Test that source errors propagate correctly."""
        error = SourceNotFoundError("test.csv not found")
        assert isinstance(error, LakeforgeException)
        with pytest.raises(SourceNotFoundError):
            raise error

    def test_connector_error_propagates(self):
        """Test that connector errors propagate correctly."""
        error = ConnectorNotAvailableError("postgres not available")
        assert isinstance(error, LakeforgeException)
        with pytest.raises(ConnectorNotAvailableError):
            raise error

    def test_execution_error_propagates(self):
        """Test that execution errors propagate correctly."""
        error = ExecutionError("query failed")
        assert isinstance(error, LakeforgeException)
        with pytest.raises(ExecutionError):
            raise error


# Summary: These tests validate Phase 12.1 error handling improvements:
# - Custom exception hierarchy for different error types
# - Helpful suggestions for common errors
# - CLI validation with detailed messages
# - Proper error propagation
