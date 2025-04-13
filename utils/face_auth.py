from deepface import DeepFace
import numpy as np
import cv2
from utils.logger import logger
import tempfile
import os

def compare_faces(known_image, unknown_image, threshold=0.6):
    """Compare known and unknown face images using DeepFace"""
    temp_known = None
    temp_unknown = None
    
    try:
        # Save images to temporary files since DeepFace works better with files
        temp_known = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_unknown = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        
        # Convert bytes to numpy arrays
        known_arr = np.frombuffer(known_image, np.uint8)
        unknown_arr = np.frombuffer(unknown_image, np.uint8)
        
        # Decode images
        known_img = cv2.imdecode(known_arr, cv2.IMREAD_COLOR)
        unknown_img = cv2.imdecode(unknown_arr, cv2.IMREAD_COLOR)
        
        if known_img is None or unknown_img is None:
            logger.error("Failed to decode image data")
            return False, "Invalid image data"
            
        # Save to temporary files
        cv2.imwrite(temp_known.name, known_img)
        cv2.imwrite(temp_unknown.name, unknown_img)
        
        # Compare using file paths
        result = DeepFace.verify(
            img1_path=temp_known.name,
            img2_path=temp_unknown.name,
            model_name="VGG-Face",
            distance_metric="cosine",
            enforce_detection=True,
            detector_backend="opencv",
            align=True
        )
        
        distance = float(result.get("distance", 1.0))
        verified = distance < threshold
        
        logger.info(f"Face comparison: distance={distance:.3f}, threshold={threshold}, verified={verified}")
        
        return verified, {
            "match": verified,
            "confidence": round((1 - distance) * 100, 2),
            "model": "VGG-Face",
            "distance": distance
        }
        
    except Exception as e:
        logger.error(f"Face comparison error: {str(e)}", exc_info=True)
        return False, f"Face comparison failed: {str(e)}"
        
    finally:
        # Cleanup temporary files
        for temp_file in [temp_known, temp_unknown]:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
