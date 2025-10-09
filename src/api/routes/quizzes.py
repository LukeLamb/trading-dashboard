"""
Quiz API Routes
Phase 2: Educational Content
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from datetime import datetime

from ..dependencies import get_db, get_current_user
from ..models import Quiz, UserLesson, Lesson, User, UserProgression, UserProfile
from ..schemas.lesson import QuizAnswerSubmission, QuizResult

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("/{quiz_id}/submit", response_model=QuizResult)
def submit_quiz(
    quiz_id: UUID,
    submission: QuizAnswerSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit quiz answers and get results.
    Awards XP if passed, updates user_lesson status.
    """
    # Get quiz
    quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Get lesson
    lesson = db.query(Lesson).filter(Lesson.lesson_id == quiz.lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Get user_lesson
    user_lesson = db.query(UserLesson).filter(
        and_(
            UserLesson.user_id == current_user.user_id,
            UserLesson.lesson_id == quiz.lesson_id
        )
    ).first()

    if not user_lesson:
        raise HTTPException(
            status_code=403,
            detail="You must start the lesson before taking the quiz"
        )

    # Check answers
    if len(submission.answers) != len(quiz.questions):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(quiz.questions)} answers, got {len(submission.answers)}"
        )

    # Grade quiz
    correct_count = 0
    feedback = []

    for i, (user_answer, question) in enumerate(zip(submission.answers, quiz.questions)):
        correct_answer = question.get("correct_answer")
        is_correct = False

        # Check based on question type
        if question.get("type") == "multiple_choice":
            is_correct = user_answer == correct_answer
        elif question.get("type") == "true_false":
            is_correct = user_answer == correct_answer
        elif question.get("type") == "fill_in_blank":
            # Case-insensitive string comparison
            is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()

        if is_correct:
            correct_count += 1

        feedback.append({
            "question_number": i + 1,
            "question": question.get("question"),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": question.get("explanation"),
        })

    # Calculate score
    score = int((correct_count / len(quiz.questions)) * 100)
    passed = score >= quiz.passing_score

    # Update user_lesson
    user_lesson.quiz_attempts += 1
    user_lesson.quiz_score = score

    if passed and user_lesson.status != 'completed':
        user_lesson.status = 'completed'
        user_lesson.completed_at = datetime.utcnow()

        # Award XP
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.user_id
        ).first()

        if user_profile:
            # Calculate XP with character multiplier
            xp_to_award = lesson.xp_reward

            # Apply character-specific multiplier for lessons
            character_multipliers = {
                "analyst": 1.1,
                "risk_taker": 1.0,
                "conservative": 1.05,
                "day_trader": 1.0,
                "hodler": 1.0,
            }
            multiplier = character_multipliers.get(user_profile.character_type, 1.0)
            xp_to_award = int(xp_to_award * multiplier)

            # Bonus for perfect score
            if score == 100:
                xp_to_award = int(xp_to_award * 1.5)

            # Award XP
            user_profile.current_xp += xp_to_award
            user_profile.total_xp += xp_to_award

            # Check for level up
            xp_for_next_level = calculate_xp_for_level(user_profile.current_level + 1)
            while user_profile.current_xp >= xp_for_next_level and user_profile.current_level < 100:
                user_profile.current_level += 1
                user_profile.current_xp -= xp_for_next_level
                xp_for_next_level = calculate_xp_for_level(user_profile.current_level + 1)

            # Log progression
            progression_entry = UserProgression(
                user_id=current_user.user_id,
                level=user_profile.current_level,
                xp_gained=xp_to_award,
                xp_source='lesson_complete',
                extra_data={
                    "lesson_id": str(lesson.lesson_id),
                    "lesson_number": lesson.lesson_number,
                    "lesson_title": lesson.title,
                    "quiz_score": score,
                    "quiz_attempts": user_lesson.quiz_attempts,
                }
            )
            db.add(progression_entry)
    elif not passed:
        user_lesson.status = 'failed'

    db.commit()

    # Determine if can retry
    can_retry = not passed

    # Calculate XP earned
    xp_earned = lesson.xp_reward if passed else 0
    if passed:
        character_multipliers = {
            "analyst": 1.1,
            "risk_taker": 1.0,
            "conservative": 1.05,
            "day_trader": 1.0,
            "hodler": 1.0,
        }
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.user_id
        ).first()
        multiplier = character_multipliers.get(user_profile.character_type, 1.0) if user_profile else 1.0
        xp_earned = int(xp_earned * multiplier)
        if score == 100:
            xp_earned = int(xp_earned * 1.5)

    return QuizResult(
        quiz_id=quiz_id,
        score=score,
        passed=passed,
        correct_count=correct_count,
        total_questions=len(quiz.questions),
        xp_earned=xp_earned,
        feedback=feedback,
        can_retry=can_retry,
    )


def calculate_xp_for_level(level: int) -> int:
    """Calculate XP required for a given level"""
    if level <= 1:
        return 0
    elif level <= 5:
        return 100 + (level - 2) * 50
    elif level <= 10:
        return 100 + (level - 2) * 100
    elif level <= 25:
        return 100 + (level - 2) * 100
    else:
        return 100 + (level - 2) * 200
