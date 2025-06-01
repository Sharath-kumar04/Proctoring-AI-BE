import cv2
import torch
import os
from datetime import datetime
import logging
from ultralytics import YOLO
from utils.logger import logger
from typing import List, Dict, Any
import mediapipe as mp

# Setup logging with more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "yolov8n.pt")

class YOLODetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        self.confidence_threshold = {
            'person': 0.85,
            'cell phone': 0.25,
            'phone': 0.25,
            'mobile phone': 0.25
        }
        self.phone_classes = {'cell phone', 'phone', 'mobile phone', 'smartphone', 'mobile'}
        self.last_person_detected = datetime.now()
        self.absence_threshold = 0.5
        self.face_classes = {'face', 'person', 'head'}
        
        try:
            self.face_detector = mp.solutions.face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.3
            )
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe face detector: {e}")
            self.face_detector = None

        # Add detection state tracking
        self.last_detection_time = {}  # Track last detection time for each event type
        self.detection_cooldown = {    # Cooldown in seconds for each event type
            'face_not_visible': 2.0,   # Wait 2 seconds before logging absence again
            'phone_detected': 3.0,     # Wait 3 seconds before logging phone again
            'multiple_people': 2.0     # Wait 2 seconds before logging multiple people again
        }
        self.min_consecutive_detections = 2  # Require multiple consecutive detections

    def _check_cooldown(self, event_type: str) -> bool:
        """Check if enough time has passed since last detection"""
        current_time = datetime.now()
        last_time = self.last_detection_time.get(event_type)
        
        if last_time is None:
            return True
            
        cooldown = self.detection_cooldown.get(event_type, 1.0)
        time_diff = (current_time - last_time).total_seconds()
        
        return time_diff >= cooldown

    def detect(self, frame) -> List[Dict[str, Any]]:
        results = self.model(frame)[0]
        detections = []
        current_time = datetime.now()
        
        # Face detection with error handling and cooldown
        face_detected = False
        if self.face_detector:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_results = self.face_detector.process(frame_rgb)
                face_detected = (mp_results.detections is not None and len(mp_results.detections) > 0)
            except Exception as e:
                logger.error(f"Face detection error: {e}")
                person_detections = [r for r in results.boxes.data.tolist() 
                                  if int(r[5]) == 0 and float(r[4]) > self.confidence_threshold['person']]
                face_detected = len(person_detections) > 0

        if not face_detected and self._check_cooldown('face_not_visible'):
            detections.append({
                "class": "absence",
                "event_type": "face_not_visible",
                "confidence": 1.0,
                "suspicious": True,
                "duration": 0,
                "reason": "Face not visible in camera"
            })
            self.last_detection_time['face_not_visible'] = current_time
            logger.warning("User absence detected")

        # Update detection state for phones and multiple people
        if face_detected:
            self.last_person_detected = current_time

        # Check for phones with cooldown
        for r in results.boxes.data.tolist():
            confidence = float(r[4])
            class_id = int(r[5])
            class_name = self.model.names[class_id].lower()
            
            if (class_name in self.phone_classes and 
                confidence > self.confidence_threshold['cell phone'] and 
                self._check_cooldown('phone_detected')):
                detections.append({
                    "class": "phone",
                    "event_type": "phone_detected",
                    "confidence": confidence,
                    "suspicious": True
                })
                self.last_detection_time['phone_detected'] = current_time
                logger.info(f"Phone detected with confidence {confidence:.2f}")

        # Check for multiple people with cooldown
        person_detections = [
            r for r in results.boxes.data.tolist()
            if (int(r[5]) == 0 and float(r[4]) > self.confidence_threshold['person'])
        ]
        
        if len(person_detections) > 1 and self._check_cooldown('multiple_people'):
            max_confidence = max(float(r[4]) for r in person_detections)
            detections.append({
                "class": "person",
                "event_type": "multiple_people",
                "confidence": max_confidence,
                "suspicious": True,
                "count": len(person_detections)
            })
            self.last_detection_time['multiple_people'] = current_time

        return detections

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_model():
    try:
        logger.info("Loading YOLOv8 model...")
        
        if os.path.exists(MODEL_PATH):
            logger.info(f"Loading model from {MODEL_PATH}")
            return YOLODetector(MODEL_PATH)
        else:
            logger.info("Downloading YOLOv8n model...")
            model = YOLO('yolov8n')
            # Save model for future use
            model.save(MODEL_PATH)
            return YOLODetector(MODEL_PATH)
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}", exc_info=True)
        return None

def detect_yolo(frame):
    logs = []
    timestamp = str(datetime.now())

    try:
        detector = load_model()
        if detector is None:
            return []

        detections = detector.detect(frame)
        
        for detection in detections:
            if detection["suspicious"]:
                event_msg = {
                    "phone": "Phone detected",
                    "person": "Multiple people detected", 
                    "absence": "user absence detected"  # Updated message
                }.get(detection["class"])
                
                if event_msg:
                    logs.append({
                        "time": timestamp,
                        "event": event_msg,
                        "event_type": detection["event_type"],
                        "details": detection.get("reason", "")  # Add reason to logs
                    })
                    
    except Exception as e:
        logger.error(f"YOLO detection error: {str(e)}")
        
    return logs