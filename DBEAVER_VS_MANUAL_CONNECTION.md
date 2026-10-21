# DBeaver vs Manual Connection - Complete Guide

## 🔄 How DBeaver Connection Works (Step-by-Step)

### The Full Flow:

```
1. User clicks "🔗 DBeaver" button
   ↓
2. Frontend calls: GET /api/dbeaver/connections
   ↓
3. Backend looks for DBeaver config file
   ├─ Windows: C:\Users\{USERNAME}\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\data-sources.json
   ├─ macOS: ~/Library/DBeaverData/workspace6/General/.dbeaver/data-sources.json
   └─ Linux: ~/.dbeaver4/General/.dbeaver/data-sources.json
   ↓
4. Backend reads data-sources.json
   └─ Extracts: connection names, drivers, host, port, database, user, password
   ↓
5. Backend returns list to Frontend
   [
     { id: "conn1", name: "Production DB", driver: "mysql", host: "prod.example.com", database: "myapp" },
     { id: "conn2", name: "Local DB", driver: "postgres", host: "localhost", database: "dev" }
   ]
   ↓
6. User selects a connection
   ↓
7. Frontend calls: POST /api/dbeaver/connections/{connection_id}
   ↓
8. Backend converts DBeaver connection to Lakeforge URI format
   Example:
   - DBeaver: { driver: "mysql", host: "prod.example.com", user: "admin", password: "pass", database: "myapp", port: 3306 }
   - Lakeforge URI: "mysql://admin:pass@prod.example.com:3306/myapp"
   ↓
9. Backend returns URI to Frontend
   { name: "Production DB", uri: "mysql://admin:pass@prod.example.com:3306/myapp", driver: "mysql" }
   ↓
10. Frontend creates a new source with this URI
    ↓
11. New source appears in Sources list
```

---

## 🎯 Why DBeaver Connection is Useful

### Advantages:

1. **No Manual Typing** ✅
   - Don't need to remember credentials
   - Don't need to manually construct URI
   - One-click import

2. **Reuses Existing Configuration** ✅
   - If you already use DBeaver, your connections are there
   - No duplication of credentials
   - Centralized connection management

3. **Automatic Format Conversion** ✅
   - DBeaver uses its own format
   - Lakeforge converts to standard database URIs
   - No manual conversion needed

4. **Less Error-Prone** ✅
   - No typos in connection string
   - No incorrect port numbers
   - No missing database names

---

## 🔧 Why Manual Connection Also Works

### When to Use Manual Connection:

1. **DBeaver is Not Installed** ✅
   - User doesn't have DBeaver
   - No DBeaver config file to read
   - Must manually enter connection string

2. **Connections Not Saved in DBeaver** ✅
   - Using DBeaver but connections are temporary
   - Want to add a new connection just for Lakeforge
   - Don't want to clutter DBeaver settings

3. **Database Not Saved in DBeaver** ✅
   - Quick connection to a one-time database
   - Testing a remote server
   - Ad-hoc inspection

4. **Custom Configuration** ✅
   - Need specific connection parameters
   - DBeaver connection doesn't have exact details needed
   - Want to modify host/port/credentials

---

## 📝 Manual Connection - How It Works

### Step-by-Step:

```
1. User goes to Settings page
   ↓
2. Clicks "+ Add Source" button
   ↓
3. Form appears with fields:
   - Source Name (what you call it in Lakeforge)
   - Database Type (dropdown with 7 options)
   - Connection URI (the actual connection string)
   - Description (optional)
   ↓
4. User selects Database Type
   └─ Automatically fills URI template based on type
      Example: Select "MySQL" → template becomes:
      "mysql://user:password@host:3306/database"
   ↓
5. User modifies URI with actual details
   Before: mysql://user:password@host:3306/database
   After:  mysql://admin:mypass@db.example.com:3306/myapp
   ↓
6. User clicks "Add Source"
   ↓
7. Backend validates URI by attempting connection
   ├─ Tries to connect to database
   ├─ Checks if URI is correct format
   └─ Returns success or error
   ↓
8. If successful → Source added to list
```

---

## 🆚 Comparison: DBeaver vs Manual

| Aspect | DBeaver | Manual |
|--------|---------|--------|
| **Setup Time** | 1 click | 2-3 minutes |
| **Requires DBeaver** | Yes | No |
| **Error Risk** | Low (auto-filled) | Medium (manual typing) |
| **Flexibility** | Only saved connections | Any database anywhere |
| **Best For** | Existing DBeaver users | New databases, non-DBeaver users |
| **Credentials Risk** | Reads from DBeaver config | You type them in |
| **Maintenance** | Auto-syncs with DBeaver | Manual updates needed |

---

## 🚨 Why DBeaver Connection Might Not Work

### Common Issues:

### 1. **DBeaver Not Installed**
```
Error: "Failed to load DBeaver connections"
Message: "DBeaver config not found"

Solution:
└─ Install DBeaver from https://dbeaver.io/download/
└─ Or use Manual connection instead
```

### 2. **DBeaver Config File Missing**
```
Error: "data-sources.json not found"

Possible Reasons:
├─ DBeaver installed but never saved connections
├─ DBeaver installed in non-standard location
└─ File permissions issue

Solution:
├─ Save a test connection in DBeaver first
├─ Close and restart DBeaver
└─ Try again
```

### 3. **DBeaver Config Path Wrong for Your OS**
```
Windows Path: C:\Users\{USERNAME}\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\
macOS Path:   ~/Library/DBeaverData/workspace6/General/.dbeaver/
Linux Path:   ~/.dbeaver4/General/.dbeaver/

Solution:
├─ Verify path exists on your computer
├─ Check file permissions (should be readable)
└─ If path is different, update code or use manual connection
```

### 4. **DBeaver Connection Uses Unsupported Driver**
```
Error: "Unsupported driver: xxx"

Reason: Driver type not in Lakeforge's conversion list
Current Supported Drivers:
├─ MySQL
├─ PostgreSQL
├─ SQL Server
├─ Oracle
├─ SQLite
├─ Databricks
└─ S3 (via DuckDB)

Solution:
├─ Use manual connection instead
├─ Or we add support for new driver type
```

### 5. **Password Encoding/Special Characters**
```
Problem: DBeaver stores password with special encoding
         Cannot convert to plain text URI

Example:
├─ Password in DBeaver: "p@ss$w0rd!"
├─ Tries to convert: "mysql://user:p@ss$w0rd!@host:3306/db"
└─ URI parser gets confused by special characters

Solution:
├─ Edit URI manually with proper escaping
├─ Or use manual connection with exact password
```

---

## ✅ Debugging DBeaver Connection Issues

### Step 1: Check if DBeaver Exists
```bash
Windows:
  dir "C:\Users\%USERNAME%\AppData\Roaming\DBeaverData"

macOS:
  ls ~/Library/DBeaverData

Linux:
  ls ~/.dbeaver4
```

### Step 2: Verify Config File
```bash
Windows:
  dir "C:\Users\%USERNAME%\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\data-sources.json"

macOS:
  ls ~/Library/DBeaverData/workspace6/General/.dbeaver/data-sources.json

Linux:
  ls ~/.dbeaver4/General/.dbeaver/data-sources.json
```

### Step 3: Check Backend Logs
```bash
Look for error messages like:
├─ "DBeaver config not found" → DBeaver not installed
├─ "Failed to read DBeaver config" → Permission issue
├─ "Unsupported driver" → Driver not supported
└─ "Failed to convert connection" → Conversion error
```

### Step 4: Try Manual Connection Instead
```
If DBeaver doesn't work:
1. Go to Settings
2. Click "+ Add Source"
3. Select Database Type
4. Manually enter connection URI
5. Click "Add Source"
```

---

## 🔐 URI Format Reference

### All Supported Database URI Formats:

#### MySQL
```
mysql://user:password@host:3306/database

Examples:
├─ mysql://root:pass123@localhost:3306/myapp
├─ mysql://admin:p@ss@prod.example.com:3306/sales_db
└─ mysql://user@remote.host:3307/test
```

#### PostgreSQL
```
postgres://user:password@host:5432/database

Examples:
├─ postgres://postgres:pass@localhost:5432/myapp
├─ postgres://admin@prod.example.com:5432/data_warehouse
└─ postgres://user:@remote.host:5433/testdb
```

#### SQL Server
```
mssql://user:password@host:1433/database

Examples:
├─ mssql://sa:P@ssw0rd@localhost:1433/master
├─ mssql://admin:pass@prod.example.com:1433/Sales
└─ mssql://user@named.instance.com:1433/testdb
```

#### Oracle
```
oracle://user:password@host:1521/SID

Examples:
├─ oracle://scott:tiger@localhost:1521/ORCL
├─ oracle://admin:pass@prod.example.com:1521/PROD
└─ oracle://user@remote.host:1522/DB1
```

#### SQLite
```
sqlite:///path/to/database.db

Examples:
├─ sqlite:///C:/Users/Admin/data/app.db          (Windows)
├─ sqlite:////home/user/data/app.db              (Linux)
└─ sqlite:////Users/admin/data/app.db            (macOS)
```

#### Databricks
```
databricks://workspace/catalog/schema/table

Example:
└─ databricks://my-workspace/hive_metastore/default/sales_table
```

#### S3 (via DuckDB)
```
s3://bucket-name/path/to/file.parquet

Example:
└─ s3://my-data-bucket/sales/2024/data.parquet
```

---

## 🎯 Quick Fix Checklist

If DBeaver connection isn't working:

- [ ] DBeaver is installed on your computer
- [ ] At least one database connection is saved in DBeaver
- [ ] DBeaver was closed and reopened since saving connections
- [ ] Config file exists at expected path (Windows/macOS/Linux)
- [ ] File permissions allow reading the config file
- [ ] Database driver is in supported list (MySQL, PostgreSQL, SQL Server, Oracle, SQLite)
- [ ] Backend error log shows what went wrong

If still not working:
- [ ] Use Manual connection instead (it always works if DB is accessible)
- [ ] Check that you can connect to database from DBeaver itself (to verify credentials)
- [ ] Review database firewall/network rules
- [ ] Test connection URI manually first

---

## 🚀 Recommended Approach

### For New Users:
```
1. Try DBeaver connection first (if you have it)
   └─ Faster, less error-prone
   
2. If DBeaver doesn't work:
   └─ Use manual connection with URI template
   └─ Copy the template and modify with your details
```

### For Existing DBeaver Users:
```
1. Make sure connections are saved in DBeaver
2. Click 🔗 DBeaver button
3. Select connection to import
4. One-click done!
```

### For Non-DBeaver Users:
```
1. Go to Settings
2. Click "+ Add Source"
3. Select database type
4. Modify URI template with your connection details
5. Add source
```

---

## 💡 Summary

| Task | Method | Time | Difficulty |
|------|--------|------|------------|
| Have DBeaver with saved connections | DBeaver Import | 5 sec | Very Easy |
| Don't have DBeaver | Manual Connection | 2 min | Easy |
| Need quick test connection | Manual Connection | 1 min | Easy |
| Move from DBeaver to Lakeforge | DBeaver Import | 10 sec | Very Easy |
| Complex connection parameters | Manual Connection | 5 min | Medium |

---

## 🔗 Both Methods Are Valid!

**DBeaver Import** = Fast & convenient (if you have DBeaver)
**Manual Connection** = Always works, maximum flexibility

✅ **Use whichever works best for your situation!**

---

### Need Help?

Check backend logs:
```bash
# When backend is running, look for errors containing:
# - "DBeaver config not found"
# - "Failed to read DBeaver config"
# - "Unsupported driver"
# - "Failed to convert connection"
```

Or use Manual connection as a backup - it's simple and reliable!
