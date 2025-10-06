"""
Pydantic schemas for XP & Progression
"""

from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
from uuid import UUID


class XPGainRequest(BaseModel):
    """Request to award XP (internal use)"""
    xp_amount: int
    source: str
    metadata: Optional[Dict] = None


class ProgressionResponse(BaseModel):
    """XP progression record"""
    progression_id: UUID
    level: int
    xp_gained: int
    xp_source: str
    timestamp: datetime
    metadata: Optional[Dict]

    class Config:
        from_attributes = True
