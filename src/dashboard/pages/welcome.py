"""
Welcome/Onboarding Page
First-time user introduction
"""

import streamlit as st


def show_welcome():
    """Main welcome interface"""
    st.markdown("""
    <style>
        .welcome-title {
            font-size: 52px;
            font-weight: 700;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 16px;
        }
        .welcome-subtitle {
            text-align: center;
            font-size: 24px;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 48px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="welcome-title">🎮 Welcome to Trading Game!</h1>', unsafe_allow_html=True)
    st.markdown('<p class="welcome-subtitle">Learn to trade through gamification</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.8); padding: 32px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1);">
            <h3 style="text-align: center; margin-bottom: 24px;">🚀 Getting Started</h3>

            <div style="margin: 24px 0;">
                <h4>📊 1. Choose Your Character</h4>
                <p>Select a trading archetype that matches your style</p>
            </div>

            <div style="margin: 24px 0;">
                <h4>🎯 2. Learn & Earn XP</h4>
                <p>Complete lessons and quizzes to level up</p>
            </div>

            <div style="margin: 24px 0;">
                <h4>💼 3. Practice Trading</h4>
                <p>Use paper trading to test your strategies</p>
            </div>

            <div style="margin: 24px 0;">
                <h4>🏆 4. Unlock Achievements</h4>
                <p>Track your progress with 63 achievements</p>
            </div>

            <div style="margin: 24px 0;">
                <h4>👥 5. Compete & Connect</h4>
                <p>Join the leaderboard and add friends</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🎮 Start Your Journey", use_container_width=True, type="primary"):
            st.session_state.page = "character_selection"
            st.session_state.show_welcome = False
            st.rerun()

        if st.button("Skip Tutorial", use_container_width=True):
            st.session_state.show_welcome = False
            st.session_state.page = "login"
            st.rerun()
