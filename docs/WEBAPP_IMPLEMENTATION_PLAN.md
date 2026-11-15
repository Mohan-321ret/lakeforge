# Lakeforge Web Application - Implementation Plan

## Phase A: Enhanced Database Connectors

### Current Status
- ✅ DuckDB (CSV, Parquet, JSON local files)
- ✅ PostgreSQL
- ✅ Databricks

### Phase A Deliverables (New Connectors)
- [ ] MySQL/MariaDB connector
- [ ] Microsoft SQL Server connector
- [ ] Oracle Database connector
- [ ] SQLite connector
- [ ] DBeaver profile importer

### Architecture
```
sources/
├── base.py                  # BaseConnector (already exists)
├── duckdb_files.py         # ✅ Existing
├── postgres.py             # ✅ Existing
├── databricks_sql.py       # ✅ Existing
├── mysql.py               # NEW
├── sqlserver.py           # NEW
├── oracle.py              # NEW
├── sqlite.py              # NEW
├── dbeaver_importer.py    # NEW - Import DBeaver profiles
└── registry.py            # Updated to handle all types
```

---

## Phase B: FastAPI Backend

### Architecture
```
backend/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration
├── dependencies.py        # Dependency injection
│
├── routes/
│   ├── __init__.py
│   ├── sources.py        # Source management endpoints
│   ├── inspector.py      # Inspection endpoints
│   ├── qa.py            # Q&A endpoints
│   └── reports.py       # Report generation
│
├── models/
│   ├── schemas.py       # Pydantic schemas for API
│   └── database.py      # SQLAlchemy models
│
├── services/
│   ├── inspection.py    # Inspection service
│   ├── qa_service.py    # Q&A service
│   └── report_service.py # Report generation
│
└── utils/
    ├── cache.py         # Caching layer
    └── logging.py       # Logging setup
```

### Key Endpoints
```
POST   /api/sources              # Add new data source
GET    /api/sources              # List sources
DELETE /api/sources/{id}         # Remove source

POST   /api/inspect              # Start inspection
GET    /api/inspect/{session_id} # Get inspection status
GET    /api/inspect/{session_id}/schema
GET    /api/inspect/{session_id}/profile
GET    /api/inspect/{session_id}/samples

POST   /api/qa                   # Ask question
GET    /api/qa/{session_id}/history

GET    /api/reports              # List reports
GET    /api/reports/{id}         # Get report
```

---

## Phase C: React Frontend

### Architecture
```
frontend/
├── public/
├── src/
│   ├── App.jsx
│   ├── index.css
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx       # Main dashboard
│   │   ├── Inspector.jsx       # Inspection UI
│   │   ├── QA.jsx             # Q&A interface
│   │   ├── Reports.jsx        # Reports list
│   │   └── Settings.jsx       # Source management
│   │
│   ├── components/
│   │   ├── SchemaExplorer.jsx
│   │   ├── DataSamples.jsx
│   │   ├── QueryBuilder.jsx
│   │   ├── ResultsTable.jsx
│   │   └── ChartCard.jsx
│   │
│   ├── services/
│   │   ├── api.js            # API client
│   │   └── websocket.js      # WebSocket for real-time
│   │
│   ├── hooks/
│   │   ├── useInspection.js
│   │   └── useQuery.js
│   │
│   └── context/
│       └── AppContext.js     # Global state
│
├── package.json
├── vite.config.js
└── tailwind.config.js
```

### Key Pages
- **Dashboard**: Overview of sources, recent reports, quick stats
- **Inspector**: File/DB upload, schema discovery, profiling
- **Q&A**: Ask questions, see generated SQL, view results
- **Reports**: Saved reports, export options, sharing
- **Settings**: Manage connections, API keys, preferences

---

## Phase D: Dashboard & Visualization

### Features
- Interactive charts (Chart.js, Recharts)
- Data distribution visualizations
- Query history and saved queries
- Report generation and export (PDF, Excel)
- Real-time profiling progress
- Cached results for performance

---

## Implementation Order

1. **Week 1**: Phase A (Database Connectors)
   - MySQL connector + tests
   - SQLServer connector + tests
   - Oracle connector + tests
   - SQLite connector + tests
   - DBeaver importer + tests

2. **Week 2**: Phase B (FastAPI Backend)
   - FastAPI setup with project structure
   - Source management endpoints
   - Inspection endpoints
   - Q&A endpoints
   - Database models for sessions/reports

3. **Week 3**: Phase C (React Frontend)
   - Vite + React setup
   - Page layouts and navigation
   - API integration
   - Form handling for source connections

4. **Week 4**: Phase D (Dashboards & Polish)
   - Visualizations and charts
   - Report generation
   - Export functionality
   - Testing and deployment

---

## Tech Stack

### Backend
- **Framework**: FastAPI (async, modern Python)
- **Database**: SQLAlchemy + PostgreSQL (sessions, reports)
- **Queue**: Celery (optional, for long-running inspections)
- **Async**: asyncio, aiohttp

### Frontend
- **Framework**: React 18
- **Build**: Vite
- **UI Library**: Tailwind CSS
- **Charts**: Recharts or Chart.js
- **State**: Context API + React Query
- **Forms**: React Hook Form

### Deployment
- **Backend**: Docker + Gunicorn/Uvicorn
- **Frontend**: Docker + Nginx
- **Database**: PostgreSQL
- **Optional**: AWS/GCP/Azure cloud deployment

---

## Dependencies to Add

### Backend
```toml
# FastAPI stack
fastapi = "^0.104.0"
uvicorn[standard] = "^0.24.0"
pydantic-settings = "^2.0.0"
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
python-multipart = "^0.0.6"
aiofiles = "^23.2.0"

# Database drivers
mysql-connector-python = "^8.1.0"
pyodbc = "^4.0.0"  # SQLServer
oracledb = "^1.4.0"

# DBeaver support
configobj = "^5.0.8"
```

### Frontend
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "vite": "^5.0.0",
  "axios": "^1.6.0",
  "react-hook-form": "^7.48.0",
  "recharts": "^2.10.0",
  "tailwindcss": "^3.3.0"
}
```

---

## Migration Path for Existing Users

✅ CLI stays functional
✅ Web app uses same Lakeforge core engine
✅ Reports compatible between CLI and Web
✅ Can use both simultaneously

---

## Success Metrics

- [ ] All 4 new database connectors working
- [ ] FastAPI backend with 20+ endpoints
- [ ] React frontend with 5+ main pages
- [ ] Dashboard with real-time updates
- [ ] All tests passing (target: 150+ tests)
- [ ] Docker deployment working
- [ ] Documentation updated
