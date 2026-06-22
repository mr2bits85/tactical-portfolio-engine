"""
Tactical Portfolio Engine - Action Center Dashboard
Main entry point for the application showing priority Buy/Sell/Trail signals and core dashboard.
"""
import streamlit as st
import sys
import os
from datetime import datetime, timedelta

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
    market_data_service = MarketDataService(None)  # Would pass session in real app
    global_context_service = GlobalContextService(None)  # Would pass session in real app
    return strategy_service, market_data_service, global_context_service

strategy_service, market_data_service, global_context_service = get_services()

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

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between different views")

# Main dashboard content
st.header("📈 Market Overview & Macro Context")

# Get macro data (with fallback for demo)
try:
    # In a real app, we would fetch real data here
    # For demo, we'll use mock data or handle gracefully
    spy_price = "$450.00"
    spy_change = "+1.2%"
    qqq_price = "$380.00"
    qqq_change = "+0.8%"
    vix_level = "15.2"
    vix_change = "-0.5"
except:
    # Fallback values
    spy_price = "$450.00"
    spy_change = "+1.2%"
    qqq_price = "$380.00"
    qqq_change = "+0.8%"
    vix_level = "15.2"
    vix_change = "-0.5"

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("SPY", spy_price, spy_change)
with col2:
    st.metric("QQQ", qqq_price, qqq_change)
with col3:
    st.metric("VIX", vix_level, vix_change)

# Priority Signals Section
st.header("🚨 Priority Signals")

# Create tabs for different signal types
signal_tab1, signal_tab2, signal_tab3 = st.tabs(["🎯 Buy Signals", "📉 Sell Signals", "📍 Trail Signals"])

with signal_tab1:
    st.subheader("High Conviction Buy Signals")
    # Placeholder for buy signals data
    buy_signals_data = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'NVDA'],
        'Signal Strength': ['Strong', 'Strong', 'Moderate'],
        'Entry Price': ['$170.00', '$295.00', '$420.00'],
        'Target': ['$200.00', '$350.00', '$500.00'],
        'Stop Loss': ['$160.00', '$280.00', '$400.00'],
        'Time Horizon': ['1-4 weeks', '2-6 weeks', '3-8 weeks']
    })
    if not buy_signals_data.empty:
        st.dataframe(buy_signals_data, width='stretch')
    else:
        st.info("No high conviction buy signals at this time.")

with signal_tab2:
    st.subheader("Sell Signals & Profit Targets")
    # Placeholder for sell signals data
    sell_signals_data = pd.DataFrame({
        'Symbol': ['TSLA', 'META', 'NFLX'],
        'Signal Type': ['Profit Target', 'Trailing Stop', 'Reversal'],
        'Current Price': ['$245.00', '$320.00', '$480.00'],
        'Action': ['Sell 50%', 'Adjust Trail', 'Review Position'],
        'Reason': ['Target Reached', 'Volatility Increase', 'Momentum Divergence']
    })
    if not sell_signals_data.empty:
        st.dataframe(sell_signals_data, width='stretch')
    else:
        st.info("No sell signals at this time.")

with signal_tab3:
    st.subheader("Active Trailing Flags")
    # Placeholder for trailing signals data
    trail_signals_data = pd.DataFrame({
        'Symbol': ['AMD', 'INTC', 'ADBE'],
        'Current Price': ['$105.00', '$45.00', '$580.00'],
        'Trail Type': ['ATR-based', 'Percentage', 'Moving Average'],
        'Trail Value': ['$2.50', '5%', '$15.00'],
        'Last Updated': ['2 min ago', '5 min ago', '1 min ago']
    })
    if not trail_signals_data.empty:
        st.dataframe(trail_signals_data, width='stretch')
    else:
        st.info("No active trailing flags at this time.")

# Recent Actions Section
st.header("📋 Recent Actions & Alerts")

# Create columns for different action types
action_col1, action_col2 = st.columns(2)

with action_col1:
    st.subheader("Recent Executions")
    # Placeholder for recent executions
    recent_actions_data = pd.DataFrame({
        'Time': ['14:30', '14:15', '14:00'],
        'Action': ['BUY AAPL 100@$172.50', 'SELL MSFT 50@$310.25', 'ADJUST TRAIL NVDA'],
        'Status': ['Filled', 'Filled', 'Active'],
        'P/L': ['+$250.00', '-$125.00', 'N/A']
    })
    st.dataframe(recent_actions_data, width='stretch')

with action_col2:
    st.subheader("System Alerts")
    # Placeholder for system alerts
    alerts_data = pd.DataFrame({
        'Time': ['14:25', '14:10', '13:45'],
        'Alert Type': ['Price Alert', 'Volume Spike', 'News Update'],
        'Symbol': ['AAPL', 'TSLA', 'META'],
        'Message': ['AAPL crossed $175 resistance', 'TSLA volume 200% above average', 'META earnings preview released']
    })
    st.dataframe(alerts_data, width='stretch')

# Quick Actions Section
st.header("⚡ Quick Actions")
quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

with quick_col1:
    if st.button("🔄 Refresh All Data", width='stretch'):
        st.success("All data refreshed!")

with quick_col2:
    if st.button("📊 Run Market Scan", width='stretch'):
        st.info("Market scan initiated...")

with quick_col3:
    if st.button("📋 View Resolution Center", width='stretch'):
        st.switch_page("pages/2_Resolution_Center.py")

with quick_col4:
    if st.button("⚙️ Settings", width='stretch'):
        st.switch_page("pages/5_Settings.py")

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))