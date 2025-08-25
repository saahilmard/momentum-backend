from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Student, Plan, Intervention, UserRole
from app.schemas import PlanCreate, PlanUpdate, PlanResponse, InterventionResponse
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


@router.get("/interventions", response_model=list[InterventionResponse])
async def get_interventions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all available interventions."""
    interventions = db.query(Intervention).all()
    return [InterventionResponse(
        id=intervention.id,
        slug=intervention.slug,
        title=intervention.title,
        category=intervention.category,
        description=intervention.description,
        protocol=intervention.protocol
    ) for intervention in interventions]


@router.post("/", response_model=PlanResponse)
async def create_plan(
    plan_data: PlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new plan for a student."""
    # Check if student exists and is in the same school
    student = db.query(Student).filter(Student.id == plan_data.student_id).first()
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
    
    # Deactivate any existing active plans for this student
    existing_active = db.query(Plan).filter(
        Plan.student_id == plan_data.student_id,
        Plan.active == True
    ).all()
    
    for plan in existing_active:
        plan.active = False
    
    # Create new plan
    plan = Plan(
        student_id=plan_data.student_id,
        created_by=current_user.id,
        plan=plan_data.plan,
        active=False  # Start as inactive
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    logger.info("Plan created", plan_id=plan.id, student_id=plan.student_id)
    
    return PlanResponse(
        id=plan.id,
        student_id=plan.student_id,
        created_by=plan.created_by,
        version=plan.version,
        active=plan.active,
        plan=plan.plan,
        created_at=plan.created_at,
        student=student,
        creator=current_user
    )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific plan by ID."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PLAN_NOT_FOUND",
                    "message": "Plan not found",
                    "details": {}
                }
            }
        )
    
    # Check school access
    check_school_access(current_user, plan.student.user.school_id)
    
    return PlanResponse(
        id=plan.id,
        student_id=plan.student_id,
        created_by=plan.created_by,
        version=plan.version,
        active=plan.active,
        plan=plan.plan,
        created_at=plan.created_at,
        student=plan.student,
        creator=plan.creator
    )


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a plan."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PLAN_NOT_FOUND",
                    "message": "Plan not found",
                    "details": {}
                }
            }
        )
    
    # Check school access
    check_school_access(current_user, plan.student.user.school_id)
    
    # Update fields
    update_data = plan_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    db.commit()
    db.refresh(plan)
    
    logger.info("Plan updated", plan_id=plan.id)
    
    return PlanResponse(
        id=plan.id,
        student_id=plan.student_id,
        created_by=plan.created_by,
        version=plan.version,
        active=plan.active,
        plan=plan.plan,
        created_at=plan.created_at,
        student=plan.student,
        creator=plan.creator
    )


@router.post("/{plan_id}/activate")
async def activate_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Activate a plan (deactivates other plans for the same student)."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PLAN_NOT_FOUND",
                    "message": "Plan not found",
                    "details": {}
                }
            }
        )
    
    # Check school access
    check_school_access(current_user, plan.student.user.school_id)
    
    # Deactivate all other plans for this student
    other_plans = db.query(Plan).filter(
        Plan.student_id == plan.student_id,
        Plan.id != plan_id,
        Plan.active == True
    ).all()
    
    for other_plan in other_plans:
        other_plan.active = False
    
    # Activate this plan
    plan.active = True
    
    db.commit()
    
    logger.info("Plan activated", plan_id=plan.id, student_id=plan.student_id)
    
    return {"message": "Plan activated successfully"}
