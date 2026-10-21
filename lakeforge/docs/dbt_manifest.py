"""dbt manifest ingester for relationships and descriptions."""

import json
from pathlib import Path
from typing import List, Any, Dict

from lakeforge.docs.base import BaseDocIngester
from lakeforge.models import GlossaryCard, RelationshipCard
from lakeforge.docs.sanitizer import DocSanitizer


class dbtManifestIngester(BaseDocIngester):
    """Ingest dbt manifest.json to extract descriptions, relationships, and tests."""

    def supports(self, source: str | Path) -> bool:
        """Check if source is a dbt manifest file."""
        path = Path(source)
        return path.name == "manifest.json"

    def ingest(self, source: str | Path) -> List[Any]:
        """
        Ingest dbt manifest.json file.

        Args:
            source: Path to manifest.json

        Returns:
            List of GlossaryCard and RelationshipCard objects
        """
        path = Path(source)

        if not path.exists():
            return []

        try:
            with open(path, encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            return []

        if not isinstance(manifest, dict):
            return []

        cards = []

        # Extract nodes (models, tests, etc.)
        nodes = manifest.get("nodes", {})
        if isinstance(nodes, dict):
            for node_id, node_info in nodes.items():
                if not isinstance(node_info, dict):
                    continue

                # Skip non-table nodes
                node_type = node_info.get("resource_type", "")
                if node_type != "model":
                    continue

                # Extract description and create glossary card
                name = node_info.get("name", "")
                description = node_info.get("description", "")

                if name and description:
                    # Sanitize description
                    description = DocSanitizer.sanitize_text(description)

                    if DocSanitizer.check_injection(description):
                        description = "[MALICIOUS CONTENT DETECTED - REDACTED]"

                    card = GlossaryCard(
                        term=name,
                        definition=description,
                        source="dbt_manifest",
                    )
                    cards.append(card)

                # Extract column descriptions
                columns = node_info.get("columns", {})
                if isinstance(columns, dict):
                    for col_name, col_info in columns.items():
                        if isinstance(col_info, dict):
                            col_desc = col_info.get("description", "")
                            if col_desc:
                                col_desc = DocSanitizer.sanitize_text(col_desc)

                                if DocSanitizer.check_injection(col_desc):
                                    col_desc = (
                                        "[MALICIOUS CONTENT DETECTED - REDACTED]"
                                    )

                                card = GlossaryCard(
                                    term=f"{name}.{col_name}",
                                    definition=col_desc,
                                    related_tables=[name],
                                    related_columns=[f"{name}.{col_name}"],
                                    source="dbt_manifest",
                                )
                                cards.append(card)

        # Extract relationships
        relations = manifest.get("child_map", {})
        parent_map = manifest.get("parent_map", {})

        if isinstance(parent_map, dict):
            for child_node, parents in parent_map.items():
                if not isinstance(parents, list):
                    continue

                # Extract table name from node ID (format: model.project.table)
                child_table = child_node.split(".")[-1] if "." in child_node else ""

                for parent_node in parents:
                    parent_table = (
                        parent_node.split(".")[-1]
                        if "." in parent_node and "model" in parent_node
                        else ""
                    )

                    if child_table and parent_table:
                        # Create relationship card
                        # Note: without explicit FK/PK info, we assume one_to_many
                        card = RelationshipCard(
                            source_table=child_table,
                            source_column="id",  # Default; dbt doesn't always have this
                            target_table=parent_table,
                            target_column="id",
                            relationship_type="one_to_many",
                            description=f"dbt dependency: {child_table} -> {parent_table}",
                        )
                        cards.append(card)

        return cards
