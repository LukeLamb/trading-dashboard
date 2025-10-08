"""
Achievement Routes
Handles achievement listing and user achievement tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import get_db
from api.models.user import User, UserProfile
from api.models.achievement import Achievement, UserAchievement
from api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[dict])
def get_all_achievements(db: Session = Depends(get_db)):
    """
    Get list of all available achievements
    """
    achievements = db.query(Achievement).order_by(
        Achievement.category,
        Achievement.rarity,
        Achievement.xp_reward.desc()
    ).all()

    return [
        {
            "achievement_id": str(ach.achievement_id),
            "achievement_code": ach.achievement_code,
            "name": ach.name,
            "description": ach.description,
            "icon_url": ach.icon_url,
            "xp_reward": ach.xp_reward,
            "category": ach.category,
            "rarity": ach.rarity,
            "unlock_criteria": ach.unlock_criteria
        }
        for ach in achievements
    ]


@router.get("/user", response_model=dict)
def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's achievements (both completed and in progress)
    """
    # Get all user achievements
    user_achievements = db.query(UserAchievement, Achievement).join(
        Achievement, UserAchievement.achievement_id == Achievement.achievement_id
    ).filter(
        UserAchievement.user_id == current_user.user_id
    ).all()

    completed = []
    in_progress = []

    for user_ach, ach in user_achievements:
        achievement_data = {
            "user_achievement_id": str(user_ach.user_achievement_id),
            "achievement_id": str(ach.achievement_id),
            "achievement_code": ach.achievement_code,
            "name": ach.name,
            "description": ach.description,
            "icon_url": ach.icon_url,
            "xp_reward": ach.xp_reward,
            "category": ach.category,
            "rarity": ach.rarity,
            "progress": user_ach.progress,
            "unlocked_at": user_ach.unlocked_at.isoformat() if user_ach.unlocked_at else None
        }

        if user_ach.completed:
            completed.append(achievement_data)
        else:
            in_progress.append(achievement_data)

    # Get total achievements count
    total_achievements = db.query(Achievement).count()
    completed_count = len(completed)

    return {
        "completed": completed,
        "in_progress": in_progress,
        "total_completed": completed_count,
        "total_achievements": total_achievements,
        "completion_percentage": round((completed_count / total_achievements * 100), 2) if total_achievements > 0 else 0
    }


@router.post("/unlock", response_model=dict)
def unlock_achievement(
    achievement_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlock an achievement for the current user (internal use)

    This is typically called by the system when achievement criteria are met
    """
    # Find achievement by code
    achievement = db.query(Achievement).filter(
        Achievement.achievement_code == achievement_code
    ).first()

    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement '{achievement_code}' not found"
        )

    # Check if user already has this achievement
    existing = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.user_id,
        UserAchievement.achievement_id == achievement.achievement_id
    ).first()

    if existing and existing.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Achievement already unlocked"
        )

    # Get user profile to award XP
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    try:
        if existing:
            # Update existing achievement to completed
            existing.completed = True
            existing.progress = 100
        else:
            # Create new user achievement
            user_achievement = UserAchievement(
                user_id=current_user.user_id,
                achievement_id=achievement.achievement_id,
                progress=100,
                completed=True
            )
            db.add(user_achievement)

        # Award XP to user profile
        profile.current_xp += achievement.xp_reward
        profile.total_xp += achievement.xp_reward

        # Check for level up (simple formula: level = floor(total_xp / 150) + 1)
        new_level = (profile.total_xp // 150) + 1
        leveled_up = new_level > profile.current_level

        if leveled_up:
            profile.current_level = new_level
            # Reset current_xp to remainder
            profile.current_xp = profile.total_xp % 150

        db.commit()

        logger.info(
            f"Achievement unlocked: {achievement.achievement_code} for user {current_user.username} "
            f"(+{achievement.xp_reward} XP)"
        )

        return {
            "message": "Achievement unlocked!",
            "achievement": {
                "name": achievement.name,
                "description": achievement.description,
                "xp_reward": achievement.xp_reward,
                "rarity": achievement.rarity
            },
            "xp_awarded": achievement.xp_reward,
            "new_total_xp": profile.total_xp,
            "new_level": profile.current_level,
            "leveled_up": leveled_up
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error unlocking achievement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlock achievement"
        )
