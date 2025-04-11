from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config.database import get_db
from models.logs import Log
from schemas.exam import ExamSummary
from datetime import datetime, timedelta
from sqlalchemy import func
from typing import Dict, Optional
from pydantic import BaseModel
from utils.connection import manager  # Import manager from new module
from models.detection_categories import DetectionCategories  # Import DetectionCategories
import secrets
from routers.auth import create_access_token, get_current_user
from fastapi.responses import JSONResponse
from utils.logger import logger  # Add logger import if not present

router = APIRouter()
security = HTTPBearer()

class SessionInfo(BaseModel):
    user_id: int
    status: str
    start_time: Optional[datetime] = None
    duration: Optional[float] = None

@router.get("/session/{user_id}", response_model=SessionInfo)
def get_session_info(user_id: int, db: Session = Depends(get_db)):
    """Get current exam session info"""
    # Get most recent log
    latest_log = db.query(Log).filter(
        Log.user_id == user_id
    ).order_by(Log.timestamp.desc()).first()
    
    if latest_log:
        start_time = db.query(func.min(Log.timestamp)).filter(
            Log.user_id == user_id
        ).scalar()
        
        duration = None
        if start_time:
            duration = (datetime.utcnow() - start_time).total_seconds() / 60

        return SessionInfo(
            user_id=user_id,
            status="running",
            start_time=start_time,
            duration=round(duration, 2) if duration else None
        )
    
    return SessionInfo(
        user_id=user_id,
        status="not_started"
    )

@router.post("/start/{user_id}")
def start_exam_session(
    user_id: int,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Start exam session with authorization"""
    # Verify user authorization with the new get_current_user function
    current_user = get_current_user(credentials.credentials, db)
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to start this session"
        )
    
    session_info = get_session_info(user_id, db)
    base_url = "ws://localhost:8080/ws"
    
    # Generate session ID and tokens
    session_id = secrets.token_hex(16)
    ws_token = create_access_token({
        "sub": str(user_id),
        "session": session_id,
        "type": "websocket"
    })
    
    if manager.is_connected(user_id):
        return {
            "message": "Session already running",
            "status": "running",
            "wsUrl": f"{base_url}/{user_id}",
            "wsConfig": {
                "sessionId": session_id,
                "token": ws_token,
                "additionalParams": {
                    "userId": user_id,
                    "startTime": session_info.start_time.isoformat() if session_info.start_time else None,
                    "duration": session_info.duration
                }
            }
        }
    
    return {
        "message": "Start new session",
        "status": "ready",
        "wsUrl": f"{base_url}/{user_id}",
        "wsConfig": {
            "sessionId": session_id,
            "token": ws_token,
            "additionalParams": {
                "userId": user_id,
                "maxDuration": 7200,  # 2 hours in seconds
                "keepAliveInterval": 15000  # 15 seconds in milliseconds
            }
        }
    }

@router.post("/pause/{user_id}")
def pause_exam_session(user_id: int):
    """Pause exam session"""
    if manager.set_paused(user_id, True):
        return {"message": "Session paused", "status": "paused"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No active session found"
    )

@router.post("/resume/{user_id}")
def resume_exam_session(user_id: int):
    """Resume exam session"""
    if manager.set_paused(user_id, False):
        return {"message": "Session resumed", "status": "running"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No active session found"
    )

@router.post("/stop/{user_id}")
async def stop_exam_session(
    user_id: int,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Stop exam session and disconnect WebSocket immediately"""
    try:
        # Quick auth check
        current_user = get_current_user(credentials.credentials, db)
        if current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        if not manager.is_connected(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active session found"
            )

        # Force disconnect connection
        await manager.force_disconnect(user_id)

        # Add final log
        try:
            db.add(Log(
                log="Exam session ended",
                event_type="session_ended",
                timestamp=datetime.utcnow(),
                user_id=user_id
            ))
            db.commit()
        except:
            db.rollback()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Session stopped and connection closed successfully"}
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Stop session error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to stop session"}
        )

@router.get("/summary/{user_id}", response_model=ExamSummary)
async def get_exam_summary(user_id: int, db: Session = Depends(get_db)):
    """Get exam summary for a user"""
    logs = db.query(Log).filter(Log.user_id == user_id).all()
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found")

    start_time = min(log.timestamp for log in logs)
    end_time = max(log.timestamp for log in logs)
    total_duration = (end_time - start_time).total_seconds() / 60

    # Initialize counters
    devices_detected = {event: 0 for event in DetectionCategories.DEVICES}
    visibility_issues = {event: 0 for event in DetectionCategories.VISIBILITY}
    suspicious_activities = {event: 0 for event in DetectionCategories.SUSPICIOUS}

    # Count face detection issues
    face_visible_count = 0
    total_checks = 0

    for log in logs:
        event = log.log
        if event in DetectionCategories.DEVICES:
            devices_detected[event] += 1
        elif event in DetectionCategories.VISIBILITY:
            visibility_issues[event] += 1
        elif event in DetectionCategories.SUSPICIOUS:
            suspicious_activities[event] += 1

        # Track face visibility
        if "Face" in event:
            total_checks += 1
            if "not" not in event and "too" not in event and "partially" not in event:
                face_visible_count += 1

    face_detection_rate = (face_visible_count / total_checks * 100) if total_checks > 0 else 0
    
    # Calculate compliance score based on all categories
    total_violations = (
        sum(devices_detected.values()) + 
        sum(visibility_issues.values()) + 
        sum(suspicious_activities.values())  # Add missing closing parenthesis
    )
    overall_compliance = max(0, 100 - (total_violations * 5))  # Deduct 5 points per violation

    return ExamSummary(
        total_duration=round(total_duration, 2),
        face_detection_rate=round(face_detection_rate, 2),
        suspicious_activities=suspicious_activities,
        devices_detected=devices_detected,
        visibility_issues=visibility_issues,
        overall_compliance=round(overall_compliance, 2)
    )

@router.post("/clear-logs/{user_id}")
async def clear_exam_logs(
    user_id: int,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Clear all logs for a user after exam completion"""
    try:
        # Verify user authorization
        current_user = get_current_user(credentials.credentials, db)
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to clear these logs"
            )

        # Delete all logs for the user
        deleted_count = db.query(Log).filter(Log.user_id == user_id).delete()
        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Successfully cleared {deleted_count} logs for user {user_id}",
                "deleted_count": deleted_count
            }
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear logs"
        )
