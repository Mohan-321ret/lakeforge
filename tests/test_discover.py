"""Tests for Phase 0 & 1 (Foundation + Discovery)."""

import json
import tempfile
from pathlib import Path

import pytest

from lakeforge.cli import app
from lakeforge.config import LakeforgeConfig, load_config_from_file
from lakeforge.discover import Catalog, ColumnMetadata, TableMetadata, discover_source
from lakeforge.report import write_report
from lakeforge.sources.duckdb_files import DuckDBConnector
from lakeforge.sources.registry import get_connector
from typer.testing import CliRunner

runner = CliRunner()


class TestConfig:
    """Tests for config loader."""

    def test_config_defaults(self):
        """Test config loads with defaults."""
        config = LakeforgeConfig()
        assert config.llm_provider == "groq"
        assert config.log_level == "INFO"
        assert config.max_query_timeout_sec == 30

    def test_config_model_dump(self):
        """Test config can be dumped to dict."""
        config = LakeforgeConfig()
        data = config.model_dump()
        assert isinstance(data, dict)
        assert "llm_provider" in data


class TestDuckDBConnector:
    """Tests for DuckDB connector."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV for testing."""
        csv_file = tmp_path / "sample.csv"
        csv_file.write_text(
            "id,name,email,age\n"
            "1,Alice,alice@example.com,30\n"
            "2,Bob,bob@example.com,25\n"
            "3,Charlie,charlie@example.com,35\n"
        )
        return str(csv_file)

    def test_duckdb_connect(self, sample_csv):
        """Test DuckDB connector can connect."""
        connector = DuckDBConnector(sample_csv)
        assert connector.connection is not None
        connector.close()

    def test_list_tables(self, sample_csv):
        """Test listing tables."""
        connector = DuckDBConnector(sample_csv)
        tables = connector.list_tables()
        assert len(tables) == 1
        assert tables[0].startswith("data_")
        connector.close()

    def test_get_schema(self, sample_csv):
        """Test getting schema."""
        connector = DuckDBConnector(sample_csv)
        table_name = connector.list_tables()[0]
        schema = connector.get_schema(table_name)

        assert "id" in schema
        assert "name" in schema
        assert "email" in schema
        assert "age" in schema
        connector.close()

    def test_get_row_count(self, sample_csv):
        """Test getting row count."""
        connector = DuckDBConnector(sample_csv)
        table_name = connector.list_tables()[0]
        row_count = connector.get_row_count(table_name)
        assert row_count == 3
        connector.close()

    def test_query(self, sample_csv):
        """Test executing query."""
        connector = DuckDBConnector(sample_csv)
        table_name = connector.list_tables()[0]
        results = connector.query(f"SELECT * FROM {table_name}")

        assert len(results) <= 3
        assert all(isinstance(row, dict) for row in results)
        connector.close()


class TestDiscover:
    """Tests for schema discovery."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV for testing."""
        csv_file = tmp_path / "sample.csv"
        csv_file.write_text(
            "id,name,email,age\n"
            "1,Alice,alice@example.com,30\n"
            "2,Bob,bob@example.com,25\n"
            "3,Charlie,charlie@example.com,35\n"
        )
        return str(csv_file)

    def test_discover_source(self, sample_csv):
        """Test discovering source schema."""
        connector = DuckDBConnector(sample_csv)
        catalog = discover_source(connector)

        assert catalog.source == sample_csv
        assert len(catalog.tables) == 1

        table = list(catalog.tables.values())[0]
        assert table.row_count == 3
        assert len(table.columns) == 4
        assert "id" in table.columns
        assert "name" in table.columns
        connector.close()

    def test_table_metadata_to_dict(self):
        """Test table metadata serialization."""
        schema = {"id": "INTEGER", "name": "VARCHAR"}
        table = TableMetadata("users", schema, row_count=100)

        data = table.to_dict()
        assert data["name"] == "users"
        assert data["row_count"] == 100
        assert "columns" in data

    def test_column_metadata_to_dict(self):
        """Test column metadata serialization."""
        col = ColumnMetadata("email", "VARCHAR", nullable=True)
        data = col.to_dict()

        assert data["name"] == "email"
        assert data["type"] == "VARCHAR"
        assert data["nullable"] is True

    def test_catalog_to_dict(self):
        """Test catalog serialization."""
        catalog = Catalog("s3://bucket/data.parquet")
        schema = {"id": "INTEGER", "name": "VARCHAR"}
        table = TableMetadata("users", schema, row_count=100)
        catalog.add_table(table)

        data = catalog.to_dict()
        assert data["source"] == "s3://bucket/data.parquet"
        assert "tables" in data
        assert "users" in data["tables"]


class TestReport:
    """Tests for report generation."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV for testing."""
        csv_file = tmp_path / "sample.csv"
        csv_file.write_text(
            "id,name,email,age\n"
            "1,Alice,alice@example.com,30\n"
            "2,Bob,bob@example.com,25\n"
            "3,Charlie,charlie@example.com,35\n"
        )
        return str(csv_file)

    def test_write_report(self, sample_csv, tmp_path):
        """Test writing report."""
        connector = DuckDBConnector(sample_csv)
        catalog = discover_source(connector)

        output_dir = tmp_path / "output"
        report_path = write_report(catalog, output_dir=output_dir)

        assert report_path.exists()
        assert report_path.name == "report.md"

        catalog_path = report_path.parent / "catalog.json"
        assert catalog_path.exists()

        connector.close()

    def test_report_markdown_content(self, sample_csv, tmp_path):
        """Test report markdown content."""
        connector = DuckDBConnector(sample_csv)
        catalog = discover_source(connector)

        output_dir = tmp_path / "output"
        report_path = write_report(catalog, output_dir=output_dir)

        report_content = report_path.read_text()
        assert "Lakeforge Inspection Report" in report_content
        assert "Summary" in report_content
        assert "Table Details" in report_content
        assert "id" in report_content
        assert "name" in report_content

        connector.close()

    def test_catalog_json_valid(self, sample_csv, tmp_path):
        """Test catalog JSON is valid."""
        connector = DuckDBConnector(sample_csv)
        catalog = discover_source(connector)

        output_dir = tmp_path / "output"
        report_path = write_report(catalog, output_dir=output_dir)

        catalog_path = report_path.parent / "catalog.json"
        with open(catalog_path) as f:
            data = json.load(f)

        assert "source" in data
        assert "tables" in data
        assert isinstance(data["tables"], dict)

        connector.close()


class TestConnectorRegistry:
    """Tests for connector registry."""

    def test_get_connector_local_csv(self, tmp_path):
        """Test getting connector for local CSV."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b,c\n1,2,3\n")

        connector = get_connector(str(csv_file))
        assert connector is not None
        assert isinstance(connector, DuckDBConnector)
        connector.close()

    def test_get_connector_unknown_source(self):
        """Test error on unknown source type."""
        with pytest.raises(ValueError, match="Unknown source type"):
            get_connector("unknown://source")


class TestCLI:
    """Tests for CLI commands."""

    def test_version_command(self):
        """Test --version command."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Lakeforge" in result.stdout

    def test_version_command_via_version(self):
        """Test version subcommand."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Lakeforge" in result.stdout

    def test_inspect_csv_success(self):
        """Test inspect command with valid CSV."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("id,name,age\n1,Alice,30\n2,Bob,25\n")
            f.flush()

            with tempfile.TemporaryDirectory() as tmpdir:
                result = runner.invoke(
                    app, ["inspect", f.name, "--output", tmpdir]
                )

                # Should succeed
                assert result.exit_code == 0
                assert "Report generated" in result.stdout

                # Report should exist
                report_files = list(Path(tmpdir).glob("report-*/report.md"))
                assert len(report_files) > 0

            Path(f.name).unlink()

    def test_inspect_missing_file(self):
        """Test inspect command with missing file."""
        result = runner.invoke(app, ["inspect", "/nonexistent/file.csv"])
        assert result.exit_code == 1
        assert "Error" in result.stdout or "Error" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
