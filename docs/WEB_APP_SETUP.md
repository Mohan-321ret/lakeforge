# Lakeforge Web Application - Setup & Installation Guide

## 🎯 Overview

The Lakeforge web application transforms the CLI tool into a full-stack web platform with:

- **Backend**: FastAPI REST API with PostgreSQL
- **Frontend**: React 18 web interface
- **Multi-database support**: MySQL, PostgreSQL, SQLServer, Oracle, SQLite, Databricks, S3
- **Real-time inspection**: Live schema discovery, profiling, and Q&A
- **Dashboard**: Analytics and report generation
- **DBeaver integration**: Import saved connections directly

---

## 📋 Prerequisites

### System Requirements
- Python 3.11+
- Node.js 18+
- npm or yarn
- Docker (optional, for deployment)

### Database (Production)
- PostgreSQL 12+ (for storing sessions and reports)

### API Keys
- Groq API key (for LLM): https://console.groq.com

---

## 🚀 Quick Start

### 1. Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/yourusername/lakeforge
cd lakeforge

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,mysql,postgres,databricks]"
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your-api-key-here
DATABASE_URL=sqlite:///./lakeforge.db
LLM_MODEL=mixtral-8x7b-32768
DEBUG=True
EOF

# Install FastAPI dependencies
pip install fastapi uvicorn pydantic-settings

# Run backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**
API docs: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Create .env file
cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000/api
EOF

# Install Node dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:5173**

---

## 📦 Installation - Detailed Steps

### Backend Installation

#### Step 1: Install Database Drivers

```bash
# MySQL
pip install mysql-connector-python

# PostgreSQL
pip install psycopg2-binary

# SQL Server
pip install pyodbc

# Oracle
pip install oracledb

# All at once
pip install mysql-connector-python psycopg2-binary pyodbc oracledb
```

#### Step 2: Database Setup

For production, use PostgreSQL:

```bash
# Install PostgreSQL (macOS with Homebrew)
brew install postgresql
brew services start postgresql

# Or with Docker
docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres

# Create database
createdb lakeforge

# Update .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/lakeforge
```

#### Step 3: Run Migrations (When Ready)

```bash
# Create tables
# (Alembic setup - to be added)
```

#### Step 4: Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend Installation

#### Step 1: Create React Project

```bash
cd frontend

# Already set up with:
# - React 18
# - Vite
# - React Router
# - Tailwind CSS
# - React Hook Form
```

#### Step 2: Install Dependencies

```bash
npm install
```

#### Step 3: Configure Environment

```bash
# .env file
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
```

#### Step 4: Start Dev Server

```bash
npm run dev
```

---

## 🗄️ Database Connectors - Usage Examples

### PostgreSQL

```bash
# From CLI
lakeforge inspect postgres://user:password@localhost:5432/mydb

# From Web UI
POST /api/sources
{
  "name": "Production DB",
  "uri": "postgres://user:password@localhost:5432/mydb"
}
```

### MySQL

```bash
# From CLI
lakeforge inspect mysql://root:password@localhost:3306/mydb

# From Web UI
POST /api/sources
{
  "name": "MySQL Server",
  "uri": "mysql://root:password@localhost:3306/mydb"
}
```

### SQL Server

```bash
# From CLI
lakeforge inspect mssql://sa:password@localhost:1433/master

# From Web UI
POST /api/sources
{
  "name": "SQL Server",
  "uri": "mssql://sa:password@localhost:1433/master"
}
```

### Oracle

```bash
# From CLI
lakeforge inspect oracle://system:password@localhost:1521/XE

# From Web UI
POST /api/sources
{
  "name": "Oracle DB",
  "uri": "oracle://system:password@localhost:1521/XE"
}
```

### SQLite

```bash
# From CLI
lakeforge inspect sqlite:///./mydata.db

# From Web UI
POST /api/sources
{
  "name": "SQLite Database",
  "uri": "sqlite:////path/to/database.db"
}
```

### DBeaver Integration

```bash
# Import DBeaver connections
python -c "
from lakeforge.sources.dbeaver_importer import DBeaverProfileImporter

# List available connections
connections = DBeaverProfileImporter.list_connections()
for conn_id, conn in connections.items():
    print(f'{conn_id}: {conn[\"name\"]} ({conn[\"driver\"]})')

# Import a connection
imported = DBeaverProfileImporter.import_connection('my-postgres-db')
print(imported['uri'])
"
```

---

## 🌐 Web Application Features

### Pages

#### Dashboard
- Overview statistics (sources, reports, sessions)
- Recent sources quick access
- Quick links to popular features

#### Inspector
- Upload CSV/Parquet files or enter database URI
- Real-time schema discovery
- Data profiling with statistics
- PII detection and masking
- Sample data viewing

#### Q&A
- Natural language questions
- Generated SQL display
- Results table with filtering/sorting
- Query history

#### Reports
- Generated reports list
- Download options (PDF, Excel, JSON)
- Report sharing
- Saved queries

#### Settings
- Data source management
- API configuration
- User preferences
- DBeaver integration

---

## 🔗 API Endpoints

### Sources
```
POST   /api/sources              # Create source
GET    /api/sources              # List sources
GET    /api/sources/{id}         # Get source details
DELETE /api/sources/{id}         # Delete source
POST   /api/sources/{id}/test    # Test connection
```

### Inspection
```
POST   /api/inspect/start        # Start inspection
GET    /api/inspect/{sid}/status # Get status
GET    /api/inspect/{sid}/schema # Get schema
GET    /api/inspect/{sid}/profile # Get profile
GET    /api/inspect/{sid}/samples # Get samples
```

### Q&A
```
POST   /api/qa                   # Ask question
GET    /api/qa/{sid}/history     # Get history
```

### Reports
```
POST   /api/reports              # Generate report
GET    /api/reports              # List reports
GET    /api/reports/{id}         # Get report
DELETE /api/reports/{id}         # Delete report
```

---

## 🐳 Docker Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: lakeforge
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/lakeforge
      GROQ_API_KEY: ${GROQ_API_KEY}
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000/api

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run pytest
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=backend/
```

### Frontend Tests

```bash
# Run Jest
npm test

# With coverage
npm run test:cov
```

---

## 🔒 Security Considerations

### Environment Variables

Never commit `.env` files. Always use environment variables for:
- API keys
- Database credentials
- Database URLs

### CORS Settings

Update `backend/main.py` for production:

```python
# Development (allow all)
allow_origins=["*"]

# Production (specify frontend URL)
allow_origins=["https://yourdomain.com"]
```

### Authentication (Future)

- JWT tokens for API
- User accounts and sessions
- Role-based access control

---

## 📊 Architecture Diagram

```
Frontend (React)
    ↓ (HTTP/WebSocket)
Backend API (FastAPI)
    ↓
┌─────────────────────────────┐
│  Connector Registry         │
│  ├── MySQL Connector        │
│  ├── PostgreSQL Connector   │
│  ├── SQLServer Connector    │
│  ├── Oracle Connector       │
│  ├── SQLite Connector       │
│  ├── Databricks Connector   │
│  └── DuckDB (Files)         │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  Lakeforge Core             │
│  ├── Schema Discovery       │
│  ├── Profiling              │
│  ├── PII Detection          │
│  ├── LLM Integration (Groq) │
│  └── Report Generation      │
└─────────────────────────────┘
    ↓
    Database (PostgreSQL)
```

---

## 🛠️ Troubleshooting

### Port Already in Use

```bash
# Backend (port 8000)
lsof -i :8000
kill -9 <PID>

# Frontend (port 5173)
lsof -i :5173
kill -9 <PID>
```

### CORS Issues

If frontend can't access backend:
1. Check API URL in `.env`
2. Verify backend CORS settings
3. Check network tab in browser DevTools

### Database Connection Errors

```bash
# Test connection
psql -U postgres -h localhost -d lakeforge

# Verify URL format
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### Missing Dependencies

```bash
# Reinstall all
pip install -e ".[dev,mysql,postgres,databricks]"
npm install
```

---

## 📚 Next Steps

1. **Run the application**
   - Backend: `uvicorn backend/main:app --reload`
   - Frontend: `npm run dev`

2. **Add a data source**
   - Use Settings page to add MySQL/PostgreSQL/etc connection
   - Or use CLI: `lakeforge inspect mysql://...`

3. **Inspect and analyze**
   - Upload CSV or connect to database
   - View schema, profile, and samples
   - Ask questions with natural language

4. **Generate reports**
   - Create reports with visualizations
   - Export to PDF/Excel
   - Share with team

---

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

---

## 📝 License

MIT License - See LICENSE file for details.

---

**Questions?** Check [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) or open an issue on GitHub.
