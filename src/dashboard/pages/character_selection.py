"""
Character Selection Page
Allows users to choose their trading character archetype
"""

import streamlit as st
import requests
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# API Configuration
API_BASE_URL = "http://localhost:8000"


def get_characters():
    """Fetch all character types from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/characters/list", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to load characters: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server. Please start the backend server.")
        st.code("python -m uvicorn src.api.main:app --reload --port 8000")
        return []
    except Exception as e:
        st.error(f"Error loading characters: {e}")
        return []


def render_character_card(character, selected=False):
    """Render a single character card"""
    emoji = character.get("emoji", "")
    name = character.get("name", "")
    description = character.get("description", "")
    personality = character.get("personality", "")
    bonuses = character.get("starting_bonuses", [])
    color = character.get("color_scheme", "#6366F1")
    char_type = character.get("character_type", "")

    # Card styling
    border_style = f"3px solid {color}" if selected else "2px solid rgba(255, 255, 255, 0.1)"
    bg_color = f"{color}15" if selected else "rgba(30, 41, 59, 0.5)"

    card_html = f"""
    <div style="
        background: {bg_color};
        border: {border_style};
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        cursor: pointer;
        {f'box-shadow: 0 8px 32px {color}40;' if selected else ''}
    " onmouseover="this.style.transform='translateY(-4px)'; this.style.borderColor='{color}';"
       onmouseout="this.style.transform='translateY(0)'; {f'this.style.borderColor=\\'{border_style.split()[2]}\\';" if not selected else ''}">

        <div style="text-align: center; margin-bottom: 16px;">
            <div style="font-size: 64px; margin-bottom: 8px;">{emoji}</div>
            <h3 style="color: {color}; margin: 8px 0;">{name}</h3>
            <p style="color: rgba(255, 255, 255, 0.7); font-size: 14px;">{description}</p>
        </div>

        <div style="margin: 16px 0;">
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 15px; font-style: italic;">
                "{personality}"
            </p>
        </div>

        <div style="margin-top: 16px;">
            <p style="color: {color}; font-weight: 600; margin-bottom: 8px;">Starting Bonuses:</p>
            <ul style="color: rgba(255, 255, 255, 0.8); font-size: 14px; padding-left: 20px;">
    """

    for bonus in bonuses:
        card_html += f"<li style='margin: 4px 0;'>{bonus}</li>"

    card_html += """
            </ul>
        </div>

        {selected_badge}
    </div>
    """.format(
        selected_badge=f"""
        <div style="
            background: {color};
            color: white;
            text-align: center;
            padding: 8px;
            border-radius: 8px;
            margin-top: 16px;
            font-weight: 600;
        ">
            ✓ SELECTED
        </div>
        """ if selected else ""
    )

    return card_html


def show_character_selection():
    """Main character selection interface"""
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

    st.markdown('<h1 class="main-title">🎮 Choose Your Trading Character</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Your character determines your learning style, bonuses, and trading approach</p>', unsafe_allow_html=True)

    # Initialize session state
    if "selected_character" not in st.session_state:
        st.session_state.selected_character = None

    # Load characters from API
    characters = get_characters()

    if not characters:
        st.warning("No characters available. Please check the API connection.")
        return

    # Display characters in rows of 2-3
    st.markdown("---")

    cols_per_row = 3
    for i in range(0, len(characters), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(characters):
                character = characters[i + j]
                char_type = character.get("character_type", "")

                with col:
                    # Render character card
                    is_selected = st.session_state.selected_character == char_type
                    st.markdown(render_character_card(character, is_selected), unsafe_allow_html=True)

                    # Selection button
                    button_label = "✓ Selected" if is_selected else f"Select {character.get('name', '')}"
                    button_type = "secondary" if is_selected else "primary"

                    if st.button(button_label, key=f"select_{char_type}", type=button_type, use_container_width=True):
                        st.session_state.selected_character = char_type
                        st.rerun()

    # Show continue button if character selected
    if st.session_state.selected_character:
        st.markdown("---")

        selected_char = next((c for c in characters if c.get("character_type") == st.session_state.selected_character), None)

        if selected_char:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {selected_char.get('color_scheme', '#6366F1')} 0%, #764ba2 100%);
                    padding: 16px;
                    border-radius: 12px;
                    text-align: center;
                    margin: 16px 0;
                ">
                    <p style="color: white; margin: 0; font-size: 16px;">
                        You've chosen <strong>{selected_char.get('name', '')}</strong> {selected_char.get('emoji', '')}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("➡️ Continue to Registration", type="primary", use_container_width=True):
                    st.session_state.page = "register"
                    st.rerun()


def main():
    """Entry point for the character selection page"""
    st.set_page_config(
        page_title="Choose Your Character",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom dark theme CSS
    st.markdown("""
    <style>
        /* Dark theme */
        .stApp {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Better text colors */
        h1, h2, h3, p, span, div {
            color: #F8FAFC !important;
        }
    </style>
    """, unsafe_allow_html=True)

    show_character_selection()


if __name__ == "__main__":
    main()
