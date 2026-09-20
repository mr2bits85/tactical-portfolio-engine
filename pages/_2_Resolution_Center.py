"""
Tactical Portfolio Engine - Resolution Center
Data issue monitoring (placeholder).
"""
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import get_current_user

st.set_page_config(
    page_title="Resolution Center",
    page_icon="🔧",
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

st.title("🔧 Resolution Center")
st.caption("Data Issue Monitoring - Symbol Mappings, Drift, Adjusted Options")

st.info("🚧 **Under Construction** - This page will be rebuilt to handle:")
st.markdown("""
- **Symbol Mapping Issues**: Failed broker-to-provider symbol translations
- **Lot Drift Anomalies**: CSV vs Database quantity discrepancies  
- **Adjusted Options**: Non-standard option contract management
""")

st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0")
