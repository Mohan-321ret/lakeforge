"""YAML document ingester for schema definitions."""

from pathlib import Path
from typing import List, Any, Dict
import yaml

from lakeforge.docs.base import BaseDocIngester
from lakeforge.models import ColumnCard, GlossaryCard
from lakeforge.docs.sanitizer import DocSanitizer


class YAMLIngester(BaseDocIngester):
    """Ingest YAML files with schema definitions and glossary terms."""

    def supports(self, source: str | Path) -> bool:
        """Check if source is a YAML file."""
        path = Path(source)
        return path.suffix.lower() in [".yaml", ".yml"]

    def ingest(self, source: str | Path) -> List[Any]:
        """
        Ingest YAML file with schema definitions.

        Expected format:
        ```yaml
        tables:
          table_name:
            description: "Table description"
            columns:
              column_name:
                description: "Column description"
                type: "VARCHAR"
                nullable: false
                pii_type: "email"
        glossary:
          - term: "Revenue"
            definition: "Total sales amount"
        ```

        Args:
            source: Path to YAML file

        Returns:
            List of ColumnCard and GlossaryCard objects
        """
        path = Path(source)

        if not path.exists():
            return []

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            return []

        if not isinstance(data, dict):
            return []

        # Sanitize the loaded data
        data = DocSanitizer.sanitize_dict(data)

        cards = []

        # Process tables section
        tables = data.get("tables", {})
        if isinstance(tables, dict):
            for table_name, table_info in tables.items():
                if not isinstance(table_info, dict):
                    continue

                columns = table_info.get("columns", {})
                if isinstance(columns, dict):
                    for col_name, col_info in columns.items():
                        if not isinstance(col_info, dict):
                            continue

                        # Create ColumnCard from YAML
                        card = ColumnCard(
                            table_name=table_name,
                            column_name=col_name,
                            data_type=col_info.get("type", "UNKNOWN"),
                            nullable=col_info.get("nullable", True),
                            description=col_info.get("description"),
                            is_pii="pii_type" in col_info,
                            pii_type=col_info.get("pii_type"),
                        )
                        cards.append(card)

        # Process glossary section
        glossary = data.get("glossary", [])
        if isinstance(glossary, list):
            for item in glossary:
                if isinstance(item, dict):
                    term = item.get("term", "")
                    definition = item.get("definition", "")

                    if term and definition:
                        # Check for injection
                        if DocSanitizer.check_injection(definition):
                            definition = "[MALICIOUS CONTENT DETECTED - REDACTED]"

                        card = GlossaryCard(
                            term=term,
                            definition=definition,
                            source="yaml",
                        )
                        cards.append(card)

        return cards
