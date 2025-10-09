"""
Lesson API Routes
Phase 2: Educational Content
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from uuid import UUID

from ..dependencies import get_db, get_current_user
from ..models import Lesson, Quiz, UserLesson, LessonBookmark, User
from ..schemas.lesson import (
    LessonResponse,
    LessonListItem,
    LessonCreate,
    LessonUpdate,
    QuizResponse,
    QuizResult,
    QuizAnswerSubmission,
    UserLessonCreate,
    UserLessonUpdate,
    UserLessonResponse,
    LessonBookmarkCreate,
    LessonBookmarkResponse,
    LearningStats,
    LessonRecommendation,
)

router = APIRouter(prefix="/lessons", tags=["Lessons"])


# ============================================
# Lesson Endpoints
# ============================================

@router.get("", response_model=List[LessonListItem])
def get_lessons(
    module: Optional[int] = Query(None, ge=1, le=4, description="Filter by module number"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all lessons with optional filters.
    Shows user's progress if authenticated.
    """
    query = db.query(Lesson)

    # Apply filters
    if module:
        query = query.filter(Lesson.module_number == module)
    if difficulty:
        query = query.filter(Lesson.difficulty == difficulty)

    # Order by lesson number
    query = query.order_by(Lesson.lesson_number)

    # Pagination
    lessons = query.offset(skip).limit(limit).all()

    # Get user's progress for each lesson
    user_lessons_dict = {}
    if current_user:
        user_lessons = db.query(UserLesson).filter(
            UserLesson.user_id == current_user.user_id
        ).all()
        user_lessons_dict = {ul.lesson_id: ul for ul in user_lessons}

    # Build response
    result = []
    for lesson in lessons:
        # Check if lesson is locked by prerequisites
        is_locked = False
        if lesson.prerequisites:
            completed_lessons = db.query(Lesson.lesson_number).join(
                UserLesson
            ).filter(
                and_(
                    UserLesson.user_id == current_user.user_id,
                    UserLesson.status == 'completed',
                    Lesson.lesson_number.in_(lesson.prerequisites)
                )
            ).all()
            completed_numbers = [l[0] for l in completed_lessons]
            is_locked = not all(prereq in completed_numbers for prereq in lesson.prerequisites)

        user_lesson = user_lessons_dict.get(lesson.lesson_id)

        result.append(LessonListItem(
            lesson_id=lesson.lesson_id,
            lesson_number=lesson.lesson_number,
            module_number=lesson.module_number,
            title=lesson.title,
            description=lesson.description,
            estimated_duration=lesson.estimated_duration,
            xp_reward=lesson.xp_reward,
            difficulty=lesson.difficulty,
            tags=lesson.tags or [],
            is_locked=is_locked,
            user_progress=user_lesson.progress_percent if user_lesson else None,
            user_status=user_lesson.status if user_lesson else None,
        ))

    return result


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed lesson content by ID.
    Checks prerequisites before allowing access.
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check prerequisites
    if lesson.prerequisites:
        completed_lessons = db.query(Lesson.lesson_number).join(
            UserLesson
        ).filter(
            and_(
                UserLesson.user_id == current_user.user_id,
                UserLesson.status == 'completed',
                Lesson.lesson_number.in_(lesson.prerequisites)
            )
        ).all()
        completed_numbers = [l[0] for l in completed_lessons]

        if not all(prereq in completed_numbers for prereq in lesson.prerequisites):
            missing = [p for p in lesson.prerequisites if p not in completed_numbers]
            raise HTTPException(
                status_code=403,
                detail=f"Prerequisites not met. Complete lessons: {missing}"
            )

    # Check if lesson has a quiz
    has_quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first() is not None

    response = LessonResponse(
        lesson_id=lesson.lesson_id,
        lesson_number=lesson.lesson_number,
        module_number=lesson.module_number,
        title=lesson.title,
        description=lesson.description,
        content=lesson.content,
        estimated_duration=lesson.estimated_duration,
        xp_reward=lesson.xp_reward,
        difficulty=lesson.difficulty,
        prerequisites=lesson.prerequisites or [],
        tags=lesson.tags or [],
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
        has_quiz=has_quiz,
    )

    return response


@router.get("/{lesson_id}/quiz", response_model=QuizResponse)
def get_lesson_quiz(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quiz for a lesson (without correct answers).
    Only available after lesson is started.
    """
    # Check lesson exists
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Get quiz
    quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for this lesson")

    # Check user has started the lesson
    user_lesson = db.query(UserLesson).filter(
        and_(
            UserLesson.user_id == current_user.user_id,
            UserLesson.lesson_id == lesson_id
        )
    ).first()

    if not user_lesson:
        raise HTTPException(
            status_code=403,
            detail="You must start the lesson before taking the quiz"
        )

    # Remove correct answers from questions
    questions_without_answers = []
    for q in quiz.questions:
        question_data = dict(q)
        # Keep everything except correct_answer
        safe_question = {
            "question": question_data.get("question"),
            "type": question_data.get("type"),
            "options": question_data.get("options"),
        }
        questions_without_answers.append(safe_question)

    return QuizResponse(
        quiz_id=quiz.quiz_id,
        lesson_id=quiz.lesson_id,
        questions=questions_without_answers,
        total_questions=len(quiz.questions),
        passing_score=quiz.passing_score,
        time_limit=quiz.time_limit,
        created_at=quiz.created_at,
    )


@router.post("/{lesson_id}/start", response_model=UserLessonResponse, status_code=status.HTTP_201_CREATED)
def start_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a lesson as started for the current user.
    Creates a user_lesson record.
    """
    # Check lesson exists
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check if already started
    existing = db.query(UserLesson).filter(
        and_(
            UserLesson.user_id == current_user.user_id,
            UserLesson.lesson_id == lesson_id
        )
    ).first()

    if existing:
        return existing

    # Create new user_lesson
    user_lesson = UserLesson(
        user_id=current_user.user_id,
        lesson_id=lesson_id,
        status='in_progress',
        progress_percent=0,
        time_spent=0,
        quiz_attempts=0,
    )

    db.add(user_lesson)
    db.commit()
    db.refresh(user_lesson)

    return user_lesson


@router.put("/{lesson_id}/progress", response_model=UserLessonResponse)
def update_lesson_progress(
    lesson_id: UUID,
    progress_data: UserLessonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's progress on a lesson.
    Tracks reading progress and time spent.
    """
    user_lesson = db.query(UserLesson).filter(
        and_(
            UserLesson.user_id == current_user.user_id,
            UserLesson.lesson_id == lesson_id
        )
    ).first()

    if not user_lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not started. Call /start first."
        )

    # Update fields
    if progress_data.progress_percent is not None:
        user_lesson.progress_percent = progress_data.progress_percent
    if progress_data.time_spent is not None:
        user_lesson.time_spent = progress_data.time_spent
    if progress_data.status:
        user_lesson.status = progress_data.status

    db.commit()
    db.refresh(user_lesson)

    return user_lesson


@router.post("/{lesson_id}/bookmark", response_model=LessonBookmarkResponse, status_code=status.HTTP_201_CREATED)
def bookmark_lesson(
    lesson_id: UUID,
    bookmark_data: LessonBookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bookmark a lesson for later.
    """
    # Check lesson exists
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check if already bookmarked
    existing = db.query(LessonBookmark).filter(
        and_(
            LessonBookmark.user_id == current_user.user_id,
            LessonBookmark.lesson_id == lesson_id
        )
    ).first()

    if existing:
        # Update note if provided
        if bookmark_data.note:
            existing.note = bookmark_data.note
            db.commit()
            db.refresh(existing)
        return LessonBookmarkResponse(
            bookmark_id=existing.bookmark_id,
            user_id=existing.user_id,
            lesson_id=existing.lesson_id,
            note=existing.note,
            created_at=existing.created_at,
            lesson_title=lesson.title,
        )

    # Create new bookmark
    bookmark = LessonBookmark(
        user_id=current_user.user_id,
        lesson_id=lesson_id,
        note=bookmark_data.note,
    )

    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    return LessonBookmarkResponse(
        bookmark_id=bookmark.bookmark_id,
        user_id=bookmark.user_id,
        lesson_id=bookmark.lesson_id,
        note=bookmark.note,
        created_at=bookmark.created_at,
        lesson_title=lesson.title,
    )


@router.delete("/{lesson_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
def remove_bookmark(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a bookmark from a lesson.
    """
    bookmark = db.query(LessonBookmark).filter(
        and_(
            LessonBookmark.user_id == current_user.user_id,
            LessonBookmark.lesson_id == lesson_id
        )
    ).first()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    db.delete(bookmark)
    db.commit()

    return None
