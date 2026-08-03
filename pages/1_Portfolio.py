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

# Import CSV upload functionality
from csv_parser import create_fidelity_parser, create_e_trade_parser
from models import BrokerageAccounts, PortfolioSnapshots, TransactionLots, SystemNotifications
from sqlalchemy import select, func
from datetime import date


# Helper functions for CSV upload
def get_user_brokerage_accounts(user_id, session):
    """Get list of user's brokerage accounts with associated brokers"""
    stmt = select(BrokerageAccounts).where(BrokerageAccounts.user_id == user_id)
    return session.execute(stmt).scalars().all()

def parse_uploaded_csv(uploaded_file):
    """Parse CSV by trying both Fidelity and E-Trade parsers, selecting the better result"""
    fidelity_parser = create_fidelity_parser()
    etrade_parser = create_e_trade_parser()

    # Try both parsers
    try:
        fidelity_data = fidelity_parser.parse_file(uploaded_file)
        fidelity_count = len([row for row in fidelity_data if row.get('symbol') and row.get('quantity') is not None])
    except Exception:
        fidelity_data = []
        fidelity_count = 0

    try:
        # Need to reset file pointer for second parse
        uploaded_file.seek(0)
        etrade_data = etrade_parser.parse_file(uploaded_file)
        etrade_count = len([row for row in etrade_data if row.get('symbol') and row.get('quantity') is not None])
    except Exception:
        etrade_data = []
        etrade_count = 0

    # Select parser with more valid rows
    if fidelity_count >= etrade_count:
        uploaded_file.seek(0)  # Reset for actual use
        return fidelity_parser.parse_file(uploaded_file)
    else:
        uploaded_file.seek(0)
        return etrade_parser.parse_file(uploaded_file)

def get_current_holdings(account_id, session):
    """Get current holdings from latest approved snapshot"""
    # Get all approved snapshots for this account (should be just one if we manage approval correctly)
    stmt = select(PortfolioSnapshots).where(
        PortfolioSnapshots.account_id == account_id,
        PortfolioSnapshots.is_approved == True
    ).order_by(PortfolioSnapshots.capture_date.desc())
    snapshots = session.execute(stmt).scalars().all()

    holdings = {}
    for snapshot in snapshots:
        key = (snapshot.symbol, snapshot.asset_type)
        if key not in holdings:  # Latest wins (we process in order)
            holdings[key] = snapshot.total_quantity
    return holdings

def compare_holdings(new_csv_data, current_holdings):
    """Compare new CSV data with current holdings"""
    # Convert new CSV data to holdings dict
    parsed_holdings = {}
    for row in new_csv_data:
        key = (row['symbol'], row['asset_type'])
        parsed_holdings[key] = row['quantity']

    all_keys = set(parsed_holdings.keys()) | set(current_holdings.keys())
    comparison = []

    for key in all_keys:
        symbol, asset_type = key
        parsed_qty = parsed_holdings.get(key, 0)
        current_qty = current_holdings.get(key, 0)
        difference = parsed_qty - current_qty

        if abs(difference) < 0.0001:  # Within threshold
            status = "UNCHANGED"
        elif key not in current_holdings:  # Only in parsed data (new)
            status = "NEW"
        elif key not in parsed_holdings:  # Only in current data (removed)
            status = "REMOVED"
        else:
            status = "CHANGED"

        comparison.append({
            "symbol": symbol,
            "asset_type": asset_type,
            "current_quantity": current_qty,
            "uploaded_quantity": parsed_qty,
            "difference": difference,
            "percent_difference": (difference / current_qty * 100) if current_qty != 0 else 0,
            "status": status
        })

    return comparison, parsed_holdings

def save_portfolio_snapshots(account_id, snapshot_data, session):
    """Save new portfolio_snapshots records and manage approval status"""
    # First, mark all existing snapshots for this account as NOT approved
    stmt = select(PortfolioSnapshots).where(PortfolioSnapshots.account_id == account_id)
    existing_snapshots = session.execute(stmt).scalars().all()
    for snapshot in existing_snapshots:
        snapshot.is_approved = False

    # Create new snapshots
    new_snapshots = []
    for row in snapshot_data:
        snapshot = PortfolioSnapshots(
            account_id=account_id,
            symbol=row['symbol'],
            asset_type=row['asset_type'],
            total_quantity=row['quantity'],
            capture_date=date.today(),
            is_approved=True  # These are the new approved/current snapshots
        )
        new_snapshots.append(snapshot)

    session.add_all(new_snapshots)
    session.commit()
    return len(new_snapshots)

def create_drift_notifications(differences, account_id, session):
    """Create system notifications for discrepancies to send to Drift Center"""
    notifications = []
    for diff in differences:
        if abs(diff['difference']) > 0.0001:  # Outside thresholds
            notification = SystemNotifications(
                category="data_discrepancy",
                is_resolved=False,
                notification_metadata={
                    "account_id": account_id,
                    "symbol": diff['symbol'],
                    "quantity_difference": diff['difference'],
                    "description": f"Holdings discrepancy for {diff['symbol']} in account {account_id} (upload pending approval)"
                }
            )
            notifications.append(notification)

    if notifications:
        session.add_all(notifications)
        session.commit()
    return len(notifications)


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
tab1, tab2, tab3, tab4 = st.tabs(["📊 Holdings", "🧾 Tax-Lots", "📉 Drift Indicators", "📤 Upload Holdings"])

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
        'P/L': ['$2550.00', '$1262.50', '$6268.75'],
        'P/L %': ['+16.7%', '+8.9%', '+11.4%']
    })
    st.dataframe(sample_holdings, width='stretch')

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
        'P/L': ['$1525.00', '$1025.00', '$1512.50'],
        'P/L %': ['+10.5%', '+6.6%', '+5.5%'],
        'Holding Period': ['Long-term', 'Long-term', 'Long-term']
    })
    st.dataframe(sample_lots, width='stretch')

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
    st.dataframe(sample_drift, width='stretch')

with tab4:
    st.subheader("Upload Holdings")
    st.info("Upload your brokerage CSV file to update your current holdings")

    # Initialize session state for upload process
    if 'upload_step' not in st.session_state:
        st.session_state.upload_step = 1
    if 'parsed_data' not in st.session_state:
        st.session_state.parsed_data = None
    if 'selected_account' not in st.session_state:
        st.session_state.selected_account = None
    if 'broker_type' not in st.session_state:
        st.session_state.broker_type = None
    if 'preview_accepted' not in st.session_state:
        st.session_state.preview_accepted = False

    # Get user's accounts
    try:
        # Get a database session for querying accounts
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import os
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()

        # Get database URL
        database_url = os.getenv("TACTICAL_DATABASE_URL")
        if not database_url:
            database_url = "postgresql://postgres:password@127.0.0.1:5432/tactical_portfolio_db"

        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        # Get current user
        current_user = get_current_user()
        if not current_user:
            current_user = "dev@example.com"  # Default for development

        # Get user's accounts
        # For MVP, we'll use a default user ID since we don't have easy access to user ID from email
        # In a production implementation, we would look up the user ID from the email
        DEFAULT_USER_ID = 1  # TODO: Replace with actual user ID lookup
        accounts = get_user_brokerage_accounts(DEFAULT_USER_ID, session)
        user_accounts = accounts  # Already filtered by user_id in the function

        # If no accounts found, show message
        if not user_accounts:
            st.warning("No brokerage accounts found. Please add an account in Settings first.")
        else:
            # Step 1: Account Selection
            if st.session_state.upload_step == 1:
                st.subheader("Step 1: Select Account")

                # Option to select existing account or add new one
                account_options = ["Select an account..."] + [f"{acc.broker_name} - Account {acc.id}" for acc in user_accounts]
                account_options.append("+ Add New Account")

                selected_account_str = st.selectbox(
                    "Choose or add a brokerage account:",
                    options=account_options,
                    key="account_selector"
                )

                if selected_account_str == "+ Add New Account":
                    # Show form to add new account
                    with st.form("new_account_form"):
                        st.subheader("Add New Account")
                        broker_type = st.selectbox("Broker Type", ["Fidelity", "E-Trade"])
                        submitted = st.form_submit_button("Create Account")

                        if submitted:
                            # Create new account
                            import hashlib
                            import secrets
                            account_hash = hashlib.sha256(secrets.token_bytes(32)).hexdigest()

                            new_account = BrokerageAccounts(
                                user_id=1,  # TODO: Get actual user ID from auth
                                broker_name=broker_type,
                                account_hash=account_hash
                            )
                            session.add(new_account)
                            session.commit()
                            st.success(f"Account created successfully! (Broker: {broker_type})")
                            # Refresh the account list
                            st.experimental_rerun()

                elif selected_account_str != "Select an account...":
                    # Existing account selected
                    selected_index = account_options.index(selected_account_str) - 1  # Subtract 1 for "Select an account..."
                    if 0 <= selected_index < len(user_accounts):
                        st.session_state.selected_account = user_accounts[selected_index]
                        st.session_state.broker_type = st.session_state.selected_account.broker_name
                        st.success(f"Selected: {st.session_state.selected_account.broker_name} account")

                        # Move to file upload step
                        if st.button("Continue to File Upload", type="primary"):
                            st.session_state.upload_step = 2
                            st.experimental_rerun()

            # Step 2: File Upload
            elif st.session_state.upload_step == 2:
                st.subheader("Step 2: Upload CSV File")

                uploaded_file = st.file_uploader(
                    "Choose a CSV file",
                    type=["csv"],
                    help="Upload your Fidelity or E-Trade export file"
                )

                if uploaded_file is not None:
                    # Show file details
                    st.write(f"Filename: {uploaded_file.name}")
                    st.write(f"File size: {uploaded_file.size} bytes")

                    # Parse the CSV
                    with st.spinner("Parsing CSV file..."):
                        try:
                            parsed_data = parse_uploaded_csv(uploaded_file)
                            st.session_state.parsed_data = parsed_data

                            if parsed_data and len(parsed_data) > 0:
                                st.success(f"Successfully parsed {len(parsed_data)} rows!")

                                # Show preview
                                st.subheader("Preview of Parsed Data")
                                preview_df = pd.DataFrame(parsed_data[:5])  # Show first 5 rows
                                st.dataframe(preview_df, width='stretch')

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Accept Preview & Continue", type="primary"):
                                        st.session_state.preview_accepted = True
                                        st.session_state.upload_step = 3
                                        st.experimental_rerun()
                                with col2:
                                    if st.button("Reject & Reupload"):
                                        st.session_state.parsed_data = None
                                        st.session_state.upload_step = 2
                                        st.experimental_rerun()
                            else:
                                st.error("No valid data found in the CSV file. Please check the format.")

                        except Exception as e:
                            st.error(f"Error parsing CSV: {str(e)}")
                            st.session_state.parsed_data = None

            # Step 3: Validation & Comparison
            elif st.session_state.upload_step == 3 and st.session_state.preview_accepted:
                st.subheader("Step 3: Review & Confirm")

                if st.session_state.parsed_data and st.session_state.selected_account:
                    # Get current holdings from database
                    current_holdings = get_current_holdings(st.session_state.selected_account.id, session)

                    # Compare holdings
                    comparison, parsed_holdings = compare_holdings(st.session_state.parsed_data, current_holdings)

                    # Display comparison table
                    if comparison:
                        st.subheader("Holdings Comparison")
                        comparison_df = pd.DataFrame(comparison)

                        # Format the dataframe for display
                        display_df = comparison_df.copy()
                        display_df['Current Quantity'] = display_df['Current Quantity'].apply(
                            lambda x: f"{x:,.3f}" if isinstance(x, float) else x
                        )
                        display_df['Uploaded Quantity'] = display_df['Uploaded Quantity'].apply(
                            lambda x: f"{x:,.3f}" if isinstance(x, float) else x
                        )
                        display_df['Difference'] = display_df['Difference'].apply(
                            lambda x: f"{x:,.3f}" if isinstance(x, float) else x
                        )
                        display_df['% Difference'] = display_df['% Difference'].apply(
                            lambda x: f"{x:+.2f}%" if isinstance(x, float) else x
                        )

                        st.dataframe(
                            display_df[['Symbol', 'Asset Type', 'Current Quantity', 'Uploaded Quantity', 'Difference', '% Difference', 'Status']],
                            width='stretch',
                            hide_index=True
                        )

                        # Summary statistics
                        new_count = sum(1 for c in comparison if c['status'] == 'NEW')
                        removed_count = sum(1 for c in comparison if c['status'] == 'REMOVED')
                        changed_count = sum(1 for c in comparison if c['status'] == 'CHANGED')
                        unchanged_count = sum(1 for c in comparison if c['status'] == 'UNCHANGED')

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("New", new_count)
                        with col2:
                            st.metric("Removed", removed_count)
                        with col3:
                            st.metric("Changed", changed_count)
                        with col4:
                            st.metric("Unchanged", unchanged_count)

                        # Action buttons
                        st.subheader("Step 4: Confirm & Upload")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if st.button("Accept & Upload to Database", type="primary"):
                                # Save to database
                                try:
                                    saved_count = save_portfolio_snapshots(
                                        st.session_state.selected_account.id,
                                        st.session_state.parsed_data,
                                        session
                                    )
                                    st.success(f"Upload approved! {saved_count} positions saved as current holdings.")
                                    # Reset for next upload
                                    st.session_state.upload_step = 1
                                    st.session_state.parsed_data = None
                                    st.session_state.selected_account = None
                                    st.session_state.broker_type = None
                                    st.session_state.preview_accepted = False
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error saving to database: {str(e)}")
                                    session.rollback()

                        with col2:
                            if st.button("Reject & Cancel"):
                                st.session_state.upload_step = 1
                                st.session_state.parsed_data = None
                                st.session_state.selected_account = None
                                st.session_state.broker_type = None
                                st.session_state.preview_accepted = False
                                st.experimental_rerun()

                        with col3:
                            if st.button("Send to Drift Center for Review"):
                                # Create drift notifications for review
                                try:
                                    notified_count = create_drift_notifications(
                                        comparison,
                                        st.session_state.selected_account.id,
                                        session
                                    )
                                    st.info(f"Drift notifications created for {notified_count} positions with significant differences.")
                                    st.info("Please review these in the Resolution Center → Drift Issues tab.")
                                    # Don't reset here - user might want to make corrections first
                                except Exception as e:
                                    st.error(f"Error creating drift notifications: {str(e)}")
                    else:
                        st.warning("No holdings data to compare")
                else:
                    st.error("Missing account or parsed data. Please go back and try again.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
    finally:
        if 'session' in locals():
            session.close()

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))