import mediapipe as mp
import numpy as np
import cv2

class HeadPostureDetector:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def detect_head_pose(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(image_rgb)
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Get nose, left eye, right eye, and chin landmarks
            nose = face_landmarks.landmark[1]
            left_eye = face_landmarks.landmark[33]
            right_eye = face_landmarks.landmark[263]
            chin = face_landmarks.landmark[152]
            
            # Calculate head rotation angles
            rotation = self._calculate_head_rotation(nose, left_eye, right_eye, chin)
            return rotation
        return None

    def _calculate_head_rotation(self, nose, left_eye, right_eye, chin):
        # Simple head rotation estimation
        yaw = (right_eye.x - left_eye.x) * 100  # Left-right rotation
        pitch = (nose.y - chin.y) * 100  # Up-down rotation
        
        return {
            'yaw': yaw,
            'pitch': pitch,
            'is_centered': abs(yaw) < 15 and abs(pitch) < 15
        }

    def __del__(self):
        self.face_mesh.close()
