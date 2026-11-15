# 🚀 QUICK REFERENCE - Manual SQL Server Connection

## In 5 Steps

### STEP 1: Open DBeaver → Edit Connection

```
DBeaver Left Sidebar:
  Database Connections
    ↓
  SQL Server Connection (right-click)
    ↓
  Edit Connection
```

---

### STEP 2: Write Down These Values

```
┌─────────────────────────────────────┐
│ WRITE THESE DOWN:                   │
├─────────────────────────────────────┤
│ Server Host:  ___________________   │
│ Port:         ___________________   │
│ Database:     ___________________   │
│ Username:     ___________________   │
│ Password:     ___________________   │
└─────────────────────────────────────┘
```

**Where to find each:**

```
DBeaver Connection Edit Window
    ↓
Main Tab
    ├─ Server Host [_____] ← First field at top
    ├─ Port [_____] ← Second field
    ├─ Database [_____] ← Third field
    ├─ User Name [_____] ← In Authentication section
    └─ Password [_____] ← Below User Name
            └─ [Show Password] button to reveal it
```

---

### STEP 3: Build Connection String

**Template:**
```
mssql://USERNAME:PASSWORD@SERVER:PORT/DATABASE
```

**Example:**
```
Given:
  Server: localhost
  Port: 1433
  Database: TestDB
  User: sa
  Pass: MyPassword123

Result:
  mssql://sa:MyPassword123@localhost:1433/TestDB
```

---

### STEP 4: Go to Lakeforge Settings

```
Browser: http://localhost:5173/settings
              ↓
       Settings Page
              ↓
       Click "+ Add Source"
```

---

### STEP 5: Fill & Submit

```
Form Fields:
┌────────────────────────────────────┐
│ Source Name: Production SQL Server │ ← Any name
│ Database Type: SQL Server          │ ← SELECT THIS
│ URI: mssql://sa:MyPass...@loc...   │ ← PASTE YOUR URI
│ Description: My test database      │ ← Optional
└────────────────────────────────────┘
                ↓
        [Add Source] Button
```

**Then:** Click "Test" to verify connection ✅

---

## Common Examples

### Example 1: Localhost
```
DBeaver Values:
  Server: localhost
  Port: 1433
  DB: master
  User: sa
  Pass: admin

Lakeforge URI:
  mssql://sa:admin@localhost:1433/master
```

### Example 2: Remote Server
```
DBeaver Values:
  Server: prod.company.com
  Port: 1433
  DB: SalesDB
  User: appuser
  Pass: SecurePass123

Lakeforge URI:
  mssql://appuser:SecurePass123@prod.company.com:1433/SalesDB
```

### Example 3: Windows Auth
```
DBeaver Values:
  Auth: Windows Authentication
  DB: TestDB
  Server: MYPC\SQLEXPRESS

Lakeforge URI:
  mssql://MYPC\SQLEXPRESS:1433/TestDB
  (password not needed)
```

---

## What If Password Has Special Characters?

**Password:** `P@ss$w0rd!`

```
Use it as-is in URI:
mssql://user:P@ss$w0rd!@server:1433/db

If it doesn't work:
→ Test in SSMS first
→ Verify exact password in DBeaver
→ Try again in Lakeforge
```

---

## ✅ URI Format Checklist

Before copying to Lakeforge:

```
☑ Format: mssql://user:pass@host:port/db
☑ Has @ symbol between password and server
☑ Has : symbol separating user and password
☑ Has : symbol separating server and port
☑ Has / before database name
☑ No extra spaces
☑ All values filled in
```

---

## 🧪 How to Test After Adding

```
Lakeforge Settings Page
        ↓
Sources List (bottom)
        ↓
Your new connection [Test] [Delete]
        ↓
Click [Test]
        ↓
✅ "Connection successful" → DONE!
❌ "Connection failed" → Check URI
```

---

## Troubleshooting Quick Map

| Error | Likely Cause | Fix |
|-------|---|---|
| Connection refused | Server not running | Check SQL Server service |
| Login failed | Wrong user/pass | Verify credentials in DBeaver |
| Database not found | DB doesn't exist | Use correct database name |
| Invalid URI | Format wrong | Check @ and : placement |
| Timeout | Server unreachable | Check firewall/network |

---

## ✨ You're Ready!

Follow these 5 steps and your SQL Server will be connected to Lakeforge manually. 🎉

**No DBeaver import needed - this always works!**
