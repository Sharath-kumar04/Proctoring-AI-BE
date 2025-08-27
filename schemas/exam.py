from pydantic import BaseModel
from typing import Dict, Union

class ViolationDetail(BaseModel):
    count: int
    first_occurrence: str

class ExamSummary(BaseModel):
    total_duration: float  # in minutes
    face_detection_rate: float  # percentage of time face was detected
    suspicious_activities: Dict[str, Union[int, ViolationDetail]]  # count or details of each suspicious activity
    overall_compliance: float  # overall compliance percentage
