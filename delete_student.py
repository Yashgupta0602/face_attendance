import sqlite3
import pickle
import os
import sys

DB_PATH = "backend/students.db"
ENC_PATH = "detector/encodings.pickle"

def delete_student(name_or_roll):
    # 1. Connect to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find student
    cursor.execute("SELECT id, name, roll_no, image_path FROM students WHERE name=? OR roll_no=?", (name_or_roll, name_or_roll))
    student = cursor.fetchone()

    if not student:
        print(f"❌ Student '{name_or_roll}' not found in DB.")
        conn.close()
        return

    student_id, name, roll_no, image_path = student
    print(f"🗑 Deleting {name} (Roll {roll_no})...")

    # Delete from DB
    cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()

    # 2. Update encodings.pickle
    if os.path.exists(ENC_PATH):
        with open(ENC_PATH, "rb") as f:
            encodings, names = pickle.load(f)

        # Remove student's entries
        new_encodings = []
        new_names = []
        for enc, n in zip(encodings, names):
            if n != name:   # keep all except this student
                new_encodings.append(enc)
                new_names.append(n)

        # Save updated encodings
        with open(ENC_PATH, "wb") as f:
            pickle.dump((new_encodings, new_names), f)

        print(f"✅ Removed {name} from encodings.pickle too.")

    print("✔ Student deleted successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_student.py <student_name_or_roll>")
    else:
        delete_student(sys.argv[1])
