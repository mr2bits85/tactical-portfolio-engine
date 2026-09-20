"""
Tactical Portfolio Engine - Discovery
Watchlist and Entry Analysis (placeholder for Phase 4).
"""
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import get_current_user

st.set_page_config(
    page_title="Discovery",
    page_icon="🔍",
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

st.title("🔍 Discovery")
st.caption("Watchlist & Entry Analysis - Phase 4")

st.info("🚧 **Under Construction** - This page will be rebuilt in Phase 4 with:")
st.markdown("""
- **Portfolio Segmentation**: Parse uploaded portfolio into "Core" and "Momentum" buckets
- **Core View**: Price, daily performance, Quant Rating (< 7 days old), Health Score/Earnings placeholders
- **Momentum View**: Trailing stops, automated triggers from legacy logic_rules.py
- **Trigger Tracking**: Checkbox to mark "Order placed at broker"
""")

st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0")
