import sqlite3

conn = sqlite3.connect("data/documents.db")
cursor = conn.cursor()

rows = cursor.execute("SELECT * FROM documents").fetchall()

print("DB ROWS:")
for row in rows:
    print(row)

conn.close()
