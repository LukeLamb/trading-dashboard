"""
Achievements Page
Display all achievements and user progress
"""

import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"


def get_user_achievements(token):
    """Get user's achievements from API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/api/achievements/user", headers=headers, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, "Failed to load achievements"
    except Exception as e:
        return False, str(e)


def show_achievements():
    """Main achievements interface"""
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login first")
        return

    st.markdown('<h1 style="text-align: center;">🏆 Achievements</h1>', unsafe_allow_html=True)

    token = st.session_state.get("token")
    success, data = get_user_achievements(token)

    if not success:
        st.error(f"Failed to load achievements: {data}")
        return

    completed = data.get("completed", [])
    in_progress = data.get("in_progress", [])
    total = data.get("total_achievements", 63)
    completion_pct = data.get("completion_percentage", 0)

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Completed", f"{len(completed)}/{total}")
    with col2:
        st.metric("In Progress", len(in_progress))
    with col3:
        st.metric("Completion", f"{completion_pct:.1f}%")

    st.progress(completion_pct / 100)
    st.markdown("---")

    # Completed achievements
    st.markdown("### ✅ Completed Achievements")
    if completed:
        cols = st.columns(3)
        for i, ach in enumerate(completed):
            with cols[i % 3]:
                rarity_colors = {"common": "#10B981", "rare": "#3B82F6", "epic": "#8B5CF6", "legendary": "#F59E0B"}
                color = rarity_colors.get(ach.get("rarity", "common"), "#10B981")

                st.markdown(f"""
                <div style="background: {color}20; border: 2px solid {color}; border-radius: 12px; padding: 16px; margin: 8px 0;">
                    <h4 style="color: {color}; margin: 0;">{ach.get('name')}</h4>
                    <p style="font-size: 12px; color: rgba(255,255,255,0.7);">{ach.get('description')}</p>
                    <p style="margin: 0;"><strong>+{ach.get('xp_reward')} XP</strong> | {ach.get('rarity').title()}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No completed achievements yet. Start learning to unlock them!")

    st.markdown("---")

    # In progress
    if in_progress:
        st.markdown("### 🔄 In Progress")
        for ach in in_progress:
            st.write(f"**{ach.get('name')}** - {ach.get('progress')}% complete")

    if st.button("← Back to Profile", use_container_width=True):
        st.session_state.page = "profile"
        st.rerun()
