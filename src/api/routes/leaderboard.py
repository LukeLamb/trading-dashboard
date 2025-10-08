"""
Leaderboard Routes
Handles leaderboard rankings and statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import get_db
from api.models.user import User, UserProfile
from api.models.achievement import UserAchievement
from api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/overall", response_model=List[dict])
def get_overall_leaderboard(
    limit: int = Query(default=100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get overall leaderboard ranked by total XP

    Returns top users ranked by total_xp, with pagination support
    """
    # Query user profiles with rankings
    leaderboard = db.query(
        UserProfile,
        User.username,
        func.count(UserAchievement.user_achievement_id).label('achievement_count')
    ).join(
        User, UserProfile.user_id == User.user_id
    ).outerjoin(
        UserAchievement,
        (UserAchievement.user_id == UserProfile.user_id) & (UserAchievement.completed == True)
    ).filter(
        User.is_active == True
    ).group_by(
        UserProfile.profile_id,
        User.username
    ).order_by(
        desc(UserProfile.total_xp),
        desc(UserProfile.current_level),
        User.username
    ).limit(limit).offset(offset).all()

    results = []
    for rank, (profile, username, achievement_count) in enumerate(leaderboard, start=offset + 1):
        results.append({
            "rank": rank,
            "user_id": str(profile.user_id),
            "username": username,
            "display_name": profile.display_name,
            "character_type": profile.character_type,
            "avatar_url": profile.avatar_url,
            "current_level": profile.current_level,
            "total_xp": profile.total_xp,
            "achievements_unlocked": achievement_count or 0
        })

    return results


@router.get("/character/{character_type}", response_model=List[dict])
def get_character_leaderboard(
    character_type: str,
    limit: int = Query(default=100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard for a specific character type

    character_type: analyst, risk_taker, conservative, day_trader, hodler
    """
    # Validate character type
    valid_characters = ['analyst', 'risk_taker', 'conservative', 'day_trader', 'hodler']
    if character_type not in valid_characters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid character type. Must be one of: {', '.join(valid_characters)}"
        )

    # Query user profiles with rankings for specific character
    leaderboard = db.query(
        UserProfile,
        User.username,
        func.count(UserAchievement.user_achievement_id).label('achievement_count')
    ).join(
        User, UserProfile.user_id == User.user_id
    ).outerjoin(
        UserAchievement,
        (UserAchievement.user_id == UserProfile.user_id) & (UserAchievement.completed == True)
    ).filter(
        User.is_active == True,
        UserProfile.character_type == character_type
    ).group_by(
        UserProfile.profile_id,
        User.username
    ).order_by(
        desc(UserProfile.total_xp),
        desc(UserProfile.current_level),
        User.username
    ).limit(limit).offset(offset).all()

    results = []
    for rank, (profile, username, achievement_count) in enumerate(leaderboard, start=offset + 1):
        results.append({
            "rank": rank,
            "user_id": str(profile.user_id),
            "username": username,
            "display_name": profile.display_name,
            "character_type": profile.character_type,
            "avatar_url": profile.avatar_url,
            "current_level": profile.current_level,
            "total_xp": profile.total_xp,
            "achievements_unlocked": achievement_count or 0
        })

    return results


@router.get("/my-rank", response_model=dict)
def get_my_rank(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's ranking (overall and by character)
    """

    # Get user's profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    # Calculate overall rank
    overall_rank = db.query(func.count(UserProfile.profile_id)).filter(
        UserProfile.total_xp > profile.total_xp
    ).scalar() + 1

    # Calculate character rank
    character_rank = db.query(func.count(UserProfile.profile_id)).filter(
        UserProfile.character_type == profile.character_type,
        UserProfile.total_xp > profile.total_xp
    ).scalar() + 1

    # Get total users
    total_users = db.query(func.count(UserProfile.profile_id)).scalar()

    # Get total users with same character
    total_character_users = db.query(func.count(UserProfile.profile_id)).filter(
        UserProfile.character_type == profile.character_type
    ).scalar()

    # Get achievement count
    achievement_count = db.query(func.count(UserAchievement.user_achievement_id)).filter(
        UserAchievement.user_id == current_user.user_id,
        UserAchievement.completed == True
    ).scalar()

    return {
        "overall_rank": overall_rank,
        "overall_total": total_users,
        "overall_percentile": round((1 - (overall_rank - 1) / total_users) * 100, 2) if total_users > 0 else 0,
        "character_rank": character_rank,
        "character_total": total_character_users,
        "character_percentile": round((1 - (character_rank - 1) / total_character_users) * 100, 2) if total_character_users > 0 else 0,
        "character_type": profile.character_type,
        "current_level": profile.current_level,
        "total_xp": profile.total_xp,
        "achievements_unlocked": achievement_count or 0
    }
