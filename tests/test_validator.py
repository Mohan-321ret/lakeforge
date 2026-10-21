"""Comprehensive tests for SQL validator module."""

import pytest
from lakeforge.validator import SQLValidator, SQLValidationError


class TestSQLValidatorBasics:
    """Test basic validator initialization and configuration."""

    def test_validator_initialization(self):
        """Test validator initializes with defaults."""
        validator = SQLValidator()
        assert validator.max_result_bytes == 10 * 1024 * 1024
        assert validator.query_timeout_sec == 30
        assert validator.allowed_schemas is None
        assert validator.allowed_tables is None

    def test_validator_custom_config(self):
        """Test validator initializes with custom config."""
        validator = SQLValidator(
            allowed_tables={"users", "orders"},
            max_result_bytes=5 * 1024 * 1024,
            query_timeout_sec=60,
        )
        assert validator.max_result_bytes == 5 * 1024 * 1024
        assert validator.query_timeout_sec == 60
        assert validator.allowed_tables == {"users", "orders"}


class TestSafeSQLOperations:
    """Test that safe SQL operations are accepted."""

    def test_validate_simple_select(self):
        """Test simple SELECT is valid."""
        validator = SQLValidator()
        result = validator.validate("SELECT * FROM users;")
        assert result["valid"] is True
        assert "SELECT" in result["operation_type"]
        assert len(result["errors"]) == 0

    def test_validate_select_with_where(self):
        """Test SELECT with WHERE is valid."""
        validator = SQLValidator()
        result = validator.validate("SELECT id, name FROM users WHERE id = 1;")
        assert result["valid"] is True
        assert result["operation_type"] == "SELECT"

    def test_validate_select_with_join(self):
        """Test SELECT with JOIN is valid."""
        validator = SQLValidator()
        sql = "SELECT u.id, u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id;"
        result = validator.validate(sql)
        assert result["valid"] is True
        assert "users" in result["tables"]
        assert "orders" in result["tables"]

    def test_validate_select_with_group_by(self):
        """Test SELECT with GROUP BY is valid."""
        validator = SQLValidator()
        sql = "SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id;"
        result = validator.validate(sql)
        assert result["valid"] is True
        assert result["operation_type"] == "SELECT"

    def test_validate_select_with_order_by(self):
        """Test SELECT with ORDER BY is valid."""
        validator = SQLValidator()
        sql = "SELECT * FROM users ORDER BY created_at DESC LIMIT 10;"
        result = validator.validate(sql)
        assert result["valid"] is True

    def test_validate_select_with_limit(self):
        """Test SELECT with LIMIT is valid."""
        validator = SQLValidator()
        sql = "SELECT * FROM users LIMIT 100;"
        result = validator.validate(sql)
        assert result["valid"] is True

    def test_validate_with_cte(self):
        """Test WITH (CTE) is valid."""
        validator = SQLValidator()
        sql = (
            "WITH user_stats AS ("
            "  SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id"
            ") SELECT * FROM user_stats;"
        )
        result = validator.validate(sql)
        assert result["valid"] is True
        # sqlglot parses WITH...SELECT as SELECT, which is fine
        assert result["operation_type"] in ("WITH", "SELECT")

    def test_validate_nested_select(self):
        """Test nested SELECT is valid."""
        validator = SQLValidator()
        sql = "SELECT * FROM (SELECT * FROM users WHERE id > 0) AS filtered;"
        result = validator.validate(sql)
        assert result["valid"] is True


class TestDangerousSQLOperations:
    """Test that dangerous SQL operations are rejected."""

    def test_validate_insert_rejected(self):
        """Test INSERT is rejected."""
        validator = SQLValidator()
        result = validator.validate("INSERT INTO users (name) VALUES ('John');")
        assert result["valid"] is False
        assert "INSERT" in result["operation_type"]
        assert len(result["errors"]) > 0

    def test_validate_update_rejected(self):
        """Test UPDATE is rejected."""
        validator = SQLValidator()
        result = validator.validate("UPDATE users SET name = 'Jane' WHERE id = 1;")
        assert result["valid"] is False
        assert "UPDATE" in result["operation_type"]

    def test_validate_delete_rejected(self):
        """Test DELETE is rejected."""
        validator = SQLValidator()
        result = validator.validate("DELETE FROM users WHERE id = 1;")
        assert result["valid"] is False
        assert "DELETE" in result["operation_type"]

    def test_validate_drop_rejected(self):
        """Test DROP is rejected."""
        validator = SQLValidator()
        result = validator.validate("DROP TABLE users;")
        assert result["valid"] is False
        assert "DROP" in result["operation_type"]

    def test_validate_create_rejected(self):
        """Test CREATE is rejected."""
        validator = SQLValidator()
        result = validator.validate("CREATE TABLE users (id INTEGER, name TEXT);")
        assert result["valid"] is False
        assert "CREATE" in result["operation_type"]

    def test_validate_alter_rejected(self):
        """Test ALTER is rejected."""
        validator = SQLValidator()
        result = validator.validate("ALTER TABLE users ADD COLUMN email TEXT;")
        assert result["valid"] is False
        assert "ALTER" in result["operation_type"]

    def test_validate_truncate_rejected(self):
        """Test TRUNCATE is rejected."""
        validator = SQLValidator()
        result = validator.validate("TRUNCATE TABLE users;")
        assert result["valid"] is False
        assert "TRUNCATE" in result["operation_type"]


class TestSchemaEnforcement:
    """Test schema and table allowlist enforcement."""

    def test_allowed_tables_pass(self):
        """Test query with allowed tables passes."""
        validator = SQLValidator(allowed_tables={"users", "orders"})
        result = validator.validate("SELECT * FROM users;")
        assert result["valid"] is True

    def test_disallowed_table_rejected(self):
        """Test query with disallowed table is rejected."""
        validator = SQLValidator(allowed_tables={"users", "orders"})
        result = validator.validate("SELECT * FROM payments;")
        assert result["valid"] is False
        assert any("not in the allowed tables" in err for err in result["errors"])

    def test_multiple_tables_one_disallowed(self):
        """Test JOIN where one table is disallowed."""
        validator = SQLValidator(allowed_tables={"users", "orders"})
        sql = "SELECT u.id FROM users u JOIN payments p ON u.id = p.user_id;"
        result = validator.validate(sql)
        assert result["valid"] is False

    def test_no_allowlist_allows_all(self):
        """Test that without allowlist, all tables are allowed."""
        validator = SQLValidator()  # No allowed_tables specified
        result = validator.validate("SELECT * FROM any_table;")
        # Should not have table allowlist errors
        assert not any("not in the allowed tables" in err for err in result["errors"])


class TestTableExtraction:
    """Test table name extraction from queries."""

    def test_extract_single_table(self):
        """Test extracting single table name."""
        validator = SQLValidator()
        result = validator.validate("SELECT * FROM users;")
        assert "users" in result["tables"]

    def test_extract_multiple_tables(self):
        """Test extracting multiple table names from JOIN."""
        validator = SQLValidator()
        sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id;"
        result = validator.validate(sql)
        assert "users" in result["tables"]
        assert "orders" in result["tables"]

    def test_extract_schema_qualified_table(self):
        """Test extracting schema-qualified table name."""
        validator = SQLValidator()
        sql = "SELECT * FROM public.users;"
        result = validator.validate(sql)
        # Should handle schema-qualified names
        assert len(result["tables"]) > 0

    def test_extract_subquery_tables(self):
        """Test extracting tables from subqueries."""
        validator = SQLValidator()
        sql = "SELECT * FROM (SELECT * FROM users) AS u;"
        result = validator.validate(sql)
        assert "users" in result["tables"]


class TestSemicolonInjection:
    """Test detection of semicolon injection (multiple statements)."""

    def test_single_statement_allowed(self):
        """Test single statement with semicolon is allowed."""
        validator = SQLValidator()
        result = validator.validate("SELECT * FROM users;")
        assert result["valid"] is True

    def test_multiple_statements_rejected(self):
        """Test multiple statements separated by semicolon are rejected."""
        validator = SQLValidator()
        result = validator.validate("SELECT * FROM users; DELETE FROM users;")
        assert result["valid"] is False
        assert any("multiple statements" in err for err in result["errors"])

    def test_semicolon_in_string_ignored(self):
        """Test semicolon inside string literal is ignored."""
        validator = SQLValidator()
        result = validator.validate("SELECT 'test;value' FROM users;")
        # Should not flag as injection
        assert not any("multiple statements" in err for err in result["errors"])


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_query_rejected(self):
        """Test empty query is rejected."""
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("")

    def test_too_short_query_rejected(self):
        """Test very short query is rejected."""
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("SEL")

    def test_malformed_sql_raises_error(self):
        """Test malformed SQL raises SQLValidationError."""
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("SELECT * FROM")

    def test_whitespace_only_rejected(self):
        """Test whitespace-only query is rejected."""
        validator = SQLValidator()
        with pytest.raises(SQLValidationError):
            validator.validate("   \n\t  ")

    def test_case_insensitive_operations(self):
        """Test that SQL operations are recognized case-insensitively."""
        validator = SQLValidator()
        result = validator.validate("select * from users;")
        assert result["valid"] is True
        assert result["operation_type"] == "SELECT"


class TestResultSizeEstimation:
    """Test result size estimation and checking."""

    def test_estimate_result_size(self):
        """Test result size estimation."""
        validator = SQLValidator()
        estimated = validator.estimate_result_size(
            "SELECT * FROM users;", row_count_estimate=1000, avg_row_bytes=1024
        )
        assert estimated == 1000 * 1024

    def test_estimate_with_defaults(self):
        """Test result size estimation with default values."""
        validator = SQLValidator()
        estimated = validator.estimate_result_size("SELECT * FROM users;")
        assert estimated == 1000 * 1024  # Default: 1000 rows * 1024 bytes

    def test_check_size_within_limit(self):
        """Test size check passes when within limit."""
        validator = SQLValidator(max_result_bytes=10 * 1024 * 1024)
        check = validator.check_result_size(5 * 1024 * 1024)
        assert check["exceeds_limit"] is False
        assert check["size_mb"] == 5.0

    def test_check_size_exceeds_limit(self):
        """Test size check fails when exceeding limit."""
        validator = SQLValidator(max_result_bytes=10 * 1024 * 1024)
        check = validator.check_result_size(15 * 1024 * 1024)
        assert check["exceeds_limit"] is True
        assert check["size_mb"] == 15.0

    def test_check_size_at_limit(self):
        """Test size check at exact limit."""
        validator = SQLValidator(max_result_bytes=10 * 1024 * 1024)
        check = validator.check_result_size(10 * 1024 * 1024)
        assert check["exceeds_limit"] is False


class TestTimeoutConfiguration:
    """Test timeout configuration."""

    def test_default_timeout(self):
        """Test default timeout configuration."""
        validator = SQLValidator()
        config = validator.get_timeout_config()
        assert config["timeout_sec"] == 30
        assert config["timeout_ms"] == 30000

    def test_custom_timeout(self):
        """Test custom timeout configuration."""
        validator = SQLValidator(query_timeout_sec=60)
        config = validator.get_timeout_config()
        assert config["timeout_sec"] == 60
        assert config["timeout_ms"] == 60000

    def test_short_timeout(self):
        """Test short timeout configuration."""
        validator = SQLValidator(query_timeout_sec=5)
        config = validator.get_timeout_config()
        assert config["timeout_sec"] == 5
        assert config["timeout_ms"] == 5000


class TestValidationErrorMessages:
    """Test validation error message clarity."""

    def test_error_messages_informative(self):
        """Test that error messages are informative."""
        validator = SQLValidator(allowed_tables={"users"})
        result = validator.validate("SELECT * FROM payments;")
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        # Error should mention the table name
        assert "payments" in result["errors"][0] or "payments" in str(result["errors"])

    def test_dangerous_operation_error_specific(self):
        """Test that dangerous operation errors are specific."""
        validator = SQLValidator()
        result = validator.validate("DELETE FROM users;")
        assert result["valid"] is False
        error_str = " ".join(result["errors"])
        assert "DELETE" in error_str or "not allowed" in error_str


class TestComplexQueries:
    """Test validation of complex but safe queries."""

    def test_complex_join_query(self):
        """Test complex multi-table JOIN query."""
        validator = SQLValidator()
        sql = (
            "SELECT u.id, u.name, COUNT(o.id) as order_count, AVG(o.amount) as avg_amount "
            "FROM users u "
            "LEFT JOIN orders o ON u.id = o.user_id "
            "WHERE u.created_at > '2020-01-01' "
            "GROUP BY u.id, u.name "
            "HAVING COUNT(o.id) > 5 "
            "ORDER BY order_count DESC "
            "LIMIT 100;"
        )
        result = validator.validate(sql)
        assert result["valid"] is True

    def test_complex_cte_query(self):
        """Test complex CTE query."""
        validator = SQLValidator()
        sql = (
            "WITH user_orders AS ("
            "  SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id"
            "), high_value_users AS ("
            "  SELECT user_id FROM user_orders WHERE order_count > 10"
            ") "
            "SELECT u.* FROM users u WHERE u.id IN (SELECT user_id FROM high_value_users);"
        )
        result = validator.validate(sql)
        assert result["valid"] is True

    def test_union_query(self):
        """Test UNION query."""
        validator = SQLValidator()
        sql = (
            "SELECT id, name FROM users WHERE created_at > '2020-01-01' "
            "UNION "
            "SELECT id, name FROM archived_users WHERE archived_date > '2020-01-01';"
        )
        result = validator.validate(sql)
        assert result["valid"] is True
