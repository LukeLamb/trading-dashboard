"""
Authentication Routes
Handles user registration, login, and logout
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import get_db
from api.models.user import User, UserProfile
from api.schemas.user import UserCreate, UserLogin, Token, UserResponse, UserProfileResponse
from api.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_token_expiry_seconds,
    validate_password_strength
)
from api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with character selection

    Creates both User and UserProfile records in a single transaction
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Check if display name already exists
    existing_profile = db.query(UserProfile).filter(
        UserProfile.display_name == user_data.display_name
    ).first()

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Display name already taken"
        )

    try:
        # Create user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            is_active=True
        )
        db.add(new_user)
        db.flush()  # Get user_id without committing

        # Create user profile with character
        new_profile = UserProfile(
            user_id=new_user.user_id,
            character_type=user_data.character_type,
            display_name=user_data.display_name,
            bio=user_data.bio,
            avatar_url=user_data.avatar_url or "/avatars/default_1.png",
            current_level=1,
            current_xp=0,
            total_xp=0,
            can_change_character=True
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_user)
        db.refresh(new_profile)

        logger.info(f"New user registered: {new_user.username} ({new_user.user_id})")

        # Create access token
        access_token = create_access_token(data={"sub": str(new_user.user_id)})

        return {
            "message": "User registered successfully",
            "user": UserResponse.model_validate(new_user),
            "profile": UserProfileResponse.model_validate(new_profile),
            "token": Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=get_token_expiry_seconds()
            )
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed due to data conflict"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=dict)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token

    Accepts either username or email for login
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == login_data.username_or_email) |
        (User.email == login_data.username_or_email)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": str(user.user_id)})

    # Get user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.user_id).first()

    logger.info(f"User logged in: {user.username} ({user.user_id})")

    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(user),
        "profile": UserProfileResponse.model_validate(profile) if profile else None,
        "token": Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=get_token_expiry_seconds()
        )
    }


@router.post("/logout")
def logout_user(current_user: User = Depends(get_current_user)):
    """
    Logout user (client-side token invalidation)

    Note: JWT tokens are stateless, so actual invalidation happens on client side
    This endpoint is mainly for logging and potential future blacklisting
    """
    logger.info(f"User logged out: {current_user.username} ({current_user.user_id})")

    return {
        "message": "Logout successful",
        "detail": "Please remove the token from client storage"
    }


@router.get("/me", response_model=dict)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's information
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()

    return {
        "user": UserResponse.model_validate(current_user),
        "profile": UserProfileResponse.model_validate(profile) if profile else None
    }


@router.post("/forgot-password", response_model=dict)
def request_password_reset(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Request a password reset link

    NOTE: Email sending not implemented yet. This returns a reset token for testing.
    In production, this would send an email with a reset link.
    """
    from api.schemas.user import PasswordResetRequest

    # Find user by email
    user = db.query(User).filter(User.email == email).first()

    # Always return success to prevent email enumeration
    # But only generate token if user exists
    if user and user.is_active:
        # Generate a reset token (expires in 1 hour)
        from api.services.auth_service import create_access_token
        from datetime import timedelta

        reset_token = create_access_token(
            data={"sub": str(user.user_id), "purpose": "password_reset"},
            expires_delta=timedelta(hours=1)
        )

        # In production, send email here
        # For now, just log it
        logger.info(f"Password reset requested for {email}. Token: {reset_token[:20]}...")

        # NOTE: In production, don't return the token. Send it via email instead.
        return {
            "message": "If the email exists, a password reset link has been sent",
            "reset_token": reset_token,  # REMOVE THIS IN PRODUCTION
            "note": "Email service not configured. Token returned for testing only."
        }

    # Return same message even if user doesn't exist (security best practice)
    return {
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post("/reset-password", response_model=dict)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """
    Reset password using the reset token
    """
    from api.schemas.user import PasswordReset
    from api.services.auth_service import verify_access_token, validate_password_strength
    from jose import JWTError

    # Validate new password
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    try:
        # Verify token
        payload = verify_access_token(token)

        # Check if token is for password reset
        if payload.get("purpose") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        # Find user
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update password
        user.password_hash = hash_password(new_password)
        db.commit()

        logger.info(f"Password reset successful for user {user.username}")

        return {
            "message": "Password reset successful. You can now login with your new password."
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )
