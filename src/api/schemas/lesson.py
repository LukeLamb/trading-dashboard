"""
Lesson Pydantic Schemas
Phase 2: Educational Content
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================
# Lesson Schemas
# ============================================

class LessonBase(BaseModel):
    """Base lesson schema"""
    lesson_number: int = Field(..., ge=1, le=100, description="Lesson number (1-100)")
    module_number: int = Field(..., ge=1, le=4, description="Module number (1-4)")
    title: str = Field(..., min_length=1, max_length=200, description="Lesson title")
    description: Optional[str] = Field(None, description="Lesson description")
    estimated_duration: int = Field(15, gt=0, description="Estimated duration in minutes")
    xp_reward: int = Field(100, ge=0, description="XP reward for completion")
    difficulty: str = Field("beginner", description="Difficulty level")
    prerequisites: List[int] = Field(default_factory=list, description="Required lesson numbers")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v):
        allowed = ["beginner", "intermediate", "advanced"]
        if v not in allowed:
            raise ValueError(f"Difficulty must be one of: {allowed}")
        return v


class LessonContentSection(BaseModel):
    """Lesson content section"""
    type: str = Field(..., description="Section type: text, image, video, interactive")
    content: Optional[str] = Field(None, description="Text content (markdown)")
    url: Optional[str] = Field(None, description="URL for image/video")
    caption: Optional[str] = Field(None, description="Caption for media")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed = ["text", "image", "video", "interactive"]
        if v not in allowed:
            raise ValueError(f"Section type must be one of: {allowed}")
        return v


class LessonContent(BaseModel):
    """Lesson content structure"""
    sections: List[LessonContentSection] = Field(..., description="Content sections")


class LessonCreate(LessonBase):
    """Schema for creating a lesson"""
    content: Dict[str, Any] = Field(..., description="Lesson content (JSONB)")


class LessonUpdate(BaseModel):
    """Schema for updating a lesson"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    estimated_duration: Optional[int] = Field(None, gt=0)
    xp_reward: Optional[int] = Field(None, ge=0)
    difficulty: Optional[str] = None
    prerequisites: Optional[List[int]] = None
    tags: Optional[List[str]] = None


class LessonResponse(LessonBase):
    """Schema for lesson response"""
    lesson_id: UUID
    content: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    has_quiz: bool = Field(default=False, description="Whether lesson has a quiz")

    model_config = {"from_attributes": True}


class LessonListItem(BaseModel):
    """Simplified lesson for list views"""
    lesson_id: UUID
    lesson_number: int
    module_number: int
    title: str
    description: Optional[str]
    estimated_duration: int
    xp_reward: int
    difficulty: str
    tags: List[str]
    is_locked: bool = Field(default=False, description="Whether lesson is locked by prerequisites")
    user_progress: Optional[int] = Field(None, ge=0, le=100, description="User's progress percentage")
    user_status: Optional[str] = Field(None, description="User's completion status")

    model_config = {"from_attributes": True}


# ============================================
# Quiz Schemas
# ============================================

class QuizQuestion(BaseModel):
    """Single quiz question"""
    question: str = Field(..., min_length=1, description="Question text")
    type: str = Field(..., description="Question type: multiple_choice, true_false, fill_in_blank")
    options: Optional[List[str]] = Field(None, description="Answer options (for multiple choice)")
    correct_answer: Any = Field(..., description="Correct answer (index for MC, bool for T/F, string for fill)")
    explanation: str = Field(..., min_length=1, description="Explanation of correct answer")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed = ["multiple_choice", "true_false", "fill_in_blank"]
        if v not in allowed:
            raise ValueError(f"Question type must be one of: {allowed}")
        return v


class QuizBase(BaseModel):
    """Base quiz schema"""
    passing_score: int = Field(70, ge=0, le=100, description="Minimum score to pass")
    time_limit: Optional[int] = Field(None, gt=0, description="Time limit in seconds")


class QuizCreate(QuizBase):
    """Schema for creating a quiz"""
    lesson_id: UUID
    questions: List[QuizQuestion] = Field(..., min_length=1, description="Quiz questions")


class QuizResponse(QuizBase):
    """Schema for quiz response (without answers)"""
    quiz_id: UUID
    lesson_id: UUID
    questions: List[Dict[str, Any]] = Field(..., description="Questions without correct answers")
    total_questions: int
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizAnswerSubmission(BaseModel):
    """Schema for submitting quiz answers"""
    answers: List[Any] = Field(..., description="User's answers (index, bool, or string)")


class QuizResult(BaseModel):
    """Schema for quiz results"""
    quiz_id: UUID
    score: int = Field(..., ge=0, le=100, description="Score percentage")
    passed: bool = Field(..., description="Whether user passed")
    correct_count: int = Field(..., ge=0, description="Number of correct answers")
    total_questions: int = Field(..., gt=0, description="Total number of questions")
    xp_earned: int = Field(..., ge=0, description="XP earned from quiz")
    feedback: List[Dict[str, Any]] = Field(..., description="Feedback for each question")
    can_retry: bool = Field(..., description="Whether user can retry")


# ============================================
# User Lesson Progress Schemas
# ============================================

class UserLessonBase(BaseModel):
    """Base user lesson schema"""
    progress_percent: int = Field(0, ge=0, le=100, description="Reading progress percentage")
    time_spent: int = Field(0, ge=0, description="Time spent in seconds")


class UserLessonCreate(UserLessonBase):
    """Schema for starting a lesson"""
    lesson_id: UUID


class UserLessonUpdate(BaseModel):
    """Schema for updating lesson progress"""
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    time_spent: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            allowed = ["in_progress", "completed", "failed"]
            if v not in allowed:
                raise ValueError(f"Status must be one of: {allowed}")
        return v


class UserLessonResponse(UserLessonBase):
    """Schema for user lesson response"""
    user_lesson_id: UUID
    user_id: UUID
    lesson_id: UUID
    started_at: datetime
    completed_at: Optional[datetime]
    quiz_score: Optional[int]
    quiz_attempts: int
    status: str
    last_accessed: datetime

    model_config = {"from_attributes": True}


# ============================================
# Lesson Bookmark Schemas
# ============================================

class LessonBookmarkCreate(BaseModel):
    """Schema for creating a bookmark"""
    lesson_id: UUID
    note: Optional[str] = Field(None, max_length=500, description="Optional note")


class LessonBookmarkResponse(BaseModel):
    """Schema for bookmark response"""
    bookmark_id: UUID
    user_id: UUID
    lesson_id: UUID
    note: Optional[str]
    created_at: datetime
    lesson_title: Optional[str] = None

    model_config = {"from_attributes": True}


# ============================================
# Learning Progress Schemas
# ============================================

class LearningStats(BaseModel):
    """User's overall learning statistics"""
    total_lessons_started: int
    total_lessons_completed: int
    total_time_spent: int  # Seconds
    average_quiz_score: float
    completion_percentage: float
    lessons_in_progress: int
    total_bookmarks: int
    current_streak: int = Field(0, description="Days of consecutive learning")


class LessonRecommendation(BaseModel):
    """Recommended lesson for user"""
    lesson_id: UUID
    lesson_number: int
    title: str
    description: Optional[str]
    xp_reward: int
    estimated_duration: int
    reason: str = Field(..., description="Why this lesson is recommended")


class ModuleProgress(BaseModel):
    """Progress summary for a module"""
    module_number: int
    module_name: str
    total_lessons: int
    completed_lessons: int
    total_xp: int
    earned_xp: int
    completion_percentage: float
    estimated_time_remaining: int  # Minutes
