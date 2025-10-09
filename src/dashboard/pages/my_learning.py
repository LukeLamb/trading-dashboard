"""
My Learning Dashboard Page
View learning progress, stats, and bookmarks
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


def get_learning_stats(token):
    """Get user's learning statistics"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/user/learning-progress",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {}
    except Exception as e:
        return False, {}


def get_user_lessons(token, status=None):
    """Get user's lessons with optional status filter"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if status:
            params["status"] = status

        response = requests.get(
            f"{API_BASE_URL}/api/user/lessons",
            headers=headers,
            params=params,
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, []
    except Exception as e:
        return False, []


def get_bookmarks(token):
    """Get user's bookmarks (placeholder - endpoint may need to be created)"""
    # Note: This endpoint doesn't exist yet, but we can add it later
    return True, []


def render_stat_card(title, value, subtitle, color, icon):
    """Render a statistics card"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}20, {color}40);
        border: 2px solid {color};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-size: 36px; margin-bottom: 8px;">{icon}</div>
        <div style="color: {color}; font-size: 32px; font-weight: 700; margin-bottom: 4px;">
            {value}
        </div>
        <div style="color: #F8FAFC; font-size: 16px; font-weight: 600; margin-bottom: 4px;">
            {title}
        </div>
        <div style="color: rgba(255, 255, 255, 0.6); font-size: 12px;">
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_lesson_progress_item(lesson_data):
    """Render a lesson progress item"""
    lesson_title = lesson_data.get("lesson_title", "Unknown Lesson")
    lesson_number = lesson_data.get("lesson_number", 0)
    module_number = lesson_data.get("module_number", 1)
    status = lesson_data.get("status", "not_started")
    reading_progress = lesson_data.get("reading_progress", 0)
    quiz_score = lesson_data.get("quiz_score")
    time_spent = lesson_data.get("time_spent_seconds", 0)

    # Status colors
    status_colors = {
        "not_started": "#6B7280",
        "in_progress": "#3B82F6",
        "completed": "#10B981"
    }
    status_icons = {
        "not_started": "⚪",
        "in_progress": "🔵",
        "completed": "✅"
    }
    status_color = status_colors.get(status, "#6B7280")
    status_icon = status_icons.get(status, "⚪")

    # Convert time to readable format
    minutes = time_spent // 60
    time_text = f"{minutes} min" if minutes > 0 else "< 1 min"

    st.markdown(f"""
    <div style="
        background: rgba(30, 41, 59, 0.5);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-left: 4px solid {status_color};
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        backdrop-filter: blur(10px);
    ">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div style="flex: 1;">
                <div style="color: rgba(255, 255, 255, 0.6); font-size: 12px; margin-bottom: 4px;">
                    Module {module_number} • Lesson {lesson_number}
                </div>
                <h4 style="color: #F8FAFC; margin: 4px 0 8px 0;">
                    {lesson_title}
                </h4>
                <div style="display: flex; gap: 16px; color: rgba(255, 255, 255, 0.6); font-size: 13px;">
                    <span>⏱️ {time_text}</span>
                    <span>📖 {reading_progress}% read</span>
                    {f'<span>📝 Quiz: {quiz_score}%</span>' if quiz_score is not None else ''}
                </div>
            </div>
            <div style="text-align: right;">
                <span style="
                    background: {status_color};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                ">{status_icon} {status.replace('_', ' ').upper()}</span>
            </div>
        </div>

        {f'''
        <div style="margin-top: 12px;">
            <div style="
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                height: 6px;
                overflow: hidden;
            ">
                <div style="
                    background: {status_color};
                    height: 100%;
                    width: {reading_progress}%;
                    transition: width 0.3s ease;
                "></div>
            </div>
        </div>
        ''' if status == 'in_progress' else ''}
    </div>
    """, unsafe_allow_html=True)


def show_my_learning():
    """Main learning dashboard interface"""
    # Check if user is authenticated
    if not st.session_state.get("authenticated") or not st.session_state.get("token"):
        st.warning("⚠️ Please login first")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.rerun()
        return

    token = st.session_state.get("token")

    # Page header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="color: #F8FAFC; font-size: 42px; margin-bottom: 8px;">📊 My Learning</h1>
        <p style="color: rgba(255, 255, 255, 0.7); font-size: 18px;">
            Track your progress and achievements
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch learning stats
    success, stats = get_learning_stats(token)

    if success:
        total_lessons = stats.get("total_lessons", 100)
        completed_lessons = stats.get("completed_lessons", 0)
        in_progress_lessons = stats.get("in_progress_lessons", 0)
        total_xp_earned = stats.get("total_xp_earned", 0)
        total_time_spent = stats.get("total_time_spent_hours", 0)
        average_quiz_score = stats.get("average_quiz_score", 0)

        # Calculate completion percentage
        completion_percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

        # Statistics cards
        st.markdown("### 📈 Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            render_stat_card(
                "Lessons Completed",
                f"{completed_lessons}/{total_lessons}",
                f"{completion_percentage}% complete",
                "#10B981",
                "✅"
            )

        with col2:
            render_stat_card(
                "In Progress",
                in_progress_lessons,
                "lessons started",
                "#3B82F6",
                "📖"
            )

        with col3:
            render_stat_card(
                "Total XP Earned",
                f"{total_xp_earned:,}",
                "from lessons",
                "#F59E0B",
                "⭐"
            )

        with col4:
            render_stat_card(
                "Study Time",
                f"{total_time_spent:.1f}h",
                "total learning",
                "#8B5CF6",
                "⏱️"
            )

        # Overall progress bar
        st.markdown("### 🎯 Overall Progress")
        st.markdown(f"""
        <div style="margin: 16px 0;">
            <div style="
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                height: 24px;
                overflow: hidden;
                position: relative;
            ">
                <div style="
                    background: linear-gradient(90deg, #3B82F6, #8B5CF6, #EC4899);
                    height: 100%;
                    width: {completion_percentage}%;
                    transition: width 0.5s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <span style="
                        color: white;
                        font-size: 12px;
                        font-weight: 600;
                        position: absolute;
                        left: 50%;
                        transform: translateX(-50%);
                    ">{completion_percentage}% Complete</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Average quiz score
        if average_quiz_score > 0:
            score_color = "#10B981" if average_quiz_score >= 80 else "#F59E0B" if average_quiz_score >= 70 else "#EF4444"
            st.markdown(f"""
            <div style="
                background: {score_color}20;
                border: 2px solid {score_color};
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                margin: 16px 0;
            ">
                <span style="color: {score_color}; font-size: 18px; font-weight: 600;">
                    Average Quiz Score: {average_quiz_score:.1f}%
                </span>
            </div>
            """, unsafe_allow_html=True)

    # Lesson progress tabs
    st.markdown("---")
    st.markdown("### 📚 My Lessons")

    tab1, tab2, tab3 = st.tabs(["In Progress", "Completed", "All Lessons"])

    with tab1:
        success, in_progress = get_user_lessons(token, status="in_progress")
        if success and in_progress:
            for lesson in in_progress:
                render_lesson_progress_item(lesson)
                if st.button(f"Continue Learning", key=f"continue_{lesson.get('lesson_id')}"):
                    st.session_state.selected_lesson_id = lesson.get("lesson_id")
                    st.session_state.page = "lesson_detail"
                    st.rerun()
        else:
            st.info("📭 No lessons in progress. Start learning from the lesson library!")
            if st.button("Browse Lessons", key="browse_from_in_progress"):
                st.session_state.page = "lessons"
                st.rerun()

    with tab2:
        success, completed = get_user_lessons(token, status="completed")
        if success and completed:
            for lesson in completed:
                render_lesson_progress_item(lesson)
                if st.button(f"Review Lesson", key=f"review_{lesson.get('lesson_id')}"):
                    st.session_state.selected_lesson_id = lesson.get("lesson_id")
                    st.session_state.page = "lesson_detail"
                    st.rerun()
        else:
            st.info("📭 No completed lessons yet. Start your learning journey!")
            if st.button("Browse Lessons", key="browse_from_completed"):
                st.session_state.page = "lessons"
                st.rerun()

    with tab3:
        success, all_lessons = get_user_lessons(token)
        if success and all_lessons:
            for lesson in all_lessons:
                render_lesson_progress_item(lesson)
                button_label = "Continue" if lesson.get("status") == "in_progress" else "Review" if lesson.get("status") == "completed" else "Start"
                if st.button(f"{button_label} Lesson", key=f"view_{lesson.get('lesson_id')}"):
                    st.session_state.selected_lesson_id = lesson.get("lesson_id")
                    st.session_state.page = "lesson_detail"
                    st.rerun()
        else:
            st.info("📭 Start learning to see your progress here!")
            if st.button("Browse Lessons", key="browse_from_all"):
                st.session_state.page = "lessons"
                st.rerun()

    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📚 Browse All Lessons", type="primary", key="browse_all_lessons"):
            st.session_state.page = "lessons"
            st.rerun()

    with col2:
        if st.button("🏆 View Achievements", type="secondary", key="view_achievements"):
            st.session_state.page = "achievements"
            st.rerun()


if __name__ == "__main__":
    # Only used for standalone testing - actual app uses game_app.py routing
    st.set_page_config(
        page_title="My Learning",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    show_my_learning()
