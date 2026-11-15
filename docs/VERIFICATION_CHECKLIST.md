# ✅ Lakeforge Web App Implementation Verification Checklist

## 🎯 PRE-FLIGHT CHECKLIST

Before you start, make sure you have:

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Node.js 16+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] At least one database available (MySQL, PostgreSQL, SQLite, SQL Server, or Oracle)
- [ ] 500MB disk space for dependencies

---

## 📦 DATABASE DRIVERS INSTALLATION

### Install All Drivers (Recommended)

```bash
cd ~/lakeforge
pip install mysql-connector-python psycopg2-binary pyodbc oracledb
```

### Verify Installation

```bash
python << 'EOF'
try:
    import mysql.connector
    print("✅ MySQL connector installed")
except:
    print("❌ MySQL connector missing")

try:
    import psycopg2
    print("✅ PostgreSQL driver installed")
except:
    print("❌ PostgreSQL driver missing")

try:
    import pyodbc
    print("✅ SQL Server driver installed")
except:
    print("❌ SQL Server driver missing")

try:
    import oracledb
    print("✅ Oracle driver installed")
except:
    print("❌ Oracle driver missing")

try:
    import sqlite3
    print("✅ SQLite installed (built-in)")
except:
    print("❌ SQLite missing (should not happen)")
EOF
```

**Expected Output:**
```
✅ MySQL connector installed
✅ PostgreSQL driver installed
✅ SQL Server driver installed
✅ Oracle driver installed
✅ SQLite installed (built-in)
```

---

## 🔌 DATABASE DRIVERS CHECKLIST

### ✅ SQLite (Built-in)
- [ ] Already included with Python
- [ ] No installation needed
- [ ] Test: Create `test.db` file

### ✅ MySQL
- [ ] `pip install mysql-connector-python`
- [ ] MySQL server running (or available)
- [ ] Test connection: `mysql -u root -p`

### ✅ PostgreSQL
- [ ] `pip install psycopg2-binary`
- [ ] PostgreSQL server available
- [ ] Test: `psql -U postgres`

### ✅ SQL Server
- [ ] `pip install pyodbc`
- [ ] ODBC Driver 17 or 18 installed
  - Windows: `py -m pip install pyodbc` (downloads driver)
  - macOS: `brew install unixodbc msodbcsql17`
  - Linux: Install from Microsoft repository
- [ ] SQL Server available

### ✅ Oracle
- [ ] `pip install oracledb`
- [ ] Oracle Database available
- [ ] Test: `sqlplus system/password@XE`

---

## 🚀 BACKEND SETUP CHECKLIST

### Step 1: Navigate to Backend Directory
```bash
cd backend
```
- [ ] You're in the `backend/` directory
- [ ] You see `main.py`, `config.py`, `models.py`, `routes/`, `services/`

### Step 2: Create Environment File
```bash
echo "GROQ_API_KEY=gsk_" > .env
echo "DEBUG=True" >> .env
```
- [ ] `.env` file created in `backend/`
- [ ] Contains `GROQ_API_KEY` (can be empty for now)
- [ ] Contains `DEBUG=True`

### Step 3: Install Backend Dependencies
```bash
pip install fastapi uvicorn pydantic-settings
```
- [ ] FastAPI installed
- [ ] Uvicorn installed
- [ ] Pydantic-settings installed

### Step 4: Start Backend Server
```bash
uvicorn main:app --reload --port 8000
```
- [ ] Server starts without errors
- [ ] Shows: `Application startup complete`
- [ ] Shows: `Uvicorn running on http://127.0.0.1:8000`

### Step 5: Verify Backend is Running
Open new terminal and test:
```bash
curl http://localhost:8000/health
```
- [ ] Returns: `{"status":"healthy","version":"0.1.0"}`
- [ ] No connection errors

### Step 6: Check API Documentation
Open in browser: `http://localhost:8000/docs`
- [ ] Swagger UI loads
- [ ] Lists all endpoints
- [ ] Can see `/api/sources`, `/api/inspect` endpoints

---

## 💻 FRONTEND SETUP CHECKLIST

### Step 1: Navigate to Frontend Directory
```bash
cd frontend
```
- [ ] You're in the `frontend/` directory
- [ ] You see `src/`, `public/`, `package.json`, `vite.config.js`

### Step 2: Create Environment File
```bash
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
```
- [ ] `.env` file created in `frontend/`
- [ ] Contains correct API URL

### Step 3: Install Frontend Dependencies
```bash
npm install
```
- [ ] Dependencies installed successfully
- [ ] No major warnings
- [ ] `node_modules/` folder created

### Step 4: Start Frontend Server
```bash
npm run dev
```
- [ ] Dev server starts without errors
- [ ] Shows: `Local: http://localhost:5173/`
- [ ] Shows: `ready in XXX ms`

### Step 5: Verify Frontend is Running
Open browser: `http://localhost:5173`
- [ ] Page loads
- [ ] Navbar visible with navigation links
- [ ] No console errors (press F12)
- [ ] Dashboard shows "Loading..." initially

### Step 6: Check API Connection
In browser console (F12):
```javascript
fetch('http://localhost:8000/api/sources')
  .then(r => r.json())
  .then(d => console.log(d))
```
- [ ] Returns empty array `[]` (no sources added yet)
- [ ] No CORS errors
- [ ] No network errors

---

## 🗄️ SAMPLE DATA SETUP

### Option A: SQLite (Easiest)

```bash
cd ~/lakeforge
python << 'EOF'
import pandas as pd
import sqlite3

# Create sample data
df = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Emma'],
    'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'david@test.com', 'emma@test.com'],
    'department': ['Sales', 'Engineering', 'Sales', 'HR', 'Engineering'],
    'salary': [50000, 75000, 55000, 60000, 70000]
})

# Save to SQLite
conn = sqlite3.connect('test_employees.db')
df.to_sql('employees', conn, if_exists='replace', index=False)
conn.close()

print("✅ Created test_employees.db")
EOF
```

- [ ] `test_employees.db` created
- [ ] No Python errors

### Option B: MySQL
```bash
mysql -u root << 'EOF'
CREATE DATABASE lakeforge_test;
USE lakeforge_test;

CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    department VARCHAR(100),
    salary INT
);

INSERT INTO employees VALUES
(1, 'Alice', 'alice@test.com', 'Sales', 50000),
(2, 'Bob', 'bob@test.com', 'Engineering', 75000),
(3, 'Charlie', 'charlie@test.com', 'Sales', 55000),
(4, 'David', 'david@test.com', 'HR', 60000),
(5, 'Emma', 'emma@test.com', 'Engineering', 70000);
EOF
```

- [ ] Database created
- [ ] Table created
- [ ] Data inserted

---

## 🧪 FUNCTIONALITY TESTS

### Test 1: CLI with Sample Data
```bash
cd ~/lakeforge
lakeforge inspect tests/data/customers.csv
```
- [ ] Command completes without errors
- [ ] Shows table information
- [ ] Output displays schema

### Test 2: CLI with SQLite
```bash
lakeforge inspect sqlite:///./test_employees.db
```
- [ ] Connects successfully
- [ ] Lists tables
- [ ] Shows employee count

### Test 3: CLI with MySQL
```bash
lakeforge inspect mysql://root@localhost:3306/lakeforge_test
```
- [ ] Connects successfully (if MySQL is running)
- [ ] Lists tables
- [ ] Shows employee data

### Test 4: Web UI - Add Source
1. Open `http://localhost:5173`
2. Click **Settings** (bottom nav)
3. Click **"Add Data Source"** (button)
4. Fill in:
   - Name: `Test SQLite`
   - URI: `sqlite:///./test_employees.db`
   - Description: `Test database`
5. Click **"Test Connection"**

- [ ] Connection test shows "✅ Success"
- [ ] Shows "Found X tables"
- [ ] Source added to list

### Test 5: Web UI - Inspect Data
1. Go to **Inspector** (top nav)
2. Select `Test SQLite` from dropdown
3. Click **"Start Inspection"**
4. Wait for completion

- [ ] Status shows "Completed"
- [ ] Schema tab shows tables
- [ ] Profile tab shows statistics
- [ ] Samples tab shows data rows

### Test 6: API Health Check
```bash
curl http://localhost:8000/health
```

- [ ] Returns: `{"status":"healthy"}`
- [ ] HTTP status 200

### Test 7: API Sources Endpoint
```bash
curl http://localhost:8000/api/sources
```

- [ ] Returns JSON array
- [ ] Contains your added sources
- [ ] HTTP status 200

### Test 8: DBeaver Importer (if DBeaver installed)
```bash
python << 'EOF'
from lakeforge.sources.dbeaver_importer import DBeaverProfileImporter

# Check if DBeaver is installed
try:
    connections = DBeaverProfileImporter.list_connections()
    print(f"✅ Found {len(connections)} DBeaver connections")
    for conn_id, info in list(connections.items())[:3]:
        print(f"   - {info['name']} ({info['driver']})")
except Exception as e:
    print(f"⚠️  DBeaver not configured: {e}")
EOF
```

- [ ] Shows DBeaver connections (if installed)
- [ ] No exceptions thrown
- [ ] Connection names displayed

---

## 🔍 VERIFICATION SUMMARY

### Core Components Status

#### Backend
- [ ] Server running on port 8000
- [ ] Health check responds
- [ ] API docs available at `/docs`
- [ ] Can connect to database

#### Frontend
- [ ] App running on port 5173
- [ ] Dashboard loads
- [ ] Can add data sources
- [ ] Can test connections

#### Database Connectors
- [ ] SQLite works
- [ ] MySQL works (if available)
- [ ] PostgreSQL works (if available)
- [ ] SQL Server works (if available)
- [ ] Oracle works (if available)

#### Documentation
- [ ] `QUICK_START_WEB_APP.md` exists
- [ ] `WEB_APP_OVERVIEW.md` exists
- [ ] `DATABASE_CONNECTORS_GUIDE.md` exists
- [ ] `START_HERE.txt` exists

---

## 🐛 TROUBLESHOOTING

### Port Already in Use

**Issue**: "Address already in use" when starting backend

```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn main:app --reload --port 8001
```

- [ ] Backend started on different port

### Database Connection Failed

**Issue**: "Connection refused" or "Authentication failed"

```bash
# Test database manually
mysql -u root -p              # MySQL
psql -U postgres              # PostgreSQL
sqlite3 test_employees.db     # SQLite

# Verify connection string format
# mysql://user:pass@host:port/database
# postgres://user:pass@host:port/database
```

- [ ] Verified database is running
- [ ] Verified credentials
- [ ] Connection string correct

### Frontend Won't Connect to Backend

**Issue**: API calls fail with CORS error

```bash
# Check .env file in frontend/
cat frontend/.env

# Should contain:
# REACT_APP_API_URL=http://localhost:8000/api

# Clear browser cache (Ctrl+Shift+Delete)
```

- [ ] `.env` file correct
- [ ] Backend running on port 8000
- [ ] Browser cache cleared

### Missing Database Driver

**Issue**: "Driver not installed" error

```bash
# Install all drivers
pip install mysql-connector-python psycopg2-binary pyodbc oracledb

# Or specific driver
pip install mysql-connector-python  # MySQL
```

- [ ] Attempted installation
- [ ] Verified with `python -c "import [driver]"`

---

## ✅ FINAL VERIFICATION

When all checks pass, you should be able to:

- [ ] Run CLI: `lakeforge inspect tests/data/customers.csv`
- [ ] Run Backend: `cd backend && uvicorn main:app --reload`
- [ ] Run Frontend: `cd frontend && npm run dev`
- [ ] Open Web UI: `http://localhost:5173`
- [ ] Add database source via UI
- [ ] Inspect database via web UI
- [ ] See schema and data in Inspector

---

## 📊 Success Metrics

✅ **All Complete When:**

| Component | Status | Check |
|-----------|--------|-------|
| Python Environment | ✅ | All drivers installed |
| Backend Server | ✅ | Running on port 8000 |
| Frontend Server | ✅ | Running on port 5173 |
| Sample Database | ✅ | SQLite or MySQL ready |
| CLI Works | ✅ | Can run lakeforge inspect |
| Web UI Works | ✅ | Dashboard loads |
| API Connection | ✅ | Frontend talks to backend |
| Database Connection | ✅ | Can add and test sources |
| Documentation | ✅ | All guides available |

---

## 🎉 YOU'RE READY!

When all checks are complete:

1. **Start exploring**: Add your databases
2. **Try features**: Inspect schemas and data
3. **Provide feedback**: Report issues or suggestions
4. **Contribute**: Help build new features

---

**Next Step**: Follow `QUICK_START_WEB_APP.md` for hands-on examples

**Questions?**: Check `TROUBLESHOOTING.md` or create a GitHub issue

🚀 **Happy exploring!**
