import cv2
import pickle

TARGET_SAMPLES = 80


def prepare_face(gray, x, y, w, h):
    face = gray[y + int(h * 0.2): y + int(h * 0.75), x + int(w * 0.15): x + int(w * 0.85)]
    face = cv2.resize(face, (100, 100))
    return cv2.equalizeHist(face)


cam = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

samples = []
capturing = False
frame_count = 0

print("📸 Look at the camera. Press SPACE to start, ESC to cancel")

while True:
    ret, frame = cam.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    face = max(faces, key=lambda f: f[2] * f[3]) if len(faces) else None

    if face is not None:
        x, y, w, h = face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.rectangle(
            frame,
            (x + int(w * 0.15), y + int(h * 0.2)),
            (x + int(w * 0.85), y + int(h * 0.75)),
            (255, 200, 0), 1
        )
        if capturing:
            frame_count += 1
            if frame_count % 3 == 0:
                samples.append(prepare_face(gray, x, y, w, h))

    display = cv2.flip(frame, 1)

    if capturing:
        msg = f"Capturing {len(samples)}/{TARGET_SAMPLES} - turn head slightly"
    elif face is None:
        msg = "No face detected"
    else:
        msg = "Press SPACE to start"
    cv2.putText(display, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Face registration", display)

    key = cv2.waitKey(1)
    if key == 27:
        print("❌ Cancelled")
        break
    if key == 32 and face is not None:
        capturing = True

    if len(samples) >= TARGET_SAMPLES:
        with open("face_data.pkl", "wb") as f:
            pickle.dump(samples, f)
        print(f"✅ Face registered successfully with {len(samples)} samples!")
        break

cam.release()
cv2.destroyAllWindows()