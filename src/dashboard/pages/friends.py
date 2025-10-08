"""
Friends Page
Manage friend connections
"""

import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"


def get_friends(token):
    """Get user's friends list"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/api/social/friends", headers=headers, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, []
    except Exception as e:
        return False, []


def show_friends():
    """Main friends interface"""
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login first")
        return

    st.markdown('<h1 style="text-align: center;">👥 Friends</h1>', unsafe_allow_html=True)

    token = st.session_state.get("token")
    success, friends = get_friends(token)

    if not success:
        st.error("Failed to load friends")
        return

    st.markdown(f"### You have {len(friends)} friends")

    if friends:
        for friend in friends:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{friend.get('display_name')}** ({friend.get('username')})")
            with col2:
                st.write(f"Level {friend.get('current_level')} - {friend.get('total_xp'):,} XP")
            with col3:
                if st.button("Remove", key=f"remove_{friend.get('user_id')}"):
                    st.info("Remove friend feature coming soon!")
    else:
        st.info("No friends yet. Start adding friends to compete!")

    st.markdown("---")
    if st.button("← Back to Profile", use_container_width=True):
        st.session_state.page = "profile"
        st.rerun()
