from typing import List, Dict
from datetime import datetime
from utils.logger import logger
import cv2
from detection.face_detection import detect_face
from detection.hand_detection import detect_hands
from detection.face_mesh_detection import detect_face_mesh
from detection.yolo_detection import detect_yolo
from concurrent.futures import ThreadPoolExecutor, as_completed

class DetectionService:
    frame_executor = ThreadPoolExecutor(max_workers=4)

    @staticmethod
    async def process_frame(frame) -> List[Dict]:
        logger.info("Processing new frame")
        all_logs = []
        
        try:
            # Run detections concurrently
            detection_tasks = {
                DetectionService.frame_executor.submit(detect_face, frame): "Face",
                DetectionService.frame_executor.submit(detect_hands, frame): "Hand",
                DetectionService.frame_executor.submit(detect_face_mesh, frame): "Face Mesh",
                DetectionService.frame_executor.submit(detect_yolo, frame): "YOLO"
            }

            # Collect results as they complete
            for future in as_completed(detection_tasks):
                detector_name = detection_tasks[future]
                try:
                    logs = future.result()
                    if logs:
                        logger.info(f"{detector_name} detection found {len(logs)} events")
                        all_logs.extend(logs)
                    else:
                        logger.debug(f"No {detector_name} detections")
                except Exception as e:
                    logger.error(f"Error in {detector_name} detection: {str(e)}")

            if all_logs:
                logger.info(f"Total events detected: {len(all_logs)}")
            
        except Exception as e:
            logger.error(f"Error in frame processing: {str(e)}", exc_info=True)
        
        return all_logs

    @classmethod
    async def cleanup(cls):
        """Cleanup thread pool on shutdown"""
        cls.frame_executor.shutdown(wait=True)
