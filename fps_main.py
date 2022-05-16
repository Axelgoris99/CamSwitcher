# Import for videoStream
import cv2
import mediapipe as mp
import numpy as np
from WebcamVideoStream import WebcamVideoStream
from imutils import resize
from obswebsocket import obsws, requests  # noqa: E402

# Import websocket
import sys
import time
import logging

# User's info
import json
# Opening JSON file
f = open('info.json')
# returns JSON object as
# a dictionary
info = json.load(f)

# Login
logging.basicConfig(level=logging.INFO)

sys.path.append('../')

host = info["host"]
port = info["port"]
password = info["password"]
scene1 = info["scene1"]
scene2 = info["scene2"]
nbWebCam = info["webcam"]

ws = obsws(host, port, password)
ws.connect()

# Face Detection
# https://github.com/khalidmeister/head-pose-estimation
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.5, min_tracking_confidence=0.5)

currentNbWebCam = nbWebCam
vs = WebcamVideoStream(src=nbWebCam, sizeX=320, sizeY=280).start()

while (True):
    time.sleep(1)
    image = vs.read()
    # Resize for quicker analysis. Might lead to some quality loss
    image = resize(image, width=320)

    # To improve performance
    image.flags.writeable = False

    # Get the result
    results = face_mesh.process(image)

    # To improve performance
    image.flags.writeable = True

    img_h, img_w, img_c = image.shape
    face_3d = []
    face_2d = []

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            for idx, lm in enumerate(face_landmarks.landmark):
                if idx == 33 or idx == 263 or idx == 1 or idx == 61 or idx == 291 or idx == 199:
                    x, y = int(lm.x * img_w), int(lm.y * img_h)
                    # Get the 2D Coordinates
                    face_2d.append([x, y])

                    # Get the 3D Coordinates
                    face_3d.append([x, y, lm.z])

                    # Convert it to the NumPy array
            face_2d = np.array(face_2d, dtype=np.float64)

            # Convert it to the NumPy array
            face_3d = np.array(face_3d, dtype=np.float64)

            # The camera matrix
            focal_length = 1 * img_w

            cam_matrix = np.array([[focal_length, 0, img_h / 2],
                                   [0, focal_length, img_w / 2],
                                   [0, 0, 1]])

            # The Distance Matrix
            dist_matrix = np.zeros((4, 1), dtype=np.float64)

            # Solve PnP
            success, rot_vec, trans_vec = cv2.solvePnP(
                face_3d, face_2d, cam_matrix, dist_matrix)

            # Get rotational matrix
            rmat, jac = cv2.Rodrigues(rot_vec)

            # Get angles
            angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

            # Get the y rotation degree
            x = angles[0] * 360
            y = angles[1] * 360

            # print(y)

            # See where the user's head tilting
            if y < -20:
                text = "Looking Right"
                print(text)
                ws.call(requests.SetCurrentScene(scene1))
            elif y > 20:
                text = "Looking Left"
                print(text)
                ws.call(requests.SetCurrentScene(scene2))
    # cv2.imshow('Webcam Swapper Test', image)

    c = cv2.waitKey(1)
    if c == 27:
        break

    currentNbWebCam = nbWebCam

vs.stop()
cv2.destroyAllWindows()
