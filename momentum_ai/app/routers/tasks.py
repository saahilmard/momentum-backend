from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Student, Task, Goal, UserRole, TaskStatus
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from datetime import datetime
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


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new task for a student."""
    # Check if student exists and is in the same school
    student = db.query(Student).filter(Student.id == task_data.student_id).first()
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
    
    # Check if goal exists and belongs to the same student (if provided)
    if task_data.goal_id:
        goal = db.query(Goal).filter(Goal.id == task_data.goal_id).first()
        if not goal or goal.student_id != task_data.student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_GOAL",
                        "message": "Goal not found or does not belong to student",
                        "details": {}
                    }
                }
            )
    
    # Create task
    task = Task(**task_data.dict())
    db.add(task)
    db.commit()
    db.refresh(task)
    
    logger.info("Task created", task_id=task.id, student_id=task.student_id)
    
    return TaskResponse(
        id=task.id,
        goal_id=task.goal_id,
        student_id=task.student_id,
        title=task.title,
        due_date=task.due_date,
        status=task.status,
        completed_at=task.completed_at,
        student=student,
        goal=task.goal if task.goal_id else None
    )


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": "Task not found",
                    "details": {}
                }
            }
        )
    
    # Check school access
    check_school_access(current_user, task.student.user.school_id)
    
    # Update fields
    update_data = task_data.dict(exclude_unset=True)
    
    # Handle status change to DONE
    if update_data.get("status") == TaskStatus.DONE and task.status != TaskStatus.DONE:
        update_data["completed_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    logger.info("Task updated", task_id=task.id)
    
    return TaskResponse(
        id=task.id,
        goal_id=task.goal_id,
        student_id=task.student_id,
        title=task.title,
        due_date=task.due_date,
        status=task.status,
        completed_at=task.completed_at,
        student=task.student,
        goal=task.goal if task.goal_id else None
    )
