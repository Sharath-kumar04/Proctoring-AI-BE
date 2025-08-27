from pydantic import BaseModel, EmailStr
from typing import Dict, Union, Optional
import base64

class ViolationDetail(BaseModel):
    count: int
    first_occurrence: str

class UserInfo(BaseModel):
    email: str
    image: Optional[str] = None  # Base64 encoded image

class ExamSummary(BaseModel):
    total_duration: float  # in minutes
    face_detection_rate: float  # percentage of time face was detected
    suspicious_activities: Dict[str, Union[int, ViolationDetail]]  # count or details of each suspicious activity
    overall_compliance: float  # overall compliance percentage
    user: UserInfo
