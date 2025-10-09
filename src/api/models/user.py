"""
User, UserProfile, and CharacterStat models
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, CheckConstraint, UUID, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import Base


class User(Base):
    """Core user authentication table"""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    progression = relationship("UserProgression", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    character_stats = relationship("CharacterStat", back_populates="user", cascade="all, delete-orphan")
    friendships = relationship(
        "Friendship",
        foreign_keys="Friendship.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    # Phase 2: Educational Content relationships
    user_lessons = relationship("UserLesson", back_populates="user", cascade="all, delete-orphan")
    lesson_bookmarks = relationship("LessonBookmark", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("char_length(username) >= 3", name="username_length"),
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="email_format"
        ),
    )

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class UserProfile(Base):
    """User profile with character selection and progression"""
    __tablename__ = "user_profiles"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    character_type = Column(String(50), nullable=False, index=True)
    display_name = Column(String(100), unique=True, nullable=False)
    avatar_url = Column(String(500))
    bio = Column(String)
    current_level = Column(Integer, default=1, index=True)
    current_xp = Column(Integer, default=0)
    total_xp = Column(Integer, default=0, index=True)
    character_changed_at = Column(DateTime(timezone=True))
    can_change_character = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")

    __table_args__ = (
        CheckConstraint(
            "character_type IN ('analyst', 'risk_taker', 'conservative', 'day_trader', 'hodler')",
            name="valid_character_type"
        ),
        CheckConstraint("current_level >= 1 AND current_level <= 100", name="valid_level"),
        CheckConstraint("current_xp >= 0 AND total_xp >= 0", name="valid_xp"),
        CheckConstraint("char_length(display_name) >= 3", name="display_name_length"),
    )

    def __repr__(self):
        return f"<UserProfile(display_name='{self.display_name}', character='{self.character_type}', level={self.current_level})>"


class CharacterStat(Base):
    """Individual character attribute tracking"""
    __tablename__ = "character_stats"

    stat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    stat_name = Column(String(100), nullable=False)
    stat_value = Column(DECIMAL(10, 2), default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="character_stats")

    __table_args__ = (
        CheckConstraint(
            "stat_name IN ('risk_tolerance', 'research_skill', 'trading_speed', 'patience_level', 'analytical_skill', 'emotional_control')",
            name="valid_stat_name"
        ),
    )

    def __repr__(self):
        return f"<CharacterStat(stat_name='{self.stat_name}', value={self.stat_value})>"
