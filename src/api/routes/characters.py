"""
Character Routes
Handles character information, selection, and character changes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import get_db
from api.models.user import User, UserProfile
from api.schemas.character import CharacterInfo, CharacterChangeRequest
from api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Character type definitions
CHARACTER_TYPES = {
    "analyst": CharacterInfo(
        character_type="analyst",
        name="The Analyst",
        emoji="📊",
        description="Data-driven, methodical, research-focused",
        personality="Prefers fundamental and technical analysis with a scientific approach",
        xp_multipliers={"lessons": 1.1, "trades": 1.0},
        starting_bonuses=[
            "+10% XP from educational content",
            "Unlock Research Tools at Level 5 (instead of Level 10)",
            "Free access to 'Technical Analysis 101' lesson"
        ],
        color_scheme="#3B82F6"  # Blue
    ),
    "risk_taker": CharacterInfo(
        character_type="risk_taker",
        name="The Risk Taker",
        emoji="🚀",
        description="Aggressive, high-reward seeking, momentum trader",
        personality="Attracted to high-growth stocks and volatile crypto markets",
        xp_multipliers={"lessons": 1.0, "volatile_trades": 1.15},
        starting_bonuses=[
            "+15% potential returns in paper trading (with +15% losses too)",
            "Unlock 'Options Trading' lesson at Level 15 (instead of Level 20)",
            "2x volatility exposure in mock portfolio"
        ],
        color_scheme="#EF4444"  # Red
    ),
    "conservative": CharacterInfo(
        character_type="conservative",
        name="The Conservative",
        emoji="🛡️",
        description="Safety-first, long-term focused, diversification advocate",
        personality="Prefers bonds, index funds, and dividend-paying stocks",
        xp_multipliers={"lessons": 1.05, "diversification": 1.1},
        starting_bonuses=[
            "-20% volatility in portfolio (smoother learning curve)",
            "Unlock 'Index Funds & ETFs' lesson at Level 3 (instead of Level 8)",
            "Pre-diversified mock portfolio with balanced allocation"
        ],
        color_scheme="#10B981"  # Green
    ),
    "day_trader": CharacterInfo(
        character_type="day_trader",
        name="The Day Trader",
        emoji="⚡",
        description="Fast-paced, technical pattern focused, active trader",
        personality="Focuses on short-term price movements and intraday opportunities",
        xp_multipliers={"lessons": 1.0, "trades": 1.05},
        starting_bonuses=[
            "+5% XP from making trades (encourages practice)",
            "Unlock 'Chart Patterns' lesson at Level 6 (instead of Level 12)",
            "Advanced charting tools unlocked from day one"
        ],
        color_scheme="#8B5CF6"  # Purple
    ),
    "hodler": CharacterInfo(
        character_type="hodler",
        name="The HODLer",
        emoji="💎",
        description="Patient, conviction-driven, long-term investor",
        personality="Buy and hold strategy with strong hands and diamond patience",
        xp_multipliers={"lessons": 1.0, "long_holds": 1.1},
        starting_bonuses=[
            "+10% returns for positions held 30+ days (in paper trading)",
            "Unlock 'Warren Buffett Strategy' lesson at Level 7 (instead of Level 15)",
            "'Diamond Hands' achievement unlocked from start"
        ],
        color_scheme="#06B6D4"  # Cyan
    )
}


@router.get("/list", response_model=list[CharacterInfo])
def list_characters():
    """
    Get list of all available character types with details
    """
    return list(CHARACTER_TYPES.values())


@router.get("/info/{character_type}", response_model=CharacterInfo)
def get_character_info(character_type: str):
    """
    Get detailed information about a specific character type
    """
    if character_type not in CHARACTER_TYPES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character type '{character_type}' not found"
        )

    return CHARACTER_TYPES[character_type]


@router.post("/change", response_model=dict)
def change_character(
    change_request: CharacterChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user's character type (allowed once at Level 5+)
    """
    # Get user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    # Validate new character type
    if change_request.new_character_type not in CHARACTER_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid character type: {change_request.new_character_type}"
        )

    # Check if already that character
    if profile.character_type == change_request.new_character_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are already playing as {CHARACTER_TYPES[profile.character_type].name}"
        )

    # Check if user is at Level 5 or higher
    if profile.current_level < 5:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Character change is only available at Level 5 or higher. You are currently Level {profile.current_level}."
        )

    # Check if character change is allowed
    if not profile.can_change_character:
        # Check if 30-day cooldown has passed
        cooldown_days = int(os.getenv("CHARACTER_CHANGE_COOLDOWN_DAYS", "30"))
        if profile.character_changed_at:
            time_since_change = datetime.utcnow() - profile.character_changed_at
            if time_since_change < timedelta(days=cooldown_days):
                days_remaining = cooldown_days - time_since_change.days
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Character change is on cooldown. You can change again in {days_remaining} days."
                )
            else:
                # Cooldown has passed, allow change
                profile.can_change_character = True

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Character change is not allowed. You have already used your one-time character change."
            )

    # Change character
    old_character = profile.character_type
    profile.character_type = change_request.new_character_type
    profile.character_changed_at = datetime.utcnow()
    profile.can_change_character = False  # Can only change once (unless cooldown system is enabled)

    db.commit()
    db.refresh(profile)

    logger.info(
        f"User {current_user.username} changed character from {old_character} to {change_request.new_character_type}"
    )

    return {
        "message": "Character changed successfully",
        "old_character": CHARACTER_TYPES[old_character].name,
        "new_character": CHARACTER_TYPES[change_request.new_character_type].name,
        "profile": {
            "character_type": profile.character_type,
            "current_level": profile.current_level,
            "can_change_again": profile.can_change_character
        }
    }


@router.get("/my-character", response_model=dict)
def get_my_character(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's character information
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    character_info = CHARACTER_TYPES[profile.character_type]

    return {
        "character": character_info,
        "can_change_character": profile.can_change_character and profile.current_level >= 5,
        "current_level": profile.current_level,
        "character_changed_at": profile.character_changed_at
    }
