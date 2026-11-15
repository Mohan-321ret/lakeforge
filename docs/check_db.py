from pathlib import Path

p = Path(__file__).resolve().parent / "sample_data.db"
print("exists:", p.exists())
if p.exists():
    print("size:", p.stat().st_size, "bytes")
    c = sqlite3.connect(p)
    rows = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("tables:", rows)
    for (name,) in rows:
        count = c.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
        print(f"  {name}: {count} rows")
    c.close()
