"""
Character Selection Page
Allows users to choose their trading character archetype
"""

import streamlit as st
import requests
import sys
import base64
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Assets path
ASSETS_PATH = Path(__file__).parent.parent / "assets" / "characters"


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


def render_character_card(character, selected=False, hide_emoji=False):
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
    box_shadow = f'box-shadow: 0 8px 32px {color}40;' if selected else ''

    # Emoji display (only show if not hidden)
    emoji_html = "" if hide_emoji else f'<div style="font-size: 64px; margin-bottom: 8px;">{emoji}</div>'

    # Build bonuses HTML
    bonuses_html = ""
    for bonus in bonuses:
        bonuses_html += f"<li style='margin: 4px 0;'>{bonus}</li>"

    # Build selected badge HTML
    selected_badge = ""
    if selected:
        selected_badge = f"<div style='background: {color}; color: white; text-align: center; padding: 8px; border-radius: 8px; margin-top: 16px; font-weight: 600;'>✓ SELECTED</div>"

    card_html = (
        f"<div style='background: {bg_color}; border: {border_style}; border-radius: 16px; padding: 24px; margin: 16px 0; transition: all 0.3s ease; backdrop-filter: blur(10px); cursor: pointer; {box_shadow}'>"
        f"<div style='text-align: center; margin-bottom: 16px;'>{emoji_html}"
        f"<h3 style='color: {color}; margin: 8px 0;'>{name}</h3>"
        f"<p style='color: rgba(255, 255, 255, 0.7); font-size: 14px;'>{description}</p></div>"
        f"<div style='margin: 16px 0;'><p style='color: rgba(255, 255, 255, 0.9); font-size: 15px; font-style: italic;'>\"{personality}\"</p></div>"
        f"<div style='margin-top: 16px;'><p style='color: {color}; font-weight: 600; margin-bottom: 8px;'>Starting Bonuses:</p>"
        f"<ul style='color: rgba(255, 255, 255, 0.8); font-size: 14px; padding-left: 20px;'>{bonuses_html}</ul></div>"
        f"{selected_badge}</div>"
    )

    return card_html, char_type


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
                    # Check if character has an image
                    image_path = ASSETS_PATH / f"{char_type}.jpg"
                    has_image = image_path.exists()

                    if has_image:
                        # Display image above the card
                        st.image(str(image_path), use_container_width=True)

                    # Render character card (without emoji if image exists)
                    is_selected = st.session_state.selected_character == char_type
                    card_html, _ = render_character_card(character, is_selected, hide_emoji=has_image)
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Selection button
                    button_label = "Selected" if is_selected else f"Select {character.get('name', '')}"
                    button_type = "secondary" if is_selected else "primary"

                    if st.button(button_label, key=f"select_{char_type}", type=button_type, width="stretch"):
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

                if st.button("Continue to Registration", key="continue_to_register", type="primary", width="stretch"):
                    st.session_state.page = "register"
                    st.rerun()


if __name__ == "__main__":
    # Only used for standalone testing - actual app uses game_app.py routing
    st.set_page_config(
        page_title="Choose Your Character",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    show_character_selection()
