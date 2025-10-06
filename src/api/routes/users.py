"""
User Profile Routes
Handles user profile management (get, update, delete)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import get_db
from api.models.user import User, UserProfile
from api.schemas.user import UserProfileResponse, UserProfileUpdate
from api.dependencies import get_current_user, get_current_user_profile

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(profile: UserProfile = Depends(get_current_user_profile)):
    """
    Get current user's profile
    """
    return UserProfileResponse.model_validate(profile)


@router.put("/profile", response_model=UserProfileResponse)
def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile (display_name, bio, avatar_url)
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    # Check if display_name is being changed and if it's already taken
    if profile_update.display_name and profile_update.display_name != profile.display_name:
        existing_profile = db.query(UserProfile).filter(
            UserProfile.display_name == profile_update.display_name
        ).first()

        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Display name already taken"
            )

        profile.display_name = profile_update.display_name
        logger.info(f"User {current_user.username} changed display name to {profile_update.display_name}")

    # Update bio
    if profile_update.bio is not None:
        profile.bio = profile_update.bio

    # Update avatar
    if profile_update.avatar_url is not None:
        profile.avatar_url = profile_update.avatar_url

    db.commit()
    db.refresh(profile)

    return UserProfileResponse.model_validate(profile)


@router.delete("/account", response_model=dict)
def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account (soft delete - marks as inactive)
    """
    # Soft delete: mark user as inactive instead of deleting from database
    current_user.is_active = False
    db.commit()

    logger.warning(f"User account deactivated: {current_user.username} ({current_user.user_id})")

    return {
        "message": "Account deactivated successfully",
        "detail": "Your account has been marked as inactive. Contact support to reactivate."
    }


@router.get("/stats", response_model=dict)
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics (level, XP, achievements, etc.)
    """
    from api.models.progression import UserProgression
    from api.models.achievement import UserAchievement

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()

    # Get achievement count
    achievement_count = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.user_id,
        UserAchievement.completed == True
    ).count()

    # Get total XP from progression
    total_xp_from_progression = db.query(UserProgression).filter(
        UserProgression.user_id == current_user.user_id
    ).count()

    # Calculate XP needed for next level (simplified formula)
    current_level = profile.current_level if profile else 1
    xp_for_next_level = 100 + (current_level * 50)  # Simple formula: 100 + (level * 50)
    xp_progress = (profile.current_xp / xp_for_next_level * 100) if profile else 0

    return {
        "level": profile.current_level if profile else 1,
        "current_xp": profile.current_xp if profile else 0,
        "total_xp": profile.total_xp if profile else 0,
        "xp_for_next_level": xp_for_next_level,
        "xp_progress_percent": round(xp_progress, 2),
        "achievements_unlocked": achievement_count,
        "total_achievements": 63,  # We have 63 achievements
        "achievement_completion_percent": round((achievement_count / 63 * 100), 2),
        "character_type": profile.character_type if profile else None,
        "can_change_character": profile.can_change_character if profile else False
    }
