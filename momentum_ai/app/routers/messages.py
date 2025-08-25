from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Message, UserRole
from app.schemas import MessageCreate, MessageResponse
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


@router.post("/", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message to another user."""
    # Check if recipient exists and is in the same school
    recipient = db.query(User).filter(User.id == message_data.recipient_user_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "Recipient not found",
                    "details": {}
                }
            }
        )
    
    check_school_access(current_user, recipient.school_id)
    
    # Create message
    message = Message(
        sender_user_id=current_user.id,
        recipient_user_id=message_data.recipient_user_id,
        text=message_data.text
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    logger.info("Message sent", message_id=message.id, sender_id=current_user.id, recipient_id=message_data.recipient_user_id)
    
    return MessageResponse(
        id=message.id,
        sender_user_id=message.sender_user_id,
        recipient_user_id=message.recipient_user_id,
        text=message.text,
        created_at=message.created_at,
        sender=current_user,
        recipient=recipient
    )
