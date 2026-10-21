# DBeaver Connection Troubleshooting - Quick Checklist

## 🔴 Immediate Steps to Fix DBeaver Connection Issue

### Step 1: Check Backend Logs
Look at your backend terminal (the one running `uvicorn main:app --reload`).

When you click the "🔗 DBeaver" button, do you see any error messages like:
- `DBeaver config not found`
- `Failed to read DBeaver config`
- `Unsupported driver`
- `Connection conversion failed`

**Copy any error message and share it with me.**

---

### Step 2: Verify DBeaver is Installed

#### Windows:
```powershell
# Check if DBeaver folder exists
Test-Path "C:\Users\$env:USERNAME\AppData\Roaming\DBeaverData"

# Should return: True or False
```

#### macOS:
```bash
ls ~/Library/DBeaverData
# Should list folders
```

#### Linux:
```bash
ls ~/.dbeaver4
# Should list folders
```

**Report what you see (exists or doesn't exist).**

---

### Step 3: Check if You Saved Connections in DBeaver

If DBeaver is installed:
1. Open DBeaver
2. Look for "Database" menu → "New Database Connection"
3. Check if you have any saved connections
4. At least one connection must be saved for Lakeforge to see it

**Do you have any saved connections in DBeaver? Yes/No?**

---

### Step 4: Check config File Directly

#### Windows:
```powershell
# Check if data-sources.json exists
Test-Path "C:\Users\$env:USERNAME\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\data-sources.json"

# Check file size
(Get-Item "C:\Users\$env:USERNAME\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\data-sources.json" -ErrorAction SilentlyContinue).Length

# Should be more than 0 bytes if it has connections
```

#### macOS/Linux:
```bash
# Check if file exists
ls ~/Library/DBeaverData/workspace6/General/.dbeaver/data-sources.json

# OR for Linux:
ls ~/.dbeaver4/General/.dbeaver/data-sources.json

# Check file size
wc -c ~/Library/DBeaverData/workspace6/General/.dbeaver/data-sources.json
```

**Does file exist and have content (size > 0)?**

---

### Step 5: Use Manual Connection Instead (Guaranteed to Work)

If DBeaver is too complicated, just use the manual method:

1. Go to **Settings** page
2. Click **"+ Add Source"** button
3. Fill in form:
   ```
   Source Name:    MyDatabase
   Database Type:  [Select your type]
   Connection URI: mysql://user:password@localhost:3306/mydb
   Description:    My test database
   ```
4. Click **"Add Source"**

**This method ALWAYS works** if your database is accessible.

---

## 📋 Information I Need From You

To help debug, please provide:

1. **Backend Error Message**
   - When you click "🔗 DBeaver" button
   - What error appears in backend terminal?

2. **DBeaver Status**
   - Is DBeaver installed on your computer?
   - Do you have saved connections in DBeaver?

3. **Config File Status**
   - Does the DBeaver config file exist?
   - (Check paths in Step 2 above)

4. **Error Message in Browser**
   - Open browser console (F12)
   - Go to Settings page
   - Click "🔗 DBeaver" button
   - What error message appears in console?
   - Copy the error text

---

## 🎯 Most Likely Issues & Solutions

### Issue 1: DBeaver Not Installed
```
Error: "DBeaver config not found"

Solution:
├─ Option A: Install DBeaver (https://dbeaver.io/download/)
│  └─ Then save connections in it
│  └─ Then try importing
└─ Option B: Use manual connection instead
```

### Issue 2: No Connections Saved in DBeaver
```
Error: Empty connection list OR no connections showing

Solution:
├─ Open DBeaver
├─ Go to Database → New Database Connection
├─ Create a test connection
├─ Save it
├─ Close DBeaver
├─ Open Lakeforge and try again
```

### Issue 3: DBeaver Config File Empty
```
Error: File exists but has no connections

Solution:
├─ Make sure you clicked "Finish" when creating connection in DBeaver
├─ Close and reopen DBeaver to ensure it's saved
├─ File should show connections after you reopen
```

### Issue 4: Unsupported Database Type
```
Error: "Unsupported driver: xxx"

Reason: Database type not supported by Lakeforge

Current Supported Types:
├─ MySQL ✅
├─ PostgreSQL ✅
├─ SQL Server ✅
├─ Oracle ✅
├─ SQLite ✅
├─ Databricks ✅
└─ S3 ✅

Solution:
├─ Use manual connection with URI
├─ Or tell me which driver so we can add support
```

### Issue 5: Connection Has Special Characters in Password
```
Problem: Password like "P@ss$w0rd!" causes URI parsing issues

Solution:
├─ Use manual connection instead
├─ URI properly handles password escaping
```

---

## ✅ Guaranteed Working Method (Use This!)

If DBeaver is too complicated, just use manual connection:

### Step 1: Get Your Database Details
```
You need:
├─ Host (e.g., localhost, prod.example.com)
├─ Port (e.g., 3306 for MySQL, 5432 for PostgreSQL)
├─ Username (e.g., root, postgres)
├─ Password (e.g., your password)
└─ Database Name (e.g., myapp, testdb)
```

### Step 2: Format the URI
```
Template based on database type:

MySQL:       mysql://user:password@host:port/database
PostgreSQL:  postgres://user:password@host:port/database
SQL Server:  mssql://user:password@host:port/database
Oracle:      oracle://user:password@host:port/SID
SQLite:      sqlite:///path/to/database.db
```

### Step 3: Go to Settings and Add
```
1. Click "+ Add Source"
2. Fill in Name
3. Select Database Type
4. Paste your URI
5. Click "Add Source"
6. Click "Test" to verify
7. Done!
```

### Example: MySQL Database
```
Source Name:     Production MySQL
Database Type:   MySQL
Connection URI:  mysql://admin:mypassword@prod.example.com:3306/sales_db
Description:     Production sales database
```

---

## 📞 Still Need Help?

Please provide:
1. What error do you see? (backend terminal error)
2. Is DBeaver installed?
3. Do you have saved connections in DBeaver?
4. What database type are you trying to connect to?

Then I can give you a specific solution!

---

**Recommendation:** Start with manual connection while we debug DBeaver. It's simpler and more reliable. You can always switch to DBeaver import later once we fix it.
