import cv2
import os
import numpy as np

path = "images"
recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

faces = []
labels = []
names = {}
current_id = 0

for img_name in os.listdir(path):
    img_path = os.path.join(path, img_name)
    gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    name = img_name.split("_")[0]

    if name not in names:
        names[name] = current_id
        current_id += 1

    faces.append(gray)
    labels.append(names[name])

recognizer.train(faces, np.array(labels))
os.makedirs("trainer", exist_ok=True)
recognizer.save("trainer/face_model.xml")

with open("trainer/names.txt", "w") as f:
    for k, v in names.items():
        f.write(f"{k}:{v}\n")

print("Training complete. Model saved in trainer/face_model.xml")
