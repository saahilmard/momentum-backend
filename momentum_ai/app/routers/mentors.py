from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Mentor, UserRole
from app.schemas import MentorCreate, MentorUpdate, MentorResponse
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


@router.get("/", response_model=list[MentorResponse])
async def get_mentors(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all mentors in the current user's school."""
    mentors = db.query(Mentor).join(User).filter(User.school_id == current_user.school_id).all()
    return [MentorResponse(
        id=mentor.id,
        user_id=mentor.user_id,
        capacity=mentor.capacity,
        specialties=mentor.specialties,
        meta=mentor.meta,
        user=mentor.user
    ) for mentor in mentors]


@router.post("/", response_model=MentorResponse)
async def create_mentor(
    mentor_data: MentorCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new mentor."""
    # Check if user exists and is in the same school
    user = db.query(User).filter(User.id == mentor_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found",
                    "details": {}
                }
            }
        )
    
    check_school_access(current_user, user.school_id)
    
    # Check if mentor already exists for this user
    existing_mentor = db.query(Mentor).filter(Mentor.user_id == mentor_data.user_id).first()
    if existing_mentor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "MENTOR_EXISTS",
                    "message": "Mentor already exists for this user",
                    "details": {}
                }
            }
        )
    
    # Create mentor
    mentor = Mentor(**mentor_data.dict())
    db.add(mentor)
    db.commit()
    db.refresh(mentor)
    
    logger.info("Mentor created", mentor_id=mentor.id, user_id=mentor.user_id)
    
    return MentorResponse(
        id=mentor.id,
        user_id=mentor.user_id,
        capacity=mentor.capacity,
        specialties=mentor.specialties,
        meta=mentor.meta,
        user=mentor.user
    )


@router.get("/{mentor_id}", response_model=MentorResponse)
async def get_mentor(
    mentor_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific mentor by ID."""
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "MENTOR_NOT_FOUND",
                    "message": "Mentor not found",
                    "details": {}
                }
            }
        )
    
    # Check school access
    check_school_access(current_user, mentor.user.school_id)
    
    return MentorResponse(
        id=mentor.id,
        user_id=mentor.user_id,
        capacity=mentor.capacity,
        specialties=mentor.specialties,
        meta=mentor.meta,
        user=mentor.user
    )


@router.patch("/{mentor_id}", response_model=MentorResponse)
async def update_mentor(
    mentor_id: int,
    mentor_data: MentorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a mentor."""
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "MENTOR_NOT_FOUND",
                    "message": "Mentor not found",
                    "details": {}
                }
            }
        )
    
    # Check school access
    check_school_access(current_user, mentor.user.school_id)
    
    # Update fields
    update_data = mentor_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mentor, field, value)
    
    db.commit()
    db.refresh(mentor)
    
    logger.info("Mentor updated", mentor_id=mentor.id)
    
    return MentorResponse(
        id=mentor.id,
        user_id=mentor.user_id,
        capacity=mentor.capacity,
        specialties=mentor.specialties,
        meta=mentor.meta,
        user=mentor.user
    )
