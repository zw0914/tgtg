### MTCNN + Facnet
### $pip install mtcnn
### load mode from facenet pre-trained model 
import h5py
import numpy as np
from mtcnn.mtcnn import MTCNN
import time
import cv2
import imutils
from scipy.spatial import distance
import tensorflow as tf
import tensorflow.keras as keras
from tensorflow.keras.models import load_model

video_file = "comein8.mp4"
face_detect = "mtcnn"

displayWidth = 500
min_faceSzie = (40, 40)

tracker_type = "MEDIANFLOW"  #BOOSTING, CSRT, TLD, MIL, KCF, MEDIANFLOW, MOSSE

valid = "valid/"

min_score = 0.90
image_size = 160
giveupScore = 0.8
face_extend_head_ratio = 1.5
black_padding_width = 2  #add padding width for the face area

dataset_file = "officedoor.h5"
model_path = 'models/facenet_keras.h5'
model = load_model(model_path)

if(face_detect=="mtcnn"):
    detector = MTCNN()
elif(face_detect=="dlib"):
    detector = dlib.get_frontal_face_detector()
else:
    detector = cv2.CascadeClassifier(cascade_path)

hf = h5py.File(dataset_file, 'r')
valid_names = hf.get('names')
valid_embs = hf.get('embs')
print("HF file loaded, valid names:", valid_names)

def get_faces(img):
    faces = []
    if(face_detect=="mtcnn"):
        allfaces = detector.detect_faces(img)
        for face in allfaces:
            print("face", face["box"])
            x = face["box"][0]
            y = face["box"][1]
            w = face["box"][2]
            h = face["box"][3]
            faces.append((int(x),int(y),int(w),int(h)))
    elif(face_detect=="dlib"):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 2)
        for rect in rects:
            (x, y, w, h) = rect_to_bb(rect)
            faces.append((int(x),int(y),int(w),int(h)))
    else:
        allfaces = detector.detectMultiScale(img, scaleFactor=1.10, minNeighbors=5)
        for face in allfaces:
            (x, y, w, h) = face
            faces.append((int(x),int(y),int(w),int(h)))
    if(len(faces)>0):
        return faces
    else:
        return None

def draw_face(img, bbox, txt):
    fontSize = round(img.shape[0] / 930, 1)
    if(fontSize<0.35): fontSize = 0.35
    boldNum = int(img.shape[0] / 500)
    if(boldNum<1): boldNum = 1
    if(bbox is not None):
        x = int(bbox[0])
        y = int(bbox[1])
        w = int(bbox[2])
        h = int(bbox[3])
        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),boldNum)
        print ("draw:", bbox)
        cv2.putText(img, txt, (x, y-(boldNum*3)), cv2.FONT_HERSHEY_COMPLEX, fontSize, (0,255,0), boldNum+1)
    return img

def prewhiten(x):
    if x.ndim == 4:
        axis = (1, 2, 3)
        size = x[0].size
    elif x.ndim == 3:
        axis = (0, 1, 2)
        size = x.size
    else:
        raise ValueError('Dimension should be 3 or 4')

    mean = np.mean(x, axis=axis, keepdims=True)
    std = np.std(x, axis=axis, keepdims=True)
    std_adj = np.maximum(std, 1.0/np.sqrt(size))
    y = (x - mean) / std_adj
    return y

def l2_normalize(x, axis=-1, epsilon=1e-10):
    output = x / np.sqrt(np.maximum(np.sum(np.square(x), axis=axis, keepdims=True), epsilon))
    return output

def preProcess(img):
    whitenImg = prewhiten(img)
    whitenImg = whitenImg[np.newaxis, :]
    return whitenImg

def process(face, img, margin):
    (x, y, w, h) = face
    if(w>min_faceSzie[0] and h>min_faceSzie[1]):
        faceArea = img[y:y+h, x:x+w]
        w = faceArea.shape[1]
        h = faceArea.shape[0]
        faceMargin = np.zeros((h+margin*2, w+margin*2, 3), dtype = "uint8")
        faceMargin[margin:margin+h, margin:margin+w] = faceArea
        cv2.imwrite("tmp/"+str(time.time())+".jpg", faceMargin)
        aligned = cv2.resize(faceMargin ,(image_size, image_size))
        aligned = preProcess(aligned)
        return aligned, (x,y,w,h)
    else:
        return None, None

def face2name(face, img, faceEMBS, faceNames):
    imgFace, bbox = process(face, img, black_padding_width)
    if(imgFace is None):
        return None, None, None
    embs = l2_normalize(np.concatenate(model.predict(imgFace)))
    smallist_id = 0
    smallist_embs = 999
    for id, valid in enumerate(faceEMBS):
        distanceNum = distance.euclidean(embs, valid)
        if(smallist_embs>distanceNum):
            smallist_embs = distanceNum
            smallist_id = id
    print(faceNames[smallist_id].decode(), smallist_embs)
    return smallist_id, faceNames[smallist_id].decode(), smallist_embs

def displayFrame(frame, head, txtStatus):
    displayImg = draw_face(frame, head, txtStatus)
    cv2.imshow("frame", imutils.resize(displayImg, width=displayWidth))
    cv2.waitKey(1)

if tracker_type == 'BOOSTING':
    tracker = cv2.TrackerBoosting_create()
if tracker_type == 'MIL':
    tracker = cv2.TrackerMIL_create()
if tracker_type == 'KCF':
    tracker = cv2.TrackerKCF_create()
if tracker_type == 'TLD':
    tracker = cv2.TrackerTLD_create()
if tracker_type == 'MEDIANFLOW':
    tracker = cv2.TrackerMedianFlow_create()
if tracker_type == 'GOTURN':
    tracker = cv2.TrackerGOTURN_create()
if tracker_type == 'MOSSE':
    tracker = cv2.TrackerMOSSE_create()
if tracker_type == "CSRT":
    tracker = cv2.TrackerCSRT_create()

VIDEO_IN = cv2.VideoCapture(video_file)
hasFrame = True
facebox = None
txtStatus = None

while hasFrame:
    hasFrame, frame = VIDEO_IN.read()
    if not hasFrame:
        break

    displayImg = frame.copy()
    faceBoxes = get_faces(frame)

    if(faceBoxes is not None):
        face = faceBoxes[0]
        valid_id, valid_name, score = face2name( face, frame, valid_embs, valid_names)
        if(valid_id is not None):
            head = (face[0], face[1], int(face[2]*face_extend_head_ratio), int(face[3]*face_extend_head_ratio))
            displayFrame(frame, head, valid_name)
            ok = tracker.init(frame, head)
            trackStatus = True

            while trackStatus is True:
                hasFrame, frame = VIDEO_IN.read()
                trackStatus, head = tracker.update(frame)
                displayFrame(frame, head, valid_name)
            facebox = head
            txtStatus = valid_name
    else:
        facebox = None
        txtStatus = "No face"
    displayFrame(frame, None, txtStatus)