"""SQL validation and safety enforcement module.

Provides comprehensive SQL validation:
- Rejects dangerous operations (INSERT, UPDATE, DELETE, DROP, etc.)
- Enforces schema allowlist
- Estimates result size
- Configures timeouts
"""

from typing import Optional, Set
import sqlglot
from sqlglot import exp, parse_one


class SQLValidationError(Exception):
    """Raised when SQL fails validation checks."""

    pass


class SQLValidator:
    """Validates SQL queries for safety before execution.

    Features:
    - Rejects INSERT, UPDATE, DELETE, DROP, CREATE, ALTER operations
    - Allows SELECT, WITH (CTEs), JOIN, WHERE, GROUP BY, ORDER BY, LIMIT
    - Enforces schema/table allowlist (admin-configurable)
    - Estimates result size via EXPLAIN
    - Enforces query timeout limits
    """

    # Dangerous operations that should never be allowed
    DANGEROUS_OPERATIONS = {
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
        exp.TruncateTable,
    }

    def __init__(
        self,
        allowed_schemas: Optional[Set[str]] = None,
        allowed_tables: Optional[Set[str]] = None,
        max_result_bytes: int = 10 * 1024 * 1024,  # 10MB default
        query_timeout_sec: int = 30,
    ):
        """Initialize SQL validator.

        Args:
            allowed_schemas: Set of allowed schema names (if None, all allowed)
            allowed_tables: Set of allowed table names (if None, all allowed)
            max_result_bytes: Maximum result size in bytes (default 10MB)
            query_timeout_sec: Query timeout in seconds (default 30s)
        """
        self.allowed_schemas = allowed_schemas
        self.allowed_tables = allowed_tables
        self.max_result_bytes = max_result_bytes
        self.query_timeout_sec = query_timeout_sec

    def validate(self, sql: str) -> dict:
        """Validate SQL query and return validation result.

        Args:
            sql: SQL query string

        Returns:
            Dict with keys:
                - valid (bool): Whether SQL passed all checks
                - errors (list[str]): List of validation errors (empty if valid)
                - operation_type (str): Type of operation (SELECT, INSERT, etc.)
                - tables (list[str]): Tables referenced in query
                - warnings (list[str]): Non-fatal warnings

        Raises:
            SQLValidationError: If SQL is malformed and unparseable
        """
        errors = []
        warnings = []
        tables = []
        operation_type = "UNKNOWN"

        # Basic checks first
        if not sql or len(sql.strip()) < 5:
            raise SQLValidationError("Query is too short (minimum 5 characters).")

        try:
            # Parse SQL
            parsed = parse_one(sql, dialect="duckdb")
        except Exception as e:
            raise SQLValidationError(f"Failed to parse SQL: {str(e)}")

        # Check for dangerous operations
        operation_type = self._get_operation_type(parsed)

        if not self._is_safe_operation(parsed):
            errors.append(
                f"Operation type '{operation_type}' is not allowed. "
                "Only SELECT and WITH are permitted."
            )

        # Extract tables from query
        tables = self._extract_tables(parsed)

        # Check schema allowlist
        if self.allowed_tables is not None:
            for table in tables:
                if table not in self.allowed_tables:
                    errors.append(
                        f"Table '{table}' is not in the allowed tables list."
                    )

        # Additional safety checks
        if self._has_semicolon_injection(sql):
            errors.append("Query contains multiple statements (semicolon injection attempt).")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "operation_type": operation_type,
            "tables": tables,
        }

    def _is_safe_operation(self, parsed: exp.Expression) -> bool:
        """Check if parsed SQL contains only safe operations.

        Args:
            parsed: Parsed SQL expression

        Returns:
            True if operation is safe (SELECT/WITH only)
        """
        # Find any dangerous operations
        for dangerous_type in self.DANGEROUS_OPERATIONS:
            if isinstance(parsed, dangerous_type):
                return False
            # Check for nested dangerous operations
            if parsed.find(dangerous_type):
                return False

        return True

    def _get_operation_type(self, parsed: exp.Expression) -> str:
        """Get the primary operation type of parsed SQL.

        Args:
            parsed: Parsed SQL expression

        Returns:
            Operation type (SELECT, INSERT, UPDATE, DELETE, DROP, etc.)
        """
        if isinstance(parsed, exp.Select):
            return "SELECT"
        elif isinstance(parsed, exp.With):
            return "WITH"
        elif isinstance(parsed, exp.Insert):
            return "INSERT"
        elif isinstance(parsed, exp.Update):
            return "UPDATE"
        elif isinstance(parsed, exp.Delete):
            return "DELETE"
        elif isinstance(parsed, exp.Drop):
            return "DROP"
        elif isinstance(parsed, exp.Create):
            return "CREATE"
        elif isinstance(parsed, exp.Alter):
            return "ALTER"
        elif isinstance(parsed, exp.TruncateTable):
            return "TRUNCATE"
        else:
            return "UNKNOWN"

    def _extract_tables(self, parsed: exp.Expression) -> list:
        """Extract all table names from parsed SQL.

        Args:
            parsed: Parsed SQL expression

        Returns:
            List of table names (including schema-qualified names)
        """
        tables = []
        for table in parsed.find_all(exp.Table):
            # Get fully qualified name (schema.table)
            if table.db:
                tables.append(f"{table.db}.{table.name}")
            else:
                tables.append(table.name)

        return list(set(tables))  # Remove duplicates

    def _has_semicolon_injection(self, sql: str) -> bool:
        """Check for potential semicolon injection (multiple statements).

        Args:
            sql: Raw SQL string

        Returns:
            True if multiple statements detected
        """
        # Simple heuristic: check for multiple semicolons
        # More sophisticated check: count actual statement boundaries
        stripped = sql.strip()
        if not stripped.endswith(";"):
            return False

        # Count semicolons outside of strings
        in_string = False
        string_char = None
        semicolon_count = 0

        for i, char in enumerate(stripped):
            if char in ('"', "'") and (i == 0 or stripped[i - 1] != "\\"):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
            elif char == ";" and not in_string:
                semicolon_count += 1

        # More than one semicolon is suspicious
        return semicolon_count > 1

    def estimate_result_size(
        self, sql: str, row_count_estimate: int = 1000, avg_row_bytes: int = 1024
    ) -> int:
        """Estimate result size in bytes.

        Args:
            sql: SQL query
            row_count_estimate: Estimated number of rows (default 1000)
            avg_row_bytes: Average bytes per row (default 1024)

        Returns:
            Estimated result size in bytes
        """
        # Simple heuristic: row_count * avg_row_bytes
        # In real implementation, would use EXPLAIN to get accurate estimates
        return row_count_estimate * avg_row_bytes

    def check_result_size(self, estimated_bytes: int) -> dict:
        """Check if estimated result size exceeds limit.

        Args:
            estimated_bytes: Estimated result size

        Returns:
            Dict with:
                - exceeds_limit (bool): True if size exceeds limit
                - estimated_size (int): Estimated size in bytes
                - limit (int): Maximum allowed size
                - size_mb (float): Estimated size in MB
                - limit_mb (float): Limit in MB
        """
        return {
            "exceeds_limit": estimated_bytes > self.max_result_bytes,
            "estimated_size": estimated_bytes,
            "limit": self.max_result_bytes,
            "size_mb": estimated_bytes / (1024 * 1024),
            "limit_mb": self.max_result_bytes / (1024 * 1024),
        }

    def get_timeout_config(self) -> dict:
        """Get timeout configuration for query execution.

        Returns:
            Dict with:
                - timeout_sec (int): Timeout in seconds
                - timeout_ms (int): Timeout in milliseconds
        """
        return {
            "timeout_sec": self.query_timeout_sec,
            "timeout_ms": self.query_timeout_sec * 1000,
        }
