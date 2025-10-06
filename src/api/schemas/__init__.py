"""
Pydantic Schemas for API Request/Response Validation
"""

from .user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileResponse,
    UserProfileUpdate,
    Token,
)
from .character import CharacterInfo, CharacterStats
from .achievement import AchievementResponse, UserAchievementResponse
from .social import FriendRequest, FriendshipResponse, LeaderboardEntry
from .progression import XPGainRequest, ProgressionResponse

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserProfileResponse",
    "UserProfileUpdate",
    "Token",
    "CharacterInfo",
    "CharacterStats",
    "AchievementResponse",
    "UserAchievementResponse",
    "FriendRequest",
    "FriendshipResponse",
    "LeaderboardEntry",
    "XPGainRequest",
    "ProgressionResponse",
]
