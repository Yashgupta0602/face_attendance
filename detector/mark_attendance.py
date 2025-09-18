import cv2
import face_recognition
import pickle
import sqlite3
from datetime import date

# -------------------------------
# Load encodings
# -------------------------------
print("🔄 Loading encodings...")
with open("detector/encodings.pickle", "rb") as f:
    known_encodings, known_rolls = pickle.load(f)

print(f"✅ Loaded {len(known_encodings)} student encodings")

# -------------------------------
# Connect to DB
# -------------------------------
conn = sqlite3.connect("backend/students.db")
cursor = conn.cursor()

# Create attendance table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT,
    date TEXT,
    status TEXT
)
""")
conn.commit()

today = str(date.today())
print(f"📅 Taking attendance for {today}")

# -------------------------------
# Start webcam
# -------------------------------
video = cv2.VideoCapture(0)

present_students = set()

while True:
    ret, frame = video.read()
    if not ret:
        break

    # Resize frame for speed
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    face_locations = face_recognition.face_locations(rgb_small)
    face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

    for encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)

        if True in matches:
            match_index = matches.index(True)
            roll_no = known_rolls[match_index]

            present_students.add(roll_no)

            # Draw box with roll no
            top, right, bottom, left = top*4, right*4, bottom*4, left*4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, roll_no, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow("Attendance System", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()

# -------------------------------
# Save attendance to DB
# -------------------------------
for roll in known_rolls:
    status = "Present" if roll in present_students else "Absent"
    cursor.execute("INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)", (roll, today, status))

conn.commit()
conn.close()

print("📋 Attendance saved to DB!")