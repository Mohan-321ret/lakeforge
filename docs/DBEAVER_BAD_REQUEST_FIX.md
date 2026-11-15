# 🔴 DBeaver Import Error: "Bad Request" - Debugging Guide

## What I Fixed

I've improved the error handling so you'll now see **detailed error messages** instead of generic "Bad Request". This will help us debug the issue.

**Changes Made:**
1. ✅ Backend now logs detailed error information
2. ✅ Frontend shows clear error messages
3. ✅ API client now returns full error details
4. ✅ Better handling of missing connections

---

## 🚀 How to Test Now

### Step 1: Restart Backend
```bash
1. Stop backend (press Ctrl+C in backend terminal)
2. Restart: cd backend && uvicorn main:app --reload --port 8000
3. Wait for "Uvicorn running on http://0.0.0.0:8000"
```

### Step 2: Test DBeaver Import Again
```
1. Go to http://localhost:5173/settings
2. Click "🔗 DBeaver" button
3. Wait for connection list to load
4. Select a connection and click "Import"
```

### Step 3: Check Error Message
```
Now you should see a DETAILED error message instead of "Bad Request"

Possible errors:
├─ "No DBeaver connections found..."
│  └─ Action: Save a connection in DBeaver first
│
├─ "Connection 'xxx' not found..."
│  └─ Action: Check connection ID
│
├─ "Could not convert DBeaver connection..."
│  └─ Action: Database type might not be supported
│
├─ "Unsupported driver: xxx"
│  └─ Action: Use manual connection for this database type
│
└─ "Failed to import connection: {specific error}"
   └─ Action: Read the specific error details
```

---

## 📋 Debugging Checklist

### Check 1: Is DBeaver Installed?
```powershell
# Windows: Check if folder exists
Test-Path "C:\Users\$env:USERNAME\AppData\Roaming\DBeaverData"

# Should return: True
```

**If False:**
```
→ Install DBeaver from https://dbeaver.io/download/
→ Then save a test connection
→ Then try Lakeforge again
```

---

### Check 2: Does DBeaver Have Saved Connections?
```
1. Open DBeaver
2. Look in the "Database Connections" section on left
3. Should show your saved connections
4. If empty:
   a. Click "New Database Connection"
   b. Select a database type (MySQL, PostgreSQL, etc.)
   c. Fill in connection details
   d. Click "Finish" to save
   e. Close DBeaver
```

**If no connections:**
```
→ Create a test connection in DBeaver
→ Save it
→ Close DBeaver
→ Try Lakeforge again
```

---

### Check 3: Check Backend Logs
When you click "🔗 DBeaver" button, look at your backend terminal for:

```
Lines to look for:
├─ "Found X DBeaver connections" = SUCCESS ✅
├─ "DBeaver config not found" = Config file missing
├─ "No DBeaver connections found" = No connections saved
├─ "Failed to read DBeaver config" = Permission issue
└─ "Unsupported driver: XXX" = Database type not supported
```

**Copy the exact error line and share it with me!**

---

### Check 4: Check Browser Console
```
Press F12 in browser
Go to "Console" tab
When you click DBeaver button, error messages appear
Should show detailed error like:
"API Error (400): Connection 'xxx' not found"
or
"API Error (500): Failed to import connection: [reason]"
```

**Copy the exact error and share it!**

---

## 🔧 Common Issues & Quick Fixes

### Issue 1: "No DBeaver connections found"
```
Cause: DBeaver installed but no connections saved

Fix:
1. Open DBeaver
2. Database → New Database Connection
3. Create a test connection (any database type)
4. Click "Finish" to save
5. Close DBeaver completely
6. Try Lakeforge again
```

### Issue 2: "Unsupported driver"
```
Cause: Database type not in Lakeforge's supported list

Supported drivers:
✅ MySQL
✅ PostgreSQL
✅ SQL Server
✅ Oracle
✅ SQLite
✅ Databricks
✅ S3/DuckDB

Workaround:
→ Use manual connection method instead
→ Go to Settings
→ Click "+ Add Source"
→ Type the connection URI manually
```

### Issue 3: "Connection XXX not found"
```
Cause: Connection ID doesn't exist (unlikely)

Fix:
1. Click DBeaver button again
2. Make sure connection is in the list
3. Click Import on the correct one
4. If still fails, restart backend and browser

Check Browser Console (F12):
→ What connection IDs are listed?
→ What ID are you trying to import?
```

### Issue 4: Backend Logs Show Nothing
```
Cause: Backend not running or not processing request

Fix:
1. Check backend terminal is still running
2. Should say "Uvicorn running on http://0.0.0.0:8000"
3. If not, restart backend
4. Try again
```

---

## 🎯 What to Tell Me If Still Not Working

Please provide:

1. **Exact Error Message**
   - What does the alert box say in browser?
   - Copy it exactly

2. **Backend Log**
   - What lines appear in backend terminal when you click DBeaver?
   - Copy them exactly

3. **Browser Console**
   - F12 → Console tab
   - What error message appears?
   - Copy it exactly

4. **System Info**
   - Is DBeaver installed?
   - How many connections saved in DBeaver?
   - What database types are they?

5. **Current State**
   - Are you on Windows/Mac/Linux?
   - Is backend running?
   - Is frontend running?

---

## ✨ If DBeaver Still Doesn't Work

**Just use the manual connection method** - it's more reliable:

```
1. Go to http://localhost:5173/settings
2. Click "+ Add Source"
3. Fill in:
   - Source Name: MyDatabase
   - Database Type: [Select your type]
   - Connection URI: [Your connection string]
4. Click "Add Source"
5. Done! ✅
```

Both methods work. DBeaver is just a shortcut.

---

## 📞 Next Steps

1. **Restart backend** (with new code)
2. **Try DBeaver import again**
3. **Note the exact error message**
4. **Share the error with me**
5. **I'll provide specific fix**

Or just use manual connection - it definitely works! 🎉
