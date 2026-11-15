# Lakeforge Web App + Database Support - Quick Start (5 Minutes)

## ⚡ 5-Minute Setup

### Step 1: Install Drivers (1 minute)

```bash
cd ~/lakeforge
pip install mysql-connector-python psycopg2-binary pyodbc oracledb
```

### Step 2: Start Backend (1 minute)

```bash
cd backend

# Create .env file
echo "GROQ_API_KEY=your-key-here" > .env
echo "DEBUG=True" >> .env

# Install dependencies
pip install fastapi uvicorn pydantic-settings

# Start server
uvicorn main:app --reload --port 8000
```

✅ Backend running at: **http://localhost:8000**
✅ API docs at: **http://localhost:8000/docs**

### Step 3: Start Frontend (1 minute)

```bash
# In new terminal
cd frontend

# Create .env
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env

# Install & run
npm install && npm run dev
```

✅ Frontend running at: **http://localhost:5173**

### Step 4: Test with Sample Data (2 minutes)

```bash
# In yet another terminal
cd ~/lakeforge

# Test CLI with existing data
lakeforge inspect tests/data/customers.csv

# Or test with database
lakeforge inspect mysql://root@localhost/testdb
```

---

## 🚀 First Steps

### 1. Create a Test Database (Pick One)

#### Option A: SQLite (Easiest)

```bash
# Create test database
python << 'EOF'
import pandas as pd
import sqlite3

# Create sample data
df = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Emma'],
    'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'david@test.com', 'emma@test.com'],
    'department': ['Sales', 'Engineering', 'Sales', 'HR', 'Engineering']
})

# Save to SQLite
conn = sqlite3.connect('test.db')
df.to_sql('employees', conn, if_exists='replace', index=False)
conn.close()

print("✅ Created test.db with 'employees' table")
EOF
```

#### Option B: MySQL

```bash
# Install MySQL (macOS)
brew install mysql
brew services start mysql

# Create database
mysql -u root << 'EOF'
CREATE DATABASE lakeforge_test;
USE lakeforge_test;

CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    department VARCHAR(100)
);

INSERT INTO employees VALUES
(1, 'Alice', 'alice@test.com', 'Sales'),
(2, 'Bob', 'bob@test.com', 'Engineering'),
(3, 'Charlie', 'charlie@test.com', 'Sales'),
(4, 'David', 'david@test.com', 'HR'),
(5, 'Emma', 'emma@test.com', 'Engineering');

SELECT * FROM employees;
EOF
```

### 2. Connect via CLI

```bash
# SQLite
lakeforge inspect sqlite:///./test.db

# MySQL
lakeforge inspect mysql://root@localhost:3306/lakeforge_test

# PostgreSQL
lakeforge inspect postgres://user:password@localhost:5432/mydb

# SQL Server
lakeforge inspect mssql://sa:password@localhost:1433/master

# Oracle
lakeforge inspect oracle://system:password@localhost:1521/XE
```

### 3. Try in Web UI

1. Open **http://localhost:5173**
2. Go to **Settings** (bottom nav)
3. Click **"Add Data Source"**
4. Fill in:
   ```
   Name: My Test Database
   URI: mysql://root@localhost:3306/lakeforge_test
   Description: Test database
   ```
5. Click **"Test Connection"**
6. Go to **Inspector**
7. Select your source
8. Click **"Start Inspection"**

---

## 🔌 Database Connection Strings by Type

### Copy-Paste Templates

#### SQLite
```bash
# Local file
sqlite:///./mydata.db

# Absolute path
sqlite:////var/data/mydata.db
```

#### MySQL
```bash
# With password
mysql://username:password@localhost:3306/database_name

# Without password
mysql://username@localhost/database_name

# Remote server
mysql://user:pass@db.company.com:3306/production
```

#### PostgreSQL
```bash
# Basic
postgres://username:password@localhost:5432/database_name

# Without password
postgres://localhost/database_name

# Remote
postgres://user:pass@postgres.company.com:5432/prod_db
```

#### SQL Server
```bash
# Windows auth
mssql://localhost:1433/database_name

# SQL auth
mssql://sa:password@localhost:1433/master

# Remote
mssql://user:pass@sqlserver.company.com:1433/Analytics
```

#### Oracle
```bash
# SID
oracle://system:password@localhost:1521/XE

# Remote
oracle://user:pass@oracle.company.com:1521/PROD
```

---

## 📱 Using the Web App

### Dashboard
- Shows all connected data sources
- Quick statistics
- Recent activity

### Inspector
```
1. Select source → "Start Inspection"
2. View → "Schema" tab (column names, types)
3. View → "Profile" tab (statistics)
4. View → "Samples" tab (example rows)
```

### Q&A (Coming Soon)
```
1. Select source
2. Type question: "How many employees?"
3. See generated SQL
4. View results
```

### Settings
```
1. "Add Data Source" (MySQL, Postgres, etc.)
2. "Test Connection" (verify it works)
3. Use in Inspector
```

---

## 🔍 Example: Analyzing a MySQL Database

### Setup (5 min)

```bash
# 1. Start everything
# Terminal 1
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev

# Terminal 3 - Optional: test CLI
lakeforge inspect mysql://root@localhost/employees
```

### Using CLI

```bash
# Test connection
lakeforge inspect mysql://root@localhost:3306/employees

# With question
lakeforge inspect mysql://root@localhost:3306/employees \
  --ask "How many employees in Sales?"

# With profiling
lakeforge inspect mysql://root@localhost:3306/employees \
  --profile --verbose
```

### Using Web UI

1. Open **http://localhost:5173**
2. Click **Settings**
3. **Add Data Source**:
   - Name: `Production Employees`
   - URI: `mysql://root@localhost:3306/employees`
4. Click **Test Connection**
5. Go to **Inspector**
6. Select `Production Employees`
7. Click **Start Inspection**
8. Browse **Schema**, **Profile**, **Samples**

---

## 📊 Sample Data Files (Already Included)

```
tests/data/
├── customers.csv    (15 customers)
├── orders.csv       (20 orders)
├── products.csv     (15 products)
└── inventory.csv    (15 inventory records)
```

Test with any:
```bash
lakeforge inspect tests/data/customers.csv --profile
```

---

## 🐛 Quick Troubleshooting

### "Connection refused"
```bash
# Make sure database is running
# MySQL: brew services start mysql
# PostgreSQL: brew services start postgresql
# SQLite: Just needs file, no service
```

### "API not responding"
```bash
# Make sure backend is running
# Check: http://localhost:8000/health
# Should show: {"status": "healthy"}
```

### "Frontend won't load"
```bash
# Make sure frontend is running
# Check: http://localhost:5173
# Check terminal for build errors
# Run: npm install
```

### "Database driver not found"
```bash
# Install all drivers
pip install mysql-connector-python psycopg2-binary pyodbc oracledb
```

---

## ✨ What You Can Do Now

✅ Connect to **7 database types**
- MySQL, PostgreSQL, SQL Server, Oracle, SQLite, Databricks, S3

✅ **Import from DBeaver**
- Auto-detect saved connections

✅ **CLI or Web UI**
- Use whichever you prefer

✅ **Real-time profiling**
- Schema discovery, statistics, samples

✅ **Natural language Q&A** (via CLI)
- Ask questions, see generated SQL

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `WEB_APP_OVERVIEW.md` | Complete architecture overview |
| `WEB_APP_SETUP.md` | Detailed installation guide |
| `DATABASE_CONNECTORS_GUIDE.md` | Database-specific examples |
| `WEBAPP_IMPLEMENTATION_PLAN.md` | Architecture & roadmap |
| `README.md` | Project overview |
| `USAGE.md` | CLI usage guide |
| `API.md` | Python API reference |

---

## 🎯 Next: Feature Roadmap

### Completed ✅
- Database connectors (5 types)
- FastAPI backend foundation
- React frontend foundation
- API client & hooks
- DBeaver importer

### Coming Soon 🚧
- Q&A endpoints
- Report generation
- Charts & visualizations
- User authentication
- Advanced filtering
- Query history

### Planned 🔮
- Real-time dashboards
- Team collaboration
- Data lineage
- Advanced profiling
- ML-powered insights

---

## 💡 Pro Tips

### 1. Use Environment Variables
```bash
export GROQ_API_KEY="gsk_..."
export MYSQL_ROOT_PASSWORD="password"
```

### 2. Keep Terminals Open
```bash
# Terminal 1: Backend (stays running)
uvicorn main:app --reload

# Terminal 2: Frontend (stays running)
npm run dev

# Terminal 3: CLI (for testing)
lakeforge inspect ...
```

### 3. Check API Docs
Visit **http://localhost:8000/docs** for interactive API documentation

### 4. Use Verbose Mode
```bash
lakeforge inspect [URI] -v --profile
```

### 5. Start Small
Test with `tests/data/customers.csv` first before connecting to production databases

---

## 🚀 You're All Set!

You now have:
- ✅ Multi-database support (MySQL, PostgreSQL, SQLServer, Oracle, SQLite)
- ✅ Web application (FastAPI backend + React frontend)
- ✅ DBeaver integration
- ✅ CLI tool (still works as before)

**Questions?** Check the documentation files or open an issue on GitHub.

**Ready to explore?**
1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173

🎉 Happy data exploring!

---

## 📞 Support

- **Documentation**: See `.md` files in project root
- **Issues**: GitHub Issues tab
- **Community**: GitHub Discussions
- **Troubleshooting**: `TROUBLESHOOTING.md`
