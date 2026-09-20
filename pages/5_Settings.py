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
from database import SessionLocal
from models import TickerMappings
from sqlalchemy import select, delete

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
        email = current_user.get('email', 'Unknown') if isinstance(current_user, dict) else str(current_user)
        st.success(f"Logged in as: {email}")
        if isinstance(current_user, dict) and current_user.get('role') == 'admin':
            st.success("🔑 Admin")
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

# Admin check using role from user object
is_admin = current_user and isinstance(current_user, dict) and current_user.get("role") == "admin"

if not is_admin:
    st.warning("🔒 Administrator access required for this page.")
    st.info("Contact your administrator to request access.")
else:
    st.success("✅ Admin Settings Unlocked")
    
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
        
        # Initialize session state for editing
        if 'editing_mapping_id' not in st.session_state:
            st.session_state.editing_mapping_id = None
        if 'show_add_form' not in st.session_state:
            st.session_state.show_add_form = False
        
        # Database session
        session = SessionLocal()
        
        try:
            # Fetch all mappings from database
            stmt = select(TickerMappings).order_by(TickerMappings.broker_name, TickerMappings.raw_symbol)
            mappings = session.execute(stmt).scalars().all()
            
            # Display mappings in an editable table
            if mappings:
                # Prepare data for display
                mapping_data = []
                for m in mappings:
                    mapping_data.append({
                        'ID': m.id,
                        'Broker': m.broker_name,
                        'Raw Symbol': m.raw_symbol,
                        'Provider Symbol': m.provider_symbol,
                        'Status': 'Active'  # Could add status field later
                    })
                
                df = pd.DataFrame(mapping_data)
                
                # Display with action buttons
                st.markdown("### Current Mappings")
                
                # Use columns for each row with edit/delete buttons
                for idx, row in df.iterrows():
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 1])
                    
                    with col1:
                        st.text(row['Broker'])
                    with col2:
                        st.text(row['Raw Symbol'])
                    with col3:
                        st.text(row['Provider Symbol'])
                    with col4:
                        st.text(row['Status'])
                    with col5:
                        if st.button("✏️", key=f"edit_{row['ID']}", help="Edit mapping"):
                            st.session_state.editing_mapping_id = row['ID']
                            st.rerun()
                    with col6:
                        if st.button("🗑️", key=f"delete_{row['ID']}", help="Delete mapping"):
                            # Delete the mapping
                            try:
                                del_stmt = delete(TickerMappings).where(TickerMappings.id == row['ID'])
                                session.execute(del_stmt)
                                session.commit()
                                st.success(f"Deleted mapping: {row['Raw Symbol']} → {row['Provider Symbol']}")
                                st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"Error deleting mapping: {str(e)}")
                
                st.markdown("---")
            else:
                st.info("No symbol mappings configured yet. Add your first mapping below.")
            
            # Add New Mapping Form
            if st.session_state.show_add_form or st.session_state.editing_mapping_id is None:
                if st.button("➕ Add New Mapping", type="secondary", key="show_add_form_btn"):
                    st.session_state.show_add_form = True
                    st.session_state.editing_mapping_id = None
                    st.rerun()
            
            # Edit Form (shows when editing_mapping_id is set)
            if st.session_state.editing_mapping_id is not None:
                st.session_state.show_add_form = True
                # Fetch the mapping to edit
                edit_mapping = session.get(TickerMappings, st.session_state.editing_mapping_id)
                if edit_mapping:
                    st.markdown(f"### ✏️ Edit Mapping (ID: {edit_mapping.id})")
                else:
                    st.error("Mapping not found")
                    st.session_state.editing_mapping_id = None
                    st.rerun()
            elif st.session_state.show_add_form:
                st.markdown("### ➕ Add New Mapping")
            
            # Show form if adding or editing
            if st.session_state.show_add_form:
                with st.form("mapping_form", clear_on_submit=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        broker = st.selectbox(
                            "Broker", 
                            ["Fidelity", "E-Trade", "Charles Schwab", "TD Ameritrade", "Interactive Brokers", "Other"],
                            index=0,
                            key="form_broker"
                        )
                        if broker == "Other":
                            broker = st.text_input("Custom Broker Name", key="custom_broker")
                        raw_symbol = st.text_input(
                            "Raw Symbol (Broker Format)", 
                            placeholder="e.g., BRK/B",
                            value=edit_mapping.raw_symbol if st.session_state.editing_mapping_id else "",
                            key="form_raw_symbol"
                        )
                    with col2:
                        provider_symbol = st.text_input(
                            "Provider Symbol (Standard)", 
                            placeholder="e.g., BRK-B",
                            value=edit_mapping.provider_symbol if st.session_state.editing_mapping_id else "",
                            key="form_provider_symbol"
                        )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        submitted = st.form_submit_button(
                            "Update Mapping" if st.session_state.editing_mapping_id else "Add Mapping", 
                            type="primary"
                        )
                    with col_cancel:
                        cancelled = st.form_submit_button("Cancel", type="secondary")
                    
                    if submitted:
                        if not broker or not raw_symbol or not provider_symbol:
                            st.error("All fields are required")
                        else:
                            try:
                                if st.session_state.editing_mapping_id:
                                    # Update existing
                                    mapping = session.get(TickerMappings, st.session_state.editing_mapping_id)
                                    if mapping:
                                        mapping.broker_name = broker
                                        mapping.raw_symbol = raw_symbol
                                        mapping.provider_symbol = provider_symbol
                                        session.commit()
                                        st.success(f"Updated mapping: {raw_symbol} → {provider_symbol}")
                                    else:
                                        st.error("Mapping not found")
                                else:
                                    # Create new
                                    new_mapping = TickerMappings(
                                        broker_name=broker,
                                        raw_symbol=raw_symbol,
                                        provider_symbol=provider_symbol
                                    )
                                    session.add(new_mapping)
                                    session.commit()
                                    st.success(f"Added mapping: {raw_symbol} → {provider_symbol}")
                                
                                # Reset form state
                                st.session_state.show_add_form = False
                                st.session_state.editing_mapping_id = None
                                st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"Error saving mapping: {str(e)}")
                    
                    if cancelled:
                        st.session_state.show_add_form = False
                        st.session_state.editing_mapping_id = None
                        st.rerun()
        
        finally:
            session.close()

st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0")
