import face_recognition
import os, pickle

image_dir = "data"  # folder with student images
known_encodings = []
known_rolls = []

print("🚀 Starting encoding...")

for file in os.listdir(image_dir):
    if file.endswith((".jpg", ".png", ".jpeg")):
        roll = os.path.splitext(file)[0]   # filename = roll_no.jpg
        path = os.path.join(image_dir, file)

        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)

        if encodings:  # if face detected
            encoding = encodings[0]  # numpy array of floats
            known_encodings.append(encoding)
            known_rolls.append(roll)
            print(f"✅ Encoded {roll}")
        else:
            print(f"⚠ No face found in {file}, skipping")

# Save encodings and rolls separately
with open("detector/encodings.pickle", "wb") as f:
    pickle.dump((known_encodings, known_rolls), f)

print("💾 Encodings saved successfully!")
