# 📖 How to Get Connection Details From DBeaver & Connect Manually

## 🎯 Complete Step-by-Step Guide

I'll show you exactly how to extract connection details from DBeaver and use them in Lakeforge.

---

## PART 1: Extract Connection Details from DBeaver

### Step 1: Open DBeaver

```
1. Launch DBeaver
2. Look at the left sidebar
3. Find "Database Connections" section
4. You should see your SQL Server connection listed
```

**If you don't see connections:**
```
→ Click "Database" menu → "New Database Connection"
→ Create and save a test connection first
→ Then come back to these steps
```

---

### Step 2: Open Your SQL Server Connection Properties

```
1. In DBeaver left sidebar, find your SQL Server connection
   (It will have a SQL Server icon - usually looks like a cylinder/database icon)

2. Right-click on it
   ┌─────────────────────────────┐
   │ Edit Connection             │
   │ Copy                        │
   │ Disconnect                  │
   │ Delete                      │
   │ ...                         │
   └─────────────────────────────┘

3. Click "Edit Connection"
```

---

### Step 3: Find the Connection Details

A window will open showing all connection settings.

```
Look for these tabs/fields:
├─ Main Tab (usually first)
│  ├─ Server Name / Host
│  ├─ Port
│  ├─ Database
│  ├─ Username / User
│  └─ Password
│
└─ Other tabs (usually not needed)
   ├─ Network
   ├─ Security
   └─ Advanced
```

---

## 📝 Example: Finding Details for SQL Server

### Open Connection Settings

Here's what you'll see:

```
┌──────────────────────────────────────────┐
│   Edit Connection - My SQL Server        │
├──────────────────────────────────────────┤
│ Tabs: Main  | Network | Security | ...   │
├──────────────────────────────────────────┤
│                                          │
│ ☑ Connect by default                    │
│                                          │
│ Server Host:  [________localhost______]  │ ← WRITE THIS DOWN
│ Port:         [________1433___________]  │ ← WRITE THIS DOWN
│ Database:     [________master________]   │ ← WRITE THIS DOWN
│                                          │
│ Authentication:                          │
│  ○ Windows Authentication                │
│  ◉ SQL Server Authentication             │
│                                          │
│ User Name:    [________sa___________]   │ ← WRITE THIS DOWN
│ Password:     [________________]        │ ← WRITE THIS DOWN
│                                          │
│ [ Show Password ]                        │
│                                          │
│ [  Test Connection  ]                    │
│ [  Cancel  ]  [  OK  ]                   │
│                                          │
└──────────────────────────────────────────┘
```

---

### Step 4: Write Down Your Connection Details

**Create a text file and copy these values:**

```
Server Host:    _______________________
Port:           _______________________
Database Name:  _______________________
Username:       _______________________
Password:       _______________________
```

**For example (SQL Server):**

```
Server Host:    localhost
Port:           1433
Database Name:  TestDB
Username:       sa
Password:       MyPassword123
```

---

## 🔐 Viewing Your Password in DBeaver

If you don't remember your password:

```
1. In Edit Connection window
2. Look for "[ Show Password ]" button
3. Click it
4. Password will be revealed
5. Write it down for Lakeforge
```

**If password field is grayed out:**
```
→ DBeaver is using Windows Authentication
→ You don't have a password to enter
→ In Lakeforge, just leave password empty
```

---

## 🎯 PART 2: Connect Manually in Lakeforge

Now that you have the details, let's add them to Lakeforge.

### Step 1: Go to Settings Page

```
1. Open Lakeforge in browser: http://localhost:5173
2. Click "Settings" in the navigation menu
3. Or go directly: http://localhost:5173/settings
```

---

### Step 2: Click "+ Add Source" Button

```
You'll see a form like this:

Settings
├─ [🔗 DBeaver]  [+ Add Source]
│
├─ Source Name:
│  ┌────────────────────────┐
│  │                        │
│  └────────────────────────┘
│
├─ Database Type:
│  ┌─ ▼ MySQL ─────────────┐
│  │ ├─ PostgreSQL         │
│  │ ├─ SQL Server         │ ← SELECT THIS
│  │ ├─ Oracle             │
│  │ ├─ SQLite             │
│  │ ├─ Databricks         │
│  │ └─ S3                 │
│  └────────────────────────┘
│
├─ Connection URI:
│  ┌────────────────────────┐
│  │ mssql://user:pass...   │
│  └────────────────────────┘
│
└─ Description (optional)
```

---

### Step 3: Fill in the Form

#### Field 1: Source Name
```
What to enter: A friendly name for this connection

Examples:
✅ "Production SQL Server"
✅ "My Local Database"
✅ "TestDB"
✅ "Corporate Database"

Enter any name you want - this is just for Lakeforge to identify it.
```

#### Field 2: Database Type
```
What to select: SQL Server

1. Click the Database Type dropdown
2. Select "SQL Server"
3. Automatically fills URI template as: mssql://user:password@host:port/database
```

#### Field 3: Connection URI
```
This is where you put your connection details.

Format: mssql://username:password@server:port/database

Using your details from DBeaver:
Server Host:    localhost
Port:           1433
Database Name:  TestDB
Username:       sa
Password:       MyPassword123

Build your URI:
mssql://sa:MyPassword123@localhost:1433/TestDB
         ↑    ↑               ↑         ↑    ↑
         |    |               |         |    └─ Database Name
         |    |               |         └─ Port
         |    |               └─ Server Host
         |    └─ Password
         └─ Username
```

#### Field 4: Description (Optional)
```
Examples:
- "My test database"
- "Production server"
- "Dev environment"
- Anything you want to remember
```

---

### Step 4: Example - Complete Form

```
Source Name:     Production SQL Server
Database Type:   SQL Server
Connection URI:  mssql://sa:MyPassword123@localhost:1433/TestDB
Description:     Production database for my application
```

---

### Step 5: Click "Add Source" Button

```
After filling all required fields:
1. Click blue "Add Source" button
2. Wait for response (might take 2-3 seconds)
3. Should see one of:
   ✅ "Source added successfully!"  → SUCCESS
   ❌ "Failed to add source: ..."    → Check error message
```

---

## 🆘 Connection URI Format - Visual Guide

### SQL Server URI Format

```
                    
mssql://username:password@server:port/database
  ↑      ↑        ↑        ↑      ↑   ↑
  |      |        |        |      |   └─ Database name (from DBeaver "Database")
  |      |        |        |      └─ Port (from DBeaver "Port")
  |      |        |        └─ Server/Host (from DBeaver "Server Host")
  |      |        └─ Password (from DBeaver "Password")
  |      └─ Username (from DBeaver "User Name")
  └─ Database type identifier (always "mssql" for SQL Server)
```

### Real Examples

**Example 1: Local SQL Server**
```
DBeaver Details:
├─ Server Host:  localhost
├─ Port:         1433
├─ Database:     master
├─ User:         sa
└─ Password:     admin123

Lakeforge URI:
mssql://sa:admin123@localhost:1433/master
```

**Example 2: Remote SQL Server**
```
DBeaver Details:
├─ Server Host:  prod-db.company.com
├─ Port:         1433
├─ Database:     SalesDB
├─ User:         app_user
└─ Password:     Secure$Pass456

Lakeforge URI:
mssql://app_user:Secure$Pass456@prod-db.company.com:1433/SalesDB
```

**Example 3: SQL Server Named Instance**
```
DBeaver Details:
├─ Server Host:  MYCOMPUTER\SQLEXPRESS
├─ Port:         1433
├─ Database:     TestDB
├─ User:         admin
└─ Password:     pass123

Lakeforge URI:
mssql://admin:pass123@MYCOMPUTER\SQLEXPRESS:1433/TestDB
```

---

## ⚠️ Special Cases

### Case 1: No Password (Windows Authentication)

```
If DBeaver shows:
├─ Authentication: Windows Authentication
├─ User Name: [empty or domain\user]
└─ Password: [empty]

You can:
Option A: Leave password empty
URI: mssql://user@localhost:1433/database

Option B: Just omit password part
URI: mssql://localhost:1433/database
```

### Case 2: Special Characters in Password

```
If password has special characters like: P@ss$w0rd!

Option A: Use exact password (might work)
URI: mssql://user:P@ss$w0rd!@server:1433/db

Option B: Test and adjust if it fails
```

### Case 3: Default Port (1433)

```
If using default SQL Server port 1433, you can omit it:

Longer:  mssql://user:pass@server:1433/db
Shorter: mssql://user:pass@server/db
         (Both work, 1433 is assumed if omitted)
```

---

## ✅ Verification Steps

After entering your URI, before clicking "Add Source":

```
Double-check:
☑ Database Type is "SQL Server" (not MySQL, PostgreSQL, etc.)
☑ Username is spelled correctly (case-sensitive sometimes)
☑ Password is exact (special characters matter)
☑ Server name matches DBeaver exactly
☑ Port is correct (usually 1433 for SQL Server)
☑ Database name exists and you have access
```

---

## 🧪 Test Your Connection

After adding the source:

```
1. You'll see it in the Sources list
2. Click "Test" button next to it
3. Get immediate feedback:
   ✅ "Connection successful"  → All good!
   ❌ "Connection failed: ..." → Check credentials
```

---

## 🐛 Troubleshooting

### Error: "Connection refused"
```
Means: SQL Server not accessible/not running

Fix:
1. Verify SQL Server is running (check Windows Services)
2. Verify server name is correct (ping it if remote)
3. Check firewall isn't blocking port 1433
```

### Error: "Login failed"
```
Means: Wrong username or password

Fix:
1. Double-check user name in DBeaver
2. Reveal password in DBeaver and verify it's correct
3. Make sure authentication type matches (SQL Auth vs Windows Auth)
```

### Error: "Database not found"
```
Means: Database name doesn't exist or user can't access it

Fix:
1. Verify database name exists in SQL Server
2. Verify user has permission to access database
3. Try different database (like "master")
```

### Error: "Invalid source URI"
```
Means: URI format is incorrect

Fix:
1. Check format: mssql://user:pass@host:port/db
2. Make sure no spaces
3. Make sure @ symbol is between password and server
4. Make sure : symbols separate components correctly
```

---

## 📋 Checklists

### Before You Start (DBeaver)
- [ ] DBeaver is installed
- [ ] You have a SQL Server connection saved
- [ ] Can connect in DBeaver (Test Connection works)
- [ ] You know your username
- [ ] You know your password (or can reveal it)
- [ ] You know the server name/host
- [ ] You know which database to connect to

### Before You Click "Add Source" (Lakeforge)
- [ ] Source Name is filled in
- [ ] Database Type is set to "SQL Server"
- [ ] Connection URI is in correct format
- [ ] All values from DBeaver are correct
- [ ] No typos in username, password, server, database
- [ ] No extra spaces in URI

### After Adding Source
- [ ] Source appears in list
- [ ] Click "Test" to verify connection
- [ ] If test passes → Ready to use! ✅
- [ ] If test fails → Check error and fix

---

## 🎯 Visual Walkthrough

Here's the complete process visualized:

```
DBeaver Connection Properties
      │
      │ Right-click → Edit Connection
      ▼
┌─────────────────────────┐
│ Server:  localhost      │
│ Port:    1433           │
│ DB:      TestDB         │
│ User:    sa             │
│ Pass:    MyPassword123  │
└─────────────────────────┘
      │
      │ Write down these values
      ▼
Build Connection URI:
mssql://sa:MyPassword123@localhost:1433/TestDB
      │
      │ Copy this URI
      ▼
Lakeforge Settings Page
      │
      │ Click "+ Add Source"
      ▼
┌──────────────────────────────┐
│ Name: My SQL Server          │
│ Type: SQL Server             │
│ URI:  mssql://sa:MyPass...   │
│ Desc: My database            │
└──────────────────────────────┘
      │
      │ Click "Add Source"
      ▼
✅ Connected! 

Now you can:
├─ Inspect schema
├─ View profiles
├─ Get sample rows
├─ Ask questions
└─ Generate reports
```

---

## 📞 Still Having Issues?

If connection fails after following these steps:

**Please provide:**
1. Your DBeaver connection details (sanitized):
   - Server name
   - Database name
   - Authentication type (Windows/SQL Auth)
   
2. The exact error message from Lakeforge

3. Can you connect in SSMS (SQL Server Management Studio)?
   - YES → Network connection works, check URI format
   - NO → Server connectivity issue

---

## 🎉 Quick Summary

1. **Get details from DBeaver:**
   - Right-click connection → Edit Connection
   - Write down: Server, Port, Database, User, Password

2. **Format as URI:**
   - `mssql://username:password@server:port/database`

3. **Add to Lakeforge:**
   - Settings → "+ Add Source"
   - Enter Name, Select "SQL Server"
   - Paste URI
   - Click "Add Source"

4. **Test:**
   - Click "Test" button
   - Should see success message ✅

---

**That's it! You now have manual SQL Server connection working in Lakeforge.** 🎉

The DBeaver import feature can be addressed later - manual connection is more reliable anyway!
