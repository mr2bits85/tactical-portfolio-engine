"""
Data processing engine for safely committing verified data chunks to the database.
Handles insertion of transaction_lots and portfolio_snapshots records.
"""
import logging
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import TransactionLots, PortfolioSnapshots

logger = logging.getLogger(__name__)


def process_transaction_lots(
    session: Session,
    lots_data: List[Dict[str, Any]],
) -> int:
    """
    Process and insert transaction lots data into the database.

    Args:
        session: SQLAlchemy session.
        lots_data: List of dictionaries, each representing a transaction lot.
                   Expected keys: portfolio_id, symbol, asset_type, quantity,
                   purchase_price, purchase_date.

    Returns:
        Number of lots successfully inserted.
    """
    inserted_count = 0
    for lot_dict in lots_data:
        try:
            # Create a TransactionLots instance from the dictionary
            lot = TransactionLots(**lot_dict)
            session.add(lot)
            session.commit()
            inserted_count += 1
            logger.debug(f"Inserted transaction lot: {lot_dict}")
        except IntegrityError as e:
            session.rollback()
            logger.warning(
                f"Integrity error inserting transaction lot {lot_dict}: {e}. Skipping."
            )
        except Exception as e:
            session.rollback()
            logger.error(
                f"Unexpected error inserting transaction lot {lot_dict}: {e}",
                exc_info=True,
            )
    logger.info(f"Processed {inserted_count} transaction lots.")
    return inserted_count


def process_portfolio_snapshots(
    session: Session,
    snapshots_data: List[Dict[str, Any]],
) -> int:
    """
    Process and insert portfolio snapshots data into the database.

    Args:
        session: SQLAlchemy session.
        snapshots_data: List of dictionaries, each representing a portfolio snapshot.
                        Expected keys: account_id, symbol, asset_type, total_quantity,
                        capture_date.

    Returns:
        Number of snapshots successfully inserted.
    """
    inserted_count = 0
    for snapshot_dict in snapshots_data:
        try:
            snapshot = PortfolioSnapshots(**snapshot_dict)
            session.add(snapshot)
            session.commit()
            inserted_count += 1
            logger.debug(f"Inserted portfolio snapshot: {snapshot_dict}")
        except IntegrityError as e:
            session.rollback()
            logger.warning(
                f"Integrity error inserting portfolio snapshot {snapshot_dict}: {e}. Skipping."
            )
        except Exception as e:
            session.rollback()
            logger.error(
                f"Unexpected error inserting portfolio snapshot {snapshot_dict}: {e}",
                exc_info=True,
            )
    logger.info(f"Processed {inserted_count} portfolio snapshots.")
    return inserted_count


# Optional: A unified processor that can handle both types based on a 'type' field.
def process_data_chunks(
    session: Session,
    data_chunks: List[Dict[str, Any]],
    chunk_type: str,
) -> int:
    """
    Process data chunks of a specified type.

    Args:
        session: SQLAlchemy session.
        data_chunks: List of dictionaries containing the data.
        chunk_type: Either 'transaction_lots' or 'portfolio_snapshots'.

    Returns:
        Number of records successfully inserted.
    """
    if chunk_type == "transaction_lots":
        return process_transaction_lots(session, data_chunks)
    elif chunk_type == "portfolio_snapshots":
        return process_portfolio_snapshots(session, data_chunks)
    else:
        raise ValueError(f"Unknown chunk type: {chunk_type}")


# Example usage (for testing)
if __name__ == "__main__":
    # This is just a demo; remove or adapt for actual use.
    print("Data processing engine for transaction_lots and portfolio_snapshots.")
    print("To use, import the functions and call them with a SQLAlchemy session and data.")