import cv2
import pickle
import numpy as np

print("📸 Look at camera")
cam = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

while True:
    ret, frame = cam.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    # Draw box around face
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)

    cv2.imshow("Press SPACE when your face is in the box", frame)

    if cv2.waitKey(1) == 32:  # spacebar
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))

            with open("face_data.pkl", "wb") as f:
                pickle.dump(face_img, f)
            print("✅ Face registered successfully!")
        else:
            print("❌ No face detected — try again")
        break

cam.release()
cv2.destroyAllWindows()