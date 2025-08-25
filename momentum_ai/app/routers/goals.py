from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Student, Goal, UserRole
from app.schemas import GoalCreate, GoalUpdate, GoalResponse
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


@router.post("/", response_model=GoalResponse)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new goal for a student."""
    # Check if student exists and is in the same school
    student = db.query(Student).filter(Student.id == goal_data.student_id).first()
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
    
    # Create goal
    goal = Goal(**goal_data.dict())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    logger.info("Goal created", goal_id=goal.id, student_id=goal.student_id)
    
    return GoalResponse(
        id=goal.id,
        student_id=goal.student_id,
        title=goal.title,
        description=goal.description,
        target_date=goal.target_date,
        status=goal.status,
        student=student
    )


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a goal."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GOAL_NOT_FOUND",
                    "message": "Goal not found",
                    "details": {}
                }
            }
        )
    
    # Check school access
    check_school_access(current_user, goal.student.user.school_id)
    
    # Update fields
    update_data = goal_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)
    
    db.commit()
    db.refresh(goal)
    
    logger.info("Goal updated", goal_id=goal.id)
    
    return GoalResponse(
        id=goal.id,
        student_id=goal.student_id,
        title=goal.title,
        description=goal.description,
        target_date=goal.target_date,
        status=goal.status,
        student=goal.student
    )
