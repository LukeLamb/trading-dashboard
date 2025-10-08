"""
UserProgression model for XP tracking
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import Base


class UserProgression(Base):
    """Historical record of all XP gains for analytics"""
    __tablename__ = "user_progression"

    progression_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(Integer, nullable=False)
    xp_gained = Column(Integer, nullable=False)
    xp_source = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    extra_data = Column(JSONB)  # Renamed from 'metadata' (reserved by SQLAlchemy)

    # Relationships
    user = relationship("User", back_populates="progression")

    __table_args__ = (
        CheckConstraint("xp_gained > 0", name="valid_xp_gained"),
        CheckConstraint(
            """xp_source IN (
                'lesson_complete', 'quiz_pass', 'module_complete',
                'first_trade', 'trade_executed', 'profitable_trade',
                'hold_position_30d', 'achievement_unlocked',
                'daily_login', 'login_streak_7d', 'manual_adjustment'
            )""",
            name="valid_xp_source"
        ),
    )

    def __repr__(self):
        return f"<UserProgression(user_id='{self.user_id}', xp_gained={self.xp_gained}, source='{self.xp_source}')>"
