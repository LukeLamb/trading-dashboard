"""
Friendship and LeaderboardCache models for social features
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, UUID, UniqueConstraint, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import Base


class Friendship(Base):
    """Social connections between users"""
    __tablename__ = "friendships"

    friendship_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    friend_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default='pending', index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="friendships")

    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
        CheckConstraint("user_id != friend_id", name="no_self_friend"),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'blocked')",
            name="valid_friendship_status"
        ),
    )

    def __repr__(self):
        return f"<Friendship(user_id='{self.user_id}', friend_id='{self.friend_id}', status='{self.status}')>"


class LeaderboardCache(Base):
    """Pre-calculated leaderboard rankings for performance"""
    __tablename__ = "leaderboard_cache"

    cache_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    username = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    character_type = Column(String(50), nullable=False)
    current_level = Column(Integer, nullable=False)
    total_xp = Column(Integer, nullable=False)
    total_trades = Column(Integer, default=0)
    total_profit = Column(DECIMAL(15, 2), default=0)
    achievement_count = Column(Integer, default=0)
    rank_overall = Column(Integer)
    rank_by_character = Column(Integer)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("rank_overall > 0 AND rank_by_character > 0", name="valid_ranks"),
    )

    def __repr__(self):
        return f"<LeaderboardCache(username='{self.username}', rank_overall={self.rank_overall}, total_xp={self.total_xp})>"
