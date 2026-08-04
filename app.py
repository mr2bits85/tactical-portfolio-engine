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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from database import SessionLocal

try:
    from dotenv import load_dotenv
    _dotenv_available = True
except ImportError:
    _dotenv_available = False

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
    try:
        # Get a database session from our new database.py file
        db_session = SessionLocal()

        # Initialize services with database session
        strategy_service = StrategyService()
        market_data_service = MarketDataService(db_session)
        global_context_service = GlobalContextService(db_session)

        return strategy_service, market_data_service, global_context_service
    except Exception as e:
        st.error(f"❌ Failed to initialize services or connect to database: {e}")
        st.stop()

strategy_service, market_data_service, global_context_service = get_services()

# Auto-refresh market data every 5 minutes (300 seconds)
@st.cache_data(ttl=300)
def refresh_market_data():
    """Automatically refresh market data every 5 minutes."""
    return global_context_service.update_anchor_metrics()

# Initial data load on app startup
initial_refresh = refresh_market_data()

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
    # Get SPY data
    spy_price_raw = global_context_service.get_latest_indicator("SPY", "price")
    spy_price = f"${spy_price_raw:.2f}" if spy_price_raw is not None else "$0.00"
    spy_change_raw = global_context_service.get_latest_indicator("SPY", "price_change")
    # Convert to float for delta; if None, set to 0.0 (no change)
    spy_change = float(spy_change_raw) if spy_change_raw is not None else 0.0

    # Get QQQ data
    qqq_price_raw = global_context_service.get_latest_indicator("QQQ", "price")
    qqq_price = f"${qqq_price_raw:.2f}" if qqq_price_raw is not None else "$0.00"
    qqq_change_raw = global_context_service.get_latest_indicator("QQQ", "price_change")
    qqq_change = float(qqq_change_raw) if qqq_change_raw is not None else 0.0

    # Get VIX data
    vix_price_raw = global_context_service.get_latest_indicator("VIX", "price")
    vix_level = f"{vix_price_raw:.2f}" if vix_price_raw is not None else "0.00"
    vix_change_raw = global_context_service.get_latest_indicator("VIX", "price_change")
    vix_change = float(vix_change_raw) if vix_change_raw is not None else 0.0
except Exception as e:
	    # Fallback values if data not available
	    spy_price = "$0.00"
	    qqq_price = "$0.00"
	    vix_level = "0.00"
	    st.warning(f"Unable to fetch live market data: {e}")

					
col1, col2, col3 = st.columns(3)
with col1:
    spy_delta = f"{spy_change:+.2f}%"
    st.metric("SPY", spy_price, spy_delta)
with col2:
    qqq_delta = f"{qqq_change:+.2f}%"
    st.metric("QQQ", qqq_price, qqq_delta)
with col3:
    vix_delta = f"{vix_change:+.2f}%"
    st.metric("VIX", vix_level, vix_delta, delta_color="inverse")

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
        with st.spinner("Refreshing market data..."):
            refresh_market_data.clear()  # Force clear the cache to ensure execution
            result = refresh_market_data()
            # Check if any errors occurred during update
            errors = [k for k, v in result.items() if isinstance(v, dict) and "error" in v]
            if errors:
                st.error(f"Failed to refresh data for: {', '.join(errors)}")
            else:
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