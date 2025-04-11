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

SUSPICIOUS_OBJECTS = {
    "cell phone": "Phone detected",
    "book": "Book detected",
    "tablet": "Tablet detected",
    "laptop": "Laptop detected",
    "tvmonitor": "Secondary screen detected",
    "remote": "Remote control detected"
}

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

        # Process frame
        results = model.predict(frame, conf=0.4)[0]
        
        if results.boxes:
            for box in results.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                name = model.names[cls]
                
                logger.info(f"Detection: {name} ({conf:.2f})")
                
                if conf > 0.4:
                    # Check for suspicious objects
                    if name in SUSPICIOUS_OBJECTS:
                        logs.append({"time": timestamp, "event": SUSPICIOUS_OBJECTS[name]})
                    # Check for multiple people
                    elif name == "person":
                        if len(results.boxes) > 1:
                            logs.append({"time": timestamp, "event": "Multiple people detected"})
                    
    except Exception as e:
        logger.error(f"YOLO detection error: {str(e)}")
        
    return logs