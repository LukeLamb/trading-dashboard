"""
Registration Page
User registration with character selection
"""

import streamlit as st
import requests
import re
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# API Configuration
API_BASE_URL = "http://localhost:8000"


def validate_username(username):
    """Validate username format"""
    if not username:
        return False, "Username is required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, hyphens, and underscores"
    return True, ""


def validate_email(email):
    """Validate email format"""
    if not email:
        return False, "Email is required"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""


def validate_password(password):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Password must contain at least one special character"
    return True, ""


def validate_display_name(display_name):
    """Validate display name"""
    if not display_name:
        return False, "Display name is required"
    if len(display_name) < 3:
        return False, "Display name must be at least 3 characters"
    if len(display_name) > 100:
        return False, "Display name must be less than 100 characters"
    return True, ""


def register_user(username, email, password, display_name, character_type, bio=""):
    """Register a new user via API"""
    try:
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "display_name": display_name,
            "character_type": character_type,
            "bio": bio or f"New {character_type.replace('_', ' ').title()} trader!"
        }

        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json=payload,
            timeout=10
        )

        if response.status_code == 201:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", "Registration failed")
            return False, error_detail

    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to API server. Please start the backend."
    except Exception as e:
        return False, f"Registration error: {str(e)}"


def show_registration():
    """Main registration interface"""
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

    st.markdown('<h1 class="main-title">📝 Create Your Profile</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Join the trading community and start your learning journey</p>', unsafe_allow_html=True)

    # Get selected character from session state
    if "selected_character" not in st.session_state or not st.session_state.selected_character:
        st.warning("⚠️ Please select a character first")
        if st.button("← Back to Character Selection"):
            st.session_state.page = "character_selection"
            st.rerun()
        return

    character_type = st.session_state.selected_character

    # Show selected character
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 16px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 32px;
    ">
        <p style="color: white; margin: 0; font-size: 16px;">
            Selected Character: <strong>{character_type.replace('_', ' ').title()}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # DEV MODE: Quick bypass button
    with st.expander("🔧 Developer Mode", expanded=False):
        st.warning("⚠️ Development Only - Remove before production!")
        if st.button("⚡ Skip Registration (Dev Mode)", type="secondary", width="stretch"):
            # Register a real test user via API
            import random
            rand_id = random.randint(1000, 9999)
            test_data = {
                "username": f"dev_user_{rand_id}",
                "email": f"dev{rand_id}@test.com",
                "password": "TestPass123!",
                "display_name": f"Dev User {rand_id}",
                "character_type": character_type,
                "bio": f"Test {character_type} user"
            }

            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/auth/register",
                    json=test_data,
                    timeout=5
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    st.session_state.user = data.get("user", {})
                    st.session_state.profile = data.get("profile", {})
                    st.session_state.token = data.get("token", {}).get("access_token")
                    st.session_state.authenticated = True
                    st.success(f"✅ Dev mode: Created {test_data['username']}!")
                    st.session_state.page = "profile"
                    st.rerun()
                else:
                    st.error(f"❌ Dev mode failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Dev mode error: {str(e)}")

    # Registration form
    with st.form("registration_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "Username *",
                placeholder="johndoe",
                help="3-50 characters, letters/numbers/hyphens/underscores only"
            )

            email = st.text_input(
                "Email *",
                placeholder="john@example.com",
                help="Valid email address"
            )

        with col2:
            password = st.text_input(
                "Password *",
                type="password",
                placeholder="••••••••",
                help="Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special character"
            )

            confirm_password = st.text_input(
                "Confirm Password *",
                type="password",
                placeholder="••••••••"
            )

        display_name = st.text_input(
            "Display Name *",
            placeholder="John Doe",
            help="This is how other users will see you (3-100 characters)"
        )

        bio = st.text_area(
            "Bio (Optional)",
            placeholder="Tell us about yourself...",
            max_chars=280,
            help="Optional bio (max 280 characters)"
        )

        terms = st.checkbox("I agree to the Terms of Service and Privacy Policy *")

        submit = st.form_submit_button("🚀 Create My Account", use_container_width=True, type="primary")

        if submit:
            # Validation
            errors = []

            # Username validation
            is_valid, error = validate_username(username)
            if not is_valid:
                errors.append(f"Username: {error}")

            # Email validation
            is_valid, error = validate_email(email)
            if not is_valid:
                errors.append(f"Email: {error}")

            # Password validation
            is_valid, error = validate_password(password)
            if not is_valid:
                errors.append(f"Password: {error}")

            # Password match
            if password != confirm_password:
                errors.append("Passwords do not match")

            # Display name validation
            is_valid, error = validate_display_name(display_name)
            if not is_valid:
                errors.append(f"Display Name: {error}")

            # Terms checkbox
            if not terms:
                errors.append("You must agree to the Terms of Service")

            # Show errors if any
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Attempt registration
                with st.spinner("Creating your account..."):
                    success, result = register_user(
                        username=username,
                        email=email,
                        password=password,
                        display_name=display_name,
                        character_type=character_type,
                        bio=bio
                    )

                    if success:
                        st.success("✅ Account created successfully!")
                        st.balloons()

                        # Store user data in session
                        st.session_state.user = result.get("user")
                        st.session_state.profile = result.get("profile")
                        st.session_state.token = result.get("token", {}).get("access_token")

                        st.info("Redirecting to dashboard...")
                        st.session_state.page = "profile"
                        st.rerun()
                    else:
                        st.error(f"❌ Registration failed: {result}")

    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← Back to Character Selection", use_container_width=True):
            st.session_state.page = "character_selection"
            st.rerun()

        if st.button("Already have an account? Login", use_container_width=True, type="secondary"):
            st.session_state.page = "login"
            st.rerun()


def main():
    """Entry point for registration page"""
    st.set_page_config(
        page_title="Register - Trading Game",
        page_icon="📝",
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

    show_registration()


if __name__ == "__main__":
    main()
