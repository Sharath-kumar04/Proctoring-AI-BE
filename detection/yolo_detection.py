import cv2
import torch
import os
from datetime import datetime
import logging
from ultralytics import YOLO
from utils.logger import logger

# Setup logging with more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "yolov8n.pt")

def load_model():
    global model
    try:
        logger.info("Loading YOLOv8 model...")
        
        if os.path.exists(MODEL_PATH):
            logger.info(f"Loading model from {MODEL_PATH}")
            model = YOLO(MODEL_PATH)
        else:
            logger.info("Downloading YOLOv8n model...")
            model = YOLO('yolov8n')
            # Save model for future use
            model.save(MODEL_PATH)
        
        model.to(device)
        logger.info(f"Model loaded successfully on {device}")
        return model
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}", exc_info=True)
        return None

def detect_yolo(frame):
    global model
    logs = []
    timestamp = str(datetime.now())

    try:
        if model is None:
            model = load_model()
            if model is None:
                logger.error("YOLO model not loaded")
                return []

        results = model.predict(frame, conf=0.4)[0]
        
        if results.boxes:
            person_count = 0
            for box in results.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                name = model.names[cls]
                
                logger.info(f"Detection: {name} ({conf:.2f})")
                
                if conf > 0.4:
                    if name == "person":
                        person_count += 1
                    elif name in ["cell phone", "mobile phone"]:
                        logs.append({"time": timestamp, "event": "Phone detected"})
                    elif name == "tablet":
                        logs.append({"time": timestamp, "event": "Tablet detected"})
                    elif name == "book":
                        logs.append({"time": timestamp, "event": "Book detected"})
                    
            # Check for multiple people after counting
            if person_count > 1:
                logs.append({"time": timestamp, "event": "Background person detected"})
            elif person_count == 0:
                logs.append({"time": timestamp, "event": "User absence detected"})
                    
    except Exception as e:
        logger.error(f"YOLO detection error: {str(e)}")
        
    return logs