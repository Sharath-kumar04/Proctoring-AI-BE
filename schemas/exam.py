from pydantic import BaseModel
from typing import Dict

class ExamSummary(BaseModel):
    total_duration: float
    face_detection_rate: float
    suspicious_activities: Dict[str, int]  # Will include all detection types
    devices_detected: Dict[str, int]  # New field for device detections
    visibility_issues: Dict[str, int]  # New field for face visibility issues
    overall_compliance: float

class DetectionCategories:
    DEVICES = ["Phone detected", "Tablet detected", "Laptop detected", "Secondary screen detected", "Remote control detected"]
    VISIBILITY = ["Face not visible in frame", "Face too far from camera", "Face too close to camera", "Face partially visible", "Face not centered in frame"]
    SUSPICIOUS = ["Multiple people detected", "Book detected", "Hand detected"]
