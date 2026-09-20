"""
Tactical Portfolio Engine - TQQQ Manager
Leveraged ETF strategy dashboard (placeholder for Phase 3).
"""
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import get_current_user

st.set_page_config(
    page_title="TQQQ Manager",
    page_icon="📊",
    layout="wide"
)

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

current_user = get_current_user()

with st.sidebar:
    st.title("Navigation")
    if current_user:
        st.success(f"Logged in as: {current_user}")
    else:
        st.warning("Running in development mode")
    
    st.markdown("---")
    st.page_link("app.py", label="📊 Dashboard", icon="🏠")
    st.page_link("pages/1_Portfolio.py", label="📈 Portfolio", icon="📁")
    st.page_link("pages/3_TQQQ_Manager.py", label="📊 TQQQ Manager", icon="📈")
    st.page_link("pages/4_Discovery.py", label="🔍 Discovery", icon="🔎")
    st.page_link("pages/5_Settings.py", label="⚙️ Settings", icon="⚙️")
    st.page_link("pages/_2_Resolution_Center.py", label="🔧 Resolution Center", icon="🔧")

st.title("📊 TQQQ Manager")
st.caption("Leveraged ETF Strategy Dashboard - Phase 3 MVP")

st.info("🚧 **Under Construction** - This page will be rebuilt in Phase 3 with:")
st.markdown("""
- **Indicators**: Current price, 45-day EMA, 235-day EMA, ADX (threshold 25)
- **Dashboard UI**: Clean display of 4 metrics
- **Action Logic**: Explicit Bullish/Bearish/Wait signals based on EMA crossovers + ADX > 25
""")

st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0")
