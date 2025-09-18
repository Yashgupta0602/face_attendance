import dlib
import numpy as np

print("dlib version:", dlib.__version__)

detector = dlib.get_frontal_face_detector()

img = np.zeros((500, 500, 3), dtype=np.uint8)
faces = detector(img)

print("Number of faces detected:", len(faces))
