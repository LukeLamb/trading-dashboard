"""
Pydantic schemas for Character system
"""

from pydantic import BaseModel
from typing import Dict, List


class CharacterInfo(BaseModel):
    """Information about a character type"""
    character_type: str
    name: str
    emoji: str
    description: str
    personality: str
    xp_multipliers: Dict[str, float]
    starting_bonuses: List[str]
    color_scheme: str

    class Config:
        json_schema_extra = {
            "example": {
                "character_type": "analyst",
                "name": "The Analyst",
                "emoji": "📊",
                "description": "Data-driven, methodical, research-focused",
                "personality": "Prefers fundamental and technical analysis",
                "xp_multipliers": {"lessons": 1.1, "trades": 1.0},
                "starting_bonuses": [
                    "+10% XP from educational content",
                    "Unlock Research Tools at Level 5",
                    "Free: Technical Analysis 101 lesson"
                ],
                "color_scheme": "#3B82F6"
            }
        }


class CharacterStats(BaseModel):
    """Character attribute statistics"""
    risk_tolerance: float
    research_skill: float
    trading_speed: float
    patience_level: float
    analytical_skill: float
    emotional_control: float

    class Config:
        json_schema_extra = {
            "example": {
                "risk_tolerance": 65.5,
                "research_skill": 85.0,
                "trading_speed": 50.0,
                "patience_level": 70.0,
                "analytical_skill": 90.0,
                "emotional_control": 75.0
            }
        }


class CharacterChangeRequest(BaseModel):
    """Request to change character type"""
    new_character_type: str

    class Config:
        json_schema_extra = {
            "example": {
                "new_character_type": "risk_taker"
            }
        }
