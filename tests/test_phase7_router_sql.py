"""Tests for Phase 7: SQL Router + Prompt Templates."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from lakeforge.llm.router import QuestionRouter, QueryType
from lakeforge.llm.sql_gen import SQLGenerator
from lakeforge.prompts.examples import (
    get_examples_for_category,
    format_examples_for_prompt,
    DESCRIBE_EXAMPLES,
    AGGREGATE_EXAMPLES,
    FILTER_EXAMPLES,
    JOIN_EXAMPLES,
    CUSTOM_EXAMPLES,
)


class TestQueryType:
    """Test QueryType enum."""

    def test_query_type_values(self):
        """Test QueryType has expected values."""
        assert QueryType.DESCRIBE.value == "DESCRIBE"
        assert QueryType.AGGREGATE.value == "AGGREGATE"
        assert QueryType.FILTER.value == "FILTER"
        assert QueryType.JOIN.value == "JOIN"
        assert QueryType.CUSTOM.value == "CUSTOM"

    def test_query_type_from_string(self):
        """Test creating QueryType from string."""
        assert QueryType["DESCRIBE"] == QueryType.DESCRIBE
        assert QueryType["CUSTOM"] == QueryType.CUSTOM


class TestPromptTemplates:
    """Test Jinja2 prompt templates exist and load."""

    @pytest.fixture
    def templates_dir(self):
        """Get templates directory."""
        return Path(__file__).parent.parent / "lakeforge" / "prompts"

    def test_route_template_exists(self, templates_dir):
        """Test route.j2 template exists."""
        template_file = templates_dir / "route.j2"
        assert template_file.exists()

    def test_route_template_has_placeholder(self, templates_dir):
        """Test route.j2 has question placeholder."""
        template_file = templates_dir / "route.j2"
        content = template_file.read_text()
        assert "{{ question }}" in content

    def test_sql_template_exists(self, templates_dir):
        """Test sql.j2 template exists."""
        template_file = templates_dir / "sql.j2"
        assert template_file.exists()

    def test_sql_template_has_placeholders(self, templates_dir):
        """Test sql.j2 has required placeholders."""
        template_file = templates_dir / "sql.j2"
        content = template_file.read_text()
        assert "{{ question }}" in content
        assert "schema" in content

    def test_summarize_template_exists(self, templates_dir):
        """Test summarize.j2 template exists."""
        template_file = templates_dir / "summarize.j2"
        assert template_file.exists()

    def test_describe_template_exists(self, templates_dir):
        """Test describe.j2 template exists."""
        template_file = templates_dir / "describe.j2"
        assert template_file.exists()


class TestExamples:
    """Test few-shot examples library."""

    def test_describe_examples(self):
        """Test DESCRIBE examples are present."""
        examples = get_examples_for_category("DESCRIBE")
        assert len(examples) >= 2
        assert all("question" in ex for ex in examples)
        assert all("sql" in ex for ex in examples)

    def test_aggregate_examples(self):
        """Test AGGREGATE examples are present."""
        examples = get_examples_for_category("AGGREGATE")
        assert len(examples) >= 3
        # Check SQL is safe (SELECT only)
        for ex in examples:
            assert ex["sql"].strip().upper().startswith("SELECT")

    def test_filter_examples(self):
        """Test FILTER examples are present."""
        examples = get_examples_for_category("FILTER")
        assert len(examples) >= 2
        for ex in examples:
            assert "WHERE" in ex["sql"].upper() or "SELECT" in ex["sql"].upper()

    def test_join_examples(self):
        """Test JOIN examples are present."""
        examples = get_examples_for_category("JOIN")
        assert len(examples) >= 2
        for ex in examples:
            assert "JOIN" in ex["sql"].upper()

    def test_custom_examples(self):
        """Test CUSTOM examples are present."""
        examples = get_examples_for_category("CUSTOM")
        assert len(examples) >= 2

    def test_format_examples_for_prompt(self):
        """Test example formatting for prompt."""
        formatted = format_examples_for_prompt("AGGREGATE", max_examples=2)
        assert isinstance(formatted, str)
        assert "Q:" in formatted or formatted == ""  # Empty or has examples

    def test_get_examples_for_invalid_category(self):
        """Test getting examples for invalid category defaults to CUSTOM."""
        examples = get_examples_for_category("INVALID")
        assert examples == CUSTOM_EXAMPLES

    def test_format_examples_limit(self):
        """Test example formatting respects max_examples."""
        formatted = format_examples_for_prompt("AGGREGATE", max_examples=1)
        # Should have at most 1 example
        count = formatted.count("Q:")
        assert count <= 1


class TestQuestionRouter:
    """Test question router and classification."""

    @patch("lakeforge.llm.router.get_llm")
    def test_router_initialization(self, mock_get_llm):
        """Test router initializes with LLM."""
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        
        router = QuestionRouter()
        assert router.llm is not None

    @patch("lakeforge.llm.router.get_llm")
    def test_router_classify_describe(self, mock_get_llm):
        """Test classifying DESCRIBE question."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "DESCRIBE"
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        router = QuestionRouter()
        result = router.classify("What columns are in users?")
        
        assert result == QueryType.DESCRIBE

    @patch("lakeforge.llm.router.get_llm")
    def test_router_classify_aggregate(self, mock_get_llm):
        """Test classifying AGGREGATE question."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "AGGREGATE"
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        router = QuestionRouter()
        result = router.classify("How many users are there?")
        
        assert result == QueryType.AGGREGATE

    @patch("lakeforge.llm.router.get_llm")
    def test_router_classify_filter(self, mock_get_llm):
        """Test classifying FILTER question."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "FILTER"
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        router = QuestionRouter()
        result = router.classify("Show users from California")
        
        assert result == QueryType.FILTER

    @patch("lakeforge.llm.router.get_llm")
    def test_router_classify_join(self, mock_get_llm):
        """Test classifying JOIN question."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "JOIN"
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        router = QuestionRouter()
        result = router.classify("Show orders with customer names")
        
        assert result == QueryType.JOIN

    @patch("lakeforge.llm.router.get_llm")
    def test_router_classify_custom(self, mock_get_llm):
        """Test classifying CUSTOM question."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "CUSTOM"
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        router = QuestionRouter()
        result = router.classify("Complex query involving joins and grouping")
        
        assert result == QueryType.CUSTOM

    @patch("lakeforge.llm.router.get_llm")
    def test_router_classify_invalid_response(self, mock_get_llm):
        """Test router handles invalid LLM response."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "INVALID_CATEGORY"
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        router = QuestionRouter()
        result = router.classify("Some question")
        
        # Should default to CUSTOM
        assert result == QueryType.CUSTOM

    @patch("lakeforge.llm.router.get_llm")
    def test_router_batch_classify(self, mock_get_llm):
        """Test batch classification."""
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        
        # Setup different responses
        responses = [
            MagicMock(text="DESCRIBE"),
            MagicMock(text="AGGREGATE"),
            MagicMock(text="FILTER"),
        ]
        mock_llm.complete.side_effect = responses
        
        router = QuestionRouter()
        questions = [
            "What columns?",
            "How many users?",
            "Show California users",
        ]
        
        results = router.classify_batch(questions)
        
        assert len(results) == 3
        assert results[questions[0]] == QueryType.DESCRIBE
        assert results[questions[1]] == QueryType.AGGREGATE
        assert results[questions[2]] == QueryType.FILTER


class TestSQLGenerator:
    """Test SQL generation."""

    def test_generator_initialization(self):
        """Test generator initializes."""
        mock_llm = MagicMock()
        mock_router = MagicMock()
        
        generator = SQLGenerator(llm=mock_llm, router=mock_router)
        assert generator.llm is not None
        assert generator.router is not None

    def test_generator_validate_sql_select(self):
        """Test SQL validation accepts SELECT."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        assert generator._validate_sql("SELECT * FROM users;") is True

    def test_generator_validate_sql_with(self):
        """Test SQL validation accepts WITH."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        assert generator._validate_sql("WITH cte AS (...) SELECT * FROM cte;") is True

    def test_generator_validate_sql_delete(self):
        """Test SQL validation rejects DELETE."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        assert generator._validate_sql("DELETE FROM users WHERE id = 1;") is False

    def test_generator_validate_sql_drop(self):
        """Test SQL validation rejects DROP."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        assert generator._validate_sql("DROP TABLE users;") is False

    def test_generator_validate_sql_insert(self):
        """Test SQL validation rejects INSERT."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        assert generator._validate_sql("INSERT INTO users VALUES (1, 'name');") is False

    def test_generator_validate_sql_update(self):
        """Test SQL validation rejects UPDATE."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        assert generator._validate_sql("UPDATE users SET name = 'foo' WHERE id = 1;") is False

    def test_generator_validate_sql_empty(self):
        """Test SQL validation rejects empty SQL."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        assert generator._validate_sql("") is False
        assert generator._validate_sql("   ") is False

    def test_generator_extract_sql_markdown(self):
        """Test SQL extraction from markdown code block."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        response = "```sql\nSELECT * FROM users;\n```"
        sql = generator._extract_sql(response)
        
        assert sql == "SELECT * FROM users;"

    def test_generator_extract_sql_plain(self):
        """Test SQL extraction from plain text."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        response = "SELECT * FROM users;"
        sql = generator._extract_sql(response)
        
        assert sql == "SELECT * FROM users;"

    def test_generator_format_schema(self):
        """Test schema formatting."""
        mock_llm = MagicMock()
        generator = SQLGenerator(llm=mock_llm)
        
        schema = {
            "users": [
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "VARCHAR"},
            ]
        }
        
        formatted = generator._format_schema(schema)
        
        assert "Table: users" in formatted
        assert "id" in formatted
        assert "INTEGER" in formatted

    @patch("lakeforge.llm.sql_gen.QuestionRouter")
    @patch("lakeforge.llm.sql_gen.get_llm")
    def test_generator_generate(self, mock_get_llm, mock_router_class):
        """Test SQL generation end-to-end."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "```sql\nSELECT COUNT(*) FROM users;\n```"
        mock_response.completion_tokens = 20
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        mock_router = MagicMock()
        mock_router.classify.return_value = QueryType.AGGREGATE
        mock_router_class.return_value = mock_router
        
        generator = SQLGenerator()
        
        schema = {"users": [{"name": "id", "type": "INTEGER"}]}
        result = generator.generate("How many users?", schema)
        
        assert "sql" in result
        assert result["valid"] is True
        assert result["query_type"] == "AGGREGATE"

    def test_generator_generate_invalid_sql(self):
        """Test generation flags invalid SQL."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "DELETE FROM users;"
        mock_response.completion_tokens = 5
        mock_llm.complete.return_value = mock_response
        
        mock_router = MagicMock()
        mock_router.classify.return_value = QueryType.AGGREGATE
        
        generator = SQLGenerator(llm=mock_llm, router=mock_router)
        
        schema = {"users": [{"name": "id", "type": "INTEGER"}]}
        result = generator.generate("Delete all users", schema)
        
        assert result["valid"] is False
        assert "DELETE" in result["sql"].upper()


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_question_to_sql(self):
        """Test full pipeline from question to SQL."""
        # Test that validate_sql correctly validates a simple SELECT statement
        generator = SQLGenerator(llm=MagicMock(), router=MagicMock())
        
        # Direct validation test
        sql = "SELECT COUNT(*) as user_count FROM users;"
        is_valid = generator._validate_sql(sql)
        assert is_valid is True, f"SQL validation failed for: {sql}"
        
        # Test with mock LLM
        mock_llm = MagicMock()
        gen_response = MagicMock()
        gen_response.text = "SELECT COUNT(*) as user_count FROM users;"
        gen_response.completion_tokens = 15
        mock_llm.complete.return_value = gen_response
        
        mock_router = MagicMock()
        mock_router.classify.return_value = QueryType.AGGREGATE
        
        generator = SQLGenerator(llm=mock_llm, router=mock_router)
        schema = {"users": [{"name": "id", "type": "INTEGER"}]}
        
        result = generator.generate("How many users?", schema)
        assert result["valid"] is True, f"Result invalid: {result}"
        assert "COUNT" in result["sql"].upper()
