"""
Pydantic schemas for Achievements
"""

from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
from uuid import UUID


class AchievementResponse(BaseModel):
    """Achievement definition response"""
    achievement_id: UUID
    achievement_code: str
    name: str
    description: Optional[str]
    icon_url: Optional[str]
    xp_reward: int
    category: str
    rarity: str
    unlock_criteria: Dict

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    """User's achievement progress"""
    user_achievement_id: UUID
    achievement: AchievementResponse
    progress: int
    completed: bool
    unlocked_at: Optional[datetime]

    class Config:
        from_attributes = True
