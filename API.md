# Lakeforge Python API

## Overview

Lakeforge provides a Python API for programmatic data inspection and analysis.

## Installation

```python
from lakeforge.sources.registry import get_connector
from lakeforge.discover import discover_source, Catalog
from lakeforge.session import QASession
```

## Basic Usage

### 1. Data Source Inspection

```python
from lakeforge.sources.registry import get_connector
from lakeforge.discover import discover_source

# Create a connector for your data source
connector = get_connector("customers.csv")

# Discover schema
catalog = discover_source(connector)

# List tables
print(catalog.tables.keys())

# Get first table's columns
first_table = list(catalog.tables.values())[0]
print(f"Table: {first_table.name}")
print(f"Columns: {list(first_table.columns.keys())}")
print(f"Row count: {first_table.row_count}")
```

### 2. Executing Queries

```python
from lakeforge.sources.registry import get_connector

connector = get_connector("customers.csv")

# Get table name
tables = connector.list_tables()
table_name = tables[0]

# Query data
results = connector.query(f"SELECT * FROM {table_name} LIMIT 10")

# Results are list of dicts
for row in results:
    print(row)
```

### 3. Q&A Session

```python
from lakeforge.session import QASession
from pathlib import Path

# Create a session
session = QASession(
    source="customers.csv",
    output_dir=Path(".lakeforge/"),
    verbose=True,
    profile=True
)

try:
    # Ask questions
    response = session.ask("How many customers are active?")
    print(response['answer'])
    
    # Get another answer
    response = session.ask("Show me customers from USA")
    print(response['answer'])
    
    # Get session summary
    summary = session.get_summary()
    print(f"Questions asked: {summary['questions_asked']}")
    
finally:
    session.close()
```

## Core Classes

### Connector

Base class for data source connections.

```python
class BaseConnector:
    def list_tables(self) -> list[str]
    def get_schema(self, table_name: str) -> dict[str, str]
    def get_row_count(self, table_name: str) -> int
    def query(self, sql: str, limit: int = 10000) -> list[dict]
```

#### Implementations

**DuckDB Connector** (Local files)

```python
from lakeforge.sources.duckdb_files import DuckDBConnector

connector = DuckDBConnector("data.csv")
# or
connector = DuckDBConnector("data.parquet")
```

**Databricks Connector**

```python
from lakeforge.sources.databricks_sql import DatabricksConnector

connector = DatabricksConnector(
    host="workspace.cloud.databricks.com",
    token="dapi...",
    warehouse_id="abc123"
)

# or use environment variables
# DATABRICKS_HOST, DATABRICKS_TOKEN
```

**PostgreSQL Connector**

```python
from lakeforge.sources.postgres import PostgresConnector

connector = PostgresConnector(
    host="localhost",
    port=5432,
    user="admin",
    password="secret",
    database="mydb"
)

# or use connection string env var
# POSTGRES_CONNECTION_STRING
```

### Schema Discovery

```python
from lakeforge.discover import discover_source, Catalog, TableMetadata, ColumnMetadata

catalog = discover_source(connector)

# catalog.source: str (source URI)
# catalog.tables: dict[str, TableMetadata]

for table_name, table in catalog.tables.items():
    print(f"Table: {table_name}")
    print(f"  Rows: {table.row_count}")
    print(f"  Columns:")
    for col_name, col in table.columns.items():
        print(f"    {col_name}: {col.type} (nullable: {col.nullable})")
```

### Executor

Execute queries and get structured results.

```python
from lakeforge.executor.duckdb_executor import DuckDBExecutor
from lakeforge.executor.base import ExecutionStatus

executor = DuckDBExecutor(source="data.csv")

# Execute query
result = executor.execute("SELECT COUNT(*) FROM table")

print(f"Status: {result.status}")           # SUCCESS, ERROR, TIMEOUT, PARTIAL
print(f"Rows: {result.rows}")                # Number of rows
print(f"Columns: {result.columns}")          # Column names
print(f"Data: {result.data}")                # List of dicts
print(f"Duration: {result.duration_ms}ms")   # Query time
print(f"Error: {result.error_message}")      # If error

if result.status == ExecutionStatus.SUCCESS:
    for row in result.data:
        print(row)
```

### Error Handling

```python
from lakeforge.errors import (
    LakeforgeException,
    SourceNotFoundError,
    InvalidSourceURIError,
    ConnectorNotAvailableError,
    AuthenticationError,
    ValidationError,
    ExecutionError
)

try:
    connector = get_connector("nonexistent.csv")
except SourceNotFoundError as e:
    print(f"Source not found: {e.message}")
    print(f"Suggestion: {e.suggestion}")

try:
    connector = get_connector("databricks://...")
except ConnectorNotAvailableError as e:
    print(f"Install missing dependency: pip install databricks-sql-connector")
```

## Advanced Usage

### Custom Configuration

```python
from lakeforge.config import LakeforgeConfig

config = LakeforgeConfig(
    llm_provider="groq",
    log_level="DEBUG",
    max_query_timeout_sec=60,
    max_result_rows=5000,
    output_dir="/custom/path/"
)
```

### Programmatic Q&A

```python
from lakeforge.session import QASession
from pathlib import Path
import json

# Automate analysis
questions = [
    "How many rows?",
    "What is the schema?",
    "Show me 3 sample rows",
    "Are there any NULL values?",
]

session = QASession(source="data.csv", output_dir=Path(".lakeforge/"))

results = []
for question in questions:
    response = session.ask(question)
    results.append({
        "question": question,
        "answer": response['answer'],
        "sql": response.get('sql'),
    })

# Save results
with open("analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)

session.close()
```

### Batch Processing

```python
from lakeforge.sources.registry import get_connector
import os

# Process multiple files
data_dir = "data/"

for filename in os.listdir(data_dir):
    if filename.endswith(".csv"):
        connector = get_connector(os.path.join(data_dir, filename))
        
        tables = connector.list_tables()
        for table in tables:
            schema = connector.get_schema(table)
            row_count = connector.get_row_count(table)
            
            print(f"{filename}: {table} ({row_count} rows, {len(schema)} columns)")
```

### Type Hints

```python
from typing import Optional, List, Dict
from lakeforge.sources.registry import BaseConnector
from lakeforge.discover import Catalog
from lakeforge.executor.base import ExecutionResult

def analyze_source(
    source: str,
    output_dir: Optional[str] = None
) -> Catalog:
    """
    Analyze a data source.
    
    Args:
        source: Data source URI
        output_dir: Optional output directory
        
    Returns:
        Catalog with schema metadata
        
    Raises:
        SourceNotFoundError: If source doesn't exist
        ConnectorNotAvailableError: If connector not installed
    """
    from lakeforge.sources.registry import get_connector
    from lakeforge.discover import discover_source
    
    connector = get_connector(source)
    return discover_source(connector)
```

## Examples

### Example 1: Customer Analysis

```python
from lakeforge.sources.registry import get_connector
from lakeforge.session import QASession
from pathlib import Path

# Analyze customer data
session = QASession(
    source="customers.csv",
    output_dir=Path("./reports/"),
    profile=True
)

questions = [
    "How many active customers?",
    "What is the customer count by country?",
    "Show me the top 10 customers by value",
]

for q in questions:
    resp = session.ask(q)
    print(f"Q: {q}")
    print(f"A: {resp['answer']}\n")

session.close()
```

### Example 2: Database Migration Analysis

```python
from lakeforge.sources.postgres import PostgresConnector
from lakeforge.discover import discover_source
import json

# Analyze source database
connector = PostgresConnector(
    host="old-db.company.com",
    user="admin",
    password="secret",
    database="production"
)

catalog = discover_source(connector)

# Export schema for migration planning
schema_report = {
    "source": catalog.source,
    "tables": {
        name: {
            "row_count": table.row_count,
            "columns": {
                col_name: {
                    "type": col.type,
                    "nullable": col.nullable
                }
                for col_name, col in table.columns.items()
            }
        }
        for name, table in catalog.tables.items()
    }
}

with open("migration_schema.json", "w") as f:
    json.dump(schema_report, f, indent=2)
```

## Environment Variables

```python
import os

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Databricks
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# PostgreSQL
POSTGRES_CONNECTION_STRING = os.getenv("POSTGRES_CONNECTION_STRING")

# AWS S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
```

## Common Patterns

### Safe Query Execution

```python
from lakeforge.executor.base import ExecutionStatus

result = executor.execute(sql)

match result.status:
    case ExecutionStatus.SUCCESS:
        process_data(result.data)
    case ExecutionStatus.TIMEOUT:
        print(f"Query timeout after {result.duration_ms}ms")
    case ExecutionStatus.PARTIAL:
        print(f"Partial results: {result.warning}")
    case ExecutionStatus.ERROR:
        print(f"Error: {result.error_message}")
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lakeforge")

# Use in code
from lakeforge.config import get_config
config = get_config()
logger.info(f"Using LLM provider: {config.llm_provider}")
```

## Performance Tips

1. **Limit Results**: Use `limit` parameter in queries
2. **Disable Profiling**: Skip profiling for speed with `profile=False`
3. **Use Parquet**: Better performance than CSV
4. **Set Timeout**: Adjust for your data size
5. **Connection Reuse**: Reuse connector/executor for multiple queries

## API Reference

For detailed API reference, see [API_REFERENCE.md](API_REFERENCE.md)

## Support

- **Documentation**: See USAGE.md and TROUBLESHOOTING.md
- **Issues**: https://github.com/lakeforge/lakeforge/issues
- **Discussions**: https://github.com/lakeforge/lakeforge/discussions
