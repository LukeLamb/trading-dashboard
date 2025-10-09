"""
Lesson Library Page
Browse and filter available lessons
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


def get_lessons(token, module=None, difficulty=None, search=None):
    """Fetch lessons from API with optional filters"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {}

        if module:
            params["module_number"] = module
        if difficulty:
            params["difficulty"] = difficulty
        if search:
            params["search"] = search

        response = requests.get(
            f"{API_BASE_URL}/api/lessons",
            headers=headers,
            params=params,
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Failed to load lessons: {response.status_code}"
    except Exception as e:
        return False, str(e)


def get_user_progress(token):
    """Get user's lesson progress"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/user/lessons",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, []
    except Exception as e:
        return False, []


def render_lesson_card(lesson, user_progress=None):
    """Render a single lesson card"""
    lesson_id = lesson.get("lesson_id")
    lesson_number = lesson.get("lesson_number", 0)
    module_number = lesson.get("module_number", 1)
    title = lesson.get("title", "")
    difficulty = lesson.get("difficulty", "beginner")
    xp_reward = lesson.get("xp_reward", 0)
    is_locked = lesson.get("is_locked", False)
    estimated_time = lesson.get("estimated_time", 15)

    # Find user progress for this lesson
    progress = 0
    is_completed = False
    if user_progress:
        for up in user_progress:
            if up.get("lesson_id") == lesson_id:
                progress = up.get("reading_progress", 0)
                is_completed = up.get("status") == "completed"
                break

    # Difficulty colors
    difficulty_colors = {
        "beginner": "#10B981",
        "intermediate": "#F59E0B",
        "advanced": "#EF4444"
    }
    difficulty_color = difficulty_colors.get(difficulty, "#10B981")

    # Module colors
    module_colors = {
        1: "#3B82F6",  # Blue
        2: "#8B5CF6",  # Purple
        3: "#EC4899",  # Pink
        4: "#F59E0B"   # Orange
    }
    module_color = module_colors.get(module_number, "#3B82F6")

    # Lock status
    if is_locked:
        opacity = "0.5"
        cursor = "not-allowed"
        lock_badge = f"""
        <div style="
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid #EF4444;
            color: #EF4444;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-top: 8px;
        ">
            🔒 LOCKED
        </div>
        """
    else:
        opacity = "1"
        cursor = "pointer"
        lock_badge = ""

    # Completion badge
    completion_badge = ""
    if is_completed:
        completion_badge = f"""
        <div style="
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid #10B981;
            color: #10B981;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-top: 8px;
        ">
            ✓ COMPLETED
        </div>
        """
    elif progress > 0:
        completion_badge = f"""
        <div style="
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid #3B82F6;
            color: #3B82F6;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-top: 8px;
        ">
            📖 IN PROGRESS ({progress}%)
        </div>
        """

    card_html = f"""
    <div style="
        background: rgba(30, 41, 59, 0.5);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-left: 4px solid {module_color};
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        opacity: {opacity};
        cursor: {cursor};
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    " onmouseover="if (this.style.opacity === '1') this.style.transform='translateX(4px)';"
       onmouseout="this.style.transform='translateX(0)';">

        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span style="
                        background: {module_color};
                        color: white;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 600;
                    ">MODULE {module_number}</span>

                    <span style="
                        background: {difficulty_color};
                        color: white;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 600;
                    ">{difficulty.upper()}</span>
                </div>

                <h3 style="color: #F8FAFC; margin: 8px 0; font-size: 18px;">
                    Lesson {lesson_number}: {title}
                </h3>

                <div style="display: flex; gap: 16px; margin-top: 12px; color: rgba(255, 255, 255, 0.6); font-size: 13px;">
                    <span>⏱️ ~{estimated_time} min</span>
                    <span>⭐ {xp_reward} XP</span>
                </div>

                {lock_badge}
                {completion_badge}
            </div>
        </div>
    </div>
    """

    return card_html, is_locked


def show_lessons():
    """Main lesson library interface"""
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
        <h1 style="color: #F8FAFC; font-size: 42px; margin-bottom: 8px;">📚 Lesson Library</h1>
        <p style="color: rgba(255, 255, 255, 0.7); font-size: 18px;">
            Master trading through 100 interactive lessons
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    st.markdown("### 🔍 Filters")
    col1, col2, col3 = st.columns(3)

    with col1:
        module_filter = st.selectbox(
            "Module",
            options=[None, 1, 2, 3, 4],
            format_func=lambda x: "All Modules" if x is None else f"Module {x}",
            key="module_filter"
        )

    with col2:
        difficulty_filter = st.selectbox(
            "Difficulty",
            options=[None, "beginner", "intermediate", "advanced"],
            format_func=lambda x: "All Levels" if x is None else x.title(),
            key="difficulty_filter"
        )

    with col3:
        search_query = st.text_input(
            "Search",
            placeholder="Search lessons...",
            key="search_query"
        )

    # Fetch lessons
    success, lessons_data = get_lessons(
        token,
        module=module_filter,
        difficulty=difficulty_filter,
        search=search_query if search_query else None
    )

    # Fetch user progress
    _, user_progress = get_user_progress(token)

    if not success:
        st.error(f"❌ {lessons_data}")
        return

    lessons = lessons_data.get("lessons", [])

    if not lessons:
        st.info("📭 No lessons found matching your filters")
        return

    # Group lessons by module
    modules = {}
    for lesson in lessons:
        module_num = lesson.get("module_number", 1)
        if module_num not in modules:
            modules[module_num] = []
        modules[module_num].append(lesson)

    # Module names
    module_names = {
        1: "Trading Fundamentals",
        2: "Broker Education - Bolero",
        3: "Advanced Trading Strategies",
        4: "Advanced Topics"
    }

    # Display lessons by module
    for module_num in sorted(modules.keys()):
        module_lessons = modules[module_num]
        module_name = module_names.get(module_num, f"Module {module_num}")

        # Calculate module progress
        completed_count = 0
        total_count = len(module_lessons)

        if user_progress:
            for lesson in module_lessons:
                for up in user_progress:
                    if up.get("lesson_id") == lesson.get("lesson_id") and up.get("status") == "completed":
                        completed_count += 1
                        break

        progress_percentage = int((completed_count / total_count) * 100) if total_count > 0 else 0

        # Module header
        st.markdown(f"""
        <div style="margin: 32px 0 16px 0;">
            <h2 style="color: #F8FAFC; margin-bottom: 8px;">Module {module_num}: {module_name}</h2>
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="flex: 1; background: rgba(255, 255, 255, 0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #3B82F6, #8B5CF6); height: 100%; width: {progress_percentage}%; transition: width 0.3s ease;"></div>
                </div>
                <span style="color: rgba(255, 255, 255, 0.7); font-size: 14px; min-width: 80px;">
                    {completed_count}/{total_count} Complete
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Display lesson cards
        for lesson in module_lessons:
            card_html, is_locked = render_lesson_card(lesson, user_progress)
            st.markdown(card_html, unsafe_allow_html=True)

            # Button to view lesson
            if not is_locked:
                if st.button(
                    f"📖 Start Lesson {lesson.get('lesson_number')}",
                    key=f"lesson_{lesson.get('lesson_id')}",
                    type="primary"
                ):
                    st.session_state.selected_lesson_id = lesson.get("lesson_id")
                    st.session_state.page = "lesson_detail"
                    st.rerun()
            else:
                st.button(
                    f"🔒 Lesson {lesson.get('lesson_number')} Locked",
                    key=f"lesson_{lesson.get('lesson_id')}",
                    disabled=True
                )


if __name__ == "__main__":
    # Only used for standalone testing - actual app uses game_app.py routing
    st.set_page_config(
        page_title="Lesson Library",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    show_lessons()
