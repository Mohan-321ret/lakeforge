# 🔐 DBeaver Import with Password Prompt

## What Changed?

DBeaver **encrypts passwords** for security. We discovered:

```
✅ CAN Extract:  Connection metadata (host, port, database, driver)
❌ CANNOT Extract: Passwords (encrypted in credentials-config.json)
```

**Solution:** Frontend now asks for password when importing DBeaver connections.

---

## 🚀 How to Use

### Step 1: Click DBeaver Import
Go to Settings → Click **🔗 DBeaver** button

### Step 2: See Your Saved Connections
The panel shows all your DBeaver connections:
```
✓ bi3-intern-2026
  sqlserver • Host: bi3interndbserver.database.windows.net
  
  [Enter password...] [✓ Import]
```

### Step 3: Enter Password
- Type the database password (NOT your DBeaver password)
- For Azure SQL: Your database password (e.g., `BrightStar136`)
- For local: Your database user password

### Step 4: Click Import
- URI is automatically built with password included
- Connection saved to Lakeforge
- Ready to inspect!

---

## 📝 Example Flow

```
DBeaver has saved:
  Server: bi3interndbserver.database.windows.net:1433
  Database: bi3-intern-2026
  Username: sa
  
Lakeforge shows password prompt:
  Enter password: [••••••••••••] [✓ Import]
  
Lakeforge generates complete URI:
  mssql://sa:BrightStar136@bi3interndbserver.database.windows.net:1433/bi3-intern-2026
  
Connection imported! Ready to inspect.
```

---

## ✅ Implementation Details

**What was updated:**

1. **Frontend (Settings.jsx)**
   - Added password input field for each DBeaver connection
   - Password validation (must enter before importing)
   - Password cleared on panel close (for security)
   - Support for multiple connections at once

2. **CSS (Settings.css)**
   - Password input styled with monospace font
   - Proper focus states and validation feedback
   - Responsive layout for mobile devices

3. **Backend (dbeaver_importer.py)**
   - Documentation explains encryption limitation
   - Backend still extracts: host, port, database, driver, username
   - Frontend adds password to complete the URI

4. **Security**
   - Passwords are NOT logged
   - Passwords are NOT stored in config files
   - Passwords only used to build connection URI
   - Passwords match DBeaver's security practices

---

## 🔒 Why This Approach?

**DBeaver's Design:**
- Encrypts passwords for security → prevents config theft
- Stores metadata unencrypted → fast connection listing
- User enters password when needed → same as manual setup

**Lakeforge's Approach:**
- Extracts metadata from DBeaver (no need to re-type server name)
- User enters password (secure, one-time entry)
- Builds complete connection URI
- Connects and inspects immediately

**Best Practices:**
✅ Don't auto-extract encrypted passwords
✅ Prompt for secrets once
✅ Use for immediate connection
✅ Don't persist in config

---

## 📋 Testing

### Test Case 1: DBeaver Import
```
1. Go to Settings page
2. Click "🔗 DBeaver" button
3. See "bi3-intern-2026" listed
4. Enter password: BrightStar136
5. Click "✓ Import"
6. Connection should appear in sources list
```

### Test Case 2: Password Validation
```
1. Click "🔗 DBeaver" button
2. Try clicking "Import" WITHOUT entering password
3. Should show alert: "Please enter the database password"
```

### Test Case 3: Panel Close
```
1. Click "🔗 DBeaver" button
2. Enter password in one connection
3. Click ✕ to close panel
4. Click "🔗 DBeaver" again
5. Password field should be empty (cleared for security)
```

---

## 🎯 Next Steps

1. **Restart Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Test Import:**
   - Go to http://localhost:5173/settings
   - Click "🔗 DBeaver"
   - Enter your database password
   - Click "Import"

3. **Verify:**
   - Check sources list shows the imported connection
   - Try inspecting data with the imported source

---

## 🆘 Troubleshooting

**Problem:** "No DBeaver connections found"
- Make sure DBeaver is installed
- Save at least one connection in DBeaver
- Close and restart Lakeforge

**Problem:** Import fails with ODBC error
- Check database server is running
- Verify password is correct
- Try manual connection instead

**Problem:** Password field not showing
- Clear browser cache (Ctrl+Shift+Delete)
- Hard refresh page (Ctrl+F5)
- Restart frontend server

---

## 📚 Related Documentation

- [Database Connectors Guide](./DATABASE_CONNECTORS_GUIDE.md)
- [Manual Connection Setup](./MANUAL_CONNECTION_SETUP.md)
- [Connection Troubleshooting](./CONNECTION_TROUBLESHOOTING.md)

---

**The password prompt is intentional and follows security best practices!** 🔐
