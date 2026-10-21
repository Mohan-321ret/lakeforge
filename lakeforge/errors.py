"""Custom exceptions and error handling for Lakeforge."""

from typing import Optional


class LakeforgeException(Exception):
    """Base exception for all Lakeforge errors."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        """Initialize exception.

        Args:
            message: Error message
            suggestion: Helpful suggestion for resolving the error
        """
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.suggestion:
            return f"{self.message}\n\n💡 Suggestion: {self.suggestion}"
        return self.message


class SourceAccessError(LakeforgeException):
    """Error accessing or validating source."""

    pass


class SourceNotFoundError(SourceAccessError):
    """Source file or URL not found."""

    pass


class InvalidSourceURIError(SourceAccessError):
    """Invalid source URI format."""

    pass


class ConnectorNotAvailableError(LakeforgeException):
    """Required connector is not installed."""

    pass


class AuthenticationError(LakeforgeException):
    """Authentication failed for remote source."""

    pass


class ValidationError(LakeforgeException):
    """Query validation failed."""

    pass


class ExecutionError(LakeforgeException):
    """Query execution failed."""

    pass


class ConfigurationError(LakeforgeException):
    """Configuration error."""

    pass


class TimeoutError(ExecutionError):
    """Query execution timed out."""

    pass


def get_error_suggestion(error: Exception) -> Optional[str]:
    """Generate helpful suggestion for common errors.

    Args:
        error: The exception

    Returns:
        Suggestion string or None
    """
    error_str = str(error).lower()

    # Table not found (check before generic "file not found")
    if "table" in error_str and ("not found" in error_str or "does not exist" in error_str):
        return (
            "The table doesn't exist in the source. "
            "Use 'SHOW TABLES' or inspect the schema first to see available tables."
        )

    # File not found
    if "no such file" in error_str or "does not exist" in error_str:
        return (
            "Make sure the file path is correct and the file exists. "
            "Use absolute paths for clarity."
        )

    # Permission denied
    if "permission denied" in error_str or "access denied" in error_str:
        return (
            "Check file permissions. Make sure you have read access to the file or database. "
            "Try running with appropriate permissions."
        )

    # Connection refused
    if "connection refused" in error_str or "could not connect" in error_str:
        return (
            "Could not connect to the remote server. "
            "Check that the host is running and accessible. "
            "Verify credentials (token, password, etc.) in environment variables."
        )

    # Authentication failed
    if "unauthorized" in error_str or "invalid token" in error_str or "authentication" in error_str:
        return (
            "Authentication failed. "
            "Check your credentials in environment variables: "
            "DATABRICKS_TOKEN, DATABRICKS_HOST, POSTGRES_CONNECTION_STRING, etc."
        )

    # SQL syntax error
    if "syntax error" in error_str or "invalid sql" in error_str:
        return (
            "There's an error in the generated SQL. "
            "Check the SQL query above and rephrase your question. "
            "Try more specific queries (e.g., 'Show me columns in users table')."
        )

    # Module/library not found
    if ("module" in error_str and "not found" in error_str) or "no module named" in error_str:
        return (
            "A required library is not installed. "
            "Install it with: pip install lakeforge[databricks] or pip install lakeforge[postgres]"
        )

    # Timeout
    if "timeout" in error_str or "timed out" in error_str:
        return (
            "The query took too long to execute. "
            "Try simplifying your query or increasing the timeout with --timeout flag."
        )

    return None
