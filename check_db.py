import os
import sqlite3

p = r"c:\Users\MohanaPrasanthSivaku\Desktop\lakeforge\sample_data.db"
print("exists:", os.path.exists(p))
if os.path.exists(p):
    print("size:", os.path.getsize(p), "bytes")
    c = sqlite3.connect(p)
    rows = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("tables:", rows)
    for (name,) in rows:
        count = c.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
        print(f"  {name}: {count} rows")
    c.close()
