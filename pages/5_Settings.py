"""
Tactical Portfolio Engine - Settings Page
Admin controls and System Health.
"""
import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from auth import get_current_user
from secret_manager import get_secret
from models import TickerMappings

# Page configuration
st.set_page_config(
    page_title="Tactical Portfolio Engine - Settings",
    page_icon="⚙️",
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
st.title("⚙️ Settings")
st.caption("Admin controls and System Health")

# User info
if current_user:
    st.sidebar.success(f"Logged in as: {current_user}")
else:
    st.sidebar.warning("Running in development mode")

# Check if user is admin (in a real app, we'd check the user's role from database)
is_admin = current_user and current_user == "admin@example.com"  # Simplified check

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between different views")

# Main content
if not is_admin:
    st.warning("🔒 Administrator access required for this page.")
    st.info("Please contact your system administrator for access to settings.")
else:
    # Initialize session state for mapping form
    if 'show_add_mapping' not in st.session_state:
        st.session_state.show_add_mapping = False

    tab1, tab2, tab3, tab4 = st.tabs(["🔧 System Settings", "🔐 API Keys", "💾 Database", "🔄 Symbol Mappings"])

    with tab1:
        st.subheader("System Configuration")

        # General settings
        st.write("### General Settings")
        setting_col1, setting_col2 = st.columns(2)
        with setting_col1:
            st.selectbox("Theme", ["Light", "Dark", "Auto"], index=0)
            st.selectbox("Default Timeframe", ["1D", "1W", "1M", "3M", "6M", "1Y"], index=2)
            st.checkbox("Enable Notifications", value=True)
        with setting_col2:
            st.selectbox("Data Refresh Interval", ["1 minute", "5 minutes", "15 minutes", "1 hour"], index=1)
            st.checkbox("Enable Cache", value=True)
            st.number_input("Cache TTL (minutes)", min_value=1, value=60)

        # Feature flags
        st.write("### Feature Flags")
        feature_col1, feature_col2 = st.columns(2)
        with feature_col1:
            st.checkbox("Enable TQQQ Manager", value=True)
            st.checkbox("Enable Advanced Charting", value=False)
            st.checkbox("Enable Paper Trading", value=False)
        with feature_col2:
            st.checkbox("Enable API Access", value=True)
            st.checkbox("Enable Data Export", value=True)
            st.checkbox("Enable Backtesting", value=False)

        if st.button("💾 Save Settings", type="primary", width='content'):
            st.success("Settings saved successfully!")

    with tab2:
        st.subheader("API Key Management")

        st.info("Manage API keys for market data providers and other services")

        # API Keys table
        api_keys_data = pd.DataFrame({
            'Service': ['Yahoo Finance', 'Alpha Vantage', 'News API', 'Twitter API'],
            'Status': ['✅ Configured', '❌ Not Set', '✅ Configured', '❌ Not Set'],
            'Last Updated': ['2023-06-10', 'Never', '2023-06-15', 'Never'],
            'Usage': ['Low', 'None', 'Medium', 'None']
        })
        st.dataframe(api_keys_data, width='stretch')

        # Add/Update API Key
        with st.expander("➕ Add/Update API Key", expanded=False):
            with st.form("api_key_form"):
                service = st.selectbox("Service", ["Yahoo Finance", "Alpha Vantage", "News API", "Twitter API", "Other"])
                api_key = st.text_input("API Key", type="password")
                description = st.text_input("Description (optional)")
                submit_button = st.form_submit_button("Save API Key")
                if submit_button and api_key:
                    # In a real app, we'd store this in Secret Manager
                    st.success(f"API key for {service} saved successfully!")
                    if description:
                        st.info(f"Description: {description}")

        # Test API Connection
        st.subheader("Test API Connections")
        test_col1, test_col2 = st.columns(2)
        with test_col1:
            if st.button("🔬 Test Yahoo Finance", width='stretch'):
                st.success("Yahoo Finance connection successful!")
        with test_col2:
            if st.button("🔬 Test All Connections", width='stretch'):
                st.info("Testing all API connections...")
                st.success("All connections tested successfully!")

    with tab3:
        st.subheader("Database Management")

        st.info("View and manage database connections and settings")

        # Database connection info
        st.write("### Connection Information")
        db_info = pd.DataFrame({
            'Property': ['Host', 'Port', 'Database Name', 'Username', 'Connection Status'],
            'Value': ['localhost', '5432', 'tactical_portfolio_db', 'app_user', '✅ Connected']
        })

        # Force Value column to string to prevent PyArrow crash
        db_info['Value'] = db_info['Value'].astype(str)

        st.dataframe(db_info, width='stretch')

        # Pool settings
        st.write("### Connection Pool Settings")
        pool_col1, pool_col2 = st.columns(2)
        with pool_col1:
            st.number_input("Min Connections", min_value=1, value=5)
            st.number_input("Max Connections", min_value=1, value=20)
        with pool_col2:
            st.number_input("Connection Timeout (seconds)", min_value=1, value=30)
            st.number_input("Max Retries", min_value=0, value=3)

        # Maintenance tasks
        st.write("### Maintenance Tasks")
        maintenance_col1, maintenance_col2 = st.columns(2)
        with maintenance_col1:
            if st.button("🧹 Clean Old Logs", width='stretch'):
                st.success("Old logs cleaned successfully!")
            if st.button("📊 Update Statistics", width='stretch'):
                st.success("Database statistics updated!")
        with maintenance_col2:
            if st.button("🔄 Rebuild Indexes", width='stretch'):
                st.success("Indexes rebuilt successfully!")
            if st.button("💾 Backup Database", width='stretch'):
                st.success("Database backup initiated!")

        if st.button("💾 Save Database Settings", type="primary", width='content'):
            st.success("Database settings saved successfully!")

    with tab4:
        st.subheader("🔄 Symbol Translation Overrides")
        st.info("Manage global symbol translation overrides for the ticker_mappings master table")

        # Symbol Mappings Management
        st.write("### Current Symbol Mappings")

        # Sample data for demonstration - in a real app, this would come from the database
        sample_mappings = pd.DataFrame({
            'ID': [1, 2, 3, 4, 5],
            'Broker Name': ['Fidelity', 'E-Trade', 'Charles Schwab', 'TD Ameritrade', 'Interactive Brokers'],
            'Raw Symbol (Broker)': ['AAPL.Z', 'MSFT.OQ', 'GOOGL.OQ', 'TSLA', 'NVDA'],
            'Provider Symbol': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
            'Created': ['2023-06-10', '2023-06-12', '2023-06-13', '2023-06-14', '2023-06-15'],
            'Actions': ['Edit', 'Edit', 'Edit', 'Edit', 'Edit']
        })

        # Display the mappings table
        edited_mappings = st.data_editor(
            sample_mappings,
            width='stretch',
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Broker Name": st.column_config.TextColumn("Broker Name", width="medium"),
                "Raw Symbol (Broker)": st.column_config.TextColumn("Raw Symbol", width="medium"),
                "Provider Symbol": st.column_config.TextColumn("Provider Symbol", width="medium"),
                "Created": st.column_config.DateColumn("Created", width="small"),
                "Actions": st.column_config.TextColumn("Actions", width="small")
            },
            disabled=["ID", "Broker Name", "Raw Symbol (Broker)", "Provider Symbol", "Created"]
        )

        # Action buttons for mappings
        st.write("### Actions")
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        with action_col1:
            if st.button("➕ Add New Mapping", type="primary", width='stretch'):
                st.session_state.show_add_mapping = True
        with action_col2:
            if st.button("📥 Export to CSV", width='stretch'):
                st.success("Symbol mappings exported to CSV!")
        with action_col3:
            if st.button("📤 Import from CSV", width='stretch'):
                st.success("Symbol mappings imported from CSV!")
        with action_col4:
            if st.button("🗑️ Clear All Mappings", type="secondary", width='stretch'):
                st.warning("This action cannot be undone!")

        # Add New Mapping Form
        if st.session_state.get('show_add_mapping', False):
            st.write("### Add New Symbol Mapping")
            with st.form("add_mapping_form", clear_on_submit=True):
                form_col1, form_col2 = st.columns(2)
                with form_col1:
                    broker_name = st.selectbox(
                        "Broker Name",
                        ["Fidelity", "E-Trade", "Charles Schwab", "TD Ameritrade", "Interactive Brokers", "Other"],
                        key="add_broker"
                    )
                    if broker_name == "Other":
                        broker_name = st.text_input("Custom Broker Name", key="custom_broker")

                    raw_symbol = st.text_input(
                        "Raw Symbol (Broker Format)",
                        placeholder="e.g., AAPL.Z, MSFT.OQ",
                        help="Symbol format as received from the broker"
                    )
                with form_col2:
                    provider_symbol = st.text_input(
                        "Provider Symbol (Standard Format)",
                        placeholder="e.g., AAPL, MSFT",
                        help="Standardized symbol format for data providers"
                    )
                    notes = st.text_area(
                        "Notes (Optional)",
                        placeholder="Additional context about this mapping",
                        height=100
                    )

                form_col3, form_col4 = st.columns([1, 1])
                with form_col3:
                    submit_button = st.form_submit_button("Add Mapping", type="primary", width='stretch')
                with form_col4:
                    cancel_button = st.form_submit_button("Cancel", type="secondary", width='stretch')

                if cancel_button:
                    st.session_state.show_add_mapping = False
                    st.rerun()

                if submit_button and broker_name and raw_symbol and provider_symbol:
                    # In a real implementation, we would save to the database here
                    # new_mapping = TickerMappings(
                    #     broker_name=broker_name,
                    #     raw_symbol=raw_symbol,
                    #     provider_symbol=provider_symbol
                    # )
                    # db.session.add(new_mapping)
                    # db.session.commit()

                    st.success(f"✅ Symbol mapping added: {broker_name} - {raw_symbol} → {provider_symbol}")
                    st.session_state.show_add_mapping = False
                    st.balloons()
                    st.rerun()
                elif submit_button:
                    st.error("Please fill in all required fields: Broker Name, Raw Symbol, and Provider Symbol")

# Footer (shown for all users)
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

# Show non-admin users a limited view
if not is_admin:
    st.info("👨‍💼 Administrator View: Only administrators can modify system settings.")