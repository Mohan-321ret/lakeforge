# Lakeforge Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### "ModuleNotFoundError: No module named 'lakeforge'"

**Cause**: Lakeforge not installed or installed in different Python environment.

**Solution**:
```bash
# Verify installation
python -m pip list | grep lakeforge

# Reinstall if needed
pip install --upgrade lakeforge

# Or from source
git clone https://github.com/lakeforge/lakeforge.git
cd lakeforge
pip install -e .
```

#### "error: Microsoft Visual C++ 14.0 or greater is required" (Windows)

**Cause**: Some dependencies require C++ compiler.

**Solution**:
```powershell
# Install build tools
pip install --upgrade setuptools wheel

# Or download from https://visualstudio.microsoft.com/downloads/
# Install "Desktop development with C++"
```

#### "No module named 'databricks'" or "No module named 'psycopg2'"

**Cause**: Optional dependencies not installed.

**Solution**:
```bash
# Install specific optional dependencies
pip install databricks-sql-connector
pip install psycopg2-binary
pip install pdfplumber

# Or install all
pip install lakeforge[databricks,postgres,pdf,semantic]
```

### Authentication Issues

#### "Groq API key not found. Set GROQ_API_KEY environment variable"

**Cause**: LLM API key not configured.

**Solution**:
```bash
# Get your API key from https://console.groq.com

# Set environment variable
export GROQ_API_KEY="your-api-key"

# Verify
echo $GROQ_API_KEY

# On Windows PowerShell
$env:GROQ_API_KEY="your-api-key"
$env:GROQ_API_KEY  # Verify
```

#### "DATABRICKS_TOKEN env var not set" or "DATABRICKS_HOST not set"

**Cause**: Missing Databricks credentials.

**Solution**:
```bash
# Get token from Databricks workspace settings

export DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."

# Or use connection parameters
lakeforge inspect "databricks://workspace/catalog/schema/table"

# Verify
lakeforge inspect "databricks://workspace/default/public/users" -v
```

#### "psycopg2.OperationalError: could not connect to server"

**Cause**: PostgreSQL connection failed.

**Solution**:
```bash
# Verify PostgreSQL is running
psql -U username -h localhost -d dbname

# Set connection string
export POSTGRES_CONNECTION_STRING="postgresql://user:password@localhost:5432/dbname"

# Test connection
lakeforge inspect "postgres://user:pass@localhost:5432/dbname/public" -v

# Check firewall
# - Verify host is accessible: ping hostname
# - Verify port is open: nc -zv hostname 5432
# - Check PostgreSQL listen address in postgresql.conf
```

#### "AWS access denied" or "Unable to locate credentials"

**Cause**: AWS credentials not configured.

**Solution**:
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"

# Verify access
aws s3 ls s3://your-bucket/
```

### File and Source Issues

#### "FileNotFoundError: [Errno 2] No such file or directory"

**Cause**: File doesn't exist or wrong path.

**Solution**:
```bash
# Use absolute path
lakeforge inspect /absolute/path/to/data.csv

# Verify file exists
ls -la /path/to/data.csv  # Linux/macOS
dir "C:\path\to\data.csv" # Windows

# Use relative path from current directory
cd ~/data
lakeforge inspect customers.csv
```

#### "Unsupported file format: .xlsx"

**Cause**: Excel files not directly supported (only CSV, Parquet, JSON).

**Solution**:
```bash
# Convert to CSV first
python -c "
import pandas as pd
df = pd.read_excel('data.xlsx')
df.to_csv('data.csv', index=False)
"

# Then analyze
lakeforge inspect data.csv

# Or use pandas for in-memory analysis
python -c "
import pandas as pd
from lakeforge.session import QASession

df = pd.read_excel('data.xlsx')
df.to_csv('temp.csv', index=False)
session = QASession(source='temp.csv')
# ... ask questions ...
"
```

#### "Connection refused" for S3 or remote URLs

**Cause**: Network/firewall issue or incorrect URL.

**Solution**:
```bash
# Verify URL format
s3://bucket-name/path/to/file.parquet

# Test connectivity
curl -I https://s3.amazonaws.com/bucket-name/file.parquet

# Use verbose mode
lakeforge inspect s3://bucket/file.csv -v

# Check firewall/VPN settings
```

### Query and Performance Issues

#### "Query execution timed out"

**Cause**: Query taking too long (default 30 seconds).

**Solution**:
```bash
# Increase timeout
lakeforge inspect data.csv --timeout 120

# For one-shot
lakeforge inspect data.csv -q "Count(*)" --timeout 60

# Optimize query
# - Use LIMIT to reduce result size
# - Filter WHERE clause before aggregation
# - Use appropriate indexes on database
```

#### "Too many results. Returned 10000 rows. Query may have been truncated"

**Cause**: Result limit exceeded (default 10,000 rows).

**Solution**:
```bash
# Ask for filtered results
> Show me first 100 rows
> Show me customers from USA only

# Or use LIMIT in custom SQL
> SELECT * FROM table WHERE status='active' LIMIT 100

# Modify config to increase limit (lakeforge-config.yaml)
max_result_rows: 50000
```

#### "DuckDB CatalogException: Table with name X does not exist"

**Cause**: Incorrect table name or table not loaded.

**Solution**:
```python
# Get actual table name
connector = get_connector("data.csv")
tables = connector.list_tables()
print(tables)  # Use this name

# DuckDB creates hash-based names for files
# e.g., "data_123456" instead of "data"
```

#### "Memory error" or "out of memory"

**Cause**: Dataset too large for available RAM.

**Solution**:
```bash
# 1. Use filtering
lakeforge inspect large_dataset.csv -q "Count(*) WHERE status='active'"

# 2. Process in batches
# Split data first:
split -l 1000000 large_file.csv chunk_

# 3. Use Parquet with compression
python -c "
import pandas as pd
df = pd.read_csv('large.csv', chunksize=100000)
for i, chunk in enumerate(df):
    chunk.to_parquet(f'chunk_{i}.parquet')
"

# 4. Increase available RAM
# Close other applications
# Use streaming if available

# 5. Use database instead of file
# Load data into PostgreSQL/Databricks first
```

### LLM and Generation Issues

#### "Failed to generate SQL" or "Empty response from LLM"

**Cause**: LLM API error or quality issue.

**Solution**:
```bash
# 1. Check API key
echo $GROQ_API_KEY

# 2. Use verbose mode to see generated SQL
lakeforge inspect data.csv -v

# 3. Check question clarity
# Instead of: "Analyze the data"
# Use: "How many customers are active?"

# 4. Check network connectivity
curl https://api.groq.com/health

# 5. Check rate limits
# Groq API has rate limits; wait and retry
```

#### "Generated SQL is invalid"

**Cause**: LLM generated incorrect SQL syntax.

**Solution**:
```bash
# 1. Check the error message
# The --verbose flag shows generated SQL

# 2. Rephrase the question more specifically
# Bad: "Show me data"
# Good: "List all customers from USA with active status"

# 3. Provide schema information
# Ask schema first to help LLM
> What is the schema?

# 4. Use simpler questions
# Break complex queries into smaller ones
```

### Configuration Issues

#### "Config file not found"

**Cause**: Wrong path to config file.

**Solution**:
```bash
# Specify full path
lakeforge inspect data.csv --config /full/path/lakeforge-config.yaml

# Or relative to current directory
lakeforge inspect data.csv --config ./config.yaml

# Create default config
cat > lakeforge-config.yaml << EOF
llm_provider: groq
log_level: INFO
max_query_timeout_sec: 60
output_dir: .lakeforge/
EOF
```

#### "Invalid YAML configuration"

**Cause**: YAML syntax error in config file.

**Solution**:
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check formatting
# - Use spaces not tabs
# - Proper indentation (2 spaces)
# - Quotes around values with special characters

# Example valid config
cat > lakeforge-config.yaml << EOF
llm_provider: "groq"
log_level: "INFO"
max_query_timeout_sec: 60
max_result_rows: 10000
output_dir: ".lakeforge/"
EOF
```

### Platform-Specific Issues

#### Windows: "long path error" or "filename too long"

**Cause**: Windows path length limit (260 characters).

**Solution**:
```powershell
# Enable long paths in Windows 10/11
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or use shorter paths
cd C:\data
lakeforge inspect customers.csv

# Or use UNC paths
lakeforge inspect "\\server\share\data.csv"
```

#### macOS: "permission denied" error

**Cause**: File permissions or security restrictions.

**Solution**:
```bash
# Fix file permissions
chmod +r data.csv

# Check file ownership
ls -la data.csv

# Allow Python in Security & Privacy settings
# System Settings > Security & Privacy > Developer Tools
```

#### Linux: "port already in use" (if using as server)

**Cause**: Another process using the port.

**Solution**:
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>

# Use different port
export LAKEFORGE_PORT=8001
```

### Docker Issues

#### "Docker build fails: "Could not build wheels for databricks-sql-connector"

**Solution**:
```dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install lakeforge[databricks,postgres]
```

#### "No such file or directory" in Docker

**Cause**: Data not mounted into container.

**Solution**:
```bash
# Mount data directory
docker run -it \
  -v /host/path/data:/app/data \
  -e GROQ_API_KEY=your-key \
  lakeforge:latest inspect /app/data/file.csv
```

## Getting Help

1. **Check logs**: Look in `.lakeforge/` directory for logs
2. **Enable verbose mode**: Use `--verbose` or `-v` flag
3. **Search issues**: https://github.com/lakeforge/lakeforge/issues
4. **Check documentation**: See README.md, USAGE.md, API.md
5. **File new issue**: https://github.com/lakeforge/lakeforge/issues/new

When reporting issues:
- Include Python version: `python --version`
- Include Lakeforge version: `lakeforge --version`
- Include error message and full stack trace
- Include command that failed: `lakeforge inspect ... -v`
- Include relevant logs from `.lakeforge/`

## Performance Tuning

### For Large Files

```bash
# 1. Convert to Parquet (faster than CSV)
python << EOF
import pandas as pd
df = pd.read_csv('large_file.csv')
df.to_parquet('large_file.parquet')
EOF

lakeforge inspect large_file.parquet

# 2. Use database for very large files
# Load into PostgreSQL first, then connect
psql mydb < large_file.sql
lakeforge inspect postgres://localhost/mydb/public/my_table

# 3. Process in chunks
# Ask specific questions with filters
lakeforge inspect data.csv -q "Count(*) WHERE year=2024"
```

### For Remote Sources

```bash
# Use --verbose to see timing
lakeforge inspect s3://bucket/file.parquet -v

# Reduce result size
lakeforge inspect databricks://... -q "Show 10 rows" --timeout 60
```

## Still Having Issues?

1. Read INSTALL.md for setup issues
2. Read USAGE.md for usage questions
3. Read API.md for programming questions
4. Open issue on GitHub with detailed information
