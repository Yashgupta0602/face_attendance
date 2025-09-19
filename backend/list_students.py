import sqlite3

conn = sqlite3.connect("backend/students.db")
cursor = conn.cursor()

cursor.execute("SELECT id, name, roll_no FROM students")
rows = cursor.fetchall()

print("📋 Current Students in DB:")
for r in rows:
    print(r)

conn.close()
