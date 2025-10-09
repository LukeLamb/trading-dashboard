"""
Quiz Page
Take quiz, submit answers, and see results
"""

import streamlit as st
import requests
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# API Configuration
API_BASE_URL = "http://localhost:8000"


def get_quiz(token, lesson_id):
    """Fetch quiz for a lesson"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/lessons/{lesson_id}/quiz",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Failed to load quiz: {response.status_code}"
    except Exception as e:
        return False, str(e)


def submit_quiz(token, quiz_id, answers):
    """Submit quiz answers"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {"answers": answers}
        response = requests.post(
            f"{API_BASE_URL}/api/quizzes/{quiz_id}/submit",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Failed to submit quiz: {response.status_code}"
    except Exception as e:
        return False, str(e)


def render_question(question, question_index):
    """Render a single quiz question"""
    question_type = question.get("type", "multiple_choice")
    question_text = question.get("question", "")
    options = question.get("options", [])

    st.markdown(f"""
    <div style="
        background: rgba(30, 41, 59, 0.5);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        backdrop-filter: blur(10px);
    ">
        <h3 style="color: #F8FAFC; margin-bottom: 16px;">
            Question {question_index + 1}
        </h3>
        <p style="color: rgba(255, 255, 255, 0.9); font-size: 16px; line-height: 1.6;">
            {question_text}
        </p>
    </div>
    """, unsafe_allow_html=True)

    answer = None

    if question_type == "multiple_choice":
        # Radio buttons for multiple choice
        answer = st.radio(
            "Select your answer:",
            options=options,
            key=f"question_{question_index}",
            label_visibility="collapsed"
        )

    elif question_type == "true_false":
        # True/False buttons
        answer = st.radio(
            "Select your answer:",
            options=["True", "False"],
            key=f"question_{question_index}",
            label_visibility="collapsed"
        )

    elif question_type == "fill_blank":
        # Text input
        answer = st.text_input(
            "Your answer:",
            key=f"question_{question_index}",
            placeholder="Type your answer here..."
        )

    return answer


def render_result(question, user_answer, result, question_index):
    """Render quiz result for a single question"""
    is_correct = result.get("is_correct", False)
    correct_answer = result.get("correct_answer", "")
    explanation = result.get("explanation", "")

    # Result color
    result_color = "#10B981" if is_correct else "#EF4444"
    result_icon = "✅" if is_correct else "❌"
    result_text = "CORRECT" if is_correct else "INCORRECT"

    st.markdown(f"""
    <div style="
        background: rgba(30, 41, 59, 0.5);
        border: 2px solid {result_color};
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        backdrop-filter: blur(10px);
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
            <h3 style="color: #F8FAFC;">Question {question_index + 1}</h3>
            <span style="
                background: {result_color};
                color: white;
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            ">{result_icon} {result_text}</span>
        </div>

        <p style="color: rgba(255, 255, 255, 0.9); font-size: 16px; margin-bottom: 16px;">
            {question.get("question", "")}
        </p>

        <div style="margin: 12px 0;">
            <div style="color: rgba(255, 255, 255, 0.6); font-size: 14px;">Your answer:</div>
            <div style="color: {result_color}; font-weight: 600; margin-top: 4px;">{user_answer}</div>
        </div>

        {f'''
        <div style="margin: 12px 0;">
            <div style="color: rgba(255, 255, 255, 0.6); font-size: 14px;">Correct answer:</div>
            <div style="color: #10B981; font-weight: 600; margin-top: 4px;">{correct_answer}</div>
        </div>
        ''' if not is_correct else ''}

        {f'''
        <div style="
            background: rgba(59, 130, 246, 0.1);
            border-left: 3px solid #3B82F6;
            padding: 12px;
            margin-top: 16px;
            border-radius: 4px;
        ">
            <div style="color: #3B82F6; font-weight: 600; margin-bottom: 4px;">💡 Explanation</div>
            <div style="color: rgba(255, 255, 255, 0.9); font-size: 14px;">{explanation}</div>
        </div>
        ''' if explanation else ''}
    </div>
    """, unsafe_allow_html=True)


def show_quiz():
    """Main quiz interface"""
    # Check if user is authenticated
    if not st.session_state.get("authenticated") or not st.session_state.get("token"):
        st.warning("⚠️ Please login first")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.rerun()
        return

    # Check if a lesson is selected
    if not st.session_state.get("selected_lesson_id"):
        st.warning("⚠️ No lesson selected")
        if st.button("← Back to Lesson Library"):
            st.session_state.page = "lessons"
            st.rerun()
        return

    token = st.session_state.get("token")
    lesson_id = st.session_state.get("selected_lesson_id")

    # Initialize quiz state
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "quiz_results" not in st.session_state:
        st.session_state.quiz_results = None

    # Fetch quiz
    success, quiz_data = get_quiz(token, lesson_id)

    if not success:
        st.error(f"❌ {quiz_data}")
        if st.button("← Back to Lesson"):
            st.session_state.page = "lesson_detail"
            st.rerun()
        return

    quiz_id = quiz_data.get("quiz_id")
    lesson_title = quiz_data.get("lesson_title", "")
    questions = quiz_data.get("questions", [])
    passing_score = quiz_data.get("passing_score", 70)
    time_limit = quiz_data.get("time_limit_minutes")

    # Page header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="color: #F8FAFC; font-size: 36px; margin-bottom: 8px;">
            📝 Quiz: {lesson_title}
        </h1>
        <p style="color: rgba(255, 255, 255, 0.7); font-size: 16px;">
            {len(questions)} questions • Passing score: {passing_score}%
            {f' • Time limit: {time_limit} minutes' if time_limit else ''}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Quiz not submitted yet - show questions
    if not st.session_state.quiz_submitted:
        st.markdown("### Answer all questions below:")

        # Collect answers
        user_answers = []
        for idx, question in enumerate(questions):
            answer = render_question(question, idx)
            user_answers.append(answer)

        # Submit button
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📤 Submit Quiz", type="primary", key="submit_quiz"):
                # Check if all questions answered
                if None in user_answers or "" in user_answers:
                    st.error("❌ Please answer all questions before submitting")
                else:
                    # Submit quiz
                    success, results = submit_quiz(token, quiz_id, user_answers)

                    if success:
                        st.session_state.quiz_submitted = True
                        st.session_state.quiz_results = results
                        st.rerun()
                    else:
                        st.error(f"❌ {results}")

        with col2:
            if st.button("← Back to Lesson", key="back_to_lesson"):
                st.session_state.page = "lesson_detail"
                st.rerun()

    # Quiz submitted - show results
    else:
        results = st.session_state.quiz_results

        score = results.get("score", 0)
        passed = results.get("passed", False)
        xp_earned = results.get("xp_earned", 0)
        correct_count = results.get("correct_count", 0)
        total_questions = results.get("total_questions", len(questions))
        result_details = results.get("results", [])

        # Results header
        result_color = "#10B981" if passed else "#EF4444"
        result_text = "PASSED! 🎉" if passed else "NOT PASSED 😔"

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {result_color}20, {result_color}40);
            border: 3px solid {result_color};
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            margin-bottom: 32px;
        ">
            <h2 style="color: {result_color}; font-size: 48px; margin-bottom: 16px;">
                {result_text}
            </h2>
            <div style="color: #F8FAFC; font-size: 24px; margin-bottom: 8px;">
                Score: {score}%
            </div>
            <div style="color: rgba(255, 255, 255, 0.8); font-size: 16px;">
                {correct_count} out of {total_questions} questions correct
            </div>
            {f'''
            <div style="
                background: rgba(16, 185, 129, 0.3);
                border-radius: 8px;
                padding: 12px;
                margin-top: 16px;
                color: #10B981;
                font-size: 20px;
                font-weight: 600;
            ">
                ⭐ +{xp_earned} XP Earned!
            </div>
            ''' if xp_earned > 0 else ''}
        </div>
        """, unsafe_allow_html=True)

        # Detailed results
        st.markdown("### 📊 Detailed Results")

        for idx, (question, user_answer, result) in enumerate(zip(questions, results.get("user_answers", []), result_details)):
            render_result(question, user_answer, result, idx)

        # Action buttons
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            if not passed:
                if st.button("🔄 Retake Quiz", type="primary", key="retake_quiz"):
                    # Reset quiz state
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_results = None
                    st.rerun()

        with col2:
            if st.button("📚 Back to Lessons", key="back_to_lessons"):
                # Clear quiz state
                st.session_state.quiz_submitted = False
                st.session_state.quiz_results = None
                del st.session_state.selected_lesson_id
                st.session_state.page = "lessons"
                st.rerun()

        with col3:
            if passed:
                if st.button("➡️ Next Lesson", type="primary", key="next_lesson"):
                    # Clear quiz state and go to lessons
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_results = None
                    del st.session_state.selected_lesson_id
                    st.session_state.page = "lessons"
                    st.rerun()


if __name__ == "__main__":
    # Only used for standalone testing - actual app uses game_app.py routing
    st.set_page_config(
        page_title="Quiz",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    show_quiz()
