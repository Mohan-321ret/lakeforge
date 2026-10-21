"""Tests for Phase 11: Databricks + Postgres Connectors."""

import os
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List


# ============================================================================
# DATABRICKS CONNECTOR TESTS
# ============================================================================


class TestDatabricksConnector:
    """Tests for DatabricksConnector from lakeforge.sources.databricks_sql."""

    def test_databricks_connector_uri_parsing_valid(self):
        """Test parsing valid Databricks URIs."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_TOKEN": "test_token",
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_connect.return_value = mock_connection

                from lakeforge.sources.databricks_sql import DatabricksConnector

                connector = DatabricksConnector("databricks://workspace/main/default/users")
                assert connector.catalog_name == "main"
                assert connector.schema_name == "default"
                assert connector.table_name == "users"

    def test_databricks_connector_uri_parsing_invalid(self):
        """Test parsing invalid Databricks URIs."""
        with patch.dict("os.environ", {"DATABRICKS_TOKEN": "test_token"}):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_connect.return_value = mock_connection

                from lakeforge.sources.databricks_sql import DatabricksConnector

                with pytest.raises(ValueError, match="Invalid Databricks URI"):
                    DatabricksConnector("databricks://workspace/invalid")

    def test_databricks_connector_missing_token(self):
        """Test that missing DATABRICKS_TOKEN raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            from lakeforge.sources.databricks_sql import DatabricksConnector

            with pytest.raises(ValueError, match="DATABRICKS_TOKEN"):
                DatabricksConnector("databricks://workspace/catalog/schema/table")

    def test_databricks_connector_list_tables(self):
        """Test listing tables from Databricks."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_TOKEN": "test_token",
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.fetchall.return_value = [("users",), ("orders",), ("products",)]
                mock_connection.cursor.return_value = mock_cursor

                mock_connect.return_value = mock_connection

                from lakeforge.sources.databricks_sql import DatabricksConnector

                connector = DatabricksConnector("databricks://workspace/main/default/users")
                tables = connector.list_tables()

                assert tables == ["users", "orders", "products"]

    def test_databricks_connector_get_schema(self):
        """Test getting table schema from Databricks."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_TOKEN": "test_token",
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.fetchall.return_value = [
                    ("id", "BIGINT"),
                    ("name", "STRING"),
                    ("email", "STRING"),
                ]
                mock_connection.cursor.return_value = mock_cursor

                mock_connect.return_value = mock_connection

                from lakeforge.sources.databricks_sql import DatabricksConnector

                connector = DatabricksConnector("databricks://workspace/main/default/users")
                schema = connector.get_schema("users")

                assert schema == {
                    "id": "BIGINT",
                    "name": "STRING",
                    "email": "STRING",
                }

    def test_databricks_connector_get_row_count(self):
        """Test getting row count from Databricks."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_TOKEN": "test_token",
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = (1000,)
                mock_connection.cursor.return_value = mock_cursor

                mock_connect.return_value = mock_connection

                from lakeforge.sources.databricks_sql import DatabricksConnector

                connector = DatabricksConnector("databricks://workspace/main/default/users")
                count = connector.get_row_count("users")

                assert count == 1000

    def test_databricks_connector_query(self):
        """Test querying Databricks."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_TOKEN": "test_token",
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
            },
        ):
            with patch(
                "lakeforge.sources.databricks_sql.databricks.sql.connect"
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.description = [("id",), ("name",)]
                mock_cursor.fetchall.return_value = [
                    (1, "Alice"),
                    (2, "Bob"),
                ]
                mock_connection.cursor.return_value = mock_cursor

                mock_connect.return_value = mock_connection

                from lakeforge.sources.databricks_sql import DatabricksConnector

                connector = DatabricksConnector("databricks://workspace/main/default/users")
                results = connector.query("SELECT id, name FROM users")

                assert len(results) == 2
                assert results[0] == {"id": 1, "name": "Alice"}
                assert results[1] == {"id": 2, "name": "Bob"}

    def test_databricks_connector_close(self):
        """Test closing Databricks connection."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_TOKEN": "test_token",
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
            },
        ):
            with patch(
                "lakeforge.sources.databricks_sql.databricks.sql.connect"
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_connect.return_value = mock_connection

                from lakeforge.sources.databricks_sql import DatabricksConnector

                connector = DatabricksConnector("databricks://workspace/main/default/users")
                connector.close()

                mock_connection.close.assert_called_once()


# ============================================================================
# POSTGRES CONNECTOR TESTS
# ============================================================================


class TestPostgresConnector:
    """Tests for PostgresConnector from lakeforge.sources.postgres."""

    def test_postgres_connector_uri_parsing_valid(self):
        """Test parsing valid Postgres URIs."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection
            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.postgres import PostgresConnector

            connector = PostgresConnector("postgres://user:pass@localhost:5432/mydb/myschema")
            assert connector.database == "mydb"
            assert connector.schema == "myschema"

    def test_postgres_connector_uri_parsing_minimal(self):
        """Test parsing minimal Postgres URIs."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection
            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.postgres import PostgresConnector

            connector = PostgresConnector("postgres://localhost/mydb")
            assert connector.database == "mydb"
            assert connector.schema == "public"

    def test_postgres_connector_list_tables(self):
        """Test listing tables from Postgres."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = Mock(return_value=iter([("users",), ("orders",)]))
            mock_connection.execute.return_value = mock_result
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.postgres import PostgresConnector

            connector = PostgresConnector("postgres://localhost/mydb/public")
            tables = connector.list_tables()

            assert tables == ["users", "orders"]

    def test_postgres_connector_get_schema(self):
        """Test getting table schema from Postgres."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = Mock(
                return_value=iter([
                    ("id", "integer"),
                    ("name", "character varying"),
                ])
            )
            mock_connection.execute.return_value = mock_result
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.postgres import PostgresConnector

            connector = PostgresConnector("postgres://localhost/mydb/public")
            schema = connector.get_schema("users")

            assert schema == {
                "id": "integer",
                "name": "character varying",
            }

    def test_postgres_connector_get_row_count(self):
        """Test getting row count from Postgres."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = (5000,)
            mock_connection.execute.return_value = mock_result
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.postgres import PostgresConnector

            connector = PostgresConnector("postgres://localhost/mydb/public")
            count = connector.get_row_count("users")

            assert count == 5000

    def test_postgres_connector_query(self):
        """Test querying Postgres."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.keys.return_value = ["id", "name"]
            mock_result.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
            mock_connection.execute.return_value = mock_result
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.postgres import PostgresConnector

            connector = PostgresConnector("postgres://localhost/mydb/public")
            results = connector.query("SELECT id, name FROM users")

            assert len(results) == 2
            assert results[0] == {"id": 1, "name": "Alice"}

    def test_postgres_connector_close(self):
        """Test closing Postgres connection."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.postgres import PostgresConnector

            connector = PostgresConnector("postgres://localhost/mydb/public")
            connector.close()

            mock_connection.close.assert_called_once()
            mock_engine.dispose.assert_called_once()


# ============================================================================
# DATABRICKS EXECUTOR TESTS
# ============================================================================


class TestDatabricksExecutor:
    """Tests for DatabricksExecutor from lakeforge.executor.databricks_."""

    def test_databricks_executor_init(self):
        """Test initializing DatabricksExecutor."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
                "DATABRICKS_TOKEN": "test_token",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_connect.return_value = mock_connection

                from lakeforge.executor.databricks_ import DatabricksExecutor

                executor = DatabricksExecutor()
                assert executor.host == "workspace.cloud.databricks.com"
                assert executor.token == "test_token"

    def test_databricks_executor_missing_credentials(self):
        """Test that missing credentials raise ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            from lakeforge.executor.databricks_ import DatabricksExecutor

            with pytest.raises(ValueError, match="credentials missing"):
                DatabricksExecutor()

    def test_databricks_executor_execute_success(self):
        """Test successful query execution."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
                "DATABRICKS_TOKEN": "test_token",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.description = [("id",), ("name",)]
                mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
                mock_connection.cursor.return_value = mock_cursor

                mock_connect.return_value = mock_connection

                from lakeforge.executor.databricks_ import DatabricksExecutor
                from lakeforge.executor.base import ExecutionStatus

                executor = DatabricksExecutor()
                result = executor.execute("SELECT * FROM users")

                assert result.status == ExecutionStatus.SUCCESS
                assert result.rows == 2
                assert len(result.data) == 2
                assert result.data[0] == {"id": 1, "name": "Alice"}

    def test_databricks_executor_execute_error(self):
        """Test error handling in query execution."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
                "DATABRICKS_TOKEN": "test_token",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.execute.side_effect = Exception("Table not found")
                mock_connection.cursor.return_value = mock_cursor

                mock_connect.return_value = mock_connection

                from lakeforge.executor.databricks_ import DatabricksExecutor
                from lakeforge.executor.base import ExecutionStatus

                executor = DatabricksExecutor()
                result = executor.execute("SELECT * FROM nonexistent")

                assert result.status == ExecutionStatus.ERROR
                assert "Table not found" in result.error_message

    def test_databricks_executor_result_truncation(self):
        """Test that large results are truncated."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
                "DATABRICKS_TOKEN": "test_token",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.description = [("id",)]
                mock_cursor.fetchall.return_value = [(i,) for i in range(15000)]
                mock_connection.cursor.return_value = mock_cursor

                mock_connect.return_value = mock_connection

                from lakeforge.executor.databricks_ import DatabricksExecutor
                from lakeforge.executor.base import ExecutionStatus

                executor = DatabricksExecutor(max_result_rows=10000)
                result = executor.execute("SELECT * FROM large_table")

                assert result.status == ExecutionStatus.PARTIAL
                assert result.rows == 10000
                assert result.total_rows == 15000
                assert "truncated" in result.warning

    def test_databricks_executor_context_manager(self):
        """Test using executor as context manager."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
                "DATABRICKS_TOKEN": "test_token",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_connect.return_value = mock_connection

                from lakeforge.executor.databricks_ import DatabricksExecutor

                with DatabricksExecutor() as executor:
                    assert executor is not None

                mock_connection.close.assert_called_once()


# ============================================================================
# POSTGRES EXECUTOR TESTS
# ============================================================================


class TestPostgresExecutor:
    """Tests for PostgresExecutor from lakeforge.executor.postgres."""

    def test_postgres_executor_init(self):
        """Test initializing PostgresExecutor."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            from lakeforge.executor.postgres import PostgresExecutor

            executor = PostgresExecutor("postgresql+psycopg2://localhost/mydb")
            assert executor.connection_string == "postgresql+psycopg2://localhost/mydb"

    def test_postgres_executor_missing_connection_string(self):
        """Test that missing connection string raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            from lakeforge.executor.postgres import PostgresExecutor

            with pytest.raises(ValueError, match="connection string missing"):
                PostgresExecutor()

    def test_postgres_executor_execute_success(self):
        """Test successful query execution."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.keys.return_value = ["id", "name"]
            mock_result.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
            mock_connection.execute.return_value = mock_result
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.executor.postgres import PostgresExecutor
            from lakeforge.executor.base import ExecutionStatus

            executor = PostgresExecutor("postgresql+psycopg2://localhost/mydb")
            result = executor.execute("SELECT * FROM users")

            assert result.status == ExecutionStatus.SUCCESS
            assert result.rows == 2
            assert len(result.data) == 2
            assert result.data[0] == {"id": 1, "name": "Alice"}

    def test_postgres_executor_execute_error(self):
        """Test error handling in query execution."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_connection.execute.side_effect = Exception("Syntax error")
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.executor.postgres import PostgresExecutor
            from lakeforge.executor.base import ExecutionStatus

            executor = PostgresExecutor("postgresql+psycopg2://localhost/mydb")
            result = executor.execute("SELECT * FROM nonexistent")

            assert result.status == ExecutionStatus.ERROR
            assert "Syntax error" in result.error_message

    def test_postgres_executor_result_truncation(self):
        """Test that large results are truncated."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.keys.return_value = ["id"]
            mock_result.fetchall.return_value = [(i,) for i in range(15000)]
            mock_connection.execute.return_value = mock_result
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.executor.postgres import PostgresExecutor
            from lakeforge.executor.base import ExecutionStatus

            executor = PostgresExecutor(
                "postgresql+psycopg2://localhost/mydb",
                max_result_rows=10000,
            )
            result = executor.execute("SELECT * FROM large_table")

            assert result.status == ExecutionStatus.PARTIAL
            assert result.rows == 10000
            assert result.total_rows == 15000
            assert "truncated" in result.warning

    def test_postgres_executor_context_manager(self):
        """Test using executor as context manager."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection

            mock_create_engine.return_value = mock_engine

            from lakeforge.executor.postgres import PostgresExecutor

            with PostgresExecutor("postgresql+psycopg2://localhost/mydb") as executor:
                assert executor is not None

            mock_connection.close.assert_called_once()
            mock_engine.dispose.assert_called_once()


# ============================================================================
# REGISTRY INTEGRATION TESTS
# ============================================================================


class TestSourceRegistry:
    """Tests for source registry routing."""

    def test_registry_databricks_routing(self):
        """Test that databricks:// routes to DatabricksConnector."""
        with patch.dict("os.environ", {"DATABRICKS_TOKEN": "test_token"}):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_connect.return_value = mock_connection

                from lakeforge.sources.registry import get_connector

                connector = get_connector("databricks://workspace/catalog/schema/table")
                from lakeforge.sources.databricks_sql import DatabricksConnector

                assert isinstance(connector, DatabricksConnector)

    def test_registry_postgres_routing(self):
        """Test that postgres:// routes to PostgresConnector."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection
            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.registry import get_connector

            connector = get_connector("postgres://localhost/mydb/public")
            from lakeforge.sources.postgres import PostgresConnector

            assert isinstance(connector, PostgresConnector)

    def test_registry_unknown_source(self):
        """Test that unknown source raises ValueError."""
        from lakeforge.sources.registry import get_connector

        with pytest.raises(ValueError, match="Unknown source type"):
            get_connector("unknown://example.com/data")


# ============================================================================
# INTERFACE COMPLIANCE TESTS
# ============================================================================


class TestConnectorInterface:
    """Test that connectors implement BaseConnector interface."""

    def test_databricks_connector_implements_interface(self):
        """Test that DatabricksConnector has all required methods."""
        with patch.dict("os.environ", {"DATABRICKS_TOKEN": "test_token"}):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_connect.return_value = mock_connection

                from lakeforge.sources.databricks_sql import DatabricksConnector

                connector = DatabricksConnector("databricks://workspace/catalog/schema/table")
                assert hasattr(connector, "connect")
                assert hasattr(connector, "list_tables")
                assert hasattr(connector, "get_schema")
                assert hasattr(connector, "get_row_count")
                assert hasattr(connector, "query")
                assert hasattr(connector, "close")

    def test_postgres_connector_implements_interface(self):
        """Test that PostgresConnector has all required methods."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection
            mock_create_engine.return_value = mock_engine

            from lakeforge.sources.postgres import PostgresConnector

            connector = PostgresConnector("postgres://localhost/mydb/public")
            assert hasattr(connector, "connect")
            assert hasattr(connector, "list_tables")
            assert hasattr(connector, "get_schema")
            assert hasattr(connector, "get_row_count")
            assert hasattr(connector, "query")
            assert hasattr(connector, "close")


class TestExecutorInterface:
    """Test that executors implement BaseExecutor interface."""

    def test_databricks_executor_implements_interface(self):
        """Test that DatabricksExecutor has all required methods."""
        with patch.dict(
            "os.environ",
            {
                "DATABRICKS_HOST": "workspace.cloud.databricks.com",
                "DATABRICKS_TOKEN": "test_token",
            },
        ):
            with patch(
                "databricks.sql.connect", create=True
            ) as mock_connect:
                mock_connection = MagicMock()
                mock_connect.return_value = mock_connection

                from lakeforge.executor.databricks_ import DatabricksExecutor

                executor = DatabricksExecutor()
                assert hasattr(executor, "execute")
                assert hasattr(executor, "close")
                assert hasattr(executor, "__enter__")
                assert hasattr(executor, "__exit__")

    def test_postgres_executor_implements_interface(self):
        """Test that PostgresExecutor has all required methods."""
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection
            mock_create_engine.return_value = mock_engine

            from lakeforge.executor.postgres import PostgresExecutor

            executor = PostgresExecutor("postgresql+psycopg2://localhost/mydb")
            assert hasattr(executor, "execute")
            assert hasattr(executor, "close")
            assert hasattr(executor, "__enter__")
            assert hasattr(executor, "__exit__")
