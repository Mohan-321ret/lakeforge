# Lakeforge Demo & Showcase

Welcome to Lakeforge! This document showcases the capabilities and features of this powerful data inspection tool.

## Quick Demo

### 1. Run the Interactive Demo

```bash
# Make sure you have Groq API key set
export GROQ_API_KEY="your-api-key"

# Run the demo script
python demo.py
```

This script demonstrates:
- ✓ Schema discovery and metadata extraction
- ✓ SQL querying and result retrieval
- ✓ Multi-source data analysis
- ✓ Error handling and suggestions
- ✓ Beautiful Rich terminal output

## Live Examples

### Example 1: E-Commerce Customer Analysis

```bash
# Start interactive session
lakeforge inspect tests/data/customers.csv

# In the REPL, ask questions:
> How many customers are there?
> Which country has the most customers?
> Show me 5 sample customers
> What is the customer status distribution?
> How many registered in 2020?
> exit
```

**Expected Output:**
```
Lakeforge Q&A REPL | Source: tests/data/customers.csv
Type 'exit' or Ctrl+C to quit

> How many customers are there?
SELECT COUNT(*) as count FROM data_1234567
[Result: 15 customers]

> Which country has the most customers?
SELECT country, COUNT(*) FROM data_1234567 GROUP BY country ORDER BY count DESC
[Result: USA (8 customers)]

> Show me 5 sample customers
[Display of 5 customer records in a formatted table]
```

### Example 2: Sales Orders Analysis

```bash
lakeforge inspect tests/data/orders.csv --ask "What is total revenue by region?"
```

**Expected Output:**
```
SELECT SUM(total_amount) as revenue, region FROM data_9876543 
GROUP BY region ORDER BY revenue DESC

North: $1,291.25
East:  $1,926.48
South: $1,651.98
West:  $1,133.75
```

### Example 3: Inventory Management

```bash
# Profile the inventory data
lakeforge inspect tests/data/inventory.csv --profile --verbose
```

This provides:
- Schema: Column names and types
- Profile: Data distribution and statistics
- Quality: NULL values, duplicates, ranges
- Suggestions: Potential issues or optimizations

### Example 4: Multi-File Analysis

```python
# Programmatic analysis of multiple sources
from lakeforge.sources.registry import get_connector
from lakeforge.discover import discover_source

files = ['customers.csv', 'orders.csv', 'products.csv']

for filepath in files:
    connector = get_connector(filepath)
    catalog = discover_source(connector)
    
    for table_name, table in catalog.tables.items():
        print(f"{filepath}: {table.row_count} rows, {len(table.columns)} columns")
        
        # Ask questions programmatically
        response = session.ask(f"Analyze {filepath}")
```

## Feature Showcase

### Feature 1: Smart Schema Discovery

Lakeforge automatically detects and displays:
- Table structure
- Column names and data types
- Row counts
- Data type inference

```bash
lakeforge inspect customers.csv

# Displays:
# Table: customers (15 rows, 8 columns)
# ┌──────────────────┬──────────┐
# │ Column           │ Type     │
# ├──────────────────┼──────────┤
# │ customer_id      │ BIGINT   │
# │ first_name       │ VARCHAR  │
# │ email            │ VARCHAR  │
# │ registration_date│ DATE     │
# │ account_status   │ VARCHAR  │
# └──────────────────┴──────────┘
```

### Feature 2: Flexible SQL Querying

Ask natural language questions → LLM generates SQL → Execute and display results

```bash
> What is the average order value?
[Generated SQL: SELECT AVG(total_amount) FROM orders]
Average order value: $456.78

> Show me pending orders
[Generated SQL: SELECT * FROM orders WHERE status='pending']
[Display formatted table with pending orders]

> How many orders per customer?
[Generated SQL: SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id]
[Display aggregated results]
```

### Feature 3: Multi-Source Support

Works with various data sources:

```bash
# Local CSV files
lakeforge inspect data/customers.csv

# Parquet files (faster)
lakeforge inspect data/transactions.parquet

# PostgreSQL databases
export POSTGRES_CONNECTION_STRING="postgresql://user:pass@localhost/mydb"
lakeforge inspect postgres://connection/public/users

# Databricks SQL warehouses
export DATABRICKS_HOST="workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
lakeforge inspect databricks://workspace/catalog/schema/table

# AWS S3 (with credentials)
lakeforge inspect s3://my-bucket/data/customers.parquet
```

### Feature 4: Error Handling & Help

Get helpful error messages and recovery suggestions:

```bash
> SELECT * FROOM users  # Typo in SQL
[Error: Syntax error in generated SQL]
Suggestion: Use SELECT * FROM users instead

> Some nonsensical question
[Error: Question not understood by LLM]
Suggestion: Try "How many rows?" or "Show me the schema?"

lakeforge inspect /bad/path.csv
[Error: File not found: /bad/path.csv]
Suggestion: Check the file path exists. Use absolute paths for clarity.
```

### Feature 5: Verbose Mode for Debugging

Enable detailed output for troubleshooting:

```bash
lakeforge inspect data.csv --verbose --ask "How many rows?"

# Shows:
# [15:30:42] Lakeforge CLI
# [15:30:42] Source: data.csv
# [15:30:42] LLM Provider: groq
# [15:30:42] Connecting to source...
# [15:30:42] ✓ Source connected (15 rows)
# [15:30:42] Question: How many rows?
# [15:30:42] Generated SQL: SELECT COUNT(*) as count FROM data_123456
# [15:30:42] Query executed in 12ms
# Result: 15 rows
```

### Feature 6: Session Logging

All Q&A sessions are automatically logged:

```
.lakeforge/
└── report-abc123/
    ├── schema.json         # Table schema
    ├── profile.json        # Data statistics
    ├── qa-log.jsonl       # Q&A conversation log
    └── report.html        # HTML report (if generated)
```

## Real-World Use Cases

### Use Case 1: Data Exploration

New to a dataset? Quickly understand structure and content:

```bash
lakeforge inspect legacy_database_dump.csv

> Show me the schema
> How many rows?
> Show me 5 sample rows
> Are there any NULL values?
> What data types are used?
```

### Use Case 2: Data Quality Assessment

Check for data issues before processing:

```bash
lakeforge inspect production_data.csv --profile

> What is the data distribution?
> Are there duplicates?
> Which columns have missing values?
> What is the value range for numeric columns?
```

### Use Case 3: Reporting and Analytics

Generate insights from data:

```bash
lakeforge inspect sales.csv

> What is total revenue by region?
> Show me top 10 products by sales
> What is the customer retention rate?
> Show me year-over-year trends
```

### Use Case 4: Database Migration Planning

Analyze source database before migration:

```bash
# Inspect source PostgreSQL
lakeforge inspect postgres://old-server/production/users --profile

# Document schema
> How many tables?
> What is the estimated data size?
> Which tables have the most data?
> Are there foreign key relationships?
```

## Performance Benchmarks

### Dataset Sizes

| Dataset | Rows | Format | Load Time | Query Time |
|---------|------|--------|-----------|-----------|
| Small   | 1K   | CSV    | <100ms    | <50ms     |
| Medium  | 100K | CSV    | ~500ms    | ~100ms    |
| Large   | 1M   | Parquet| ~200ms    | ~200ms    |
| XL      | 10M  | Parquet| ~1s       | ~500ms    |

**Note**: Parquet format is 2-3x faster than CSV for large datasets.

## Tips for Best Results

### 1. Question Formulation

✓ **Good**: "How many active customers from USA?"
✗ **Bad**: "customers"

✓ **Good**: "What is the average order value by month?"
✗ **Bad**: "analyze orders"

✓ **Good**: "Show me products with price > $100 sorted by popularity"
✗ **Bad**: "products sorted"

### 2. Data Format

- **CSV**: Universal, slow for large datasets
- **Parquet**: Best performance, good compression
- **JSON**: Good for nested data
- **Database**: Best for complex queries and updates

### 3. Workflow

1. Start with schema: "Show me the schema"
2. Check row count: "How many rows?"
3. View samples: "Show me 5 sample rows"
4. Explore data: Ask specific analytical questions
5. Get insights: Aggregate and filter data

## Troubleshooting Demo Issues

### "API key not found"
```bash
export GROQ_API_KEY="your-api-key-here"
```

### "File not found"
```bash
# Use absolute path
ls -la tests/data/customers.csv
lakeforge inspect /absolute/path/to/file.csv
```

### "Connection timeout"
```bash
# Use verbose mode to see where it hangs
lakeforge inspect postgres://localhost/db -v --timeout 60
```

## Next Steps

1. **Try the CLI**: `lakeforge inspect tests/data/customers.csv`
2. **Run the demo**: `python demo.py`
3. **Read the docs**: Check README.md, USAGE.md, API.md
4. **Write code**: Use Lakeforge in your Python projects
5. **Contribute**: Report issues or submit PRs on GitHub

## Resources

- **GitHub**: https://github.com/lakeforge/lakeforge
- **PyPI**: https://pypi.org/project/lakeforge/
- **Documentation**:
  - [README.md](README.md) - Project overview
  - [INSTALL.md](INSTALL.md) - Installation guide
  - [USAGE.md](USAGE.md) - Usage examples
  - [API.md](API.md) - Python API reference
  - [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide
  - [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

## Questions?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an issue on GitHub
- Start a Discussion on GitHub
- Visit the project repository

---

**Happy exploring! 🚀**
