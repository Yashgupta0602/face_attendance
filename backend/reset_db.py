import sqlite3

conn = sqlite3.connect("backend/students.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM students")
conn.commit()
conn.close()

print("✅ All students deleted, database reset.")
