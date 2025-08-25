from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import (
    get_password_hash, authenticate_user, create_tokens, 
    verify_token, denylist_token, get_current_active_user
)
from app.models import User, TokenDenylist
from app.schemas import (
    UserRegister, UserLogin, TokenResponse, RefreshToken, UserResponse
)
from app.websocket_manager import manager
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "USER_EXISTS",
                    "message": "User with this email already exists",
                    "details": {}
                }
            }
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        school_id=user_data.school_id
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create tokens
    tokens = create_tokens(user)
    
    logger.info("User registered", user_id=user.id, email=user.email)
    
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = authenticate_user(user_data.email, user_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password",
                    "details": {}
                }
            }
        )
    
    # Create tokens
    tokens = create_tokens(user)
    
    logger.info("User logged in", user_id=user.id, email=user.email)
    
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: RefreshToken, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = verify_token(token_data.refresh_token, "refresh")
        
        # Check if token is denylisted
        jti = payload.get("jti")
        if jti:
            denylisted = db.query(TokenDenylist).filter(TokenDenylist.jti == jti).first()
            if denylisted:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": {
                            "code": "TOKEN_REVOKED",
                            "message": "Refresh token has been revoked",
                            "details": {}
                        }
                    }
                )
        
        # Get user
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "User not found",
                        "details": {}
                    }
                }
            )
        
        # Create new tokens
        tokens = create_tokens(user)
        
        # Denylist old refresh token
        if jti:
            denylist_token(jti, payload.get("exp"), db)
        
        logger.info("Token refreshed", user_id=user.id)
        
        return tokens
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Invalid refresh token",
                    "details": {}
                }
            }
        )


@router.post("/logout")
async def logout(
    token_data: RefreshToken,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout and revoke refresh token."""
    try:
        # Verify refresh token
        payload = verify_token(token_data.refresh_token, "refresh")
        jti = payload.get("jti")
        
        if jti:
            # Add to denylist
            denylist_token(jti, payload.get("exp"), db)
        
        logger.info("User logged out", user_id=current_user.id)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Invalid refresh token",
                    "details": {}
                }
            }
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user
