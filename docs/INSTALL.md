# Lakeforge Installation Guide

## System Requirements

- **Python**: 3.11+ (tested on 3.11, 3.12, 3.13)
- **OS**: Linux, macOS, Windows
- **RAM**: Minimum 2GB (4GB recommended for profiling large datasets)
- **Disk**: 500MB for installation and dependencies

## Quick Start

### Using pip (Recommended)

```bash
# Basic installation
pip install lakeforge

# Or with optional dependencies
pip install lakeforge[databricks]    # Databricks connector
pip install lakeforge[postgres]      # PostgreSQL connector
pip install lakeforge[pdf]           # PDF support
pip install lakeforge[semantic]      # Semantic search
pip install lakeforge[dev]           # Development tools
```

### From Source

```bash
git clone https://github.com/lakeforge/lakeforge.git
cd lakeforge

# Install with dev dependencies
pip install -e ".[dev,databricks,postgres]"

# Run tests to verify installation
pytest tests/ -v
```

## Authentication Setup

### Groq API (Required for LLM Features)

```bash
# Set your Groq API key
export GROQ_API_KEY="your-api-key-here"
```

Get your API key at: https://console.groq.com

### Databricks (Optional)

```bash
export DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-api-token"
```

### PostgreSQL (Optional)

```bash
export POSTGRES_CONNECTION_STRING="postgres://user:password@host:5432/database"
```

### AWS S3 (Optional)

```bash
# Use standard AWS credential methods
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

## Verification

After installation, verify everything works:

```bash
# Test CLI
lakeforge --version

# Test with sample data
lakeforge inspect tests/data/customers.csv

# Run unit tests
pytest tests/ -v --tb=short
```

## Docker Installation

```dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir lakeforge[databricks,postgres]

ENV GROQ_API_KEY=your-api-key

ENTRYPOINT ["lakeforge"]
```

Build and run:

```bash
docker build -t lakeforge:latest .
docker run -it -e GROQ_API_KEY=your-key lakeforge --version
```

## Troubleshooting

### "Module not found" Errors

Install the missing optional dependency:

```bash
# For Databricks
pip install databricks-sql-connector

# For PostgreSQL
pip install psycopg2-binary

# For PDF support
pip install pdfplumber
```

### API Key Issues

Verify your environment variable is set:

```bash
# macOS/Linux
echo $GROQ_API_KEY

# Windows PowerShell
$env:GROQ_API_KEY
```

### Connection Timeouts

- Verify firewall settings
- Check that remote service (Databricks, PostgreSQL) is accessible
- Increase timeout with `--timeout` flag (see USAGE.md)

### Performance Issues

- Close other applications to free up RAM
- Disable profiling if not needed: `--no-profile`
- Process data in batches for large datasets
- Use Parquet format instead of CSV for better performance

## Uninstallation

```bash
pip uninstall lakeforge
```

## Getting Help

- **Documentation**: https://github.com/lakeforge/lakeforge/blob/main/README.md
- **Issues**: https://github.com/lakeforge/lakeforge/issues
- **Discussion**: https://github.com/lakeforge/lakeforge/discussions

## Next Steps

- Read [USAGE.md](USAGE.md) for command-line examples
- Check [API.md](API.md) for programmatic usage
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
