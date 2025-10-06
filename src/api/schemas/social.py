"""
Pydantic schemas for Social features (Friends & Leaderboard)
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class FriendRequest(BaseModel):
    """Request to add a friend"""
    friend_username: str


class FriendshipResponse(BaseModel):
    """Friendship status response"""
    friendship_id: UUID
    friend_id: UUID
    friend_username: str
    friend_display_name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Single entry in leaderboard"""
    rank: int
    user_id: UUID
    username: str
    display_name: str
    character_type: str
    current_level: int
    total_xp: int
    total_trades: int
    total_profit: Decimal
    achievement_count: int

    class Config:
        from_attributes = True
