from statistics import mode

import cv2
from keras.models import load_model
import numpy as np

from emo_utils.datasets import get_labels
from emo_utils.inference import detect_faces
from emo_utils.inference import draw_text
from emo_utils.inference import draw_bounding_box
from emo_utils.inference import apply_offsets
from emo_utils.inference import load_detection_model
from emo_utils.preprocessor import preprocess_input
import subprocess
import fr_image 
#import or_image
#from webapp import db,Actor

# parameters for loading data and images
detection_model_path = '../trained_models/detection_models/haarcascade_frontalface_default.xml'
emotion_model_path = '../trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5'
emotion_labels = get_labels('fer2013')

# hyper-parameters for bounding boxes shape
frame_window = 10
emotion_offsets = (20, 40)

# loading models
face_detection = load_detection_model(detection_model_path)
emotion_classifier = load_model(emotion_model_path, compile=False)

# getting input model shapes for inference
emotion_target_size = emotion_classifier.input_shape[1:3]

# starting lists for calculating modes
emotion_window = []

# starting video streaming



cv2.namedWindow('window_frame')
video_capture = cv2.VideoCapture('videoplayback.mp4')
frame_no=0
length = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
while frame_no<20:
    bgr_image = video_capture.read()[1]
    gray_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    faces = detect_faces(face_detection, gray_image)

    # object_predictions=or_image.evaluate(rgb_image,video_capture)
    # print(object_predictions)

    for face_coordinates in faces:
        x1, x2, y1, y2 = apply_offsets(face_coordinates, emotion_offsets)

        rgbfacerec=rgb_image[y1:y2, x1:x2]
        face_predictions=fr_image.predict(rgbfacerec,model_path="face_reco_models/trained_knn_model.clf")
        if face_predictions:
            print(face_predictions)

        gray_face = gray_image[y1:y2, x1:x2]
        try:
            gray_face = cv2.resize(gray_face, (emotion_target_size))
        except:
            continue

        gray_face = preprocess_input(gray_face, True)
        gray_face = np.expand_dims(gray_face, 0)
        gray_face = np.expand_dims(gray_face, -1)
        emotion_prediction = emotion_classifier.predict(gray_face)
        emotion_probability = np.max(emotion_prediction)
        emotion_label_arg = np.argmax(emotion_prediction)
        emotion_text = emotion_labels[emotion_label_arg]
        emotion_window.append(emotion_text)
        print(face_coordinates)
        
        if len(emotion_window) > frame_window:
            emotion_window.pop(0)
        try:
            emotion_mode = mode(emotion_window)
        except:
            continue

        if emotion_text == 'angry':
            color = emotion_probability * np.asarray((255, 0, 0))
        elif emotion_text == 'sad':
            color = emotion_probability * np.asarray((0, 0, 255))
        elif emotion_text == 'happy':
            color = emotion_probability * np.asarray((255, 255, 0))
        elif emotion_text == 'surprise':
            color = emotion_probability * np.asarray((0, 255, 255))
        else:
            color = emotion_probability * np.asarray((0, 255, 0))

        color = color.astype(int)
        color = color.tolist()

        draw_bounding_box(face_coordinates, rgb_image, color)
        draw_text(face_coordinates, rgb_image, emotion_mode,
                  color, 0, -45, 1, 1)

    bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
    cv2.imshow('window_frame', bgr_image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    frame_no+=1

subprocess.check_output("python eval.py --video='videoplayback.mp4'",shell=True)
# video_capture = cv2.VideoCapture('videoplayback.mp4')
# frame_no=0
# while frame_no<length:
#     bgr_image = video_capture.read()[1]
#     object_predictions=or_image.evaluate(rgb_image,video_capture)
#     print(object_predictions)
#     frame_no+=1




