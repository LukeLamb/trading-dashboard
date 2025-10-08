"""
Login Page
User authentication
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


def login_user(username_or_email, password):
    """Authenticate user via API"""
    try:
        payload = {
            "username_or_email": username_or_email,
            "password": password
        }

        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", "Login failed")
            return False, error_detail

    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to API server. Please start the backend."
    except Exception as e:
        return False, f"Login error: {str(e)}"


def show_login():
    """Main login interface"""
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
        .subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.7);
            font-size: 18px;
            margin-bottom: 32px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-title">🔐 Welcome Back!</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Login to continue your trading journey</p>', unsafe_allow_html=True)

    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            username_or_email = st.text_input(
                "Username or Email",
                placeholder="johndoe or john@example.com"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••"
            )

            submit = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")

            if submit:
                if not username_or_email or not password:
                    st.error("❌ Please enter both username/email and password")
                else:
                    with st.spinner("Logging in..."):
                        success, result = login_user(username_or_email, password)

                        if success:
                            st.success("✅ Login successful!")

                            # Store user data in session
                            st.session_state.user = result.get("user")
                            st.session_state.profile = result.get("profile")
                            st.session_state.token = result.get("token", {}).get("access_token")
                            st.session_state.authenticated = True

                            st.info("Redirecting to profile...")
                            st.session_state.page = "profile"
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")

        # Footer links
        st.markdown("---")

        if st.button("Don't have an account? Register", use_container_width=True, type="secondary"):
            st.session_state.page = "character_selection"
            st.rerun()

        if st.button("Forgot Password?", use_container_width=True):
            st.info("Password reset feature coming soon!")


def main():
    """Entry point for login page"""
    st.set_page_config(
        page_title="Login - Trading Game",
        page_icon="🔐",
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

    show_login()


if __name__ == "__main__":
    main()
