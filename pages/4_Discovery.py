"""
Tactical Portfolio Engine - Discovery Page
Watchlist and Entry Analysis.
"""
import streamlit as st
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from strategy_service import StrategyService
from market_data_service import MarketDataService
from auth import get_current_user
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Tactical Portfolio Engine - Discovery",
    page_icon="🔍",
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
    market_data_service = MarketDataService(None)  # In real app, pass db session
    return strategy_service, market_data_service

strategy_service, market_data_service = get_services()

# Get current user
current_user = get_current_user()

# Initialize watchlist in session state if it doesn't exist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Page header
st.title("🔍 Discovery")
st.caption("Watchlist and Entry Analysis")

# User info
if current_user:
    st.sidebar.success(f"Logged in as: {current_user}")
else:
    st.sidebar.warning("Running in development mode")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between different views")

# Main content
tab1, tab2 = st.tabs(["👀 Watchlist", "🎯 Entry Analysis"])

with tab1:
    st.subheader("My Watchlist")

    # Watchlist management
    with st.expander("➕ Add to Watchlist", expanded=False):
        with st.form("add_to_watchlist"):
            symbol = st.text_input("Symbol (e.g., AAPL)").upper()
            notes = st.text_area("Notes (optional)")
            submit_button = st.form_submit_button("Add to Watchlist")
            if submit_button and symbol:
                # Check if symbol already exists in watchlist
                existing_symbols = [item['Symbol'] for item in st.session_state.watchlist]
                if symbol not in existing_symbols:
                    # Add to watchlist with current date and price (placeholder)
                    from datetime import datetime
                    new_item = {
                        'Symbol': symbol,
                        'Added Date': datetime.now().strftime('%Y-%m-%d'),
                        'Notes': notes if notes else '',
                        'Price': 0.0,  # Placeholder - would be fetched from market data in real app
                        'Change': '0.0%'  # Placeholder
                    }
                    st.session_state.watchlist.append(new_item)
                    st.success(f"Added {symbol} to watchlist!")
                    if notes:
                        st.info(f"Notes: {notes}")
                else:
                    st.warning(f"{symbol} is already in your watchlist!")

    # Watchlist display - use session state watchlist
    if st.session_state.watchlist:
        # Convert session state watchlist to DataFrame for display
        watchlist_data = []
        for item in st.session_state.watchlist:
            watchlist_data.append({
                'Symbol': item['Symbol'],
                'Added Date': item['Added Date'],
                'Notes': item['Notes'] if item['Notes'] else '-',
                'Price': f"${item['Price']:.2f}" if item['Price'] > 0 else '-',
                'Change': item['Change']
            })

        sample_watchlist = pd.DataFrame(watchlist_data)

        st.dataframe(sample_watchlist, width='stretch')

        # Watchlist actions
        st.subheader("Watchlist Actions")
        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if st.button("🔄 Refresh Prices", width='stretch'):
                st.success("Watchlist prices refreshed!")
                # In a real app, we would update prices from market data here
        with action_col2:
            if st.button("📊 Analyze Watchlist", width='stretch'):
                if st.session_state.watchlist:
                    symbols = [item['Symbol'] for item in st.session_state.watchlist]
                    st.info(f"Running analysis on watchlist symbols: {', '.join(symbols)}")
                else:
                    st.info("Your watchlist is empty. Add symbols to analyze.")
        with action_col3:
            if st.button("🗑️ Clear Watchlist", width='stretch'):
                st.session_state.watchlist = []  # Clear the session state watchlist
                st.success("Watchlist cleared!")
                st.rerun()  # Rerun to update the display immediately
    else:
        st.info("Your watchlist is empty. Add symbols to get started.")

with tab2:
    st.subheader("Entry Analysis")

    # Symbol search
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        symbol_to_analyze = st.text_input("Enter Symbol to Analyze (e.g., AAPL)", placeholder="AAPL").upper()
    with search_col2:
        analyze_button = st.button("Analyze", type="primary", width='stretch')

    if analyze_button and symbol_to_analyze:
        with st.spinner(f"Analyzing {symbol_to_analyze}..."):
            # In a real app, we'd fetch data and run analysis
            st.success(f"Analysis complete for {symbol_to_analyze}!")

            # Analysis results
            analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["📊 Technical", "📈 Fundamental", "💡 Strategy"])

            with analysis_tab1:
                st.write("### Technical Analysis")
                # Sample technical indicators
                tech_data = pd.DataFrame({
                    'Indicator': ['RSI (14)', 'MACD', 'SMA (50)', 'SMA (200)', 'Volume'],
                    'Value': [65.2, 'Bullish Cross', 165.20, 155.80, 'Above Avg'],
                    'Signal': ['Neutral', 'Bullish', 'Bullish', 'Bullish', 'Strong']
                })

                # Force Value column to string to prevent PyArrow crash
                tech_data['Value'] = tech_data['Value'].astype(str)

                st.dataframe(tech_data, width='stretch')

            with analysis_tab2:
                st.write("### Fundamental Analysis")
                # Sample fundamental data
                fund_data = pd.DataFrame({
                    'Metric': ['P/E Ratio', 'Forward P/E', 'PEG Ratio', 'Dividend Yield', 'Market Cap'],
                    'Value': ['28.5', '24.3', '1.8', '0.5%', '$2.8T'],
                    'Assessment': ['Fairly Valued', 'Reasonable', 'Acceptable', 'Low', 'Large Cap']
                })

                # Force Value column to string to prevent PyArrow crash
                fund_data['Value'] = fund_data['Value'].astype(str)

                st.dataframe(fund_data, width='stretch')

            with analysis_tab3:
                st.write("### Strategy Analysis")
                # Sample strategy recommendation
                st.info("**Recommended Strategy**: Growth")
                st.write("**Buy Point**: $168.50 (Pullback to 50-Day SMA)")
                st.write("**Stop Loss**: $155.00 (8% below buy point)")
                st.write("**Target**: $210.00 (+25% from buy point)")

                # Strategy actions
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    if st.button("📝 Add to Watchlist", width='stretch'):
                        # Check if symbol already exists in watchlist
                        existing_symbols = [item['Symbol'] for item in st.session_state.watchlist]
                        if symbol_to_analyze not in existing_symbols:
                            # Add to watchlist with current date and placeholder price
                            from datetime import datetime
                            new_item = {
                                'Symbol': symbol_to_analyze,
                                'Added Date': datetime.now().strftime('%Y-%m-%d'),
                                'Notes': f"Added from analysis on {datetime.now().strftime('%Y-%m-%d')}",
                                'Price': 0.0,  # Placeholder - would be fetched from market data in real app
                                'Change': 'N/A'
                            }
                            st.session_state.watchlist.append(new_item)
                            st.success(f"{symbol_to_analyze} added to watchlist!")
                            st.rerun()  # Rerun to update the watchlist display immediately
                        else:
                            st.info(f"{symbol_to_analyze} is already in your watchlist!")
                with action_col2:
                    if st.button("📋 Create Alert", width='stretch'):
                        st.success(f"Price alert created for {symbol_to_analyze}!")

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))