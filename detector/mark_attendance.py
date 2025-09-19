import cv2
import face_recognition
import pickle
import sqlite3
import time
from datetime import date

# ---------------- Load encodings (supports dict or tuple formats) ----------------
ENCODINGS_PATH = "detector/encodings.pickle"

print("📂 Loading encodings from", ENCODINGS_PATH)
try:
    with open(ENCODINGS_PATH, "rb") as f:
        loaded = pickle.load(f)
except FileNotFoundError:
    raise SystemExit(f"❌ encodings file not found at {ENCODINGS_PATH}. Run encode script first.")

# Normalize loaded format to (encodings, names)
if isinstance(loaded, dict):
    encodings = loaded.get("encodings") or loaded.get("encs") or []
    names     = loaded.get("names")     or loaded.get("rolls") or []
elif isinstance(loaded, (list, tuple)):
    if len(loaded) >= 2:
        encodings, names = loaded[0], loaded[1]
    else:
        raise SystemExit("❌ encodings.pickle has unexpected tuple/list structure.")
else:
    raise SystemExit("❌ encodings.pickle has unknown structure. Inspect it with check_pickle.py")

if not encodings or not names or len(encodings) != len(names):
    print("⚠ Warning: encodings/names length mismatch or empty. Proceeding but results may be wrong.")
print(f"✅ Loaded {len(encodings)} known faces")

# ---------------- Database setup ----------------
DB_PATH = "backend/students.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ensure attendance table exists (timestamp default)
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    roll_no TEXT,
    status TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ---------------- Open camera ----------------
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    conn.close()
    raise SystemExit("❌ Could not open webcam. Check your camera or camera index.")

print("📷 Camera started. Scanning for 30 seconds. Press 'q' to stop early.")
start_time = time.time()
present_names = set()

# Loop: read frames until 30 seconds elapse (or user quits)
while True:
    ret, frame = video_capture.read()
    if not ret:
        # sometimes camera may briefly fail; try next iteration
        print("⚠ Warning: no frame received; retrying...")
        time.sleep(0.1)
        # still check timeout
        if time.time() - start_time >= 30:
            print("⏳ 30s elapsed while waiting for frames. Exiting.")
            break
        continue

    # Resize for speed (process on smaller frame)
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Detect & encode faces in the small frame
    face_locs = face_recognition.face_locations(rgb_small)
    face_encs = face_recognition.face_encodings(rgb_small, face_locs)

    # For each detected face, compare with known encodings
    for (face_encoding, face_loc) in zip(face_encs, face_locs):
        # Compare & get distances
        matches = face_recognition.compare_faces(encodings, face_encoding, tolerance=0.5)
        # choose best match by distance (more robust than first True)
        if any(matches):
            distances = face_recognition.face_distance(encodings, face_encoding)
            # find index among matches with smallest distance
            matched_idxs = [i for i, m in enumerate(matches) if m]
            best_idx = min(matched_idxs, key=lambda i: distances[i])
            name = names[best_idx]
            # scale face_loc back to original frame size (we downscaled by 0.25)
            top, right, bottom, left = face_loc
            top *= 4; right *= 4; bottom *= 4; left *= 4

            # Add to present set and write to DB immediately (if first time seen)
            if name not in present_names:
                present_names.add(name)
                print(f"✅ Detected: {name}")

                # Look up roll_no in DB using name (fallback to UNKNOWN)
                cursor.execute("SELECT roll_no FROM students WHERE name = ?", (name,))
                row = cursor.fetchone()
                roll_no = row[0] if row else "UNKNOWN"

                # Upsert for today's date (avoid duplicates): update if exists, else insert
                today = date.today().isoformat()
                cursor.execute("SELECT id FROM attendance WHERE roll_no = ? AND DATE(timestamp) = ?", (roll_no, today))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("UPDATE attendance SET student_name=?, status=?, timestamp=CURRENT_TIMESTAMP WHERE id = ?",
                                   (name, "Present", existing[0]))
                else:
                    cursor.execute("INSERT INTO attendance (student_name, roll_no, status) VALUES (?, ?, ?)",
                                   (name, roll_no, "Present"))
                conn.commit()

            # Draw box + label on original frame
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"{name}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Show the camera feed
    cv2.imshow("Attendance Camera", frame)

    # check keyboard (q to quit early)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("🛑 Stopped by user.")
        break

    # check timeout
    if time.time() - start_time >= 30:
        print("⏰ 30 seconds completed.")
        break

# release resources
video_capture.release()
cv2.destroyAllWindows()

# ---------------- Mark absent students (optional, ensures everyone gets an entry) ----------------
print("📝 Finalizing attendance (marking absentees)...")
today = date.today().isoformat()
cursor.execute("SELECT name, roll_no FROM students")
students = cursor.fetchall()  # list of (name, roll_no)

for name, roll in students:
    # If student already has a record for today, skip (we updated/inset present above)
    cursor.execute("SELECT id FROM attendance WHERE roll_no = ? AND DATE(timestamp) = ?", (roll, today))
    if cursor.fetchone():
        continue
    # otherwise insert Absent
    cursor.execute("INSERT INTO attendance (student_name, roll_no, status) VALUES (?, ?, ?)", (name, roll, "Absent"))

conn.commit()
conn.close()
print(f"✅ Attendance complete. Present: {len(present_names)} | Total students checked: {len(students)}")
