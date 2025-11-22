import sqlite3
import sys

if len(sys.argv) < 2:
    print("❌ Usage: python delete_student.py <roll_no or name>")
    sys.exit(1)

target = sys.argv[1]

conn = sqlite3.connect("backend/students.db")
cursor = conn.cursor()

# Try deleting by roll_no or by name
cursor.execute("DELETE FROM students WHERE roll_no = ? OR name = ?", (target, target))
if cursor.rowcount > 0:
    conn.commit()
    print(f"✅ Student '{target}' deleted successfully from DB.")
else:
    print(f"❌ Student '{target}' not found in DB.")

conn.close()
