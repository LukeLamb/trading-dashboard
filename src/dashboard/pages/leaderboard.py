"""
Leaderboard Page
Display rankings and compete with other users
"""

import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"


def get_leaderboard(limit=50):
    """Get overall leaderboard"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/leaderboard/overall?limit={limit}", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, []
    except Exception as e:
        return False, []


def get_my_rank(token):
    """Get user's ranking"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/api/leaderboard/my-rank", headers=headers, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, {}
    except Exception as e:
        return False, {}


def show_leaderboard():
    """Main leaderboard interface"""
    st.markdown('<h1 style="text-align: center;">🏆 Leaderboard</h1>', unsafe_allow_html=True)

    # My rank (if authenticated)
    if st.session_state.get("authenticated"):
        token = st.session_state.get("token")
        success, rank_data = get_my_rank(token)

        if success:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Your Rank", f"#{rank_data.get('overall_rank', 'N/A')}")
            with col2:
                st.metric("Total XP", f"{rank_data.get('total_xp', 0):,}")
            with col3:
                st.metric("Percentile", f"{rank_data.get('overall_percentile', 0):.1f}%")
            st.markdown("---")

    # Overall leaderboard
    success, leaderboard = get_leaderboard(50)

    if not success or not leaderboard:
        st.warning("Unable to load leaderboard. Please check API connection.")
        return

    st.markdown("### 🌟 Top 50 Traders")

    # Display leaderboard as table
    for entry in leaderboard:
        rank = entry.get("rank", 0)
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else ""

        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        with col1:
            st.write(f"**#{rank}** {medal}")
        with col2:
            st.write(f"**{entry.get('display_name')}**")
        with col3:
            st.write(f"Level {entry.get('current_level')}")
        with col4:
            st.write(f"{entry.get('total_xp'):,} XP")

    if st.button("← Back to Profile", use_container_width=True):
        st.session_state.page = "profile"
        st.rerun()
