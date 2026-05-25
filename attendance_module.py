import cv2
import pandas as pd
import os
from datetime import datetime

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/face_model.xml")

# Load names
names = {}
with open("trainer/names.txt", "r") as f:
    for line in f:
        name, id_ = line.strip().split(":")
        names[int(id_)] = name

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
attendance_file = "attendance.csv"

if not os.path.exists(attendance_file):
    pd.DataFrame(columns=["Name", "Date", "Time"]).to_csv(attendance_file, index=False)

cam = cv2.VideoCapture(0)
print("Press 'q' to quit")

while True:
    ret, frame = cam.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        id_, conf = recognizer.predict(gray[y:y+h, x:x+w])
        if conf < 60:
            name = names[id_]
            cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            today = datetime.now().strftime("%Y-%m-%d")
            now = datetime.now().strftime("%H:%M:%S")

            df = pd.read_csv(attendance_file)
            if not ((df["Name"] == name) & (df["Date"] == today)).any():
                df.loc[len(df)] = [name, today, now]
                df.to_csv(attendance_file, index=False)
                print(f"{name} marked at {now}")
        else:
            cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)

    cv2.imshow("Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
