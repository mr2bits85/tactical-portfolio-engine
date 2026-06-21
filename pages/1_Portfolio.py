"""
Tactical Portfolio Engine - Portfolio Holdings Page
Shows holdings, tax-lots, and drift indicators.
"""
import streamlit as st
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from strategy_service import StrategyService
from data_processor import process_transaction_lots, process_portfolio_snapshots
from drift_engine import DriftEngine
from auth import get_current_user
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Tactical Portfolio Engine - Portfolio",
    page_icon="📈",
    layout="wide"
)

# Load custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize services
@st.cache_resource
def get_services():
    strategy_service = StrategyService()
    return strategy_service

strategy_service = get_services()

# Get current user
current_user = get_current_user()

# Page header
st.title("📊 Portfolio Holdings")
st.caption("View your holdings, tax-lots, and drift indicators")

# User info
if current_user:
    st.sidebar.success(f"Logged in as: {current_user}")
else:
    st.sidebar.warning("Running in development mode")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between different views")

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Holdings", "🧾 Tax-Lots", "📉 Drift Indicators"])

with tab1:
    st.subheader("Current Holdings")
    # Placeholder for holdings data
    st.info("Holdings data will be displayed here")

    # Sample data structure
    sample_holdings = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'Quantity': [100, 50, 25],
        'Avg Cost': [150.00, 280.00, 2200.00],
        'Current Price': [175.50, 305.25, 2450.75],
        'Market Value': [17550.00, 15262.50, 61268.75],
        'P/L': [$2550.00, $1262.50, $6268.75],
        'P/L %': [+16.7%, +8.9%, +11.4%]
    })
    st.dataframe(sample_holdings, use_container_width=True)

with tab2:
    st.subheader("Tax-Lot Details")
    # Placeholder for tax-lots data
    st.info("Tax-lot data will be displayed here")

    # Sample data structure
    sample_lots = pd.DataFrame({
        'Symbol': ['AAPL', 'AAPL', 'MSFT'],
        'Purchase Date': ['2023-01-15', '2023-03-22', '2023-02-10'],
        'Quantity': [50, 50, 50],
        'Purchase Price': [145.00, 155.00, 275.00],
        'Current Price': [175.50, 175.50, 305.25],
        'Market Value': [8775.00, 8775.00, 15262.50],
        'P/L': [$1525.00, $1025.00, $1512.50],
        'P/L %': [+10.5%, +6.6%, +5.5%],
        'Holding Period': ['Long-term', 'Long-term', 'Long-term']
    })
    st.dataframe(sample_lots, use_container_width=True)

with tab3:
    st.subheader("Drift Indicators")
    # Placeholder for drift data
    st.info("Drift indicators will be displayed here")

    # Sample data structure
    sample_drift = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'CSV Quantity': [100.000, 50.000, 25.000],
        'DB Quantity': [100.001, 49.999, 25.000],
        'Difference': [-0.001, +0.001, 0.000],
        'Status': ['✅ Within Threshold', '✅ Within Threshold', '✅ Within Threshold']
    })
    st.dataframe(sample_drift, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))