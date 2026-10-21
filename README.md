# Lakeforge

**Data Engineer's Source Inspection & Insight Tool**

Point at any data source (S3, Databricks, JDBC, local files) + optional context docs, and get instant schema, profile, and natural-language Q&A over that source — safely and cheaply, from a laptop.

## Features

- **Multi-source support:** Local files, S3 Parquet, Databricks, Postgres (coming)
- **Instant schema inspection:** Extract table and column metadata in seconds
- **Smart profiling:** Sample rows, compute statistics, detect PII
- **Context enrichment:** Load Markdown docs, YAML metadata, dbt manifests
- **Natural language Q&A:** Ask questions, get safe SQL, execute queries
- **Zero cost:** Uses free-tier LLMs (Groq) + optional offline Ollama
- **Privacy first:** Masks PII before any output, read-only by default
- **Reproducible:** Runs on laptop, in CI, or in Databricks notebooks

## Installation

```bash
pip install lakeforge
```

For optional features:

```bash
pip install lakeforge[databricks]  # Databricks SQL support
pip install lakeforge[postgres]    # Postgres support
pip install lakeforge[pdf]         # PDF document parsing
pip install lakeforge[semantic]    # Semantic search via Chroma
```

## Quick Start

### Inspect a local CSV

```bash
lakeforge inspect data.csv
```

Outputs:
- `report.md` — Human-readable summary
- `catalog.json` — Machine-readable schema + stats
- `samples/` — Masked sample rows
- `qa.log.jsonl` — Audit trail

### Ask a question (one-shot)

```bash
lakeforge inspect data.csv --ask "How many unique customers?"
```

### Interactive REPL

```bash
lakeforge inspect data.csv
> What is the email column distribution?
> Show me sample values from the phone column
> exit
```

## Architecture

```
CLI / REPL
    ↓
┌─────────────────────────────────────┐
│   Discovery (L1 Schema)             │
│   Profile (L2 Stats + Samples)      │
│   PII Masking                       │
│                                     │
│   Card Model + Retriever            │
│   (Dict → BM25 → Chroma)            │
│                                     │
│   Question Router                   │
│   ↓                                 │
│   SQL Generator (LLM)               │
│   ↓                                 │
│   Validator (sqlglot)               │
│   ↓                                 │
│   Executor (per source)             │
│   ↓                                 │
│   Summarizer (LLM) → Answer         │
└─────────────────────────────────────┘
```

## Development Setup

### Clone and install dependencies

```bash
git clone https://github.com/yourusername/lakeforge
cd lakeforge
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/ -v
```

### Run linter and type checker

```bash
black lakeforge/
ruff check lakeforge/
mypy lakeforge/
```

## Configuration

Create `.lakeforge.yaml` or use environment variables:

```yaml
llm_provider: groq
groq_api_key: ${GROQ_API_KEY}
max_query_timeout_sec: 30
max_result_bytes: 10485760
```

Or:

```bash
export LAKEFORGE_LLM_PROVIDER=ollama
export LAKEFORGE_OLLAMA_BASE_URL=http://localhost:11434
lakeforge inspect data.csv
```

## Project Status

**Phase 0–1 Complete:** Foundation + Local Discovery (CSV/Parquet inspection)

- [x] CLI skeleton (Typer)
- [x] Config loader (YAML + env vars)
- [x] DuckDB connector
- [x] L1 schema discovery
- [x] Report generation (Markdown + JSON)

**Phase 2–3 In Progress:** Profiling + Card Model

- [ ] Column statistics (null%, unique, min/max)
- [ ] PII detection + masking
- [ ] Card model + dict retriever

**Phase 4+ Future:** Docs, LLM Q&A, Multi-source

- [ ] Doc ingesters (Markdown, YAML, dbt)
- [ ] BM25 retriever
- [ ] LLM clients (Groq, Ollama)
- [ ] SQL router + validator + executor
- [ ] REPL + one-shot --ask
- [ ] Databricks + Postgres connectors

## Cost

- **Local files + DuckDB:** Free
- **Groq (free tier):** ~$0 during development (30k tokens/min)
- **Ollama (offline):** Free (run locally)
- **S3 egress:** Minimal (DuckDB footer scans only)

**Target:** $0 during full dev cycle via free tiers + caching.

## Data Governance

- ✅ Read-only by default (no writes)
- ✅ PII masking before output
- ✅ SQL validation + byte caps + timeouts
- ✅ Audit logging of every query
- ✅ Credentials in env vars (not in code)

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Add tests + docs
4. Submit a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT — See [LICENSE](LICENSE)

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/lakeforge/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/lakeforge/discussions)

---

**Built by data engineers, for data engineers.** 🚀
