# 🔧 Practical Examples: DBeaver vs Manual Connection

## 📚 Real-World Scenario

Let's say you have these databases:

```
Database 1: Production MySQL Server
├─ Host: prod-db.company.com
├─ Port: 3306
├─ Username: app_user
├─ Password: SecurePass123!
└─ Database: production_db

Database 2: Local Development PostgreSQL
├─ Host: localhost
├─ Port: 5432
├─ Username: postgres
├─ Password: dev123
└─ Database: dev_db

Database 3: Corporate SQL Server
├─ Host: sqlserver.internal.com
├─ Port: 1433
├─ Username: DOMAIN\admin
├─ Password: Corp@Pass456
└─ Database: enterprise_db
```

---

## 🔄 Method 1: Using DBeaver Import

### Scenario: You Already Have These in DBeaver

#### Step 1: Open DBeaver
```
Applications → DBeaver → Open
```

#### Step 2: Your Saved Connections Look Like This
```
Database Connections (in DBeaver):
├─ Production MySQL
│  ├─ Host: prod-db.company.com
│  ├─ Port: 3306
│  ├─ User: app_user
│  ├─ Password: [Saved]
│  └─ Database: production_db
│
├─ Dev PostgreSQL
│  ├─ Host: localhost
│  ├─ Port: 5432
│  ├─ User: postgres
│  ├─ Password: [Saved]
│  └─ Database: dev_db
│
└─ Corp SQL Server
   ├─ Host: sqlserver.internal.com
   ├─ Port: 1433
   ├─ User: DOMAIN\admin
   ├─ Password: [Saved]
   └─ Database: enterprise_db
```

#### Step 3: Import to Lakeforge
```
1. Open Lakeforge → Go to Settings page
   
2. Click "🔗 DBeaver" button
   └─ Wait for it to load
   
3. You see this list:
   ┌─────────────────────────────────────────┐
   │ DBeaver Connections                     │
   ├─────────────────────────────────────────┤
   │ ☐ Production MySQL          [Import]    │
   │ ☐ Dev PostgreSQL            [Import]    │
   │ ☐ Corp SQL Server           [Import]    │
   └─────────────────────────────────────────┘

4. Click [Import] next to "Production MySQL"
   └─ Connection automatically added to Lakeforge
   └─ Lakeforge URI: mysql://app_user:SecurePass123!@prod-db.company.com:3306/production_db

5. Click [Import] next to "Dev PostgreSQL"
   └─ Connection automatically added
   └─ Lakeforge URI: postgres://postgres:dev123@localhost:5432/dev_db

6. Click [Import] next to "Corp SQL Server"
   └─ Connection automatically added
   └─ Lakeforge URI: mssql://DOMAIN\admin:Corp@Pass456@sqlserver.internal.com:1433/enterprise_db

7. All done! ✅
   └─ All 3 databases now in Lakeforge Sources list
   └─ No typing, no errors, automatic!
```

#### What Happened Behind the Scenes:
```
Frontend → Backend → DBeaver Config File
   ↓          ↓            ↓
Click     Read config   Read JSON file at:
DBeaver    file path    C:\Users\...\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\data-sources.json
button     (Windows)    └─ Extracts all saved connections
           (macOS)
           (Linux)      └─ Parses each connection's details
                          ├─ Connection name: "Production MySQL"
                          ├─ Driver: "mysql"
                          ├─ Host: "prod-db.company.com"
                          ├─ Port: "3306"
                          ├─ User: "app_user"
                          ├─ Password: "SecurePass123!"
                          └─ Database: "production_db"
                        
                        └─ Converts to Lakeforge format:
                          "mysql://app_user:SecurePass123!@prod-db.company.com:3306/production_db"
                        
                        └─ Returns to Frontend
                        
                        └─ Frontend creates source with this URI
```

---

## ✏️ Method 2: Manual Connection (Type It Yourself)

### Same Scenario, But Without DBeaver

#### Step 1: Go to Settings
```
Lakeforge → Settings page
```

#### Step 2: Click "+ Add Source"
```
┌──────────────────────────────────────────────┐
│ Add New Data Source                       [✕] │
├──────────────────────────────────────────────┤
│ Source Name *                                 │
│ ┌────────────────────────────────────────┐   │
│ │ [Click here and type name]             │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ Database Type *                               │
│ ┌────────────────────────────────────────┐   │
│ │ ▼ MySQL                                │   │
│ │ ├─ PostgreSQL                          │   │
│ │ ├─ SQL Server                          │   │
│ │ ├─ Oracle                              │   │
│ │ ├─ SQLite                              │   │
│ │ ├─ Databricks                          │   │
│ │ └─ S3                                  │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ Connection URI *                              │
│ ┌────────────────────────────────────────┐   │
│ │ mysql://user:password@host:3306/db... │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ Description                                  │
│ ┌────────────────────────────────────────┐   │
│ │ [Optional description]                 │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ [   Cancel   ]  [   Add Source   ]           │
└──────────────────────────────────────────────┘
```

#### Step 3: Fill in First Database (Production MySQL)
```
Source Name:      Production MySQL
                  ↓
Database Type:    MySQL (auto-fills template)
                  ↓
Template shows:   mysql://user:password@host:3306/database
                  ↓
You replace with: mysql://app_user:SecurePass123!@prod-db.company.com:3306/production_db
                  ↓
Description:      Production sales database
                  ↓
Click "Add Source"
                  ↓
✅ Added successfully!
```

#### Step 4: Add Second Database (Dev PostgreSQL)
```
Click "+ Add Source" again
                  ↓
Source Name:      Dev PostgreSQL
                  ↓
Database Type:    PostgreSQL (auto-fills template)
                  ↓
Template shows:   postgres://user:password@host:5432/database
                  ↓
You replace with: postgres://postgres:dev123@localhost:5432/dev_db
                  ↓
Description:      Local development database
                  ↓
Click "Add Source"
                  ↓
✅ Added successfully!
```

#### Step 5: Add Third Database (Corp SQL Server)
```
Click "+ Add Source" again
                  ↓
Source Name:      Corp SQL Server
                  ↓
Database Type:    SQL Server (auto-fills template)
                  ↓
Template shows:   mssql://user:password@host:1433/database
                  ↓
You replace with: mssql://DOMAIN\admin:Corp@Pass456@sqlserver.internal.com:1433/enterprise_db
                  ↓
Description:      Enterprise database
                  ↓
Click "Add Source"
                  ↓
✅ Added successfully!
```

---

## 🆚 Side-by-Side Comparison

### For Same 3 Databases:

| Step | DBeaver Method | Manual Method |
|------|---|---|
| 1 | Open Lakeforge | Open Lakeforge |
| 2 | Go to Settings | Go to Settings |
| 3 | Click "🔗 DBeaver" | Click "+ Add Source" |
| 4 | Wait for list to load | Fill in Name |
| 5 | Click "Import" for DB1 | Select Database Type |
| 6 | Click "Import" for DB2 | Paste/Type Connection URI |
| 7 | Click "Import" for DB3 | Click "Add Source" |
| 8 | Done! (30 seconds) | Repeat for DB2 (type URI, add) |
| — | — | Repeat for DB3 (type URI, add) |
| — | — | Done! (3 minutes) |
| **Total Time** | 30 seconds | 3-5 minutes |
| **Errors** | Almost impossible | Easy to make typos |
| **Prerequisites** | DBeaver must have connections saved | Know your connection details |

---

## 📊 Why Choose Each Method?

### ✅ Choose DBeaver Import If:
```
✅ You already use DBeaver
✅ Your connections are saved there
✅ You want fastest method (30 seconds)
✅ You want to avoid typos
✅ You want it once-click easy
```

### ✅ Choose Manual Connection If:
```
✅ DBeaver not installed
✅ Only need connection once
✅ Adding new database you haven't used before
✅ Want maximum control/flexibility
✅ DBeaver connection has special setup
```

---

## 🔍 What Happens During Import

### DBeaver Import Process:

```
1. FRONTEND
   └─ You click "🔗 DBeaver" button
   
2. BACKEND RECEIVES REQUEST
   ├─ Gets request: GET /api/dbeaver/connections
   └─ Starts looking for DBeaver config file
   
3. BACKEND FINDS CONFIG
   ├─ Windows: C:\Users\...\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\data-sources.json
   ├─ macOS:   ~/Library/DBeaverData/workspace6/General/.dbeaver/data-sources.json
   └─ Linux:   ~/.dbeaver4/General/.dbeaver/data-sources.json
   
4. BACKEND READS JSON FILE
   └─ Extracts all connection entries
   └─ For each connection:
      ├─ Gets connection name
      ├─ Gets database driver type
      ├─ Gets host, port, username, password, database
      └─ Stores temporarily
   
5. BACKEND SENDS TO FRONTEND
   └─ List of all connections found
   └─ Example:
      [
        { id: "conn_123", name: "Production MySQL", driver: "mysql", host: "prod.com", database: "myapp" },
        { id: "conn_456", name: "Dev PostgreSQL", driver: "postgres", host: "localhost", database: "dev_db" }
      ]
   
6. FRONTEND DISPLAYS LIST
   └─ User sees checkboxes with connection names
   └─ User clicks "Import" for one
   
7. BACKEND CONVERTS CONNECTION
   ├─ Receives: connection_id = "conn_123"
   ├─ Looks up connection details from DBeaver config
   ├─ Converts to Lakeforge URI format
   │  ├─ Input: { driver: "mysql", host: "prod.com", port: 3306, user: "admin", password: "pass", database: "myapp" }
   │  └─ Output: "mysql://admin:pass@prod.com:3306/myapp"
   └─ Returns to frontend
   
8. FRONTEND CREATES SOURCE
   ├─ Calls: POST /api/sources
   ├─ Sends: { name: "Production MySQL", uri: "mysql://admin:pass@prod.com:3306/myapp", description: "...", tags: ["dbeaver"] }
   └─ Backend stores in database
   
9. LAKEFORGE SOURCES LIST UPDATED
   └─ New source appears in list
   └─ You can now inspect, query, profile, etc.
```

### Manual Connection Process:

```
1. FRONTEND
   └─ You click "+ Add Source" button
   
2. FORM APPEARS
   ├─ Source Name field (empty)
   ├─ Database Type dropdown (default: MySQL)
   ├─ Connection URI field (shows template based on type)
   └─ Description field (empty)
   
3. YOU FILL IN FORM
   ├─ Type name: "Production MySQL"
   ├─ Select type: MySQL (template shows)
   ├─ Type URI: "mysql://admin:pass@prod.com:3306/myapp"
   └─ Type description: "My production database"
   
4. YOU CLICK "Add Source"
   └─ Frontend collects your inputs
   └─ Sends: { name: "Production MySQL", uri: "mysql://admin:pass@prod.com:3306/myapp", description: "...", tags: [] }
   
5. BACKEND RECEIVES SOURCE
   ├─ Parses URI
   ├─ Attempts to connect to database
   ├─ Validates connection works
   └─ If successful: stores source
   
6. BACKEND RESPONDS
   └─ Returns success or error
   
7. FRONTEND UPDATES
   └─ New source appears in list
   └─ If error, shows error message
   
8. YOU CAN USE SOURCE
   └─ Start inspections
   └─ Query databases
   └─ Generate reports
```

---

## 🎯 Troubleshooting: Why One Method Doesn't Work

### DBeaver Import Not Working?

```
Possible Reasons:
├─ 1. DBeaver not installed → Install from https://dbeaver.io
├─ 2. No connections saved in DBeaver → Save a connection first
├─ 3. Config file doesn't exist → Create connection in DBeaver
├─ 4. Unsupported database type → Use manual method
└─ 5. Backend can't read config file → Check file permissions

Solution: Use manual connection instead (guaranteed to work)
```

### Manual Connection Not Working?

```
Possible Reasons:
├─ 1. Wrong connection URI format → Check URI syntax
├─ 2. Database not accessible → Check firewall/network
├─ 3. Wrong credentials → Verify username/password
├─ 4. Database doesn't exist → Create database first
└─ 5. Port number wrong → Check database port

Solution: Test connection outside Lakeforge first
├─ Try connecting with DBeaver itself
├─ Or use database CLI (mysql, psql, sqlplus)
└─ Then come back to Lakeforge
```

---

## 💡 Pro Tips

### Tip 1: Template Auto-Fill
```
When you select database type, URI template auto-fills:

MySQL:       mysql://user:password@host:3306/database
PostgreSQL:  postgres://user:password@host:5432/database
SQL Server:  mssql://user:password@host:1433/database
Oracle:      oracle://user:password@host:1521/SID
SQLite:      sqlite:///path/to/database.db

Just replace the placeholders with your actual values!
```

### Tip 2: Test Connection First
```
If you're not sure if connection works:

1. Add source with connection URI
2. Click "Test" button next to it
3. Get immediate feedback
4. Fix if needed and try again
```

### Tip 3: Special Characters in Password
```
If password has special characters:

Problem:   Password "P@ss!word" breaks URI parser
Solution:  Type it anyway, Lakeforge handles it

Example:
Before: mysql://user:P@ss!word@localhost:3306/db
After:  Lakeforge parses it correctly

DBeaver can't handle this complexity, use manual method!
```

### Tip 4: Port Numbers
```
Default ports (if you don't specify):
├─ MySQL: 3306
├─ PostgreSQL: 5432
├─ SQL Server: 1433
├─ Oracle: 1521
└─ SQLite: N/A (file-based)

If your database uses standard port, you can omit it:
❌ mysql://user:pass@host:3306/db
✅ mysql://user:pass@host/db       (assumes port 3306)
```

---

## ✨ Final Summary

```
┌─────────────────────────────────────────────────────────┐
│ BOTH METHODS WORK! Choose What's Best for You:          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 🔗 DBeaver Import         ✏️ Manual Connection          │
│ ├─ Fast (30 sec)          ├─ Flexible                   │
│ ├─ No typing              ├─ Works anywhere             │
│ ├─ Automatic              ├─ More control               │
│ └─ Requires DBeaver       └─ Requires details           │
│                                                          │
└─────────────────────────────────────────────────────────┘

RECOMMENDED: Start with DBeaver if you have it.
If not, or if it doesn't work, use manual method.

Both lead to the same result: Database available in Lakeforge! ✅
```
