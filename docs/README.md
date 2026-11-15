# Lakeforge

**Data Engineer's Source Inspection & Insight Tool**

Point at any data source (SQLite, PostgreSQL, MySQL, SQL Server, Oracle, Databricks, DuckDB, local CSV/Parquet) + optional context docs, and get instant schema, statistical profiling, privacy auditing, and natural-language Q&A over that source — safely, cheaply, and local-first.

---

## 🚀 Key Capabilities

- **Multi-Source Connectors:** SQLite, PostgreSQL, MySQL, SQL Server, Oracle, Databricks, DuckDB, and CSV/Parquet files.
- **DBeaver Workspace Import:** Automatically detect and import database connections configured in local DBeaver workspaces.
- **L1 Structural Schema Discovery:** Fast metadata inspection without loading full tables.
- **L2 Statistical Profiling & Privacy Auditing:** Sample rows, calculate null rates, compute min/max/distinct statistics, and detect sensitive PII (emails, SSNs, phone numbers) with automated masking.
- **Natural Language Text-to-SQL Engine:** Ask plain English questions and get verified, AST-safe SQL.
- **Automated SQL Self-Correction:** Reflection loop automatically catches syntax or column mismatches, feeds errors back to the LLM, and self-corrects up to 2 retries.
- **Multi-Turn Conversational Memory:** Preserves antecedent context across follow-up questions within sessions.
- **AST Safety Guardrails:** Strict SQL validation (read-only SELECT/WITH enforcement, DDL/DML rejection, semicolon injection prevention).
- **Interactive Modern Web App:** React 18 + Vite frontend with real-time profiling, data samples grids, and Markdown audit export.
- **Docker Compose Ready:** Single-command production deployment for both backend and frontend.

---

## 🛠️ Quick Start

### 1. Run with Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/lakeforge.git
cd lakeforge

# Set your Groq API key for Text-to-SQL (optional, local SQLite inspection works without LLM)
export GROQ_API_KEY="your-groq-api-key"

# Start the full stack
docker-compose up --build
```

- **Web Dashboard & Inspector:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend:** [http://localhost:8000](http://localhost:8000)
- **Swagger Interactive API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Run Locally

#### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -e .

# Run the FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser.

---

### 3. CLI Usage

#### Inspect a local database or CSV file:
```bash
lakeforge inspect sample_data.db
```

#### One-shot natural language query via CLI:
```bash
lakeforge inspect sample_data.db --ask "How many customers are in the database?"
```

#### Interactive REPL mode:
```bash
lakeforge inspect sample_data.db
> What is the customer count?
> List the top 5 highest value orders
> exit
```

---

## 🧪 Running Tests

The test suite covers unit tests, AST validation, multi-dialect execution, multi-turn conversational Q&A, and API integration:

```bash
# Run complete test suite (398 tests)
python -m pytest tests/ -v
```

---

## 📦 Project Architecture

```
lakeforge/
├── backend/                  # FastAPI REST API
│   ├── routes/               # API routes (sources, inspection, qa, dbeaver)
│   ├── services/             # Business logic (qa_service, source_service, inspection_service)
│   └── models.py             # Pydantic V2 request & response schemas
├── frontend/                 # Vite + React 18 Web App
│   ├── src/pages/            # Dashboard, Inspector, QA, Reports, Settings
│   └── src/index.css         # Modern design system & token styles
├── lakeforge/                # Core Python SDK
│   ├── sources/              # Connectors (sqlite, postgres, mysql, oracle, sqlserver, databricks, duckdb)
│   ├── discover.py           # L1 structural catalog discovery
│   ├── profile.py            # L2 statistical profiling & sampling
│   ├── pii.py                # PII scanner & masking engines
│   ├── validator.py          # sqlglot-powered AST SQLValidator
│   └── llm/                  # SQLGenerator, router, cache, cost tracking
├── Dockerfile.backend        # Container build for FastAPI backend
├── docker-compose.yml        # Multi-container orchestration
└── tests/                    # 398 automated unit & integration tests
```

---

## 📄 License & Governance

- **Read-Only by Default:** Zero write risk against production databases.
- **PII Masking:** Salted hashes or redaction prior to data staging.
- **AST Validated:** Strict AST validation blocks DDL/DML operations before execution.
- **License:** MIT License.
