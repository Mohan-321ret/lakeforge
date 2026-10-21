"""Tests for Phase 2 (Profiling + PII Masking)."""

import json
import tempfile
from pathlib import Path

import pytest

from lakeforge.discover import discover_source, profile_source
from lakeforge.pii import PIIDetector, PIIMasker, PIIMaskingMethod
from lakeforge.profile import ColumnProfile, Sampler, StatCalculator
from lakeforge.sources.duckdb_files import DuckDBConnector


class TestPIIDetector:
    """Tests for PII detection."""

    def test_detect_email(self):
        """Test email detection."""
        detector = PIIDetector()
        assert detector.detect_pii_type("alice@example.com") == "email"
        assert detector.detect_pii_type("not_an_email") is None

    def test_detect_phone(self):
        """Test phone detection."""
        detector = PIIDetector()
        assert detector.detect_pii_type("555-0101") == "phone"
        assert detector.detect_pii_type("123") is None

    def test_detect_ssn(self):
        """Test SSN detection."""
        detector = PIIDetector()
        assert detector.detect_pii_type("123-45-6789") == "ssn"
        assert detector.detect_pii_type("invalid") is None

    def test_risky_column_names(self):
        """Test risky column name detection."""
        detector = PIIDetector()
        assert detector.is_column_risky_by_name("email") is True
        assert detector.is_column_risky_by_name("phone") is True
        assert detector.is_column_risky_by_name("ssn") is True
        assert detector.is_column_risky_by_name("customer_id") is False

    def test_analyze_column_with_risky_name(self):
        """Test column analysis with risky name."""
        detector = PIIDetector()
        is_pii, pii_type, confidence = detector.analyze_column(
            "email", ["alice@example.com", "bob@example.com"]
        )
        assert is_pii is True
        assert confidence >= 0.5

    def test_analyze_column_with_pii_values(self):
        """Test column analysis with PII values."""
        detector = PIIDetector()
        is_pii, pii_type, confidence = detector.analyze_column(
            "contact", ["555-0101", "555-0102", "555-0103"]
        )
        assert is_pii is True
        assert pii_type == "phone"


class TestPIIMasker:
    """Tests for PII masking."""

    def test_mask_with_hash(self):
        """Test hashing masking."""
        masker = PIIMasker(PIIMaskingMethod.HASH)
        masked = masker.mask_value("alice@example.com")
        assert "***" in masked
        assert "alice" not in masked

    def test_mask_with_redact(self):
        """Test redaction masking."""
        masker = PIIMasker(PIIMaskingMethod.REDACT)
        masked = masker.mask_value("alice@example.com", "email")
        assert "REDACTED" in masked or "alice" not in masked

    def test_mask_row(self):
        """Test masking a row."""
        masker = PIIMasker()
        row = {"id": 1, "email": "alice@example.com", "name": "Alice"}
        pii_columns = {"email": "email"}

        masked_row = masker.mask_row(row, pii_columns)

        assert masked_row["id"] == 1
        assert masked_row["name"] == "Alice"
        assert "alice" not in str(masked_row["email"]).lower()

    def test_mask_none_value(self):
        """Test masking None values."""
        masker = PIIMasker()
        masked = masker.mask_value(None)
        assert masked is None

    def test_mask_empty_string(self):
        """Test masking empty strings."""
        masker = PIIMasker()
        masked = masker.mask_value("")
        assert masked == ""


class TestSampler:
    """Tests for row sampling."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV with more rows."""
        csv_file = tmp_path / "large_sample.csv"
        lines = ["id,name,email\n"]
        for i in range(100):
            lines.append(f"{i},User{i},user{i}@example.com\n")
        csv_file.write_text("".join(lines))
        return str(csv_file)

    def test_sampler_respects_max_rows(self, sample_csv):
        """Test sampler respects max_rows limit."""
        sampler = Sampler(max_rows=10)
        connector = DuckDBConnector(sample_csv)
        table_name = connector.list_tables()[0]

        samples = sampler.sample_from_connector(connector, table_name)
        assert len(samples) <= 10
        connector.close()

    def test_sampler_returns_dicts(self, sample_csv):
        """Test sampler returns rows as dicts."""
        sampler = Sampler(max_rows=5)
        connector = DuckDBConnector(sample_csv)
        table_name = connector.list_tables()[0]

        samples = sampler.sample_from_connector(connector, table_name)
        assert all(isinstance(row, dict) for row in samples)
        connector.close()


class TestStatCalculator:
    """Tests for statistics calculation."""

    def test_calculate_null_rate(self):
        """Test null rate calculation."""
        calculator = StatCalculator()
        values = [1, 2, None, 4, None]

        stats = calculator.calculate_column_stats("col", "INTEGER", values)
        assert stats["null_count"] == 2
        assert stats["null_rate"] == 0.4

    def test_calculate_unique_count(self):
        """Test unique count calculation."""
        calculator = StatCalculator()
        values = [1, 2, 2, 3, 3, 3]

        stats = calculator.calculate_column_stats("col", "INTEGER", values)
        assert stats["unique_count"] == 3

    def test_calculate_min_max(self):
        """Test min/max calculation for numeric."""
        calculator = StatCalculator()
        values = [10, 20, 30, 40, 50]

        stats = calculator.calculate_column_stats("col", "INTEGER", values)
        assert stats["min_value"] == "10"
        assert stats["max_value"] == "50"

    def test_calculate_top_values(self):
        """Test top values calculation."""
        calculator = StatCalculator()
        values = ["a", "a", "a", "b", "b", "c"]

        stats = calculator.calculate_column_stats("col", "VARCHAR", values)
        assert len(stats["top_values"]) > 0
        assert stats["top_values"][0]["value"] == "a"
        assert stats["top_values"][0]["count"] == 3

    def test_empty_values(self):
        """Test with empty values."""
        calculator = StatCalculator()
        values = [None, None, None]

        stats = calculator.calculate_column_stats("col", "VARCHAR", values)
        assert stats["null_rate"] == 1.0
        assert stats["unique_count"] == 0


class TestColumnProfile:
    """Tests for column profiling."""

    def test_column_profile_basic(self):
        """Test basic column profile."""
        values = ["alice@example.com", "bob@example.com", "charlie@example.com"]
        profile = ColumnProfile("email", "VARCHAR", True, values)

        assert profile.is_pii is True
        assert profile.pii_type is None  # Detected by name
        assert profile.stats["unique_count"] == 3

    def test_column_profile_with_nulls(self):
        """Test column profile with nulls."""
        values = [1, 2, None, None, 5]
        profile = ColumnProfile("value", "INTEGER", True, values)

        assert profile.stats["null_count"] == 2
        assert profile.stats["null_rate"] == 0.4

    def test_column_profile_to_dict(self):
        """Test column profile serialization."""
        values = ["value1", "value2"]
        profile = ColumnProfile("col", "VARCHAR", True, values)

        data = profile.to_dict()
        assert data["name"] == "col"
        assert data["type"] == "VARCHAR"
        assert "stats" in data


class TestL2Profile:
    """Tests for L2 profiling end-to-end."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV with PII."""
        csv_file = tmp_path / "pii_sample.csv"
        csv_file.write_text(
            "customer_id,name,email,phone,age\n"
            "1,Alice,alice@example.com,555-0101,30\n"
            "2,Bob,bob@example.com,555-0102,25\n"
            "3,Charlie,,555-0103,35\n"
        )
        return str(csv_file)

    def test_profile_source_integration(self, sample_csv):
        """Test end-to-end profiling."""
        connector = DuckDBConnector(sample_csv)
        from lakeforge.discover import discover_source

        catalog = discover_source(connector)
        profile = profile_source(connector, catalog)

        assert len(profile.tables) == 1
        table_profile = list(profile.tables.values())[0]

        assert len(table_profile.pii_columns) > 0
        assert "email" in table_profile.pii_columns
        assert "phone" in table_profile.pii_columns

        connector.close()

    def test_profile_detects_pii_columns(self, sample_csv):
        """Test PII column detection."""
        connector = DuckDBConnector(sample_csv)
        from lakeforge.discover import discover_source

        catalog = discover_source(connector)
        profile = profile_source(connector, catalog)

        table_profile = list(profile.tables.values())[0]
        assert "email" in table_profile.pii_columns
        assert "phone" in table_profile.pii_columns

        connector.close()

    def test_profile_to_dict(self, sample_csv):
        """Test profile serialization."""
        connector = DuckDBConnector(sample_csv)
        from lakeforge.discover import discover_source

        catalog = discover_source(connector)
        profile = profile_source(connector, catalog)

        data = profile.to_dict()
        assert "source" in data
        assert "tables" in data

        connector.close()


class TestMaskedSamples:
    """Tests for masked sample output."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV with PII."""
        csv_file = tmp_path / "masked_sample.csv"
        csv_file.write_text(
            "id,email,name\n"
            "1,alice@example.com,Alice\n"
            "2,bob@example.com,Bob\n"
        )
        return str(csv_file)

    def test_write_masked_samples(self, sample_csv, tmp_path):
        """Test writing masked samples."""
        from lakeforge.discover import discover_source
        from lakeforge.report import write_report

        connector = DuckDBConnector(sample_csv)
        catalog = discover_source(connector)
        profile = profile_source(connector, catalog)

        output_dir = tmp_path / "output"
        report_path = write_report(catalog, profile=profile, output_dir=output_dir)

        # Check samples exist
        samples_dir = report_path.parent / "samples"
        assert samples_dir.exists()

        # Check sample files exist
        sample_files = list(samples_dir.glob("*.json"))
        assert len(sample_files) > 0

        # Load and check samples are masked
        sample_file = sample_files[0]
        with open(sample_file) as f:
            samples = json.load(f)

        assert len(samples) > 0
        # Email should be masked
        if "email" in samples[0]:
            assert "alice" not in str(samples[0]["email"]).lower()

        connector.close()

    def test_masked_samples_preserve_non_pii(self, sample_csv, tmp_path):
        """Test that non-PII data is preserved in masked samples."""
        from lakeforge.discover import discover_source
        from lakeforge.report import write_report

        connector = DuckDBConnector(sample_csv)
        catalog = discover_source(connector)
        profile = profile_source(connector, catalog)

        output_dir = tmp_path / "output"
        report_path = write_report(catalog, profile=profile, output_dir=output_dir)

        samples_dir = report_path.parent / "samples"
        sample_file = list(samples_dir.glob("*.json"))[0]

        with open(sample_file) as f:
            samples = json.load(f)

        # Name should not be masked
        assert samples[0]["name"] in ["Alice", "Bob"]

        connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
