"""Chunker for rendering catalog data into searchable cards."""

from typing import List, Dict, Any

from lakeforge.discover import Catalog
from lakeforge.models import TableCard, ColumnCard, GlossaryCard
from lakeforge.profile import L2Profile


class Chunker:
    """Convert catalog and profiles into searchable Card objects."""

    @staticmethod
    def chunk_catalog(catalog: Catalog, profile: Any = None) -> List[Any]:
        """
        Render catalog into a list of cards (TableCard, ColumnCard, etc.).

        Args:
            catalog: Catalog from discover_source()
            profile: Optional L2Profile from profile_source()

        Returns:
            List of card objects (TableCard, ColumnCard, etc.)
        """
        cards = []

        # Process each table in the catalog
        for table_name, table_metadata in catalog.tables.items():
            # Create TableCard
            columns_summary = list(table_metadata.columns.keys())
            table_card = TableCard(
                name=table_name,
                row_count=table_metadata.row_count,
                columns_summary=columns_summary,
            )
            cards.append(table_card)

            # Create ColumnCard for each column
            for col_name, col_metadata in table_metadata.columns.items():
                col_type = col_metadata.type
                col_nullable = col_metadata.nullable

                # Get stats and PII info from profile if available
                stats = {}
                is_pii = False
                pii_type = None
                sample_values = []

                if profile and table_name in profile.tables:
                    table_profile = profile.tables[table_name]
                    if col_name in table_profile.columns:
                        col_profile = table_profile.columns[col_name]
                        stats = col_profile.statistics or {}
                        is_pii = col_profile.is_pii
                        pii_type = col_profile.pii_type
                        sample_values = col_profile.sample_values[:5]  # First 5 samples

                column_card = ColumnCard(
                    table_name=table_name,
                    column_name=col_name,
                    data_type=col_type,
                    nullable=col_nullable,
                    sample_values=sample_values,
                    statistics=stats,
                    is_pii=is_pii,
                    pii_type=pii_type,
                )
                cards.append(column_card)

        return cards

    @staticmethod
    def render_cards(cards: List[Any]) -> Dict[str, str]:
        """
        Render cards into searchable text format.

        Args:
            cards: List of Card objects

        Returns:
            Dict mapping card id to rendered text
        """
        rendered = {}

        for i, card in enumerate(cards):
            card_id = f"{card.to_dict()['type']}_{i}"
            rendered[card_id] = card.render()

        return rendered

    @staticmethod
    def chunk_catalog_and_render(
        catalog: Catalog, profile: Any = None
    ) -> tuple[List[Any], Dict[str, str]]:
        """
        Chunk catalog and render cards in one call.

        Args:
            catalog: Catalog from discover_source()
            profile: Optional L2Profile from profile_source()

        Returns:
            Tuple of (cards, rendered_dict)
        """
        cards = Chunker.chunk_catalog(catalog, profile)
        rendered = Chunker.render_cards(cards)
        return cards, rendered
