"""
XP History Page
View XP gains and progression history
"""

import streamlit as st

def show_xp_history():
    """Main XP history interface"""
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login first")
        return

    st.markdown('<h1 style="text-align: center;">📊 XP History</h1>', unsafe_allow_html=True)

    st.info("📝 XP history tracking will be available soon!")
    st.markdown("""
    This page will show:
    - Recent XP gains
    - XP sources (lessons, trades, achievements)
    - Level-up history
    - XP trends over time
    """)

    if st.button("← Back to Profile", use_container_width=True):
        st.session_state.page = "profile"
        st.rerun()
