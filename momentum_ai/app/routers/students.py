from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Student, Plan, UserRole
from app.schemas import (
    StudentCreate, StudentUpdate, StudentResponse, StudentSearch, PaginatedResponse
)
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


@router.get("/", response_model=PaginatedResponse)
async def get_students(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of students."""
    # Build query
    query = db.query(Student).join(User).filter(User.school_id == current_user.school_id)
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Student.grade_level.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    students = query.offset((page - 1) * size).limit(size).all()
    
    # Get current plan for each student
    student_responses = []
    for student in students:
        current_plan = None
        active_plan = db.query(Plan).filter(
            Plan.student_id == student.id,
            Plan.active == True
        ).first()
        if active_plan:
            current_plan = active_plan.plan
        
        student_response = StudentResponse(
            id=student.id,
            user_id=student.user_id,
            grade_level=student.grade_level,
            gpa=student.gpa,
            risk_score=student.risk_score,
            meta=student.meta,
            user=student.user,
            current_plan=current_plan
        )
        student_responses.append(student_response)
    
    return PaginatedResponse(
        items=student_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.post("/", response_model=StudentResponse)
async def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new student."""
    # Check if user exists and is in the same school
    user = db.query(User).filter(User.id == student_data.user_id).first()
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
    
    # Check if student already exists for this user
    existing_student = db.query(Student).filter(Student.user_id == student_data.user_id).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "STUDENT_EXISTS",
                    "message": "Student already exists for this user",
                    "details": {}
                }
            }
        )
    
    # Create student
    student = Student(**student_data.dict())
    db.add(student)
    db.commit()
    db.refresh(student)
    
    logger.info("Student created", student_id=student.id, user_id=student.user_id)
    
    return StudentResponse(
        id=student.id,
        user_id=student.user_id,
        grade_level=student.grade_level,
        gpa=student.gpa,
        risk_score=student.risk_score,
        meta=student.meta,
        user=student.user
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific student by ID."""
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
    
    # Check school access
    check_school_access(current_user, student.user.school_id)
    
    # Get current plan
    current_plan = None
    active_plan = db.query(Plan).filter(
        Plan.student_id == student.id,
        Plan.active == True
    ).first()
    if active_plan:
        current_plan = active_plan.plan
    
    return StudentResponse(
        id=student.id,
        user_id=student.user_id,
        grade_level=student.grade_level,
        gpa=student.gpa,
        risk_score=student.risk_score,
        meta=student.meta,
        user=student.user,
        current_plan=current_plan
    )


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a student."""
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
    
    # Check school access
    check_school_access(current_user, student.user.school_id)
    
    # Update fields
    update_data = student_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    
    db.commit()
    db.refresh(student)
    
    logger.info("Student updated", student_id=student.id)
    
    return StudentResponse(
        id=student.id,
        user_id=student.user_id,
        grade_level=student.grade_level,
        gpa=student.gpa,
        risk_score=student.risk_score,
        meta=student.meta,
        user=student.user
    )
