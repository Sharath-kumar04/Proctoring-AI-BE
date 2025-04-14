import mediapipe as mp
import numpy as np
from utils.logger import logger
from datetime import datetime

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# Store previous landmarks for movement detection
prev_landmarks = None

def detect_face(frame):
    global prev_landmarks
    logs = []
    timestamp = str(datetime.now())

    try:
        results = face_mesh.process(frame)
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            
            # Log face detection
            logs.append({
                "time": timestamp,
                "event": "Face detected",
                "event_type": "face_detected"
            })
            
            # Eye movement detection
            if prev_landmarks:
                eye_movement = detect_eye_movement(landmarks, prev_landmarks)
                if eye_movement:
                    logs.append({
                        "time": timestamp,
                        "event": "Eye movement detected",
                        "event_type": "eye_movement"
                    })
                
                mouth_movement = detect_mouth_movement(landmarks, prev_landmarks)
                if mouth_movement:
                    logs.append({
                        "time": timestamp,
                        "event": "Mouth movement detected",
                        "event_type": "mouth_movement"
                    })
            
            prev_landmarks = landmarks
            
    except Exception as e:
        logger.error(f"Face detection error: {str(e)}")
        
    return logs

def detect_eye_movement(current, previous, threshold=0.02):
    left_eye = np.mean([
        [current.landmark[33].x, current.landmark[33].y],
        [current.landmark[133].x, current.landmark[133].y]
    ], axis=0)
    
    prev_left_eye = np.mean([
        [previous.landmark[33].x, previous.landmark[33].y],
        [previous.landmark[133].x, previous.landmark[133].y]
    ], axis=0)
    
    return np.linalg.norm(left_eye - prev_left_eye) > threshold

def detect_mouth_movement(current, previous, threshold=0.03):
    mouth = np.mean([
        [current.landmark[0].x, current.landmark[0].y],
        [current.landmark[17].x, current.landmark[17].y]
    ], axis=0)
    
    prev_mouth = np.mean([
        [previous.landmark[0].x, previous.landmark[0].y],
        [previous.landmark[17].x, previous.landmark[17].y]
    ], axis=0)
    
    return np.linalg.norm(mouth - prev_mouth) > threshold
