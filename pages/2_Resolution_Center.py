"""
Tactical Portfolio Engine - Resolution Center Page
Manual fixes for all data issues (Mapping, Drift, Adjusted Options).
"""
import streamlit as st
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from bootstrap_diagnostic import run_bootstrap_diagnostic
from auth import get_current_user
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Tactical Portfolio Engine - Resolution Center",
    page_icon="🔧",
    layout="wide"
)

# Load custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Get current user
current_user = get_current_user()

# Page header
st.title("🔧 Resolution Center")
st.caption("Manual fixes for data issues including symbol mapping, drift, and adjusted options")

# User info
if current_user:
    st.sidebar.success(f"Logged in as: {current_user}")
else:
    st.sidebar.warning("Running in development mode")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between different views")

# Main content
tab1, tab2, tab3 = st.tabs(["🔄 Symbol Mapping", "📉 Drift Issues", "⚙️ Adjusted Options"])

with tab1:
    st.subheader("Symbol Mapping Issues")
    st.info("View and fix symbols that failed to map to provider data")

    # Bootstrap diagnostic section
    st.subheader("Bootstrap Diagnostic")
    if st.button("Run Symbol Validation"):
        with st.spinner("Validating symbols against market data providers..."):
            # In a real app, we'd get symbols from the database and a database session
            # For demo, we'll use a sample list
            sample_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
            # We would normally pass a database session here
            # results = run_bootstrap_diagnostic(db_session, sample_symbols)
            st.success("Validation complete! (Demo mode)")
            st.info("In a real implementation, this would show validation results and route errors to system_notifications")

    # Sample mapping issues table
    sample_mapping_issues = pd.DataFrame({
        'Broker Symbol': ['AAPL.Z', 'MSFT.OQ', 'GOOGL.OQ'],
        'Provider Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'Broker': ['Fidelity', 'E-Trade', 'Charles Schwab'],
        'Status': ['Unmapped', 'Partially Mapped', 'Unmapped'],
        'Last Seen': ['2023-06-15', '2023-06-14', '2023-06-13']
    })
    st.dataframe(sample_mapping_issues, use_container_width=True)

    # Manual mapping form
    st.subheader("Manual Symbol Mapping")
    with st.form("manual_mapping_form"):
        broker = st.selectbox("Broker", ["Fidelity", "E-Trade", "Charles Schwab", "TD Ameritrade"])
        broker_symbol = st.text_input("Broker Symbol")
        provider_symbol = st.text_input("Provider Symbol (e.g., AAPL)")
        submit_button = st.form_submit_button("Create Mapping")
        if submit_button:
            st.success(f"Mapping created: {broker_symbol} -> {provider_symbol} for {broker}")

with tab2:
    st.subheader("Drift Issues")
    st.info("View and fix discrepancies between physical reality (CSV) and database lots")

    # Sample drift issues
    sample_drift_issues = pd.DataFrame({
        'Account': ['ACC001', 'ACC002', 'ACC003'],
        'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'CSV Quantity': [100.000, 50.000, 25.000],
        'DB Quantity': [99.950, 50.050, 24.900],
        'Difference': [+0.050, -0.050, +0.100],
        'Status': ['⚠️ Review Needed', '⚠️ Review Needed', '⚠️ Review Needed'],
        'Last CSV Update': ['2023-06-15', '2023-06-14', '2023-06-13']
    })
    st.dataframe(sample_drift_issues, use_container_width=True)

    # Drift resolution form
    st.subheader("Resolve Drift Issue")
    with st.form("drift_resolution_form"):
        selected_issue = st.selectbox("Select Issue to Resolve", ["AAPL in ACC001", "MSFT in ACC002", "GOOGL in ACC003"])
        action = st.radio("Action", ["Accept CSV as Correct", "Accept DB as Correct", "Enter Custom Values"])
        if action == "Enter Custom Values":
            custom_quantity = st.number_input("Custom Quantity", min_value=0.0, step=0.001)
        submit_button = st.form_submit_button("Resolve Issue")
        if submit_button:
            st.success(f"Drift issue resolved for {selected_issue}")

with tab3:
    st.subheader("Adjusted Options")
    st.info("View and manage adjusted options contracts (non-standard contracts)")

    # Sample adjusted options
    sample_adjusted_options = pd.DataFrame({
        'OCC Symbol': ['AAPL210618C00150000', 'TSLA210618P00800000'],
        'Shares per Contract': [100, 50],  # Non-standard: 50 instead of 100
        'Cash Deliverable': [0.00, 25.50],  # Cash in lieu of fractional shares
        'Description': ['Standard call option', 'Put option with cash settlement'],
        'Last Updated': ['2023-06-10', '2023-06-12']
    })
    st.dataframe(sample_adjusted_options, use_container_width=True)

    # Add adjusted option form
    st.subheader("Add Adjusted Option")
    with st.form("adjusted_option_form"):
        occ_symbol = st.text_input("OCC Symbol")
        shares_per_contract = st.number_input("Shares per Contract", min_value=1, value=100)
        cash_deliverable = st.number_input("Cash Deliverable ($)", min_value=0.0, value=0.0, step=0.01)
        description = st.text_input("Description")
        submit_button = st.form_submit_button("Add Adjusted Option")
        if submit_button:
            st.success(f"Adjusted option added: {occ_symbol}")

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))