"""
Profile Page
Display user profile, XP, level, and character info
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


def get_user_stats(token):
    """Get user statistics from API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/users/stats",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, "Failed to load stats"
    except Exception as e:
        return False, str(e)


def show_profile():
    """Main profile interface"""
    # Check if user is authenticated
    if not st.session_state.get("authenticated") or not st.session_state.get("token"):
        st.warning("⚠️ Please login first")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.rerun()
        return

    user = st.session_state.get("user", {})
    profile = st.session_state.get("profile", {})
    token = st.session_state.get("token")

    st.markdown("""
    <style>
        .main-title {
            font-size: 42px;
            font-weight: 700;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<h1 class="main-title">👤 {profile.get("display_name", "Profile")}</h1>', unsafe_allow_html=True)

    # Get stats
    success, stats = get_user_stats(token)

    if not success:
        st.error(f"Failed to load stats: {stats}")
        stats = {}

    # Profile header
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        character_type = profile.get("character_type", "unknown")
        character_emoji_map = {
            "analyst": "📊",
            "risk_taker": "🚀",
            "conservative": "🛡️",
            "day_trader": "⚡",
            "hodler": "💎"
        }
        emoji = character_emoji_map.get(character_type, "🎮")

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 32px;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 24px;
        ">
            <div style="font-size: 80px; margin-bottom: 16px;">{emoji}</div>
            <h2 style="color: white; margin: 8px 0;">{profile.get("display_name")}</h2>
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 18px;">
                The {character_type.replace('_', ' ').title()}
            </p>
            <p style="color: rgba(255, 255, 255, 0.8); margin-top: 16px;">
                <strong>Level {stats.get('level', 1)}</strong> |
                <strong>{stats.get('total_xp', 0):,} XP</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

    # XP Progress Bar
    current_xp = stats.get('current_xp', 0)
    xp_for_next = stats.get('xp_for_next_level', 100)
    xp_progress = stats.get('xp_progress_percent', 0)

    st.markdown("### 📊 Experience Progress")
    st.progress(xp_progress / 100)
    st.markdown(f"**{current_xp} / {xp_for_next} XP** ({xp_progress:.1f}% to next level)")

    st.markdown("---")

    # Stats grid
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🏆 Level",
            value=stats.get('level', 1)
        )

    with col2:
        st.metric(
            label="⭐ Total XP",
            value=f"{stats.get('total_xp', 0):,}"
        )

    with col3:
        achievements_unlocked = stats.get('achievements_unlocked', 0)
        total_achievements = stats.get('total_achievements', 63)
        st.metric(
            label="🎯 Achievements",
            value=f"{achievements_unlocked}/{total_achievements}"
        )

    with col4:
        completion = stats.get('achievement_completion_percent', 0)
        st.metric(
            label="📈 Completion",
            value=f"{completion:.1f}%"
        )

    st.markdown("---")

    # Profile details
    st.markdown("### 📝 Profile Details")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Username:** {user.get('username', 'N/A')}")
        st.markdown(f"**Email:** {user.get('email', 'N/A')}")
        st.markdown(f"**Character:** {character_type.replace('_', ' ').title()}")

    with col2:
        st.markdown(f"**Member since:** {user.get('created_at', 'N/A')[:10]}")
        st.markdown(f"**Can change character:** {'✅ Yes' if profile.get('can_change_character') else '❌ No (Level 5+ required)'}")
        st.markdown(f"**Bio:** {profile.get('bio', 'No bio yet')}")

    # Action buttons
    st.markdown("---")

    # Phase 2: Learning section
    st.markdown("### 📚 Learning")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📖 Browse Lessons", use_container_width=True, type="primary"):
            st.session_state.page = "lessons"
            st.rerun()

    with col2:
        if st.button("📊 My Learning Progress", use_container_width=True):
            st.session_state.page = "my_learning"
            st.rerun()

    st.markdown("---")

    # Phase 1: Profile & Social section
    st.markdown("### 🎮 Profile & Social")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🏆 Achievements", use_container_width=True):
            st.session_state.page = "achievements"
            st.rerun()

    with col2:
        if st.button("🏆 Leaderboard", use_container_width=True):
            st.session_state.page = "leaderboard"
            st.rerun()

    with col3:
        if st.button("⚙️ Edit Profile", use_container_width=True):
            st.session_state.page = "edit_profile"
            st.rerun()

    with col4:
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out successfully!")
            st.session_state.page = "login"
            st.rerun()


def main():
    """Entry point for profile page"""
    st.set_page_config(
        page_title="Profile - Trading Game",
        page_icon="👤",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom dark theme CSS
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    show_profile()


if __name__ == "__main__":
    main()
