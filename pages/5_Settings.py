"""
Tactical Portfolio Engine - Settings
Admin controls and Symbol Mapping (Phase 1 Step 3 target).
"""
import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import get_current_user

st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
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

st.title("⚙️ Settings")
st.caption("Admin Controls & System Health")

# Admin check (Phase 1 Step 2 will fix this properly)
is_admin = current_user and current_user == "admin@example.com"

if not is_admin:
    st.warning("🔒 Administrator access required for this page.")
    st.info("Phase 1 Step 2 will implement proper admin role detection.")
else:
    st.success("✅ Admin access confirmed")
    
    tab1, tab2 = st.tabs(["🔧 System Settings", "🔄 Symbol Mappings"])

    with tab1:
        st.subheader("System Configuration")
        st.info("System settings will be implemented here.")
        
        st.selectbox("Theme", ["Light", "Dark", "Auto"], index=0)
        st.selectbox("Data Refresh Interval", ["1 minute", "5 minutes", "15 minutes", "1 hour"], index=1)
        st.checkbox("Enable Cache", value=True)
        
        if st.button("💾 Save Settings", type="primary"):
            st.success("Settings saved!")

    with tab2:
        st.subheader("🔄 Symbol Translation Overrides")
        st.info("Manage global symbol translation overrides (e.g., BRK/B → BRK-B)")
        st.caption("Phase 1 Step 3: Build CRUD UI for ticker_mappings table")
        
        # Placeholder for mappings table
        sample_mappings = pd.DataFrame({
            'Broker': ['Fidelity', 'E-Trade', 'Schwab'],
            'Raw Symbol': ['BRK/B', 'BRK.B', 'BRK/B'],
            'Provider Symbol': ['BRK-B', 'BRK-B', 'BRK-B'],
            'Status': ['Active', 'Active', 'Active']
        })
        st.dataframe(sample_mappings, width='stretch', hide_index=True)
        
        with st.expander("➕ Add New Mapping"):
            with st.form("add_mapping"):
                col1, col2 = st.columns(2)
                with col1:
                    broker = st.selectbox("Broker", ["Fidelity", "E-Trade", "Charles Schwab", "TD Ameritrade", "Interactive Brokers"])
                    raw_symbol = st.text_input("Raw Symbol (Broker Format)", placeholder="e.g., BRK/B")
                with col2:
                    provider_symbol = st.text_input("Provider Symbol (Standard)", placeholder="e.g., BRK-B")
                
                if st.form_submit_button("Add Mapping", type="primary"):
                    if raw_symbol and provider_symbol:
                        st.success(f"Mapping added: {raw_symbol} → {provider_symbol} (UI only - DB integration in Step 3)")
                    else:
                        st.error("Fill in both fields")

st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0")
