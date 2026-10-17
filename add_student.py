import cv2
import face_recognition
import pickle
import sqlite3
import os
import sys


DB_PATH = "backend/students.db"
ENCODINGS_PATH = "detector/encodings.pickle"


def add_student(name, roll_no, image_path=None):
    
    if os.path.exists(ENCODINGS_PATH):
        with open(ENCODINGS_PATH, "rb") as f:
            encodings, names = pickle.load(f)
    else:
        encodings, names = [], []

    
    if image_path:
        image = cv2.imread(image_path)
    else:
        cap = cv2.VideoCapture(0)
        print("📷 Capturing photo... Press 's' to save when ready")
        while True:
            ret, frame = cap.read()
            cv2.imshow("Capture Student Face", frame)
            if cv2.waitKey(1) & 0xFF == ord("s"):
                image = frame
                break
        cap.release()
        cv2.destroyAllWindows()

    
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb)
    encs = face_recognition.face_encodings(rgb, boxes)

    if len(encs) == 0:
        print("❌ No face found in image. Try again.")
        return

    encodings.append(encs[0])
    names.append(name)

    
    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump((encodings, names), f)
    print(f"✅ Encoding saved for {name}")

    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (name, roll_no) VALUES (?, ?)",
        (name, roll_no)
    )
    conn.commit()
    conn.close()
    print(f"✅ Added {name} (Roll {roll_no}) to database")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_student.py <Name> <RollNo> [ImagePath]")
        sys.exit(1)

    name = sys.argv[1]
    roll_no = sys.argv[2]
    image_path = sys.argv[3] if len(sys.argv) > 3 else None

    add_student(name, roll_no, image_path)
