"""
Data processing engine for safely committing verified data chunks to the database.
Handles the Authoritative State Override for portfolio snapshots.
"""
import logging
from typing import Dict, List, Any
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import BrokerageAccounts, PortfolioSnapshots

logger = logging.getLogger(__name__)


def execute_state_override(parsed_accounts: Dict[str, List[Dict[str, Any]]], session: Session) -> int:
    """
    Authoritative State Override:
    Wipes existing snapshot holdings for each matched account in the CSV
    and replaces them with fresh parsed data.

    Executes as a single atomic transaction.
    """
    total_saved = 0
    today = date.today()

    try:
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
                session.flush()  # Obtain assigned ID without committing

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
                    earnings_date=item.get('earnings_date'),
                    div_ex_date=item.get('div_ex_date'),
                    capture_date=today,
                    is_approved=True
                )
                session.add(snapshot)
                total_saved += 1

        # 4. Commit all deletions and insertions as a single atomic transaction
        session.commit()
        logger.info(f"State override successful. Processed {total_saved} portfolio snapshots.")
        return total_saved

    except Exception as e:
        # If any part of the process fails, roll back the entire transaction
        session.rollback()
        logger.error(f"Error during state override: {e}", exc_info=True)
        raise e