"""
Lesson SQLAlchemy Models
Phase 2: Educational Content
"""

from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import Base


class Lesson(Base):
    """Lesson model - stores educational lesson content"""
    __tablename__ = "lessons"

    lesson_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_number = Column(Integer, unique=True, nullable=False)
    module_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(JSONB, nullable=False)  # Structured lesson content
    estimated_duration = Column(Integer, default=15)  # Minutes
    xp_reward = Column(Integer, default=100)
    difficulty = Column(String(20), default='beginner')
    prerequisites = Column(JSONB, default=list)  # Array of lesson_numbers
    tags = Column(JSONB, default=list)  # Array of tags
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    quizzes = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")
    user_lessons = relationship("UserLesson", back_populates="lesson", cascade="all, delete-orphan")
    bookmarks = relationship("LessonBookmark", back_populates="lesson", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('module_number BETWEEN 1 AND 4', name='check_module_number'),
        CheckConstraint('lesson_number BETWEEN 1 AND 100', name='check_lesson_number'),
        CheckConstraint("difficulty IN ('beginner', 'intermediate', 'advanced')", name='check_difficulty'),
        CheckConstraint('xp_reward >= 0', name='check_xp_reward'),
        CheckConstraint('estimated_duration > 0', name='check_estimated_duration'),
        Index('idx_lessons_module', 'module_number'),
        Index('idx_lessons_number', 'lesson_number'),
        Index('idx_lessons_difficulty', 'difficulty'),
    )

    def __repr__(self):
        return f"<Lesson(id={self.lesson_id}, number={self.lesson_number}, title='{self.title}')>"


class Quiz(Base):
    """Quiz model - stores quiz questions for lessons"""
    __tablename__ = "quizzes"

    quiz_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('lessons.lesson_id', ondelete='CASCADE'), nullable=False)
    questions = Column(JSONB, nullable=False)  # Array of question objects
    passing_score = Column(Integer, default=70)
    time_limit = Column(Integer)  # Optional time limit in seconds
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    lesson = relationship("Lesson", back_populates="quizzes")

    # Constraints
    __table_args__ = (
        CheckConstraint('passing_score BETWEEN 0 AND 100', name='check_passing_score'),
        Index('idx_quizzes_lesson', 'lesson_id'),
    )

    def __repr__(self):
        return f"<Quiz(id={self.quiz_id}, lesson_id={self.lesson_id})>"


class UserLesson(Base):
    """UserLesson model - tracks user progress through lessons"""
    __tablename__ = "user_lessons"

    user_lesson_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('lessons.lesson_id', ondelete='CASCADE'), nullable=False)
    started_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP)
    quiz_score = Column(Integer)
    quiz_attempts = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)  # Seconds
    progress_percent = Column(Integer, default=0)  # 0-100
    status = Column(String(20), default='in_progress')
    last_accessed = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="user_lessons")
    lesson = relationship("Lesson", back_populates="user_lessons")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson'),
        CheckConstraint("status IN ('in_progress', 'completed', 'failed')", name='check_status'),
        CheckConstraint('quiz_score IS NULL OR (quiz_score BETWEEN 0 AND 100)', name='check_quiz_score'),
        CheckConstraint('quiz_attempts >= 0', name='check_quiz_attempts'),
        CheckConstraint('time_spent >= 0', name='check_time_spent'),
        CheckConstraint('progress_percent BETWEEN 0 AND 100', name='check_progress_percent'),
        Index('idx_user_lessons_user', 'user_id'),
        Index('idx_user_lessons_lesson', 'lesson_id'),
        Index('idx_user_lessons_status', 'status'),
    )

    def __repr__(self):
        return f"<UserLesson(user_id={self.user_id}, lesson_id={self.lesson_id}, status='{self.status}')>"


class LessonBookmark(Base):
    """LessonBookmark model - user bookmarks for lessons"""
    __tablename__ = "lesson_bookmarks"

    bookmark_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('lessons.lesson_id', ondelete='CASCADE'), nullable=False)
    note = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="lesson_bookmarks")
    lesson = relationship("Lesson", back_populates="bookmarks")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson_bookmark'),
        Index('idx_lesson_bookmarks_user', 'user_id'),
        Index('idx_lesson_bookmarks_lesson', 'lesson_id'),
    )

    def __repr__(self):
        return f"<LessonBookmark(user_id={self.user_id}, lesson_id={self.lesson_id})>"
