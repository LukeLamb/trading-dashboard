"""
Edit Profile Page
Allow users to update their profile information
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

# Avatar library (10 avatars)
AVATARS = [
    "/avatars/default_1.png",
    "/avatars/default_2.png",
    "/avatars/default_3.png",
    "/avatars/default_4.png",
    "/avatars/default_5.png",
    "/avatars/analyst.png",
    "/avatars/risk_taker.png",
    "/avatars/conservative.png",
    "/avatars/day_trader.png",
    "/avatars/hodler.png",
]

# Emoji avatars as fallback
EMOJI_AVATARS = ["📊", "🚀", "🛡️", "⚡", "💎", "👤", "🎮", "💼", "📈", "🎯"]


def update_profile(token, display_name=None, bio=None, avatar_url=None):
    """Update user profile via API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {}

        if display_name:
            payload["display_name"] = display_name
        if bio is not None:
            payload["bio"] = bio
        if avatar_url:
            payload["avatar_url"] = avatar_url

        response = requests.put(
            f"{API_BASE_URL}/api/users/profile",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", "Update failed")
            return False, error_detail

    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to API server"
    except Exception as e:
        return False, f"Update error: {str(e)}"


def show_edit_profile():
    """Main edit profile interface"""
    # Check authentication
    if not st.session_state.get("authenticated") or not st.session_state.get("token"):
        st.warning("⚠️ Please login first")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.rerun()
        return

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

    st.markdown('<h1 class="main-title">⚙️ Edit Profile</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Edit form
    with st.form("edit_profile_form"):
        st.markdown("### 📝 Profile Information")

        display_name = st.text_input(
            "Display Name",
            value=profile.get("display_name", ""),
            help="This is how other users will see you (3-100 characters)"
        )

        bio = st.text_area(
            "Bio",
            value=profile.get("bio", ""),
            max_chars=280,
            help="Tell us about yourself (max 280 characters)"
        )

        st.markdown("### 🎨 Choose Avatar")

        # Avatar selection using emoji avatars
        cols = st.columns(5)
        selected_avatar_idx = 0
        current_avatar = profile.get("avatar_url", AVATARS[0])

        for i, emoji in enumerate(EMOJI_AVATARS):
            with cols[i % 5]:
                is_selected = AVATARS[i] == current_avatar
                button_type = "primary" if is_selected else "secondary"

                if st.form_submit_button(
                    f"{emoji}",
                    key=f"avatar_{i}",
                    help=f"Avatar {i+1}",
                    use_container_width=True
                ):
                    selected_avatar_idx = i

        avatar_url = AVATARS[selected_avatar_idx] if 'selected_avatar_idx' in locals() else current_avatar

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")

        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if cancel:
            st.session_state.page = "profile"
            st.rerun()

        if submit:
            # Validation
            if not display_name or len(display_name) < 3:
                st.error("❌ Display name must be at least 3 characters")
            elif len(display_name) > 100:
                st.error("❌ Display name must be less than 100 characters")
            else:
                # Update profile
                with st.spinner("Updating profile..."):
                    success, result = update_profile(
                        token=token,
                        display_name=display_name if display_name != profile.get("display_name") else None,
                        bio=bio if bio != profile.get("bio") else None,
                        avatar_url=avatar_url if avatar_url != current_avatar else None
                    )

                    if success:
                        st.success("✅ Profile updated successfully!")

                        # Update session state
                        st.session_state.profile = result

                        st.info("Redirecting to profile...")
                        st.session_state.page = "profile"
                        st.rerun()
                    else:
                        st.error(f"❌ Update failed: {result}")

    # Back button
    st.markdown("---")
    if st.button("← Back to Profile", use_container_width=True):
        st.session_state.page = "profile"
        st.rerun()


def main():
    """Entry point for edit profile page"""
    st.set_page_config(
        page_title="Edit Profile - Trading Game",
        page_icon="⚙️",
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

    show_edit_profile()


if __name__ == "__main__":
    main()
