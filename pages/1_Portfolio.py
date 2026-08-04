"""
Tactical Portfolio Engine - Portfolio Holdings Page
Shows current holdings, tax-lots, and handles authoritative state override CSV ingestion.
"""
import os
import sys
import pandas as pd
import streamlit as st
from datetime import date
from sqlalchemy import select

# Add project root to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Project imports
from strategy_service import StrategyService
from auth import get_current_user
from csv_parser import FidelityPortfolioParser
from models import BrokerageAccounts, PortfolioSnapshots
from database import SessionLocal

# ==========================================
# Helper Functions & State Override Service
# ==========================================

def execute_state_override(parsed_accounts: dict, session) -> int:
    """
    Authoritative State Override:
    Wipes existing snapshot holdings for each matched account in the CSV
    and replaces them with fresh parsed data.
    """
    total_saved = 0
    today = date.today()

    for account_str, holdings in parsed_accounts.items():
        # 1. Match or locate account by string identifier (e.g., 'ROTH *1234')
        stmt = select(BrokerageAccounts).where(BrokerageAccounts.account_number == account_str)
        account = session.execute(stmt).scalar_one_or_none()

        # Auto-provision account if not found
        if not account:
            account = BrokerageAccounts(
                user_id=1,  # Default dev user
                broker_name="Fidelity",
                account_number=account_str
            )
            session.add(account)
            session.flush()  # Obtain assigned ID

        # 2. Wipe current active snapshot positions for this account
        session.query(PortfolioSnapshots).filter(
            PortfolioSnapshots.account_id == account.id
        ).delete()

        # 3. Insert fresh state from CSV
        for item in holdings:
            snapshot = PortfolioSnapshots(
                account_id=account.id,
                symbol=item['symbol'],
                description=item['description'],
                total_quantity=item['quantity'],
                last_price=item['last_price'],
                avg_cost=item['avg_cost'],
                basis=item['basis'],
                value=item['value'],
                earnings_date=item['earnings_date'],
                div_ex_date=item['div_ex_date'],
                capture_date=today,
                is_approved=True
            )
            session.add(snapshot)
            total_saved += 1

    session.commit()
    return total_saved


# ==========================================
# Page Configuration & Styling
# ==========================================

st.set_page_config(
    page_title="Tactical Portfolio Engine - Portfolio",
    page_icon="📈",
    layout="wide"
)

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize Services & User Context
@st.cache_resource
def get_services():
    return StrategyService()

strategy_service = get_services()
current_user = get_current_user()

# Header & Sidebar
st.title("📊 Portfolio Holdings")
st.caption("View current holdings, tax-lots, and update account state via CSV export.")

if current_user:
    st.sidebar.success(f"Logged in as: {current_user}")
else:
    st.sidebar.warning("Running in development mode")

st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between TPE modules.")
# ==========================================
# Main Layout Tabs
# ==========================================

# Open the session globally for the page
session = SessionLocal()

try:
    # Update to your new 2-tab layout
    tab1, tab2 = st.tabs(["🎯 Holdings", "📤 Upload Holdings"])

    # ------------------------------------------
    # Tab 1: Current Holdings
    # ------------------------------------------
    with tab1:
        st.subheader("Current Holdings")
        st.info("Displaying active snapshot holdings across accounts.")

        # Execute a JOIN to retrieve the account number alongside the snapshot data
        stmt = (
            select(
                BrokerageAccounts.account_number,
                PortfolioSnapshots.symbol,
                PortfolioSnapshots.description,
                PortfolioSnapshots.total_quantity,
                PortfolioSnapshots.last_price,
                PortfolioSnapshots.avg_cost,
                PortfolioSnapshots.value
            )
            .join(PortfolioSnapshots, BrokerageAccounts.id == PortfolioSnapshots.account_id)
        )

        holdings_records = session.execute(stmt).fetchall()

        # Render the dataframe if data exists, otherwise show a prompt to upload
        if holdings_records:
            df = pd.DataFrame(holdings_records)

            # Rename columns for a clean UI presentation
            df.columns = [
                "Account",
                "Symbol",
                "Description",
                "Quantity",
                "Last Price",
                "Avg Cost",
                "Market Value"
            ]

            # Format currency columns for better readability
            format_mapping = {
                "Last Price": "${:,.2f}",
                "Avg Cost": "${:,.2f}",
                "Market Value": "${:,.2f}"
            }
            for col, format_str in format_mapping.items():
                if col in df.columns:
                    # Convert to numeric first to avoid formatting errors on strings
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[col] = df[col].apply(lambda x: format_str.format(x) if pd.notnull(x) else x)

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No active holdings found. Please use the 'Upload Holdings' tab to process a CSV export.")


    # ------------------------------------------
    # Tab 2: Authoritative Ingestion Pipeline
    # ------------------------------------------
    with tab2:
        st.subheader("Upload Active Trader Pro CSV")
        st.info("Upload your Fidelity 'All Accounts' export file to set current portfolio state.")

        if 'upload_step' not in st.session_state:
            st.session_state.upload_step = 1
        if 'parsed_data' not in st.session_state:
            st.session_state.parsed_data = None
        if 'preview_accepted' not in st.session_state:
            st.session_state.preview_accepted = False

            # Step 1: Upload File
            if st.session_state.upload_step == 1:
                uploaded_file = st.file_uploader(
                    "Choose a Fidelity Active Trader Pro CSV export",
                    type=["csv"],
                    help="Upload your 'All Accounts' export file."
                )

                if uploaded_file is not None:
                    st.write(f"**Filename:** {uploaded_file.name}")
                    st.write(f"**File size:** {uploaded_file.size} bytes")

                    with st.spinner("Parsing portfolio state..."):
                        try:
                            file_contents = uploaded_file.getvalue().decode("utf-8")
                            parsed_accounts = FidelityPortfolioParser.parse_csv(file_contents)
                            st.session_state.parsed_data = parsed_accounts

                            if parsed_accounts:
                                st.success(f"Successfully parsed {len(parsed_accounts)} account(s)!")
                                st.session_state.upload_step = 2
                                st.rerun()
                            else:
                                st.error("No valid account holdings found in the CSV file.")

                        except Exception as e:
                            st.error(f"Error parsing CSV: {str(e)}")
                            st.session_state.parsed_data = None

            # Step 2: Review Preview
            elif st.session_state.upload_step == 2:
                st.subheader("Step 2: Preview Incoming State")
                parsed_accounts = st.session_state.parsed_data

                if parsed_accounts:
                    for account_id, holdings in parsed_accounts.items():
                        st.markdown(f"### Account: `{account_id}` ({len(holdings)} positions)")
                        preview_df = pd.DataFrame(holdings)
                        st.dataframe(preview_df, use_container_width=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Accept Preview & Proceed to Confirmation", type="primary"):
                            st.session_state.preview_accepted = True
                            st.session_state.upload_step = 3
                            st.rerun()
                    with col2:
                        if st.button("Reject & Start Over"):
                            st.session_state.parsed_data = None
                            st.session_state.upload_step = 1
                            st.rerun()

            # Step 3: Authoritative Override Confirmation
            elif st.session_state.upload_step == 3 and st.session_state.preview_accepted:
                st.subheader("Step 3: Confirm & Execute State Override")

                if st.session_state.parsed_data:
                    st.warning(
                        "⚠️ **Notice:** Confirming this action will **wipe and replace** existing "
                        "portfolio snapshots for all matched accounts with the fresh CSV data."
                    )

                    summary_rows = []
                    for account_id, holdings in st.session_state.parsed_data.items():
                        total_val = sum(h.get("value", 0.0) for h in holdings)
                        summary_rows.append({
                            "Account Identifier": account_id,
                            "Total Positions": len(holdings),
                            "Total Value": f"${total_val:,.2f}"
                        })

                    st.table(pd.DataFrame(summary_rows))

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Confirm & Overwrite Portfolio State", type="primary"):
                            try:
                                saved_count = execute_state_override(st.session_state.parsed_data, session)
                                st.success(
                                    f"State override complete! Updated {saved_count} total positions across accounts.")

                                st.session_state.upload_step = 1
                                st.session_state.parsed_data = None
                                st.session_state.preview_accepted = False
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error executing state override: {str(e)}")
                                session.rollback()

                    with col2:
                        if st.button("Cancel & Discard"):
                            st.session_state.upload_step = 1
                            st.session_state.parsed_data = None
                            st.session_state.preview_accepted = False
                            st.rerun()

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
finally:
    # Ensure the session closes cleanly when the page finishes rendering[cite: 3]
    session.close()
# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | System Date: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))