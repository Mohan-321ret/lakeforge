"""Document merger for combining docs and detecting conflicts."""

from typing import List, Dict, Any, Tuple
from pathlib import Path

from lakeforge.docs.markdown import MarkdownIngester
from lakeforge.docs.yaml_ import YAMLIngester
from lakeforge.docs.dbt_manifest import dbtManifestIngester
from lakeforge.models import ColumnCard, GlossaryCard, RelationshipCard


class DocMerger:
    """Merge multiple doc sources and detect conflicts."""

    def __init__(self):
        """Initialize with all available ingesters."""
        self.ingesters = [
            MarkdownIngester(),
            YAMLIngester(),
            dbtManifestIngester(),
        ]

    def merge_docs(self, doc_dir: str | Path) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """
        Merge all docs from a directory.

        Args:
            doc_dir: Directory containing documentation files

        Returns:
            Tuple of (merged_cards, conflicts)
            - merged_cards: List of Card objects from all sources
            - conflicts: List of conflict dictionaries
        """
        doc_dir = Path(doc_dir)

        if not doc_dir.exists():
            return [], []

        # Collect all cards from all docs
        all_cards = []
        card_sources = {}  # card -> source file mapping

        # Process all files in directory
        for doc_file in doc_dir.iterdir():
            if doc_file.is_file():
                # Find matching ingester
                for ingester in self.ingesters:
                    if ingester.supports(doc_file):
                        try:
                            cards = ingester.ingest(doc_file)
                            for card in cards:
                                all_cards.append(card)
                                card_key = self._card_key(card)
                                if card_key not in card_sources:
                                    card_sources[card_key] = []
                                card_sources[card_key].append(str(doc_file))
                        except Exception:
                            pass
                        break

        # Detect conflicts
        conflicts = self._detect_conflicts(all_cards, card_sources)

        return all_cards, conflicts

    def _card_key(self, card: Any) -> str:
        """Generate a unique key for a card."""
        card_dict = card.to_dict()
        card_type = card_dict.get("type")

        if card_type == "column":
            return f"column:{card_dict['table_name']}.{card_dict['column_name']}"
        elif card_type == "glossary":
            return f"glossary:{card_dict['term']}"
        elif card_type == "table":
            return f"table:{card_dict['name']}"
        elif card_type == "relationship":
            return f"relationship:{card_dict['source_table']}.{card_dict['source_column']}->{card_dict['target_table']}.{card_dict['target_column']}"
        else:
            return f"{card_type}:{id(card)}"

    def _detect_conflicts(
        self, cards: List[Any], card_sources: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between cards from different sources.

        Args:
            cards: List of all cards
            card_sources: Mapping of card key to source files

        Returns:
            List of conflict dictionaries
        """
        conflicts = []

        # Group cards by key
        card_map: Dict[str, List[Any]] = {}
        for card in cards:
            key = self._card_key(card)
            if key not in card_map:
                card_map[key] = []
            card_map[key].append(card)

        # Check for conflicts
        for key, card_list in card_map.items():
            if len(card_list) < 2:
                continue

            # Check if cards have conflicting information
            card_type = card_list[0].to_dict().get("type")

            if card_type == "column":
                # Check for type mismatches
                types = set(
                    c.to_dict().get("data_type") for c in card_list
                )
                if len(types) > 1:
                    conflicts.append(
                        {
                            "type": "type_mismatch",
                            "key": key,
                            "sources": card_sources.get(key, []),
                            "values": list(types),
                        }
                    )

                # Check for nullable conflicts
                nullables = set(
                    c.to_dict().get("nullable") for c in card_list
                )
                if len(nullables) > 1:
                    conflicts.append(
                        {
                            "type": "nullable_mismatch",
                            "key": key,
                            "sources": card_sources.get(key, []),
                            "values": list(nullables),
                        }
                    )

                # Check for PII conflicts
                pii_flags = set(
                    c.to_dict().get("is_pii") for c in card_list
                )
                if len(pii_flags) > 1:
                    conflicts.append(
                        {
                            "type": "pii_flag_mismatch",
                            "key": key,
                            "sources": card_sources.get(key, []),
                            "values": list(pii_flags),
                        }
                    )

            elif card_type == "glossary":
                # Check for definition conflicts
                definitions = set(
                    c.to_dict().get("definition") for c in card_list
                )
                if len(definitions) > 1:
                    # Only flag as conflict if definitions are very different
                    defs_list = list(definitions)
                    if all(len(d) > 10 for d in defs_list):
                        conflicts.append(
                            {
                                "type": "definition_mismatch",
                                "key": key,
                                "sources": card_sources.get(key, []),
                                "count": len(definitions),
                            }
                        )

        return conflicts

    def write_conflict_report(
        self, conflicts: List[Dict[str, Any]], output_path: str | Path
    ) -> None:
        """
        Write conflicts to a report file.

        Args:
            conflicts: List of conflict dictionaries
            output_path: Path to write the report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = ["# Document Conflicts Report\n"]

        if not conflicts:
            lines.append("No conflicts detected.\n")
        else:
            for i, conflict in enumerate(conflicts, 1):
                lines.append(f"## Conflict {i}: {conflict['type']}\n")
                lines.append(f"**Key:** `{conflict['key']}`\n\n")
                lines.append(f"**Sources:**\n")
                for source in conflict.get("sources", []):
                    lines.append(f"- {source}\n")
                lines.append("\n")

                if "values" in conflict:
                    lines.append(f"**Conflicting Values:**\n")
                    for value in conflict["values"]:
                        lines.append(f"- {value}\n")
                    lines.append("\n")

                if "count" in conflict:
                    lines.append(f"**Distinct Definitions:** {conflict['count']}\n\n")

        output_path.write_text("".join(lines), encoding="utf-8")
