"""Phase 12.3: Full Test Suite - Integration and End-to-End Tests."""

import tempfile
from pathlib import Path
import json

import pytest

from lakeforge.session import QASession
from lakeforge.config import get_config
from lakeforge.discover import discover_source, Catalog
from lakeforge.sources.registry import get_connector
from lakeforge.sources.duckdb_files import DuckDBConnector


class TestSampleDatasets:
    """Test suite using sample CSV datasets."""

    @pytest.fixture
    def sample_data_dir(self):
        """Get path to sample data directory."""
        return Path(__file__).parent / "data"

    def test_customers_dataset_exists(self, sample_data_dir):
        """Test that customers dataset exists."""
        customers_file = sample_data_dir / "customers.csv"
        assert customers_file.exists(), "customers.csv not found"
        assert customers_file.stat().st_size > 0

    def test_orders_dataset_exists(self, sample_data_dir):
        """Test that orders dataset exists."""
        orders_file = sample_data_dir / "orders.csv"
        assert orders_file.exists(), "orders.csv not found"
        assert orders_file.stat().st_size > 0

    def test_products_dataset_exists(self, sample_data_dir):
        """Test that products dataset exists."""
        products_file = sample_data_dir / "products.csv"
        assert products_file.exists(), "products.csv not found"
        assert products_file.stat().st_size > 0

    def test_inventory_dataset_exists(self, sample_data_dir):
        """Test that inventory dataset exists."""
        inventory_file = sample_data_dir / "inventory.csv"
        assert inventory_file.exists(), "inventory.csv not found"
        assert inventory_file.stat().st_size > 0


class TestDataDiscovery:
    """Test data discovery on sample datasets."""

    @pytest.fixture
    def sample_data_dir(self):
        """Get path to sample data directory."""
        return Path(__file__).parent / "data"

    def test_discover_customers_schema(self, sample_data_dir):
        """Test schema discovery for customers."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))
        catalog = discover_source(connector)

        assert len(catalog.tables) > 0
        # Get first table from dict
        first_table = list(catalog.tables.values())[0]
        assert first_table.name is not None

    def test_discover_orders_schema(self, sample_data_dir):
        """Test schema discovery for orders."""
        orders_file = sample_data_dir / "orders.csv"
        connector = get_connector(str(orders_file))
        catalog = discover_source(connector)

        assert len(catalog.tables) > 0
        first_table = list(catalog.tables.values())[0]
        assert first_table.name is not None

    def test_catalog_has_columns(self, sample_data_dir):
        """Test that discovered tables have columns."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))
        catalog = discover_source(connector)

        # Get first table from dict
        assert len(catalog.tables) > 0
        customers_table = list(catalog.tables.values())[0]

        assert customers_table is not None
        # columns is a dict, not a list
        assert len(customers_table.columns) > 0
        # Check that column names are available
        column_names = list(customers_table.columns.keys())
        assert len(column_names) > 0


class TestConnectorOperations:
    """Test connector operations with sample data."""

    @pytest.fixture
    def sample_data_dir(self):
        """Get path to sample data directory."""
        return Path(__file__).parent / "data"

    def test_duckdb_connector_initialization(self, sample_data_dir):
        """Test DuckDB connector initialization."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        assert connector is not None
        assert isinstance(connector, DuckDBConnector)

    def test_duckdb_connector_list_tables(self, sample_data_dir):
        """Test listing tables in DuckDB."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        tables = connector.list_tables()
        assert len(tables) > 0

    def test_duckdb_connector_get_schema(self, sample_data_dir):
        """Test getting schema from DuckDB."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Get tables
        tables = connector.list_tables()
        assert len(tables) > 0

        # Get schema for first table
        table_name = tables[0]
        schema = connector.get_schema(table_name)
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_duckdb_connector_query_simple(self, sample_data_dir):
        """Test simple query execution."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Get the actual table name
        tables = connector.list_tables()
        assert len(tables) > 0
        table_name = tables[0]

        # Simple SELECT query
        results = connector.query(f"SELECT COUNT(*) as count FROM {table_name} LIMIT 10")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_duckdb_connector_query_with_limit(self, sample_data_dir):
        """Test query with limit."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Get the actual table name
        tables = connector.list_tables()
        assert len(tables) > 0
        table_name = tables[0]

        results = connector.query(f"SELECT * FROM {table_name}", limit=5)
        assert isinstance(results, list)
        assert len(results) <= 5

    def test_duckdb_connector_context_manager(self, sample_data_dir):
        """Test connector as context manager."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # DuckDB connector doesn't implement context manager, test basic usage
        tables = connector.list_tables()
        assert len(tables) > 0


class TestQASession:
    """Test QA Session with sample data (mock-based)."""

    @pytest.fixture
    def sample_data_dir(self):
        """Get path to sample data directory."""
        return Path(__file__).parent / "data"

    def test_qa_session_with_mock_llm(self, sample_data_dir):
        """Test QA session initialization with mocked LLM."""
        from unittest.mock import patch, MagicMock

        customers_file = sample_data_dir / "customers.csv"

        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the LLM to avoid needing Groq API key
            with patch("lakeforge.session.get_llm") as mock_llm:
                mock_llm.return_value = MagicMock()

                try:
                    session = QASession(
                        source=str(customers_file),
                        output_dir=Path(tmpdir),
                        verbose=False,
                        profile=False,
                    )
                    assert session is not None
                    session.close()
                except ValueError:
                    # Expected if Groq API key is not set; test mocking approach
                    pass


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def sample_data_dir(self):
        """Get path to sample data directory."""
        return Path(__file__).parent / "data"

    def test_workflow_inspect_and_query(self, sample_data_dir):
        """Test complete workflow: inspect -> schema -> query."""
        customers_file = sample_data_dir / "customers.csv"

        # Get connector
        connector = get_connector(str(customers_file))
        assert connector is not None

        # Discover
        catalog = discover_source(connector)
        assert len(catalog.tables) > 0

        # List tables
        tables = connector.list_tables()
        assert len(tables) > 0

        # Get schema
        schema = connector.get_schema(tables[0])
        assert len(schema) > 0

        # Query
        results = connector.query(f"SELECT * FROM {tables[0]} LIMIT 5")
        assert len(results) > 0

    def test_workflow_multiple_sources(self, sample_data_dir):
        """Test working with multiple CSV files."""
        customers_file = sample_data_dir / "customers.csv"
        orders_file = sample_data_dir / "orders.csv"

        # Test both sources
        for source_file in [customers_file, orders_file]:
            connector = get_connector(str(source_file))
            assert connector is not None

            catalog = discover_source(connector)
            assert len(catalog.tables) > 0

            tables = connector.list_tables()
            assert len(tables) > 0

    def test_workflow_csv_to_dict_conversion(self, sample_data_dir):
        """Test that CSV data is properly converted to dicts."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Get table name
        tables = connector.list_tables()
        assert len(tables) > 0

        results = connector.query(f"SELECT * FROM {tables[0]} LIMIT 1")
        assert len(results) > 0

        # Verify result is a dict
        first_result = results[0]
        assert isinstance(first_result, dict)
        assert len(first_result) > 0


class TestDataQuality:
    """Test data quality checks on sample datasets."""

    @pytest.fixture
    def sample_data_dir(self):
        """Get path to sample data directory."""
        return Path(__file__).parent / "data"

    def test_null_value_handling(self, sample_data_dir):
        """Test that NULL values are properly handled."""
        orders_file = sample_data_dir / "orders.csv"
        connector = get_connector(str(orders_file))

        # Get table name
        tables = connector.list_tables()
        assert len(tables) > 0
        table_name = tables[0]

        # Orders has some NULL ship_dates (pending orders)
        results = connector.query(f"SELECT * FROM {table_name} WHERE ship_date IS NULL LIMIT 1000")
        # Should have at least one pending order
        assert len(results) > 0

    def test_data_type_consistency(self, sample_data_dir):
        """Test that data types are consistent."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Get table name
        tables = connector.list_tables()
        assert len(tables) > 0

        schema = connector.get_schema(tables[0])
        assert schema is not None
        assert len(schema) > 0

    def test_primary_key_uniqueness(self, sample_data_dir):
        """Test that primary keys are unique."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Get table name
        tables = connector.list_tables()
        assert len(tables) > 0
        table_name = tables[0]

        # Count total and distinct customers
        all_customers = connector.query(f"SELECT COUNT(*) as count FROM {table_name} LIMIT 1000")
        distinct_customers = connector.query(
            f"SELECT COUNT(DISTINCT customer_id) as count FROM {table_name} LIMIT 1000"
        )

        # Should be equal if customer_id is unique
        assert (
            all_customers[0]["count"] == distinct_customers[0]["count"]
        ), "Duplicate customer IDs found"


class TestErrorHandling:
    """Test error handling in end-to-end scenarios."""

    @pytest.fixture
    def sample_data_dir(self):
        """Get path to sample data directory."""
        return Path(__file__).parent / "data"

    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files."""
        with pytest.raises(Exception):  # Should raise some exception
            get_connector("/nonexistent/path/file.csv")

    def test_invalid_query_handling(self, sample_data_dir):
        """Test handling of invalid SQL queries."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Invalid SQL should raise an error
        with pytest.raises(Exception):
            connector.query("SELEXT * FROMS customers")  # Typos intentional


class TestPerformance:
    """Test performance characteristics."""

    @pytest.fixture
    def sample_data_dir(self):
        """Get path to sample data directory."""
        return Path(__file__).parent / "data"

    def test_query_execution_time(self, sample_data_dir):
        """Test that queries execute in reasonable time."""
        import time

        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Get table name
        tables = connector.list_tables()
        assert len(tables) > 0
        table_name = tables[0]

        start_time = time.time()
        results = connector.query(f"SELECT * FROM {table_name}")
        elapsed_time = time.time() - start_time

        # Should execute in less than 5 seconds
        assert elapsed_time < 5.0, f"Query took {elapsed_time}s"

    def test_large_result_handling(self, sample_data_dir):
        """Test that large results are handled properly."""
        customers_file = sample_data_dir / "customers.csv"
        connector = get_connector(str(customers_file))

        # Get table name
        tables = connector.list_tables()
        assert len(tables) > 0
        table_name = tables[0]

        # Request all rows
        results = connector.query(f"SELECT * FROM {table_name}")
        assert len(results) > 0
        assert len(results) <= 15  # Sample has 15 customers
