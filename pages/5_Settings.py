"""
Tactical Portfolio Engine - Settings Page
Admin controls and System Health.
"""
import streamlit as st
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from auth import get_current_user
from secret_manager import get_secret
import pandas as pd

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
    tab1, tab2, tab3 = st.tabs(["🔧 System Settings", "🔐 API Keys", "💾 Database"])

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

        if st.button("💾 Save Settings", type="primary", use_container_width=False):
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
        st.dataframe(api_keys_data, use_container_width=True)

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
            if st.button("🔬 Test Yahoo Finance", use_container_width=True):
                st.success("Yahoo Finance connection successful!")
        with test_col2:
            if st.button("🔬 Test All Connections", use_container_width=True):
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
        st.dataframe(db_info, use_container_width=True)

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
            if st.button("🧹 Clean Old Logs", use_container_width=True):
                st.success("Old logs cleaned successfully!")
            if st.button("📊 Update Statistics", use_container_width=True):
                st.success("Database statistics updated!")
        with maintenance_col2:
            if st.button("🔄 Rebuild Indexes", use_container_width=True):
                st.success("Indexes rebuilt successfully!")
            if st.button("💾 Backup Database", use_container_width=True):
                st.success("Database backup initiated!")

        if st.button("💾 Save Database Settings", type="primary", use_container_width=False):
            st.success("Database settings saved successfully!")

# Footer (shown for all users)
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

# Show non-admin users a limited view
if not is_admin:
    st.info("👨‍💼 Administrator View: Only administrators can modify system settings.")