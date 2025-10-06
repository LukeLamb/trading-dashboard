"""
Achievement and UserAchievement models
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, UUID, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import Base


class Achievement(Base):
    """Master list of all available achievements"""
    __tablename__ = "achievements"

    achievement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    achievement_code = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String)
    icon_url = Column(String(500))
    xp_reward = Column(Integer, default=0)
    category = Column(String(50), nullable=False, index=True)
    rarity = Column(String(20), default='common', index=True)
    unlock_criteria = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "category IN ('education', 'trading', 'social', 'milestones', 'special')",
            name="valid_category"
        ),
        CheckConstraint(
            "rarity IN ('common', 'rare', 'epic', 'legendary')",
            name="valid_rarity"
        ),
        CheckConstraint("xp_reward >= 0", name="valid_xp_reward"),
    )

    def __repr__(self):
        return f"<Achievement(code='{self.achievement_code}', name='{self.name}', rarity='{self.rarity}')>"


class UserAchievement(Base):
    """User achievement progress and unlocks"""
    __tablename__ = "user_achievements"

    user_achievement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.achievement_id", ondelete="CASCADE"), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False, index=True)

    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),
        CheckConstraint("progress >= 0", name="valid_progress"),
    )

    def __repr__(self):
        return f"<UserAchievement(user_id='{self.user_id}', achievement_id='{self.achievement_id}', completed={self.completed})>"
