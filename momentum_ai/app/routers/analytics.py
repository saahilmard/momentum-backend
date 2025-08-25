from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Student, Task, Checkin, Goal, UserRole, TaskStatus, GoalStatus
from app.schemas import EngagementAnalytics, RiskAnalytics
from app.risk_scoring import RiskScoringEngine
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


@router.get("/engagement", response_model=EngagementAnalytics)
async def get_engagement_analytics(
    student_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get engagement analytics for a student."""
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
    
    # Calculate current streak
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    completed_tasks = db.query(Task.completed_at).filter(
        and_(
            Task.student_id == student_id,
            Task.status == TaskStatus.DONE,
            Task.completed_at >= cutoff_date
        )
    ).all()
    
    # Get unique dates with completed tasks
    completion_dates = set(
        task[0].date() for task in completed_tasks if task[0]
    )
    
    # Calculate current streak
    current_streak = 0
    current_date = datetime.utcnow().date()
    
    for i in range(30):
        check_date = current_date - timedelta(days=i)
        if check_date in completion_dates:
            current_streak += 1
        else:
            break
    
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    sorted_dates = sorted(completion_dates)
    
    for i in range(len(sorted_dates)):
        if i == 0 or (sorted_dates[i] - sorted_dates[i-1]).days == 1:
            temp_streak += 1
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 1
    
    longest_streak = max(longest_streak, temp_streak)
    
    # Calculate check-in frequency (check-ins per week)
    checkin_count = db.query(Checkin).filter(
        and_(
            Checkin.student_id == student_id,
            Checkin.created_at >= cutoff_date
        )
    ).count()
    
    checkin_frequency = checkin_count / 4  # 4 weeks
    
    # Calculate task completion rate
    total_tasks = db.query(Task).filter(
        and_(
            Task.student_id == student_id,
            Task.created_at >= cutoff_date
        )
    ).count()
    
    completed_tasks_count = db.query(Task).filter(
        and_(
            Task.student_id == student_id,
            Task.status == TaskStatus.DONE,
            Task.completed_at >= cutoff_date
        )
    ).count()
    
    task_completion_rate = completed_tasks_count / max(total_tasks, 1)
    
    return EngagementAnalytics(
        student_id=student_id,
        current_streak=current_streak,
        longest_streak=longest_streak,
        checkin_frequency=checkin_frequency,
        task_completion_rate=task_completion_rate
    )


@router.get("/risk", response_model=RiskAnalytics)
async def get_risk_analytics(
    student_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get risk analytics for a student."""
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
    
    # Calculate current risk score
    risk_engine = RiskScoringEngine(db)
    risk_data = risk_engine.calculate_student_risk(student_id)
    
    # Get historical risk trend (last 30 days)
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    events = db.query(Event).filter(
        and_(
            Event.student_id == student_id,
            Event.type == "risk_score_updated",
            Event.created_at >= cutoff_date
        )
    ).order_by(Event.created_at).all()
    
    trend = []
    for event in events:
        if event.payload and "risk_score" in event.payload:
            trend.append({
                "date": event.created_at.isoformat(),
                "score": event.payload["risk_score"],
                "severity": event.payload.get("severity", "medium")
            })
    
    # Add current score to trend
    trend.append({
        "date": datetime.utcnow().isoformat(),
        "score": risk_data["risk_score"],
        "severity": risk_data["severity"]
    })
    
    return RiskAnalytics(
        student_id=student_id,
        current_score=risk_data["risk_score"],
        trend=trend,
        factors=risk_data["factors"]
    )
