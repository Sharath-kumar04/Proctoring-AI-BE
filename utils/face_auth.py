from deepface import DeepFace
import numpy as np
import io
import cv2
from PIL import Image
from utils.logger import logger

def compare_faces(known_image, unknown_image, threshold=0.6):
    """
    Compare known and unknown face images using DeepFace
    Args:
        known_image: Stored user image (bytes)
        unknown_image: Live captured image (bytes)
        threshold: Face recognition threshold (higher is more strict)
    """
    try:
        # Convert bytes to numpy arrays
        known_img = cv2.imdecode(np.frombuffer(known_image, np.uint8), cv2.IMREAD_COLOR)
        unknown_img = cv2.imdecode(np.frombuffer(unknown_image, np.uint8), cv2.IMREAD_COLOR)
        
        # Use DeepFace verify with VGG-Face model
        result = DeepFace.verify(
            img1_path=known_img,
            img2_path=unknown_img,
            model_name="VGG-Face",
            distance_metric="cosine",
            enforce_detection=True,
            detector_backend="retinaface"
        )
        
        distance = float(result.get("distance", 1.0))
        verified = distance < threshold
        
        logger.info(f"Face comparison result: distance={distance:.3f}, verified={verified}")
        
        return verified, {
            "match": verified,
            "confidence": round((1 - distance) * 100, 2),
            "model": "VGG-Face",
            "distance": distance
        }
        
    except ValueError as ve:
        logger.error(f"Face detection error: {str(ve)}")
        return False, "No face detected in one or both images"
    except Exception as e:
        logger.error(f"Face comparison error: {str(e)}")
        return False, f"Face comparison error: {str(e)}"
