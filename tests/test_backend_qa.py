"""Tests for backend Q&A service and query execution engine."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.services.qa_service import QAService


class TestBackendQAService:
    """Test QAService query execution against real connectors."""

    @pytest.fixture
    def sample_sqlite_db(self, tmp_path):
        """Create a temporary SQLite database with sample data."""
        db_file = tmp_path / "test_data.db"
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, score INTEGER)")
        conn.executemany(
            "INSERT INTO users VALUES (?, ?, ?, ?)",
            [
                (1, "Alice", "alice@example.com", 95),
                (2, "Bob", "bob@example.com", 80),
                (3, "Carol", "carol@example.com", 90),
            ],
        )
        conn.commit()
        conn.close()
        return f"sqlite:///{db_file.as_posix()}"

    @pytest.mark.anyio
    async def test_ask_question_executes_real_query(self, sample_sqlite_db):
        """Verify that ask_question executes against the real database and returns actual data."""
        qa_service = QAService()

        # Mock the SQL generator to return valid SQL without calling external LLM
        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "sql": "SELECT COUNT(*) as total_users FROM users",
            "valid": True,
            "query_type": "AGGREGATE",
        }

        with patch.object(qa_service, "_get_generator", return_value=mock_generator):
            res = await qa_service.ask_question(
                source_uri=sample_sqlite_db,
                question="How many users are in the database?",
            )

            assert res["execution_status"] == "success"
            assert res["generated_sql"] == "SELECT COUNT(*) as total_users FROM users"
            assert res["results"] is not None
            assert len(res["results"]) == 1
            assert res["results"][0]["total_users"] == 3
            assert res["error_message"] is None
            assert res["execution_time_ms"] >= 0

    @pytest.mark.anyio
    async def test_ask_question_rejects_dangerous_sql(self, sample_sqlite_db):
        """Verify that SQLValidator catches and rejects destructive statements."""
        qa_service = QAService()

        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "sql": "DROP TABLE users;",
            "valid": True,
            "query_type": "CUSTOM",
        }

        with patch.object(qa_service, "_get_generator", return_value=mock_generator):
            res = await qa_service.ask_question(
                source_uri=sample_sqlite_db,
                question="Delete all users",
            )

            assert res["execution_status"] == "error"
            assert res["results"] is None
            assert "Safety validation failed" in res["error_message"]

    @pytest.mark.anyio
    async def test_ask_question_handles_generator_failure(self, sample_sqlite_db):
        """Verify that failed SQL generation returns a clean error."""
        qa_service = QAService()

        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "sql": None,
            "valid": False,
        }

        with patch.object(qa_service, "_get_generator", return_value=mock_generator):
            res = await qa_service.ask_question(
                source_uri=sample_sqlite_db,
                question="Unintelligible question",
            )

            assert res["execution_status"] == "error"
    @pytest.mark.anyio
    async def test_ask_question_self_correction_on_db_error(self, sample_sqlite_db):
        """Verify that QAService triggers self-correction loop when initial query has bad column."""
        qa_service = QAService()

        mock_generator = MagicMock()
        # Initial attempt generates invalid column
        mock_generator.generate.return_value = {
            "sql": "SELECT bad_column FROM users",
            "valid": True,
            "query_type": "FILTER",
        }
        # Self-correction generates valid query
        mock_generator.correct.return_value = {
            "sql": "SELECT name, score FROM users",
            "valid": True,
            "query_type": "CORRECTION",
        }

        with patch.object(qa_service, "_get_generator", return_value=mock_generator):
            res = await qa_service.ask_question(
                source_uri=sample_sqlite_db,
                question="Show user scores",
                session_id="test_self_correct_sess",
            )

            assert res["execution_status"] == "success"
            assert res["self_corrected"] is True
            assert res["attempts"] == 2
            assert len(res["corrections"]) == 1
            assert "bad_column" in res["corrections"][0]
            assert res["results"] is not None
            assert len(res["results"]) == 3

    @pytest.mark.anyio
    async def test_ask_question_multi_turn_history(self, sample_sqlite_db):
        """Verify that subsequent questions in the same session retain conversation history."""
        qa_service = QAService()

        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "sql": "SELECT COUNT(*) as count FROM users",
            "valid": True,
            "query_type": "AGGREGATE",
        }

        session_id = "test_multiturn_session_999"

        with patch.object(qa_service, "_get_generator", return_value=mock_generator):
            res1 = await qa_service.ask_question(
                source_uri=sample_sqlite_db,
                question="How many users are there?",
                session_id=session_id,
            )
            assert res1["execution_status"] == "success"

            res2 = await qa_service.ask_question(
                source_uri=sample_sqlite_db,
                question="And how many are active?",
                session_id=session_id,
            )
            assert res2["execution_status"] == "success"

            history = qa_service.get_history(session_id)
            assert len(history) == 2
            assert history[0]["question"] == "How many users are there?"
            assert history[1]["question"] == "And how many are active?"


class TestBackendQARoutes:
    """Test Q&A FastAPI HTTP endpoints."""

    @pytest.fixture
    def client(self):
        """Create a FastAPI test client."""
        from fastapi.testclient import TestClient
        from backend.main import app
        return TestClient(app)

    @pytest.fixture
    def test_source_id(self, tmp_path):
        """Create a test source and return its ID."""
        from backend.services.source_service import SourceService
        from backend.models import SourceCreate
        import asyncio

        db_file = tmp_path / "route_test.db"
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, title TEXT, price REAL)")
        conn.executemany(
            "INSERT INTO products VALUES (?, ?, ?)",
            [
                (1, "Widget A", 19.99),
                (2, "Widget B", 29.99),
            ],
        )
        conn.commit()
        conn.close()

        service = SourceService()
        source = asyncio.run(
            service.create_source(
                SourceCreate(
                    name="Test Products DB",
                    uri=f"sqlite:///{db_file.as_posix()}",
                    description="Test SQLite source for QA routes",
                )
            )
        )
        return source.id

    def test_qa_endpoint_success(self, client, test_source_id):
        """Test POST /api/qa returns 200 and query results."""
        qa_service = QAService()
        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "sql": "SELECT COUNT(*) as count FROM products",
            "valid": True,
            "query_type": "AGGREGATE",
        }

        with patch.object(qa_service, "_get_generator", return_value=mock_generator), \
             patch("backend.routes.qa.get_qa_service", return_value=qa_service):
            response = client.post(
                "/api/qa",
                json={
                    "source_id": test_source_id,
                    "question": "How many products exist?",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["execution_status"] == "success"
            assert data["generated_sql"] == "SELECT COUNT(*) as count FROM products"
            assert data["results"] == [{"count": 2}]
            assert data["error_message"] is None

    def test_qa_endpoint_source_not_found(self, client):
        """Test POST /api/qa with nonexistent source returns 404."""
        response = client.post(
            "/api/qa",
            json={
                "source_id": "nonexistent_source_9999",
                "question": "How many items?",
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Source not found"

    def test_qa_history_with_real_turns(self, client, test_source_id):
        """Test GET /api/qa/{session_id}/history endpoint returns real conversational turns."""
        qa_service = QAService()
        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "sql": "SELECT * FROM products LIMIT 5",
            "valid": True,
            "query_type": "FILTER",
        }

        session_id = "test_turn_sess_456"

        with patch.object(qa_service, "_get_generator", return_value=mock_generator), \
             patch("backend.routes.qa.get_qa_service", return_value=qa_service):
            # Send question in session
            post_res = client.post(
                "/api/qa",
                json={
                    "source_id": test_source_id,
                    "question": "Show top products",
                    "session_id": session_id,
                },
            )
            assert post_res.status_code == 200
            assert post_res.json()["session_id"] == session_id

            # Retrieve history
            hist_res = client.get(f"/api/qa/{session_id}/history")
            assert hist_res.status_code == 200
            data = hist_res.json()
            assert data["session_id"] == session_id
            assert len(data["history"]) >= 1
            assert data["history"][-1]["question"] == "Show top products"
            assert data["history"][-1]["execution_status"] == "success"


