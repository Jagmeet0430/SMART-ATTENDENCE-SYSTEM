import cv2
import os

name = input("Enter student name: ")
folder = "images"
os.makedirs(folder, exist_ok=True)

cam = cv2.VideoCapture(0)
count = 0

print("Press 'q' to stop capturing")
while True:
    ret, frame = cam.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        count += 1
        cv2.imwrite(f"{folder}/{name}_{count}.jpg", gray[y:y+h, x:x+w])
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

    cv2.imshow("Capture Faces", frame)
    if cv2.waitKey(1) & 0xFF == ord('q') or count >= 30:
        break

cam.release()
cv2.destroyAllWindows()
print(f"Captured {count} images for {name}")
