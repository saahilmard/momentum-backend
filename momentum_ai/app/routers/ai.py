from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import uuid
import os
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Student, Transcript, UserRole
from app.schemas import AITranscribeResponse, AISummarizeRequest, AISummarizeResponse, AIPlanRequest, AIPlanResponse
from app.config import settings
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


@router.post("/transcribe", response_model=AITranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload audio file for transcription (background job)."""
    # Validate file type
    if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": "Only audio files are supported",
                    "details": {}
                }
            }
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create storage directory if it doesn't exist
    os.makedirs(settings.storage_path, exist_ok=True)
    
    # Save file
    file_path = os.path.join(settings.storage_path, f"{job_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create transcript record
    transcript = Transcript(
        storage_uri=file_path,
        student_id=None,  # Will be updated when processing completes
        mentor_id=current_user.id if current_user.role.value == "mentor" else None
    )
    
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    logger.info("Audio transcription job created", job_id=job_id, file_path=file_path)
    
    # In a real implementation, you would queue this job for background processing
    # For now, we'll just return the job ID
    
    return AITranscribeResponse(job_id=job_id)


@router.post("/summarize", response_model=AISummarizeResponse)
async def summarize_transcript(
    request: AISummarizeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Summarize a transcript and extract action items."""
    # Get transcript
    transcript = db.query(Transcript).filter(Transcript.id == request.transcript_id).first()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TRANSCRIPT_NOT_FOUND",
                    "message": "Transcript not found",
                    "details": {}
                }
            }
        )
    
    # Check access (mentor can access their own transcripts, students can access their own)
    if current_user.role.value == "mentor":
        if transcript.mentor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ACCESS_DENIED",
                        "message": "Access denied to this transcript",
                        "details": {}
                    }
                }
            )
    elif current_user.role.value == "student":
        if transcript.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ACCESS_DENIED",
                        "message": "Access denied to this transcript",
                        "details": {}
                    }
                }
            )
    
    # In a real implementation, you would call an AI service here
    # For now, return a mock summary
    summary = "This is a mock summary of the conversation. The student discussed their challenges with time management and expressed interest in developing better study habits."
    action_items = [
        "Schedule regular check-ins to monitor progress",
        "Implement time-blocking technique for study sessions",
        "Set up accountability system with mentor"
    ]
    
    # Update transcript with summary
    transcript.summary = summary
    db.commit()
    
    logger.info("Transcript summarized", transcript_id=transcript.id)
    
    return AISummarizeResponse(
        summary=summary,
        action_items=action_items
    )


@router.post("/plan", response_model=AIPlanResponse)
async def recommend_plan(
    request: AIPlanRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI recommendations for a student's plan."""
    # Check if student exists and is in the same school
    student = db.query(Student).filter(Student.id == request.student_id).first()
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
    
    # In a real implementation, you would analyze the student's data and context
    # to generate personalized recommendations
    # For now, return mock recommendations
    
    recommended_items = [
        {
            "intervention_id": 1,
            "title": "Timeboxing Technique",
            "description": "Break study sessions into focused 25-minute blocks",
            "cadence": "daily",
            "priority": "high"
        },
        {
            "intervention_id": 2,
            "title": "Mood Tracking",
            "description": "Regular check-ins to monitor emotional well-being",
            "cadence": "3x/week",
            "priority": "medium"
        },
        {
            "intervention_id": 3,
            "title": "Goal Setting Workshop",
            "description": "SMART goal development session",
            "cadence": "weekly",
            "priority": "medium"
        }
    ]
    
    logger.info("Plan recommendations generated", student_id=request.student_id)
    
    return AIPlanResponse(recommended_items=recommended_items)
