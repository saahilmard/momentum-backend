from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Student, Checkin, UserRole
from app.schemas import CheckinCreate, CheckinResponse
import structlog

logger = structlog.get_logger()
router = APIRouter()


def check_school_access(user: User, school_id: int):
    """Check if user has access to the school."""
    if user.role == UserRole.ADMIN and user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCESS_DENIED",
                    "message": "Access denied to this school",
                    "details": {}
                }
            }
        )


@router.post("/", response_model=CheckinResponse)
async def create_checkin(
    checkin_data: CheckinCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new check-in for a student."""
    # Check if student exists and is in the same school
    student = db.query(Student).filter(Student.id == checkin_data.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "STUDENT_NOT_FOUND",
                    "message": "Student not found",
                    "details": {}
                }
            }
        )
    
    check_school_access(current_user, student.user.school_id)
    
    # Create check-in
    checkin = Checkin(**checkin_data.dict())
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    
    logger.info("Check-in created", checkin_id=checkin.id, student_id=checkin.student_id)
    
    return CheckinResponse(
        id=checkin.id,
        student_id=checkin.student_id,
        mentor_id=checkin.mentor_id,
        mood=checkin.mood,
        obstacles=checkin.obstacles,
        notes=checkin.notes,
        created_at=checkin.created_at,
        student=student,
        mentor=checkin.mentor if checkin.mentor_id else None
    )


@router.get("/", response_model=List[CheckinResponse])
async def get_checkins(
    student_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get check-ins, optionally filtered by student."""
    query = db.query(Checkin)
    
    if student_id:
        # Check if student exists and is in the same school
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "STUDENT_NOT_FOUND",
                        "message": "Student not found",
                        "details": {}
                    }
                }
            )
        
        check_school_access(current_user, student.user.school_id)
        query = query.filter(Checkin.student_id == student_id)
    else:
        # Filter by school
        query = query.join(Student).join(User).filter(User.school_id == current_user.school_id)
    
    checkins = query.order_by(Checkin.created_at.desc()).all()
    
    return [CheckinResponse(
        id=checkin.id,
        student_id=checkin.student_id,
        mentor_id=checkin.mentor_id,
        mood=checkin.mood,
        obstacles=checkin.obstacles,
        notes=checkin.notes,
        created_at=checkin.created_at,
        student=checkin.student,
        mentor=checkin.mentor if checkin.mentor_id else None
    ) for checkin in checkins]
