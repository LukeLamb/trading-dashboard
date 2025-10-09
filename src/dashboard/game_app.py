"""
Trading Game Main Application
Entry point for the gamified trading education platform
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import pages
from src.dashboard.pages import (
    character_selection,
    register,
    login,
    profile,
    edit_profile
)

# Import additional Phase 1 pages (will be created)
try:
    from src.dashboard.pages import achievements, friends, leaderboard, xp_history
except ImportError:
    achievements = friends = leaderboard = xp_history = None

# Import Phase 2 lesson pages
try:
    from src.dashboard.pages import lessons, lesson_detail, quiz, my_learning
except ImportError:
    lessons = lesson_detail = quiz = my_learning = None


def main():
    """Main application entry point with page routing"""

    # Initialize session state
    if "page" not in st.session_state:
        # Check if user is already authenticated
        if "authenticated" in st.session_state and st.session_state.authenticated:
            st.session_state.page = "profile"
        else:
            st.session_state.page = "character_selection"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Page routing
    current_page = st.session_state.page

    if current_page == "character_selection":
        character_selection.show_character_selection()

    elif current_page == "register":
        register.show_registration()

    elif current_page == "login":
        login.show_login()

    elif current_page == "profile":
        profile.show_profile()

    elif current_page == "edit_profile":
        edit_profile.show_edit_profile()

    elif current_page == "achievements" and achievements:
        achievements.show_achievements()

    elif current_page == "friends" and friends:
        friends.show_friends()

    elif current_page == "leaderboard" and leaderboard:
        leaderboard.show_leaderboard()

    elif current_page == "xp_history" and xp_history:
        xp_history.show_xp_history()

    # Phase 2: Educational Content Pages
    elif current_page == "lessons" and lessons:
        lessons.show_lessons()

    elif current_page == "lesson_detail" and lesson_detail:
        lesson_detail.show_lesson_detail()

    elif current_page == "quiz" and quiz:
        quiz.show_quiz()

    elif current_page == "my_learning" and my_learning:
        my_learning.show_my_learning()

    else:
        st.error(f"Unknown page: {current_page}")
        if st.button("Go to Home"):
            st.session_state.page = "character_selection"
            st.rerun()


if __name__ == "__main__":
    # Configure page
    st.set_page_config(
        page_title="Trading Game - Learn to Trade",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Global dark theme CSS
    st.markdown("""
    <style>
        /* Dark theme */
        .stApp {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Better text colors for dark theme */
        h1, h2, h3, h4, h5, h6, p, span, div, label {
            color: #F8FAFC !important;
        }

        /* Input fields styling */
        .stTextInput input, .stTextArea textarea {
            background-color: rgba(30, 41, 59, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: #F8FAFC !important;
        }

        /* Buttons */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
        }

        /* Form styling */
        .stForm {
            background: rgba(30, 41, 59, 0.5);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Metrics */
        .stMetric {
            background: rgba(30, 41, 59, 0.5);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Progress bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
    </style>
    """, unsafe_allow_html=True)

    main()
