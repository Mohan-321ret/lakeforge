# Lakeforge API Reference

Comprehensive documentation for the **Lakeforge REST API** and **Python SDK**.

---

## 1. Overview & Architecture

Lakeforge is a local-first source inspection, profiling, privacy auditing, and natural-language Q&A tool. It provides:
- **REST API**: Built on FastAPI with async endpoint handlers, connection pooling, and AST validation.
- **Python SDK**: Directly embeddable into scripts, Airflow DAGs, and Databricks notebooks.
- **Supported Connectors**: SQLite, PostgreSQL, MySQL, SQL Server, Oracle, DuckDB, Databricks, and CSV/Parquet files.

---

## 2. REST API Endpoints

Base URL: `http://localhost:8000/api` (or `/api` behind reverse proxy).

### Healthcheck

#### `GET /health`
Returns service status.
```json
{
  "status": "healthy",
  "version": "0.2.0"
}
```

---

### Data Sources Management

#### `POST /api/sources`
Register a new data source connector.

**Request Body:**
```json
{
  "name": "Production Analytics Replica",
  "uri": "sqlite:///d:/lakeforge/sample_data.db",
  "description": "Primary SQLite replica containing customers and orders",
  "tags": ["prod", "analytics"]
}
```

**Response (`201 Created`):**
```json
{
  "id": "src_1",
  "name": "Production Analytics Replica",
  "uri": "sqlite:///d:/lakeforge/sample_data.db",
  "source_type": "sqlite",
  "description": "Primary SQLite replica containing customers and orders",
  "tags": ["prod", "analytics"],
  "table_count": 0,
  "created_at": "2026-10-25T20:00:00Z"
}
```

#### `GET /api/sources`
List all registered sources.

#### `GET /api/sources/{source_id}`
Retrieve source details by ID.

#### `POST /api/sources/{source_id}/test`
Verify connectivity and retrieve table count.
```json
{
  "status": "connected",
  "message": "Successfully connected to SQLite database",
  "table_count": 2,
  "tables": ["customers", "orders"]
}
```

#### `DELETE /api/sources/{source_id}`
Remove a registered data source.

---

### Schema Discovery & Profiling

#### `POST /api/inspect/start`
Trigger background inspection and profiling.

**Request Body:**
```json
{
  "source_id": "src_1",
  "include_profile": true,
  "sample_size": 100
}
```

**Response (`200 OK`):**
```json
{
  "session_id": "sess_1",
  "status": "started"
}
```

#### `GET /api/inspect/{session_id}/status`
Check session status (`in_progress`, `completed`, `error`).

#### `GET /api/inspect/{session_id}/schema`
Retrieve discovered table schemas and column types.

**Response:**
```json
{
  "schema": {
    "source": "sqlite:///...",
    "tables": {
      "customers": {
        "name": "customers",
        "row_count": 5,
        "columns": {
          "id": { "name": "id", "type": "INTEGER", "nullable": false },
          "name": { "name": "name", "type": "TEXT", "nullable": true },
          "email": { "name": "email", "type": "TEXT", "nullable": true }
        }
      }
    }
  }
}
```

#### `GET /api/inspect/{session_id}/profile`
Retrieve column-level statistics (null rates, distinct values, min/max ranges, top frequent values) and PII scanner detection flags.

#### `GET /api/inspect/{session_id}/samples?limit=100`
Retrieve sampled rows for data preview.

---

### Natural Language Q&A & Text-to-SQL

#### `POST /api/qa`
Convert a natural language question into verified, AST-safe SQL and execute it on the live source. Includes multi-turn context memory and automated self-correction on failure.

**Request Body:**
```json
{
  "source_id": "src_1",
  "question": "How many customers are in the database?",
  "session_id": "optional_session_id"
}
```

**Response:**
```json
{
  "session_id": "qa_sess_1730000000",
  "question": "How many customers are in the database?",
  "generated_sql": "SELECT COUNT(*) as total_customers FROM customers",
  "execution_status": "success",
  "results": [
    { "total_customers": 5 }
  ],
  "error_message": null,
  "execution_time_ms": 14.2,
  "attempts": 1,
  "self_corrected": false,
  "corrections": []
}
```

**Self-Correction Example (When Error Occurs):**
If the initial generated query has a column error, Lakeforge invokes the LLM self-correction loop up to 2 retries:
```json
{
  "session_id": "qa_sess_1730000000",
  "question": "Show top customer scores",
  "generated_sql": "SELECT name, score FROM customers ORDER BY score DESC",
  "execution_status": "success",
  "results": [...],
  "attempts": 2,
  "self_corrected": true,
  "corrections": [
    "Database error fixed: no such column: user_score -> corrected to score"
  ]
}
```

#### `GET /api/qa/{session_id}/history`
Retrieve all exchanges within a multi-turn conversation.

---

### DBeaver Connections Integration

#### `GET /api/dbeaver/connections`
Scan local DBeaver workspaces and list saved database connections.

#### `POST /api/dbeaver/connections/{connection_id}`
Import a DBeaver connection directly into Lakeforge as an active source.

---

## 3. Python SDK Usage

### Source Discovery & Profiling

```python
from lakeforge.sources.registry import get_connector
from lakeforge.discover import discover_source, profile_source

# 1. Connect
connector = get_connector("sqlite:///sample_data.db")
connector.connect()

# 2. Discover Schema (L1)
catalog = discover_source(connector)
for table_name, table_meta in catalog.tables.items():
    print(f"Table: {table_name} ({table_meta.row_count} rows)")
    for col_name, col_meta in table_meta.columns.items():
        print(f"  - {col_name}: {col_meta.type} (nullable={col_meta.nullable})")

# 3. Profile & PII Detection (L2)
profile = profile_source(connector, catalog, max_rows=500)
for table_name, table_prof in profile.tables.items():
    if table_prof.pii_columns:
        print(f"⚠️ PII Detected in {table_name}: {table_prof.pii_columns}")

connector.close()
```

### Safe Query Execution with AST Validation

```python
from lakeforge.validator import SQLValidator
from lakeforge.sources.registry import get_connector

validator = SQLValidator()
connector = get_connector("sqlite:///sample_data.db")

query = "SELECT name, email FROM customers WHERE id = 1"

# Validate AST safety (blocks DROP, DELETE, INSERT, UPDATE, semicolon injection)
validation = validator.validate(query)
if validation["valid"]:
    results = connector.query(query, limit=100)
    print(results)
else:
    print(f"Query rejected: {validation['errors']}")
```

### Programmatic Q&A Service with Self-Correction

```python
import asyncio
from backend.services.qa_service import QAService

async def run_qa():
    qa_service = QAService()
    response = await qa_service.ask_question(
        source_uri="sqlite:///sample_data.db",
        question="How many orders were placed by each customer?",
    )
    print("Generated SQL:", response["generated_sql"])
    print("Results:", response["results"])
    print("Self-Corrected:", response["self_corrected"])

asyncio.run(run_qa())
```

---

## 4. Docker & Production Deployment

Run the complete stack with a single command:

```bash
docker-compose up --build
```

- **Frontend**: http://localhost:3000
- **FastAPI Backend**: http://localhost:8000
- **Swagger Documentation**: http://localhost:8000/docs
