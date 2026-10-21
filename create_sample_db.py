import os
import sqlite3

db_path = r"c:\Users\MohanaPrasanthSivaku\Desktop\lakeforge\sample_data.db"

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        country TEXT,
        signup_date TEXT
    )
""")

cursor.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        amount REAL,
        order_date TEXT,
        status TEXT
    )
""")

customers = [
    (1, "Alice Johnson", "alice@example.com", "USA", "2024-01-15"),
    (2, "Bob Smith", "bob@example.com", "UK", "2024-02-20"),
    (3, "Carol White", "carol@example.com", "Canada", "2024-03-10"),
    (4, "David Brown", "david@example.com", "USA", "2024-01-25"),
    (5, "Eve Davis", "eve@example.com", "Australia", "2024-04-05"),
]

orders = [
    (1, 1, 150.50, "2024-02-01", "completed"),
    (2, 2, 200.00, "2024-02-15", "completed"),
    (3, 1, 75.25, "2024-03-01", "pending"),
    (4, 3, 320.00, "2024-03-10", "completed"),
    (5, 2, 45.99, "2024-03-20", "cancelled"),
    (6, 4, 189.50, "2024-04-01", "completed"),
    (7, 5, 599.99, "2024-04-05", "completed"),
]

cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)

conn.commit()
conn.close()

print(f"Created {db_path}")
print(f"Size: {os.path.getsize(db_path)} bytes")

# Verify
conn = sqlite3.connect(db_path)
for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    count = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
    print(f"  {name}: {count} rows")
conn.close()
