"""
Lesson Detail Page
Display lesson content, track progress, and navigate to quiz
"""

import streamlit as st
import requests
from pathlib import Path
import sys
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# API Configuration
API_BASE_URL = "http://localhost:8000"


def get_lesson_content(token, lesson_id):
    """Fetch lesson content from API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/lessons/{lesson_id}",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        elif response.status_code == 403:
            return False, "🔒 This lesson is locked. Complete prerequisites first."
        else:
            return False, f"Failed to load lesson: {response.status_code}"
    except Exception as e:
        return False, str(e)


def start_lesson(token, lesson_id):
    """Mark lesson as started"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE_URL}/api/lessons/{lesson_id}/start",
            headers=headers,
            timeout=5
        )

        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, None
    except Exception as e:
        return False, None


def update_progress(token, lesson_id, progress, time_spent):
    """Update reading progress"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "reading_progress": progress,
            "time_spent_seconds": time_spent
        }
        response = requests.put(
            f"{API_BASE_URL}/api/lessons/{lesson_id}/progress",
            headers=headers,
            json=data,
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, None
    except Exception as e:
        return False, None


def add_bookmark(token, lesson_id, section_index, note=""):
    """Add a bookmark to the lesson"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "section_index": section_index,
            "note": note
        }
        response = requests.post(
            f"{API_BASE_URL}/api/lessons/{lesson_id}/bookmark",
            headers=headers,
            json=data,
            timeout=5
        )

        if response.status_code in [200, 201]:
            return True, "Bookmark added!"
        else:
            return False, "Failed to add bookmark"
    except Exception as e:
        return False, str(e)


def render_lesson_section(section, section_index):
    """Render a single lesson section"""
    section_type = section.get("type", "text")
    content = section.get("content", "")

    if section_type == "text":
        st.markdown(f"""
        <div style="
            color: rgba(255, 255, 255, 0.9);
            font-size: 16px;
            line-height: 1.8;
            margin: 16px 0;
        ">
            {content}
        </div>
        """, unsafe_allow_html=True)

    elif section_type == "heading":
        level = section.get("level", 2)
        st.markdown(f"""
        <h{level} style="color: #F8FAFC; margin: 24px 0 12px 0;">
            {content}
        </h{level}>
        """, unsafe_allow_html=True)

    elif section_type == "list":
        items = section.get("items", [])
        list_html = "<ul style='color: rgba(255, 255, 255, 0.9); font-size: 16px; line-height: 1.8; margin: 16px 0; padding-left: 24px;'>"
        for item in items:
            list_html += f"<li style='margin: 8px 0;'>{item}</li>"
        list_html += "</ul>"
        st.markdown(list_html, unsafe_allow_html=True)

    elif section_type == "callout":
        callout_type = section.get("callout_type", "info")
        colors = {
            "info": ("#3B82F6", "ℹ️"),
            "warning": ("#F59E0B", "⚠️"),
            "success": ("#10B981", "✅"),
            "tip": ("#8B5CF6", "💡")
        }
        color, icon = colors.get(callout_type, ("#3B82F6", "ℹ️"))

        st.markdown(f"""
        <div style="
            background: {color}15;
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        ">
            <div style="color: {color}; font-weight: 600; margin-bottom: 8px;">
                {icon} {callout_type.upper()}
            </div>
            <div style="color: rgba(255, 255, 255, 0.9);">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif section_type == "example":
        title = section.get("title", "Example")
        st.markdown(f"""
        <div style="
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid #8B5CF6;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        ">
            <div style="color: #8B5CF6; font-weight: 600; margin-bottom: 8px;">
                📝 {title}
            </div>
            <div style="color: rgba(255, 255, 255, 0.9); font-family: monospace; font-size: 14px;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Add bookmark button for each section
    if st.button(f"🔖 Bookmark this section", key=f"bookmark_{section_index}"):
        return True
    return False


def show_lesson_detail():
    """Main lesson detail interface"""
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

    # Initialize session state for tracking
    if "lesson_start_time" not in st.session_state:
        st.session_state.lesson_start_time = time.time()
    if "lesson_started" not in st.session_state:
        st.session_state.lesson_started = False

    # Fetch lesson content
    success, lesson_data = get_lesson_content(token, lesson_id)

    if not success:
        st.error(f"❌ {lesson_data}")
        if st.button("← Back to Lesson Library"):
            st.session_state.page = "lessons"
            st.rerun()
        return

    # Start lesson if not already started
    if not st.session_state.lesson_started:
        start_lesson(token, lesson_id)
        st.session_state.lesson_started = True

    # Extract lesson data
    lesson_number = lesson_data.get("lesson_number", 0)
    module_number = lesson_data.get("module_number", 1)
    title = lesson_data.get("title", "")
    xp_reward = lesson_data.get("xp_reward", 0)
    difficulty = lesson_data.get("difficulty", "beginner")
    estimated_time = lesson_data.get("estimated_time", 15)
    content_sections = lesson_data.get("content", {}).get("sections", [])
    prerequisites = lesson_data.get("prerequisites", [])

    # Module colors
    module_colors = {
        1: "#3B82F6",
        2: "#8B5CF6",
        3: "#EC4899",
        4: "#F59E0B"
    }
    module_color = module_colors.get(module_number, "#3B82F6")

    # Page header
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 24px;">
            <div style="margin-bottom: 8px;">
                <span style="
                    background: {module_color};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                ">MODULE {module_number}</span>
                <span style="
                    background: rgba(255, 255, 255, 0.1);
                    color: white;
                    padding: 4px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-left: 8px;
                ">{difficulty.upper()}</span>
            </div>
            <h1 style="color: #F8FAFC; margin: 8px 0;">
                Lesson {lesson_number}: {title}
            </h1>
            <div style="color: rgba(255, 255, 255, 0.6); font-size: 14px;">
                ⏱️ ~{estimated_time} min  •  ⭐ {xp_reward} XP reward
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("← Back to Library", key="back_to_library"):
            st.session_state.page = "lessons"
            # Calculate time spent
            time_spent = int(time.time() - st.session_state.lesson_start_time)
            update_progress(token, lesson_id, 50, time_spent)  # Assume 50% if going back
            del st.session_state.lesson_start_time
            del st.session_state.lesson_started
            st.rerun()

    # Prerequisites section
    if prerequisites:
        st.markdown("### 📋 Prerequisites")
        prereq_text = ", ".join([f"Lesson {p}" for p in prerequisites])
        st.markdown(f"""
        <div style="
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid #3B82F6;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 24px;
            color: rgba(255, 255, 255, 0.8);
        ">
            Complete these lessons first: {prereq_text}
        </div>
        """, unsafe_allow_html=True)

    # Lesson content
    st.markdown("---")

    for idx, section in enumerate(content_sections):
        bookmark_clicked = render_lesson_section(section, idx)

        if bookmark_clicked:
            note = st.text_input(
                "Add a note (optional)",
                key=f"note_input_{idx}",
                placeholder="Why is this important?"
            )
            if st.button("Save Bookmark", key=f"save_bookmark_{idx}"):
                success, message = add_bookmark(token, lesson_id, idx, note)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # Completion section
    st.markdown("---")
    st.markdown("### 🎯 Ready to test your knowledge?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 Take the Quiz", type="primary", key="take_quiz"):
            # Mark lesson as 100% read
            time_spent = int(time.time() - st.session_state.lesson_start_time)
            update_progress(token, lesson_id, 100, time_spent)

            # Navigate to quiz
            st.session_state.page = "quiz"
            del st.session_state.lesson_start_time
            del st.session_state.lesson_started
            st.rerun()

    with col2:
        if st.button("💾 Save Progress & Exit", key="save_exit"):
            # Save partial progress
            time_spent = int(time.time() - st.session_state.lesson_start_time)
            update_progress(token, lesson_id, 75, time_spent)

            st.success("✅ Progress saved!")
            time.sleep(1)
            st.session_state.page = "lessons"
            del st.session_state.lesson_start_time
            del st.session_state.lesson_started
            st.rerun()


if __name__ == "__main__":
    # Only used for standalone testing - actual app uses game_app.py routing
    st.set_page_config(
        page_title="Lesson Detail",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    show_lesson_detail()
