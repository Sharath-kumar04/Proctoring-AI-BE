import cv2
import torch
import os
from datetime import datetime
import logging
from ultralytics import YOLO
from utils.logger import logger
from typing import List, Dict, Any

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
        self.confidence_threshold = 0.85  # Set higher confidence threshold

    def detect(self, frame) -> List[Dict[str, Any]]:
        results = self.model(frame, conf=self.confidence_threshold)[0]
        detections = []
        
        person_count = 0
        max_confidence = 0.0
        
        for r in results.boxes.data.tolist():
            confidence = float(r[4])
            class_id = int(r[5])
            
            # Only process person class (usually class 0)
            if class_id == 0:  # person class
                person_count += 1
                max_confidence = max(max_confidence, confidence)
        
        # Only report if we detect more than one person with high confidence
        if person_count > 1 and max_confidence > self.confidence_threshold:
            detections.append({
                "class": "person",
                "count": person_count,
                "confidence": max_confidence,
                "suspicious": True
            })
            logger.warning(f"Multiple people detected: {person_count} with confidence {max_confidence}")
        
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
            logger.error("YOLO model not loaded")
            return []

        detections = detector.detect(frame)
        
        for detection in detections:
            if detection["suspicious"]:
                logs.append({
                    "time": timestamp,
                    "event": f"Suspicious activity detected: {detection['count']} people with confidence {detection['confidence']:.2f}"
                })
                    
    except Exception as e:
        logger.error(f"YOLO detection error: {str(e)}")
        
    return logs