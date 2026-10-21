"""Tests for Phase 3: Retrieval cards and search."""

import pytest
from lakeforge.models import TableCard, ColumnCard, GlossaryCard, RelationshipCard
from lakeforge.chunker import Chunker
from lakeforge.retriever.base import BaseRetriever
from lakeforge.retriever.dict_ import DictRetriever
from lakeforge.discover import Catalog, TableMetadata, ColumnMetadata
from lakeforge.profile import L2Profile, ColumnProfile


class TestTableCard:
    """Test TableCard model."""

    def test_table_card_basic(self):
        """Test basic TableCard creation."""
        card = TableCard(name="customers", row_count=1000)
        assert card.name == "customers"
        assert card.row_count == 1000
        assert card.description is None
        assert card.columns_summary == []

    def test_table_card_with_columns(self):
        """Test TableCard with column summary."""
        card = TableCard(
            name="orders",
            row_count=5000,
            columns_summary=["order_id", "customer_id", "amount"],
        )
        assert len(card.columns_summary) == 3
        assert "customer_id" in card.columns_summary

    def test_table_card_to_dict(self):
        """Test TableCard serialization."""
        card = TableCard(name="users", row_count=100)
        card_dict = card.to_dict()
        assert card_dict["type"] == "table"
        assert card_dict["name"] == "users"
        assert card_dict["row_count"] == 100

    def test_table_card_render(self):
        """Test TableCard rendering to text."""
        card = TableCard(
            name="products",
            row_count=500,
            description="Product catalog",
            columns_summary=["product_id", "name", "price"],
        )
        text = card.render()
        assert "Table: products" in text
        assert "Rows: 500" in text
        assert "Description: Product catalog" in text
        assert "product_id" in text


class TestColumnCard:
    """Test ColumnCard model."""

    def test_column_card_basic(self):
        """Test basic ColumnCard creation."""
        card = ColumnCard(
            table_name="customers", column_name="email", data_type="VARCHAR"
        )
        assert card.table_name == "customers"
        assert card.column_name == "email"
        assert card.data_type == "VARCHAR"
        assert card.is_pii is False

    def test_column_card_with_pii(self):
        """Test ColumnCard with PII detection."""
        card = ColumnCard(
            table_name="users",
            column_name="email",
            data_type="VARCHAR",
            is_pii=True,
            pii_type="email",
        )
        assert card.is_pii is True
        assert card.pii_type == "email"

    def test_column_card_with_stats(self):
        """Test ColumnCard with statistics."""
        stats = {
            "null_rate": 0.1,
            "unique_count": 950,
            "min_value": "2023-01-01",
            "max_value": "2024-01-01",
        }
        card = ColumnCard(
            table_name="events",
            column_name="timestamp",
            data_type="DATE",
            statistics=stats,
        )
        assert card.statistics == stats
        assert card.statistics["null_rate"] == 0.1

    def test_column_card_to_dict(self):
        """Test ColumnCard serialization."""
        card = ColumnCard(
            table_name="orders",
            column_name="total",
            data_type="FLOAT",
            is_pii=False,
        )
        card_dict = card.to_dict()
        assert card_dict["type"] == "column"
        assert card_dict["table_name"] == "orders"
        assert card_dict["column_name"] == "total"

    def test_column_card_render(self):
        """Test ColumnCard rendering."""
        card = ColumnCard(
            table_name="users",
            column_name="phone",
            data_type="VARCHAR",
            is_pii=True,
            pii_type="phone",
            statistics={"unique_count": 100},
        )
        text = card.render()
        assert "Column: users.phone" in text
        assert "Type: VARCHAR" in text
        assert "Contains: phone" in text


class TestGlossaryCard:
    """Test GlossaryCard model."""

    def test_glossary_card_basic(self):
        """Test basic GlossaryCard creation."""
        card = GlossaryCard(
            term="customer_id",
            definition="Unique identifier for a customer",
        )
        assert card.term == "customer_id"
        assert "Unique identifier" in card.definition

    def test_glossary_card_with_relations(self):
        """Test GlossaryCard with related tables and columns."""
        card = GlossaryCard(
            term="order_id",
            definition="Unique identifier for an order",
            related_tables=["orders", "order_items"],
            related_columns=["orders.order_id", "order_items.order_id"],
        )
        assert len(card.related_tables) == 2
        assert "orders.order_id" in card.related_columns

    def test_glossary_card_to_dict(self):
        """Test GlossaryCard serialization."""
        card = GlossaryCard(
            term="revenue",
            definition="Total amount of sales",
            source="data_dictionary",
        )
        card_dict = card.to_dict()
        assert card_dict["type"] == "glossary"
        assert card_dict["term"] == "revenue"


class TestRelationshipCard:
    """Test RelationshipCard model."""

    def test_relationship_card_basic(self):
        """Test basic RelationshipCard creation."""
        card = RelationshipCard(
            source_table="orders",
            source_column="customer_id",
            target_table="customers",
            target_column="customer_id",
        )
        assert card.source_table == "orders"
        assert card.target_table == "customers"
        assert card.relationship_type == "one_to_many"

    def test_relationship_card_to_dict(self):
        """Test RelationshipCard serialization."""
        card = RelationshipCard(
            source_table="order_items",
            source_column="order_id",
            target_table="orders",
            target_column="order_id",
            relationship_type="many_to_one",
        )
        card_dict = card.to_dict()
        assert card_dict["type"] == "relationship"
        assert card_dict["relationship_type"] == "many_to_one"


class TestChunker:
    """Test Chunker for rendering catalog into cards."""

    @pytest.fixture
    def sample_catalog(self):
        """Create a sample catalog for testing."""
        catalog = Catalog(source="test://source")

        # Add a table with columns
        columns = {
            "user_id": ColumnMetadata(
                name="user_id",
                type="BIGINT",
                nullable=False,
                ordinal_position=1,
            ),
            "email": ColumnMetadata(
                name="email",
                type="VARCHAR",
                nullable=True,
                ordinal_position=2,
            ),
            "name": ColumnMetadata(
                name="name",
                type="VARCHAR",
                nullable=True,
                ordinal_position=3,
            ),
        }

        table = TableMetadata(
            name="users", schema={}, row_count=100
        )
        # Add columns directly
        table.columns = columns
        catalog.add_table(table)

        return catalog

    def test_chunk_catalog_creates_table_card(self, sample_catalog):
        """Test that chunking creates a TableCard."""
        cards = Chunker.chunk_catalog(sample_catalog)
        table_cards = [c for c in cards if c.to_dict()["type"] == "table"]
        assert len(table_cards) == 1
        assert table_cards[0].name == "users"
        assert table_cards[0].row_count == 100

    def test_chunk_catalog_creates_column_cards(self, sample_catalog):
        """Test that chunking creates ColumnCards for each column."""
        cards = Chunker.chunk_catalog(sample_catalog)
        column_cards = [c for c in cards if c.to_dict()["type"] == "column"]
        assert len(column_cards) == 3
        assert any(c.column_name == "email" for c in column_cards)

    def test_render_cards(self, sample_catalog):
        """Test rendering cards to text."""
        cards = Chunker.chunk_catalog(sample_catalog)
        rendered = Chunker.render_cards(cards)
        assert len(rendered) == 4  # 1 table + 3 columns
        assert all(isinstance(v, str) for v in rendered.values())

    def test_chunk_and_render(self, sample_catalog):
        """Test chunk_catalog_and_render convenience method."""
        cards, rendered = Chunker.chunk_catalog_and_render(sample_catalog)
        assert len(cards) == 4
        assert len(rendered) == 4


class TestDictRetriever:
    """Test DictRetriever implementation."""

    @pytest.fixture
    def retriever_with_cards(self):
        """Create a retriever with indexed cards."""
        retriever = DictRetriever()

        cards = [
            TableCard(name="customers", row_count=1000),
            ColumnCard(
                table_name="customers",
                column_name="email",
                data_type="VARCHAR",
                is_pii=True,
                pii_type="email",
            ),
            ColumnCard(
                table_name="customers",
                column_name="age",
                data_type="INT",
                is_pii=False,
            ),
            TableCard(name="orders", row_count=5000),
            ColumnCard(
                table_name="orders",
                column_name="customer_id",
                data_type="BIGINT",
                is_pii=False,
            ),
        ]

        rendered = {f"card_{i}": card.render() for i, card in enumerate(cards)}
        retriever.index(cards, rendered)

        return retriever

    def test_dict_retriever_indexing(self, retriever_with_cards):
        """Test that retriever indexes cards correctly."""
        assert len(retriever_with_cards.cards) == 5
        assert len(retriever_with_cards.rendered) == 5

    def test_search_exact_match(self, retriever_with_cards):
        """Test exact string matching."""
        results = retriever_with_cards.search("customers", top_k=5)
        assert len(results) > 0
        # Scores should be sorted descending
        if len(results) > 1:
            assert results[0][1] >= results[-1][1]

    def test_search_returns_top_k(self, retriever_with_cards):
        """Test that search returns at most top_k results."""
        results = retriever_with_cards.search("", top_k=2)
        # Empty query should return empty or limited results
        assert len(results) <= 2

    def test_search_by_table(self, retriever_with_cards):
        """Test searching by table name."""
        results = retriever_with_cards.search_by_table("customers")
        assert len(results) == 3  # 1 table + 2 columns
        assert any(
            c.to_dict()["type"] == "table"
            for _, c in results
        )

    def test_search_by_column(self, retriever_with_cards):
        """Test searching for a specific column."""
        result = retriever_with_cards.search_by_column("orders", "customer_id")
        assert result is not None
        card_id, card = result
        assert card.column_name == "customer_id"

    def test_search_by_column_not_found(self, retriever_with_cards):
        """Test searching for non-existent column."""
        result = retriever_with_cards.search_by_column("orders", "nonexistent")
        assert result is None

    def test_search_pii_columns(self, retriever_with_cards):
        """Test finding all PII columns."""
        results = retriever_with_cards.search_pii_columns()
        assert len(results) == 1
        card_id, card = results[0]
        assert card.is_pii is True
        assert card.pii_type == "email"

    def test_get_card(self, retriever_with_cards):
        """Test retrieving a specific card by ID."""
        card = retriever_with_cards.get_card("card_0")
        assert card.name == "customers"

    def test_get_card_not_found(self, retriever_with_cards):
        """Test getting non-existent card raises KeyError."""
        with pytest.raises(KeyError):
            retriever_with_cards.get_card("nonexistent")

    def test_clear(self, retriever_with_cards):
        """Test clearing the retriever."""
        retriever_with_cards.clear()
        assert len(retriever_with_cards.cards) == 0
        assert len(retriever_with_cards.rendered) == 0

    def test_search_substring_match(self, retriever_with_cards):
        """Test substring matching in search."""
        results = retriever_with_cards.search("email", top_k=5)
        assert len(results) > 0
        # Should find email column
        assert any("email" in str(card.to_dict()) for _, _, card in results)

    def test_search_empty_query(self, retriever_with_cards):
        """Test search with empty query."""
        results = retriever_with_cards.search("", top_k=5)
        assert len(results) == 0

    def test_search_empty_retriever(self):
        """Test search on empty retriever."""
        retriever = DictRetriever()
        results = retriever.search("test", top_k=5)
        assert len(results) == 0


class TestRetrieverIntegration:
    """Integration tests for Chunker and Retriever."""

    def test_full_pipeline_index_and_search(self):
        """Test full pipeline: catalog -> chunk -> index -> search."""
        # Create a sample catalog
        catalog = Catalog(source="test://source")
        columns = {
            "id": ColumnMetadata(
                name="id", type="BIGINT", nullable=False, ordinal_position=1
            ),
            "username": ColumnMetadata(
                name="username",
                type="VARCHAR",
                nullable=False,
                ordinal_position=2,
            ),
        }
        table = TableMetadata(
            name="users", schema={}, row_count=1000
        )
        table.columns = columns
        catalog.add_table(table)

        # Chunk and render
        cards, rendered = Chunker.chunk_catalog_and_render(catalog)

        # Index
        retriever = DictRetriever()
        retriever.index(cards, rendered)

        # Search
        results = retriever.search("users")
        assert len(results) > 0
        assert any("users" in str(card.to_dict()) for _, _, card in results)

    def test_retriever_type_compliance(self):
        """Test that DictRetriever complies with BaseRetriever interface."""
        retriever = DictRetriever()
        assert isinstance(retriever, BaseRetriever)
        assert hasattr(retriever, "index")
        assert hasattr(retriever, "search")
        assert hasattr(retriever, "get_card")
        assert hasattr(retriever, "clear")
