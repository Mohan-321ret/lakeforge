# Lakeforge Usage Guide

## Command-Line Interface

### Basic Commands

```bash
# Show version
lakeforge --version

# Get help
lakeforge --help
lakeforge inspect --help
```

## Inspect Command

The main command for analyzing data sources.

### Interactive Mode (REPL)

Start an interactive session to ask multiple questions:

```bash
lakeforge inspect data.csv
```

Then type your questions:

```
> How many rows are in this table?
> Show me the schema
> List all column names
> What are the data types?
> exit
```

### One-Shot Mode

Ask a single question and exit:

```bash
lakeforge inspect data.csv --ask "How many rows?"
lakeforge inspect data.csv -q "What is the average price?"
```

## Data Source Examples

### Local Files

```bash
# CSV files
lakeforge inspect customers.csv

# Parquet files
lakeforge inspect data.parquet

# JSON files
lakeforge inspect data.json
```

### S3 Buckets

```bash
# Requires AWS credentials configured
lakeforge inspect s3://my-bucket/data/customers.parquet
lakeforge inspect s3://company-data/reports/sales-2024.csv
```

### Databricks

```bash
# Format: databricks://workspace/catalog/schema/table
lakeforge inspect databricks://my-workspace/main/default/users

# Requires DATABRICKS_HOST and DATABRICKS_TOKEN env vars
export DATABRICKS_HOST="company.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

### PostgreSQL

```bash
# Format: postgres://user:password@host:port/database/schema
lakeforge inspect postgres://admin:password@localhost:5432/mydb/public

# Or use connection string env var
export POSTGRES_CONNECTION_STRING="postgresql://user:pass@host/db"
lakeforge inspect postgres://connection-string
```

## Common Questions

### Schema and Structure

```bash
> Show me the schema
> What columns are in this table?
> How many columns?
> What are the data types?
> Which columns are numeric?
> Which columns are text/string?
```

### Row Count and Size

```bash
> How many rows?
> What is the row count?
> How big is this dataset?
> How many records?
```

### Data Statistics

```bash
> What is the average salary?
> What is the minimum price?
> What is the maximum age?
> What is the count of unique values in status?
> What is the median income?
```

### Data Quality

```bash
> Are there any NULL values?
> Which columns have missing data?
> Show me rows with NULL values
> Are there duplicate records?
> What is the data distribution?
```

### Filtering and Selection

```bash
> Show me 5 sample rows
> Show me customers from USA
> Show me active users only
> List all product categories
> Show distinct values in status
```

### Relationships (multi-table queries)

```bash
> Join customers with orders
> Show total orders per customer
> What is the revenue by region?
> Which customers are in multiple regions?
```

## Command-Line Options

### Output Directory

```bash
# Save results to specific directory
lakeforge inspect data.csv --output ./my-reports/
lakeforge inspect data.csv -o /tmp/reports/
```

### Verbose Mode

```bash
# Enable debug logging
lakeforge inspect data.csv --verbose
lakeforge inspect data.csv -v

# One-shot with verbose
lakeforge inspect data.csv -q "How many rows?" -v
```

### Profiling

```bash
# Include statistical profiling
lakeforge inspect data.csv --profile
lakeforge inspect data.csv -p

# More detailed (slower)
lakeforge inspect data.csv --profile --verbose
```

### Configuration File

```bash
# Use custom configuration
lakeforge inspect data.csv --config config.yaml
lakeforge inspect data.csv -c ./lakeforge-config.yaml
```

### Query Timeout

```bash
# Set custom timeout in seconds
lakeforge inspect data.csv --timeout 60
lakeforge inspect data.csv -t 120
```

## Configuration File Example

Create `lakeforge-config.yaml`:

```yaml
llm_provider: groq
log_level: INFO
max_query_timeout_sec: 60
output_dir: .lakeforge/
max_result_rows: 10000
enable_pii_detection: true
```

Then use it:

```bash
lakeforge inspect data.csv --config lakeforge-config.yaml
```

## Real-World Examples

### E-Commerce Analysis

```bash
# Inspect customer data
lakeforge inspect customers.csv --profile

# Ask analytical questions
> How many customers are active?
> What countries have the most customers?
> What is the average customer lifetime value?

# Inspect orders
lakeforge inspect orders.csv -q "What is the total revenue by region?"
```

### Database Exploration

```bash
# Explore Postgres database
lakeforge inspect postgres://admin@localhost/mydb/public/users -p

# Interactive exploration
lakeforge inspect postgres://admin@localhost/mydb/public/orders

> Show me the schema
> How many orders are pending?
> What is the average order value?
> What is the revenue by month?
```

### Data Quality Assessment

```bash
# One-shot quality check
lakeforge inspect data.csv -q "Are there any NULL values or duplicates?"

# Interactive deep dive
lakeforge inspect data.csv -v -p

> Show me columns with missing data
> What is the data distribution?
> List all distinct values in status column
```

## Tips and Best Practices

### Performance

1. **For Large Files**: Use Parquet format instead of CSV for faster loading
2. **Profiling**: Disable profiling (`--no-profile`) for quick analysis
3. **Limits**: Results are limited to 10,000 rows by default for performance
4. **Timeout**: Adjust timeout for complex queries (`--timeout 120`)

### Question Formulation

1. **Be Specific**: "Count customers from USA" > "Show me customers"
2. **Use Column Names**: Reference actual column names when available
3. **One Topic**: Ask about one thing per question
4. **Clear Intent**: "What is the total revenue?" > "Revenue?"

### Workflow

1. **Start with Schema**: Always ask for schema first
2. **Then Count**: Check row count and data size
3. **Then Profile**: Look at data distribution
4. **Then Analyze**: Ask specific analytical questions

## Output Format

Results are displayed in the REPL with:

- **Green text**: Successful queries
- **Red text**: Errors or warnings
- **SQL shown**: The generated SQL (for transparency)
- **Formatted tables**: When displaying results

## Saving Results

Results are automatically logged to:

```
.lakeforge/
├── report-<session-id>/
│   ├── schema.json          # Table schema
│   ├── profile.json         # Data profile (if --profile)
│   ├── qa-log.jsonl         # Q&A session log
│   └── report.html          # HTML report (if generated)
```

## Next Steps

- Read [API.md](API.md) for programmatic usage
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## Getting Help

```bash
# Show command help
lakeforge --help
lakeforge inspect --help

# Report issues
# https://github.com/lakeforge/lakeforge/issues
```
