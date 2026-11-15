# Lakeforge Database Connectors - Quick Reference

## 🚀 Getting Started

### Install Database Drivers

```bash
# All databases at once
pip install mysql-connector-python psycopg2-binary pyodbc oracledb
```

### Set Environment Variables

```bash
# LLM API Key (required)
export GROQ_API_KEY="gsk_..."

# Database credentials (optional, use in connection string instead)
export MYSQL_HOST="localhost"
export POSTGRES_PASSWORD="..."
```

---

## 📚 Database-Specific Examples

### 1. 🐘 PostgreSQL

#### CLI Usage
```bash
# Basic connection
lakeforge inspect postgres://user:password@localhost:5432/mydb

# With questions
lakeforge inspect postgres://localhost/mydb --ask "How many tables?"

# Verbose mode
lakeforge inspect postgres://localhost/mydb -v --profile
```

#### Web API
```bash
POST /api/sources
{
  "name": "My PostgreSQL Database",
  "uri": "postgres://user:password@localhost:5432/mydb",
  "tags": ["database", "production"],
  "description": "Production PostgreSQL server"
}
```

#### Connection String Format
```
postgres://[user[:password]@][host][:port][/database]

Examples:
- postgres://localhost/mydb
- postgres://user@host:5432/database
- postgres://user:pass@192.168.1.100:5432/prod_db
```

---

### 2. 🐬 MySQL / MariaDB

#### Installation
```bash
pip install mysql-connector-python
```

#### CLI Usage
```bash
# Basic connection
lakeforge inspect mysql://root:password@localhost:3306/mydb

# Local MySQL
lakeforge inspect mysql://root@localhost/mydb

# Remote MySQL
lakeforge inspect mysql://user:pass@db.company.com:3306/production

# With inspection options
lakeforge inspect mysql://localhost/mydb --profile --verbose
```

#### Web API
```bash
POST /api/sources
{
  "name": "Production MySQL",
  "uri": "mysql://user:password@mysql.company.com:3306/myapp",
  "description": "Customer application database"
}
```

#### Connection String Format
```
mysql://[user[:password]@][host][:port][/database]

Examples:
- mysql://root@localhost/testdb
- mysql://app_user:p@ssw0rd@db.example.com:3306/myapp
- mysql://localhost/database
```

#### Key Features
- ✅ Supports MySQL 5.7+ and MariaDB 10.3+
- ✅ Automatic charset detection (UTF-8)
- ✅ Connection pooling support
- ✅ Handles NULL values properly

---

### 3. 🪟 Microsoft SQL Server

#### Installation
```bash
pip install pyodbc
# Also requires ODBC driver installed (17 or 18)
```

#### Installing ODBC Driver

**Windows (Automatic with PyODBC):**
```bash
pip install pyodbc
# Will prompt to download driver
```

**macOS:**
```bash
brew install unixodbc
brew tap microsoft/mssql-release
brew install msodbcsql17
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo apt-add-repository https://packages.microsoft.com/ubuntu/20.04/prod
sudo apt-get install msodbcsql17
```

#### CLI Usage
```bash
# Basic connection
lakeforge inspect mssql://sa:password@localhost:1433/master

# Windows Authentication (if available)
lakeforge inspect mssql://localhost:1433/mydb

# With specific database
lakeforge inspect mssql://user:pass@sqlserver.company.com:1433/production
```

#### Web API
```bash
POST /api/sources
{
  "name": "SQL Server Production",
  "uri": "mssql://sa:Admin123@sqlserver.local:1433/Analytics",
  "tags": ["windows", "mssql"]
}
```

#### Connection String Format
```
mssql://[user[:password]@][server][:port][/database]

Examples:
- mssql://sa:password@localhost:1433/master
- mssql://domain\user@server/database
- mssql://sqlserver.company.com:1433/prod_db
```

#### Key Features
- ✅ Windows and SQL authentication
- ✅ Supports SQL Server 2016+
- ✅ Connection pooling
- ✅ Azure SQL Database compatible

---

### 4. 🦁 Oracle Database

#### Installation
```bash
pip install oracledb
# Or: pip install cx_Oracle (for older versions)
```

#### CLI Usage
```bash
# Basic connection (SID)
lakeforge inspect oracle://system:password@localhost:1521/XE

# Connection string with service name
lakeforge inspect oracle://system:password@oracle.company.com:1521/ORCL

# With verbose output
lakeforge inspect oracle://user@host:1521/PROD -v --profile
```

#### Web API
```bash
POST /api/sources
{
  "name": "Oracle Production",
  "uri": "oracle://system:password@oracle.db.com:1521/PROD",
  "description": "Main Oracle database",
  "tags": ["oracle", "production"]
}
```

#### Connection String Format
```
oracle://[user[:password]@][host][:port][/sid]

Examples:
- oracle://system:password@localhost:1521/XE
- oracle://user@oracledb.company.com:1521/ORCL
- oracle://schema:pass@192.168.1.50/orcl
```

#### Key Features
- ✅ Supports Oracle 11g+
- ✅ SID and service name support
- ✅ Automatic connection tuning
- ✅ PL/SQL support (future)

---

### 5. 📦 SQLite

#### CLI Usage
```bash
# Local SQLite file
lakeforge inspect sqlite:///./mydata.db

# Absolute path
lakeforge inspect sqlite:////var/data/mydata.db

# Windows path
lakeforge inspect sqlite:///C:/Users/data/mydata.db

# In-memory (testing)
lakeforge inspect sqlite://:memory:
```

#### Web API
```bash
POST /api/sources
{
  "name": "Local SQLite Database",
  "uri": "sqlite:////home/user/mydata.db",
  "description": "Local development database"
}
```

#### Connection String Format
```
sqlite://[/path/to/database.db]

Examples:
- sqlite:////data/mydata.db
- sqlite:///./local.db
- sqlite://:memory:  (in-memory)
```

#### Key Features
- ✅ No server required
- ✅ Perfect for development/testing
- ✅ Full SQL support
- ✅ Fast local queries

#### Creating SQLite Database
```bash
# From CSV
python -c "
import pandas as pd
df = pd.read_csv('data.csv')
df.to_sql('mytable', 'sqlite:///mydata.db', if_exists='replace')
"

# Then inspect
lakeforge inspect sqlite:///mydata.db
```

---

### 6. 📊 Databricks SQL Warehouse

#### Installation
```bash
pip install databricks-sql-connector
```

#### Setup
```bash
export DATABRICKS_HOST="workspace-name.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

#### CLI Usage
```bash
# Format: databricks://workspace/catalog/schema/table
lakeforge inspect databricks://my-workspace/main/default/customers

# With profiling
lakeforge inspect databricks://prod-workspace/sales_db/public/orders --profile
```

#### Connection String Format
```
databricks://workspace_name/catalog/schema/table

Examples:
- databricks://prod/main/default/customers
- databricks://analytics/sales_db/public/transactions
```

---

### 7. ☁️ AWS S3 + DuckDB

#### CLI Usage
```bash
# S3 Parquet file
lakeforge inspect s3://my-bucket/data/customers.parquet

# S3 CSV file
lakeforge inspect s3://company-data/reports/sales-2024.csv

# Local Parquet
lakeforge inspect data.parquet

# Local CSV
lakeforge inspect data.csv
```

#### Setup for S3
```bash
# AWS credentials
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

---

## 🎯 DBeaver Integration

### List Saved Connections

```bash
python -c "
from lakeforge.sources.dbeaver_importer import DBeaverProfileImporter

# List all connections
connections = DBeaverProfileImporter.list_connections()
for conn_id, conn_info in connections.items():
    print(f'{conn_id}: {conn_info[\"name\"]} ({conn_info[\"driver\"]})')
"
```

### Import a Connection

```bash
python -c "
from lakeforge.sources.dbeaver_importer import DBeaverProfileImporter

# Import by name
imported = DBeaverProfileImporter.import_connection('my-postgres-db')
print(f'Name: {imported[\"name\"]}')
print(f'Driver: {imported[\"driver\"]}')
print(f'URI: {imported[\"uri\"]}')
"
```

### Use in Lakeforge

```bash
python -c "
from lakeforge.sources.dbeaver_importer import DBeaverProfileImporter
from lakeforge.sources.registry import get_connector

# Get URI from DBeaver
imported = DBeaverProfileImporter.import_connection('production-db')
uri = imported['uri']

# Use with Lakeforge
connector = get_connector(uri)
connector.connect()
tables = connector.list_tables()
print(f'Found {len(tables)} tables')
"
```

---

## 🔧 Common Tasks

### Test Connection Before Inspection

```bash
# CLI with test flag
lakeforge inspect mysql://localhost/db --ask "SELECT 1"

# Or via Web API
POST /api/sources/src_1/test
Response: {
  "status": "success",
  "message": "Connected successfully, found 5 tables",
  "table_count": 5
}
```

### Inspect Specific Table

```bash
# PostgreSQL
lakeforge inspect postgres://localhost/mydb --ask "Show schema for customers table"

# MySQL
lakeforge inspect mysql://root@localhost/mydb --ask "How many rows in orders?"
```

### Generate Profile Report

```bash
# All databases support profiling
lakeforge inspect [YOUR_CONNECTION_STRING] --profile --verbose
```

### Export Results

```bash
# CLI output to .lakeforge/report-*/
lakeforge inspect data.csv --ask "SELECT * LIMIT 100"

# Results in: .lakeforge/report-abc123/qa.log.jsonl

# Web API export (future)
POST /api/reports
{
  "source_id": "src_1",
  "title": "Customer Analysis",
  "format": "pdf"
}
```

---

## ⚠️ Troubleshooting

### Connection Refused

```bash
# Check if server is running
# MySQL: mysql -u root -p
# PostgreSQL: psql -U postgres
# SQL Server: sqlcmd -S localhost -U sa
# Oracle: sqlplus system/password@XE
# SQLite: sqlite3 mydata.db

# Check firewall
# Make sure port is accessible
# Add to firewall rules if needed
```

### Authentication Failed

```bash
# Verify credentials
# Check username and password
# Verify database/schema name
# Check character encoding (especially for MySQL)

# Test manually
mysql -u user -p -h hostname database
```

### Driver Not Installed

```bash
# Install all drivers
pip install mysql-connector-python psycopg2-binary pyodbc oracledb

# Or specific driver
pip install mysql-connector-python  # MySQL
pip install psycopg2-binary        # PostgreSQL
pip install pyodbc                 # SQL Server
pip install oracledb               # Oracle
```

### Timeout or Slow Queries

```bash
# Increase timeout in CLI
lakeforge inspect [URI] --timeout 120

# Or in Web API
POST /api/inspect/start
{
  "source_id": "src_1",
  "timeout_seconds": 120
}

# Optimize queries
# Add WHERE clauses to limit results
# Use LIMIT in custom queries
# Create indexes on frequently queried columns
```

---

## 📊 Connection Format Summary

| Database | Install | URI Format | Port |
|----------|---------|------------|------|
| PostgreSQL | `psycopg2-binary` | `postgres://user:pass@host/db` | 5432 |
| MySQL | `mysql-connector-python` | `mysql://user:pass@host/db` | 3306 |
| SQL Server | `pyodbc` | `mssql://user:pass@host/db` | 1433 |
| Oracle | `oracledb` | `oracle://user:pass@host/sid` | 1521 |
| SQLite | Built-in | `sqlite:///path/to/db.db` | N/A |
| Databricks | `databricks-sql-connector` | `databricks://ws/catalog/schema/table` | N/A |
| S3 | Built-in (DuckDB) | `s3://bucket/key` | N/A |

---

## 🎓 Next Steps

1. **Install drivers**: `pip install mysql-connector-python psycopg2-binary pyodbc oracledb`

2. **Test a connection**:
   ```bash
   lakeforge inspect mysql://root@localhost/test_db
   ```

3. **Try the web app**:
   ```bash
   # Backend
   cd backend && uvicorn main:app --reload
   
   # Frontend
   cd frontend && npm run dev
   ```

4. **Add sources in web UI**: Go to http://localhost:5173/settings

---

## 📖 Additional Resources

- PostgreSQL: https://www.postgresql.org/docs/
- MySQL: https://dev.mysql.com/doc/
- SQL Server: https://learn.microsoft.com/en-us/sql/
- Oracle: https://docs.oracle.com/
- SQLite: https://www.sqlite.org/docs.html
- Databricks: https://docs.databricks.com/

---

**Need help?** Check `TROUBLESHOOTING.md` or `WEB_APP_SETUP.md`

**Questions about specific database?** See the section above or open an issue on GitHub.

🚀 Happy querying!
