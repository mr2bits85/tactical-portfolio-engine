"""
Tactical Portfolio Engine - Action Center Dashboard
Main entry point for the application showing priority Buy/Sell/Trail signals and core dashboard.
"""
import streamlit as st
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our services
from strategy_service import StrategyService
from market_data_service import MarketDataService
from global_context_service import GlobalContextService
from macro_gating import require_fresh_macro_data
from auth import get_current_user
from secret_manager import get_secret
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Tactical Portfolio Engine - Action Center",
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

# Initialize services
@st.cache_resource
def get_services():
    # In a real app, we'd get a database session from Secret Manager or environment
    # For now, we'll just initialize the services without a session for demo purposes
    strategy_service = StrategyService()
    return strategy_service

strategy_service = get_services()

# Get current user
current_user = get_current_user()

# Header
st.title("🎯 Tactical Portfolio Engine")
st.subheader("Action Center Dashboard")

# User info
if current_user:
    st.sidebar.success(f"Logged in as: {current_user}")
else:
    st.sidebar.warning("Running in development mode")

# Main dashboard content
st.header("📈 Market Overview")

# Placeholder for macro data
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("SPY", "$450.00", "+1.2%")
with col2:
    st.metric("QQQ", "$380.00", "+0.8%")
with col3:
    st.metric("VIX", "15.2", "-0.5")

st.header("🚨 Priority Signals")
st.info("No priority signals at this time.")

st.header("📋 Recent Actions")
st.info("No recent actions.")

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))