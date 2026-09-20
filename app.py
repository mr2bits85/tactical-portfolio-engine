"""
Tactical Portfolio Engine - Action Center Dashboard
Main entry point for the application.
"""
import streamlit as st
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import get_current_user

# Page configuration
st.set_page_config(
    page_title="Tactical Portfolio Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Get current user
current_user = get_current_user()

# Header
st.title("🎯 Tactical Portfolio Engine")
st.subheader("Signal vs Noise Dashboard")

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    if current_user:
        email = current_user.get('email', 'Unknown') if isinstance(current_user, dict) else str(current_user)
        st.success(f"Logged in as: {email}")
        if isinstance(current_user, dict) and current_user.get('role') == 'admin':
            st.success("🔑 Admin")
    else:
        st.warning("Running in development mode")
    
    st.markdown("---")
    st.page_link("app.py", label="📊 Dashboard", icon="🏠")
    st.page_link("pages/1_Portfolio.py", label="📈 Portfolio", icon="📁")
    st.page_link("pages/3_TQQQ_Manager.py", label="📊 TQQQ Manager", icon="📈")
    st.page_link("pages/4_Discovery.py", label="🔍 Discovery", icon="🔎")
    st.page_link("pages/5_Settings.py", label="⚙️ Settings", icon="⚙️")
    st.page_link("pages/_2_Resolution_Center.py", label="🔧 Resolution Center", icon="🔧")

# Main dashboard content - minimal placeholder
st.header("Welcome to the Signal vs Noise Dashboard")
st.info("This is the clean slate. Phase 1 complete. Ready for Phase 2 implementation.")

st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0")
