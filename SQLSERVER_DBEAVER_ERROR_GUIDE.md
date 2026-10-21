# 🔴 SQL Server DBeaver Import Error - Debugging Guide

## Error Details
```
Failed to import: API Error (400): Invalid source URI: CIM002: '[IM002] 
[Microsoft][ODBC Driver Manager] Data source name not found and no 
default driver specified (0) (SQLDriverConnect)'
```

---

## 🔍 What This Error Means

This is an **ODBC Driver Error**, which happens when:

1. ❌ The SQL Server isn't accessible from your computer
2. ❌ The server name/host is incorrect  
3. ❌ The credentials are wrong
4. ❌ Network/firewall is blocking the connection
5. ❌ SQL Server isn't running
6. ❌ The URI format is incorrect

---

## 🛠️ Step-by-Step Debugging

### Step 1: Check if SQL Server is Running

**Windows - Using SQL Server Management Studio:**
```
1. Open SQL Server Management Studio (SSMS)
2. Try to connect to your server
3. If it connects → Server is running ✅
4. If it fails → Server is down ❌
```

**Windows - Using Command Line:**
```powershell
# Check if SQL Server service is running
Get-Service MSSQLSERVER | Select-Object Status

# Should show: Status : Running
```

**If Not Running:**
```powershell
# Start SQL Server service
Start-Service MSSQLSERVER

# Wait a few seconds, then try again
```

---

### Step 2: Verify Server Name is Correct

**In DBeaver:**
```
1. Open DBeaver
2. Database Connections (left panel)
3. Right-click on your SQL Server connection
4. Properties or Edit Connection
5. Look for "Server Name" or "Host"
6. Note the exact server name
```

**Common Server Names:**
```
✅ localhost
✅ 127.0.0.1
✅ (local)
✅ COMPUTERNAME
✅ COMPUTERNAME\SQLEXPRESS
✅ sql.example.com
✅ sql-server.internal
```

**If you see something like:**
```
❌ Not found
❌ (blank)
❌ MISSING_SERVER
```
→ Server details not properly saved in DBeaver

---

### Step 3: Test Connection Outside Lakeforge

**Using SQL Server Management Studio:**
```
1. Open SSMS
2. Server name: [paste from DBeaver]
3. Authentication: Windows / SQL Server Auth
4. Username: [your username]
5. Password: [your password]
6. Click "Connect"
7. If successful → Connection works ✅
8. If fails → Check credentials/network
```

**If it fails in SSMS, it will also fail in Lakeforge.**

---

### Step 4: Check Credentials in DBeaver

**In DBeaver Connection Settings:**
```
1. Right-click connection → Edit Connection
2. Go to "Main" tab
3. Check these fields:
   ├─ Server Name: [correct?]
   ├─ Port: [default 1433]
   ├─ Database: [filled in?]
   ├─ Username: [correct?]
   ├─ Password: [correct?]
   └─ Authentication: Windows / SQL Auth
4. Click "Test Connection"
5. If passes → Credentials are correct ✅
6. If fails → Fix credentials in DBeaver
```

---

### Step 5: Check Network/Firewall

**If server is remote (not localhost):**

```
1. Can you ping the server?
   ping [server-name]
   Should see: "Reply from..." ✅
   
2. Can you telnet to port 1433?
   telnet [server-name] 1433
   Should show connection response ✅
   
3. Windows Firewall might be blocking:
   Windows Defender Firewall with Advanced Security
   → Inbound Rules
   → Look for "SQL Server" rules
   → Should be "Allowed" ✅
```

---

### Step 6: Check DBeaver Connection Details

The error suggests the URI being generated might be missing critical details.

**What we need from DBeaver:**
```
✅ Server/Host
✅ Port (default 1433)
✅ Username
✅ Password
✅ Database Name
```

**If any of these are missing, the import will fail.**

---

## ✅ Quick Fix Checklist

Before trying import again:

- [ ] SQL Server is running (service is up)
- [ ] Can connect to SQL Server using SSMS
- [ ] Server name is correct
- [ ] Credentials (user/pass) are correct
- [ ] Port is accessible (not blocked by firewall)
- [ ] Database exists and you have access
- [ ] DBeaver connection has "Test Connection" as passing ✅

If ALL are checked ✅, try importing again.

---

## 🎯 Most Likely Fix

Based on the error, the URI format is probably missing key details.

**Current (Broken) URI might be:**
```
mssql://@localhost:1433/   ← Missing server name
```

**Correct format should be:**
```
mssql://username:password@servername:1433/databasename
```

**To check the URI being generated:**
1. Open browser Console (F12)
2. Go to Settings page
3. Click DBeaver button
4. Look at console log line: "Generated URI for..."
5. Copy the full URI
6. Check if it has all details:
   - ✅ Has username
   - ✅ Has password
   - ✅ Has server name
   - ✅ Has port
   - ✅ Has database name

**If URI is missing any part → Problem is in DBeaver configuration**

---

## 🔧 Workaround: Use Manual Connection

If DBeaver import isn't working, use manual connection:

**Step 1: Get Connection String**
```
Format: mssql://username:password@servername:port/database

Example: mssql://sa:MyPassword123@localhost:1433/TestDB
```

**Step 2: Add in Lakeforge**
```
1. Go to Settings
2. Click "+ Add Source"
3. Name: My SQL Server
4. Type: SQL Server
5. URI: [paste your connection string]
6. Click "Add Source"
```

**This method works because:**
- You provide exact details
- No parameter conversion needed
- Direct connection attempt

---

## 📋 Information to Gather (For Support)

If you need help debugging:

1. **Browser Console Error:**
   - F12 → Console tab
   - Copy exact error message

2. **Backend Log:**
   - Look at backend terminal
   - Copy lines mentioning "Converting connection" and "Built SQL Server URI"

3. **Connection Details (Sanitized):**
   - Server: [your server]
   - Database: [your database]
   - Auth Type: Windows / SQL Auth
   - Port: [your port]

4. **DBeaver Connection:**
   - Does it work in DBeaver? (Test Connection status)
   - What's the exact Server Name in DBeaver?

5. **Lakeforge Manual Connection:**
   - Can you connect using manual method?
   - (Proves it's just a DBeaver extraction issue)

---

## 💡 Summary

| Check | Status | Action |
|-------|--------|--------|
| SQL Server running? | ? | Check services / SSMS connection |
| Can connect in SSMS? | ? | Verify credentials and server name |
| DBeaver connection works? | ? | Test Connection in DBeaver |
| Network accessible? | ? | Ping server, check firewall |
| URI has all parts? | ? | Check browser console log |
| Manual connection works? | ? | Proves SQL Server is accessible |

If manual connection works but DBeaver doesn't → DBeaver extraction issue (we can fix)
If neither works → SQL Server accessibility issue (check above)

---

## 🚀 Next Steps

1. **First try:** Restart SQL Server service
2. **Then:** Test in SSMS to verify connection
3. **Then:** Test manual connection in Lakeforge
4. **Finally:** Try DBeaver import again

If manual works but DBeaver doesn't:
- Copy the working manual URI
- Edit the DBeaver connection to make sure all details are saved
- Try import again with improved parameter extraction

---

## 📞 Still Not Working?

Please provide:
1. Backend log output (lines with "Converting connection" and "Built SQL Server URI")
2. Browser console error message (F12)
3. The manual connection URI that DOES work
4. Your DBeaver server name and database name

Then I can fix the DBeaver extraction code!

---

## ⚠️ Common Mistakes

**Mistake 1:** Server name is "(local)" or "."
```
❌ Won't work: mssql://@.:1433/db
✅ Use: mssql://user:pass@localhost:1433/db
```

**Mistake 2:** Password has special characters
```
❌ mssql://user:P@ss$123@server:1433/db   ← @ and $ confuse parser
✅ Manual connection with exact password    ← Better to handle special chars
```

**Mistake 3:** Using Windows Auth without server
```
❌ Needs explicit server: mssql://DOMAIN\user@localhost:1433/db
```

---

**Remember:** If DBeaver import doesn't work, manual connection always does! 🎉
