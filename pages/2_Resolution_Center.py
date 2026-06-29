"""
Tactical Portfolio Engine - Resolution Center Page
Interactive dashboard for monitoring and resolving data issues including
failed symbol mappings, lot drift anomalies, and adjusted options.
"""
import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from bootstrap_diagnostic import run_bootstrap_diagnostic, BootstrapDiagnostic
from auth import get_current_user

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
st.caption("Active inbox for monitoring and resolving data issues: failed symbol mappings, lot drift anomalies, and adjusted options")

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
    st.subheader("🔄 Symbol Mapping Issues")
    st.info("View and fix symbols that failed to map to provider data")

    # Inbox-style header with metrics
    inbox_col1, inbox_col2, inbox_col3 = st.columns([2, 1, 1])
    with inbox_col1:
        st.subheader("Active Mapping Issues")
    with inbox_col2:
        st.metric("Total Issues", "3", "2 new")
    with inbox_col3:
        if st.button("🔄 Refresh Diagnostics", width='stretch'):
            with st.spinner("Running symbol validation..."):
                # In a real app, we'd get symbols from the database and a database session
                # For demo, we'll use a sample list
                sample_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META']
                # We would normally pass a database session here
                # results = run_bootstrap_diagnostic(db_session, sample_symbols)
                st.success("Validation complete! (Demo mode)")
                st.info("In a real implementation, this would show validation results and route errors to system_notifications")

    # Bootstrap diagnostic section
    with st.expander("🔍 Run Bootstrap Diagnostic", expanded=False):
        st.write("Run validation checks against market data providers and route lookup errors to system_notifications")
        if st.button("Run Full Validation", width='stretch'):
            with st.spinner("Validating symbols against market data providers..."):
                # In a real app, we'd get symbols from the database and a database session
                # For demo, we'll use a sample list
                sample_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX', 'INTC', 'AMD']
                # We would normally pass a database session here
                # results = run_bootstrap_diagnostic(db_session, sample_symbols)
                st.success("Validation complete! (Demo mode)")
                st.info("In a real implementation, this would show validation results and route errors to system_notifications")

    # Enhanced mapping issues table with actionable items
    mapping_issues = pd.DataFrame({
        'Issue ID': ['MAP-001', 'MAP-002', 'MAP-003'],
        'Broker Symbol': ['AAPL.Z', 'MSFT.OQ', 'GOOGL.OQ'],
        'Provider Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'Broker': ['Fidelity', 'E-Trade', 'Charles Schwab'],
        'Status': ['Unmapped', 'Partially Mapped', 'Unmapped'],
        'Severity': ['🔴 High', '🟡 Medium', '🔴 High'],
        'First Seen': ['2023-06-10', '2023-06-12', '2023-06-13'],
        'Last Seen': ['2023-06-15', '2023-06-14', '2023-06-13'],
        'Actions': ['Review', 'Review', 'Review']
    })

    # Display the table with selection capabilities
    edited_df = st.data_editor(
        mapping_issues,
        width='stretch',
        hide_index=True,
        column_config={
            "Issue ID": st.column_config.TextColumn("Issue ID", width="small"),
            "Broker Symbol": st.column_config.TextColumn("Broker Symbol", width="medium"),
            "Provider Symbol": st.column_config.TextColumn("Provider Symbol", width="medium"),
            "Broker": st.column_config.TextColumn("Broker", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Severity": st.column_config.TextColumn("Severity", width="small"),
            "First Seen": st.column_config.DateColumn("First Seen", width="small"),
            "Last Seen": st.column_config.DateColumn("Last Seen", width="small"),
            "Actions": st.column_config.TextColumn("Actions", width="small")
        },
        disabled=["Issue ID", "Broker Symbol", "Provider Symbol", "Broker", "Status", "Severity", "First Seen", "Last Seen"]
    )

    # Check if any rows were modified/selected
    # In newer Streamlit versions, we need to check the returned dataframe for changes
    selected_rows = []
    if hasattr(edited_df, 'index') and not edited_df.equals(mapping_issues):
        # Find rows that were changed (this is a simplified approach)
        # For now, we'll just use all rows if any changes were made
        # A more sophisticated approach would compare specific fields
        selected_rows = list(range(len(edited_df)))

    # Action buttons for selected issues
    st.subheader("Take Action on Selected Issues")
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("✅ Mark as Resolved", width='stretch'):
            if selected_rows:
                st.success(f"{len(selected_rows)} issue(s) marked as resolved!")
            else:
                st.warning("Please modify at least one item in the table to select it for action.")
    with action_col2:
        if st.button("📧 Notify Team", width='stretch'):
            if selected_rows:
                st.info(f"Team notified about {len(selected_rows)} selected issue(s)!")
            else:
                st.warning("Please modify at least one item in the table to select it for action.")
    with action_col3:
        if st.button("📥 Export to CSV", key="export_mapping_csv", width='stretch'):
            if selected_rows:
                st.success(f"Exported {len(selected_rows)} selected issue(s) to CSV!")
            else:
                st.warning("Please modify at least one item in the table to select it for export.")

    # Manual mapping form
    st.subheader("➕ Create New Symbol Mapping")
    with st.form("manual_mapping_form", clear_on_submit=True):
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            broker = st.selectbox("Broker", ["Fidelity", "E-Trade", "Charles Schwab", "TD Ameritrade", "Interactive Brokers"])
            broker_symbol = st.text_input("Broker Symbol", placeholder="e.g., AAPL.Z")
        with form_col2:
            provider_symbol = st.text_input("Provider Symbol (e.g., AAPL)", placeholder="e.g., AAPL")
            notes = st.text_area("Notes (optional)", placeholder="Additional context about this mapping")

        submit_button = st.form_submit_button("Create Mapping", type="primary", width='stretch')
        if submit_button and broker_symbol and provider_symbol:
            st.success(f"✅ Mapping created: {broker_symbol} → {provider_symbol} for {broker}")
            st.balloons()
        elif submit_button:
            st.error("Please fill in both Broker Symbol and Provider Symbol")

with tab2:
    st.subheader("📉 Lot Drift Anomalies")
    st.info("View and fix discrepancies between physical reality (CSV) and database lots")

    # Inbox-style header with metrics
    inbox_col1, inbox_col2, inbox_col3 = st.columns([2, 1, 1])
    with inbox_col1:
        st.subheader("Active Drift Issues")
    with inbox_col2:
        st.metric("Total Anomalies", "3", "1 new")
    with inbox_col3:
        if st.button("🔄 Refresh Drift Scan", width='stretch'):
            with st.spinner("Scanning for lot drift anomalies..."):
                st.success("Drift scan complete! (Demo mode)")
                st.info("In a real implementation, this would compare CSV data with database lots and flag discrepancies")

    # Enhanced drift issues table with actionable items
    drift_issues = pd.DataFrame({
        'Issue ID': ['DRIFT-001', 'DRIFT-002', 'DRIFT-003'],
        'Account': ['ACC001', 'ACC002', 'ACC003'],
        'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'CSV Quantity': [100.000, 50.000, 25.000],
        'DB Quantity': [99.950, 50.050, 24.900],
        'Difference': [+0.050, -0.050, +0.100],
        'Difference %': ['+0.05%', '-0.10%', '+0.40%'],
        'Severity': ['🟡 Low', '🟡 Medium', '🔴 High'],
        'First Seen': ['2023-06-10', '2023-06-12', '2023-06-13'],
        'Last Seen': ['2023-06-15', '2023-06-14', '2023-06-13'],
        'Actions': ['Review', 'Review', 'Review']
    })

    # Display the table with selection capabilities
    edited_df = st.data_editor(
        drift_issues,
        width='stretch',
        hide_index=True,
        column_config={
            "Issue ID": st.column_config.TextColumn("Issue ID", width="small"),
            "Account": st.column_config.TextColumn("Account", width="small"),
            "Symbol": st.column_config.TextColumn("Symbol", width="small"),
            "CSV Quantity": st.column_config.NumberColumn("CSV Quantity", format="%.3f", width="small"),
            "DB Quantity": st.column_config.NumberColumn("DB Quantity", format="%.3f", width="small"),
            "Difference": st.column_config.NumberColumn("Difference", format="+%.3f", width="small"),
            "Difference %": st.column_config.TextColumn("Difference %", width="small"),
            "Severity": st.column_config.TextColumn("Severity", width="small"),
            "First Seen": st.column_config.DateColumn("First Seen", width="small"),
            "Last Seen": st.column_config.DateColumn("Last Seen", width="small"),
            "Actions": st.column_config.TextColumn("Actions", width="small")
        },
        disabled=["Issue ID", "Account", "Symbol", "CSV Quantity", "DB Quantity", "Difference", "Difference %", "Severity", "First Seen", "Last Seen"]
    )

    # Check if any rows were modified/selected
    selected_rows = []
    if hasattr(edited_df, 'index') and not edited_df.equals(drift_issues):
        # Find rows that were changed (this is a simplified approach)
        selected_rows = list(range(len(edited_df)))

    # Action buttons for selected issues
    st.subheader("Take Action on Selected Issues")
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    with action_col1:
        if st.button("✅ Accept CSV as Correct", width='stretch'):
            if selected_rows:
                st.success(f"{len(selected_rows)} issue(s) resolved: CSV accepted as correct!")
            else:
                st.warning("Please modify at least one item in the table to select it for action.")
    with action_col2:
        if st.button("✅ Accept DB as Correct", width='stretch'):
            if selected_rows:
                st.success(f"{len(selected_rows)} issue(s) resolved: Database accepted as correct!")
            else:
                st.warning("Please modify at least one item in the table to select it for action.")
    with action_col3:
        if st.button("✏️ Enter Custom Values", width='stretch'):
            if selected_rows:
                st.info(f"Custom value entry form would appear here for {len(selected_rows)} selected issue(s)!")
            else:
                st.warning("Please modify at least one item in the table to select it for editing.")
    with action_col4:
        if st.button("📥 Export to CSV", key="export_drift_csv", width='stretch'):
            if selected_rows:
                st.success(f"Exported {len(selected_rows)} selected issue(s) to CSV!")
            else:
                st.warning("Please modify at least one item in the table to select it for export.")

    # Drift resolution form
    st.subheader("⚙️ Resolve Selected Drift Issue")
    with st.form("drift_resolution_form", clear_on_submit=True):
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            selected_symbol = st.selectbox("Symbol", ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"])
            selected_account = st.selectbox("Account", ["ACC001", "ACC002", "ACC003", "ACC004", "ACC005"])
            csv_quantity = st.number_input("CSV Quantity", min_value=0.0, step=0.001, value=100.000)
        with form_col2:
            db_quantity = st.number_input("Database Quantity", min_value=0.0, step=0.001, value=99.950)
            action_taken = st.selectbox("Resolution Action", [
                "Accept CSV as Correct",
                "Accept DB as Correct",
                "Enter Custom Values",
                "Investigate Further"
            ])
            if action_taken == "Enter Custom Values":
                custom_quantity = st.number_input("Custom Quantity", min_value=0.0, step=0.001, value=100.000)

        notes = st.text_area("Resolution Notes (optional)", placeholder="Explain the resolution decision")

        submit_button = st.form_submit_button("Resolve Drift Issue", type="primary", width='stretch')
        if submit_button:
            if action_taken == "Enter Custom Values":
                st.success(f"✅ Drift issue resolved for {selected_symbol} in {selected_account} with custom quantity: {custom_quantity:.3f}")
            else:
                st.success(f"✅ Drift issue resolved for {selected_symbol} in {selected_account} by accepting {action_taken.split()[0]} as correct")
            st.balloons()

with tab3:
    st.subheader("⚙️ Adjusted Options")
    st.info("View and manage adjusted options contracts (non-standard contracts)")

    # Inbox-style header with metrics
    inbox_col1, inbox_col2, inbox_col3 = st.columns([2, 1, 1])
    with inbox_col1:
        st.subheader("Active Adjusted Options")
    with inbox_col2:
        st.metric("Total Contracts", "2", "0 new")
    with inbox_col3:
        if st.button("🔄 Refresh Options Data", width='stretch'):
            with st.spinner("Loading adjusted options data..."):
                st.success("Options data refreshed! (Demo mode)")
                st.info("In a real implementation, this would load current adjusted options from the ticker_mappings and option_instruments tables")

    # Enhanced adjusted options table with actionable items
    adjusted_options = pd.DataFrame({
        'Issue ID': ['OPT-001', 'OPT-002'],
        'OCC Symbol': ['AAPL210618C00150000', 'TSLA210618P00800000'],
        'Shares per Contract': [100, 50],  # Non-standard: 50 instead of 100
        'Cash Deliverable': [0.00, 25.50],  # Cash in lieu of fractional shares
        'Description': ['Standard call option', 'Put option with cash settlement'],
        'Underlying': ['AAPL', 'TSLA'],
        'Expiration': ['2021-06-18', '2021-06-18'],
        'Option Type': ['Call', 'Put'],
        'Strike Price': [150.00, 80.00],
        'Last Updated': ['2023-06-10', '2023-06-12'],
        'Status': ['Active', 'Active'],
        'Actions': ['Review', 'Review']
    })

    # Display the table with selection capabilities
    edited_df = st.data_editor(
        adjusted_options,
        width='stretch',
        hide_index=True,
        column_config={
            "Issue ID": st.column_config.TextColumn("Issue ID", width="small"),
            "OCC Symbol": st.column_config.TextColumn("OCC Symbol", width="medium"),
            "Shares per Contract": st.column_config.NumberColumn("Shares/Contract", width="small"),
            "Cash Deliverable": st.column_config.NumberColumn("Cash ($)", format="$%.2f", width="small"),
            "Description": st.column_config.TextColumn("Description", width="medium"),
            "Underlying": st.column_config.TextColumn("Underlying", width="small"),
            "Expiration": st.column_config.DateColumn("Expiration", width="small"),
            "Option Type": st.column_config.TextColumn("Type", width="small"),
            "Strike Price": st.column_config.NumberColumn("Strike", format="$%.2f", width="small"),
            "Last Updated": st.column_config.DateColumn("Updated", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Actions": st.column_config.TextColumn("Actions", width="small")
        },
        disabled=["Issue ID", "OCC Symbol", "Shares per Contract", "Cash Deliverable", "Description", "Underlying", "Expiration", "Option Type", "Strike Price", "Last Updated", "Status"]
    )

    # Check if any rows were modified/selected
    selected_rows = []
    if hasattr(edited_df, 'index') and not edited_df.equals(adjusted_options):
        # Find rows that were changed (this is a simplified approach)
        selected_rows = list(range(len(edited_df)))

    # Action buttons for selected options
    st.subheader("Take Action on Selected Options")
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("📋 View Details", width='stretch'):
            if selected_rows:
                st.info(f"Detailed view would show contract specifications and Greeks for {len(selected_rows)} selected option(s)!")
            else:
                st.warning("Please modify at least one item in the table to select it for viewing details.")
    with action_col2:
        if st.button("📥 Export to CSV", key="export_options_csv", width='stretch'):
            if selected_rows:
                st.success(f"Exported {len(selected_rows)} selected option(s) to CSV!")
            else:
                st.warning("Please modify at least one item in the table to select it for export.")
    with action_col3:
        if st.button("🔍 Validate Contract", width='stretch'):
            if selected_rows:
                st.success(f"Validation initiated for {len(selected_rows)} selected contract(s)!")
            else:
                st.warning("Please modify at least one item in the table to select it for validation.")

    # Add adjusted option form
    st.subheader("➕ Add New Adjusted Option")
    with st.form("adjusted_option_form", clear_on_submit=True):
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            occ_symbol = st.text_input("OCC Symbol", placeholder="e.g., AAPL210618C00150000")
            underlying = st.text_input("Underlying Symbol", placeholder="e.g., AAPL")
            option_type = st.selectbox("Option Type", ["Call", "Put"])
        with form_col2:
            shares_per_contract = st.number_input("Shares per Contract", min_value=1, value=100, step=1)
            strike_price = st.number_input("Strike Price ($)", min_value=0.0, value=100.0, step=0.01)
            expiration_date = st.date_input("Expiration Date", value=datetime.now() + timedelta(days=30))

        form_col3, form_col4 = st.columns(2)
        with form_col3:
            cash_deliverable = st.number_input("Cash Deliverable ($)", min_value=0.0, value=0.0, step=0.01, help="Cash in lieu of fractional shares")
        with form_col4:
            description = st.text_area("Description", placeholder="Additional details about this adjusted option")

        submit_button = st.form_submit_button("Add Adjusted Option", type="primary", width='stretch')
        if submit_button and occ_symbol and underlying:
            st.success(f"✅ Adjusted option added: {occ_symbol}")
            st.balloons()
        elif submit_button:
            st.error("Please fill in both OCC Symbol and Underlying Symbol")

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))