"""
Bootstrap diagnostic engine for validating market data provider connectivity.
Runs dry-run validation checks against market data providers (e.g., yfinance) and
routes lookup errors to the `system_notifications` table.
"""
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

# Try to import yfinance; if not available, we'll log and skip.
try:
    import yfinance as yf
    _yfinance_available = True
except ImportError:
    _yfinance_available = False

from .models import SystemNotifications

logger = logging.getLogger(__name__)


class BootstrapDiagnostic:
    """
    Runs validation checks on market data providers and logs any errors
    to the system_notifications table.
    """

    def __init__(self, db_session: Session):
        """
        Initialize the diagnostic engine with a database session.

        Args:
            db_session: SQLAlchemy session for writing notifications.
        """
        self.db_session = db_session
        if not _yfinance_available:
            logger.warning(
                "yfinance library not installed. Bootstrap diagnostic will not be able to validate symbols."
            )

    def validate_symbols(
        self,
        symbols: List[str],
        provider: str = "yfinance",
        check_price: bool = True,
        check_info: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate a list of symbols by attempting to fetch data from the provider.

        Args:
            symbols: List of ticker symbols to validate.
            provider: Name of the market data provider (default: "yfinance").
            check_price: If True, attempt to fetch the current price.
            check_info: If True, attempt to fetch additional info (more expensive).

        Returns:
            A dictionary with summary counts: total, succeeded, failed, and a list of failed symbols with errors.
        """
        if not _yfinance_available:
            logger.error("Cannot validate symbols because yfinance is not available.")
            return {
                "total": len(symbols),
                "succeeded": 0,
                "failed": len(symbols),
                "errors": [{"symbol": s, "error": "yfinance not installed"} for s in symbols],
            }

        results = {
            "total": len(symbols),
            "succeeded": 0,
            "failed": 0,
            "errors": [],
        }

        for symbol in symbols:
            symbol = symbol.strip().upper()
            if not symbol:
                continue

            try:
                ticker = yf.Ticker(symbol)
                if check_price:
                    # Try to get the current price (fast)
                    # We can use .info but that might be heavy; instead use .history for 1 day?
                    # Or use .fast_info if available (yfinance>=0.2.0)
                    # We'll try to get the last close price from history for the last 2 days.
                    hist = ticker.history(period="2d")
                    if hist.empty:
                        raise ValueError("No historical data returned")
                    # We don't actually need to store the price, just that we got data.
                if check_info:
                    # This is more expensive; we'll do it only if requested.
                    info = ticker.info
                    if not info:
                        raise ValueError("No info returned")
                # If we get here, the symbol is valid.
                results["succeeded"] += 1
                logger.debug(f"Symbol '{symbol}' validated successfully.")
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Validation failed for symbol '{symbol}': {error_msg}")
                results["failed"] += 1
                results["errors"].append({"symbol": symbol, "error": error_msg})
                # Record the failure in the system_notifications table
                self._log_provider_failure(symbol, provider, error_msg)

        logger.info(
            f"Bootstrap diagnostic completed: {results['succeeded']} succeeded, {results['failed']} failed out of {results['total']} symbols."
        )
        return results

    def _log_provider_failure(
        self, symbol: str, provider: str, error_message: str
    ) -> None:
        """
        Log a provider failure to the system_notifications table.

        Args:
            symbol: The symbol that failed.
            provider: The provider name (e.g., "yfinance").
            error_message: The error message from the validation attempt.
        """
        try:
            notification = SystemNotifications(
                category="provider_fetch_failed",
                is_resolved=False,
                metadata={
                    "symbol": symbol,
                    "provider": provider,
                    "error": error_message,
                },
            )
            self.db_session.add(notification)
            self.db_session.commit()
            logger.debug(
                f"Logged provider failure for symbol '{symbol}' to system_notifications."
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(
                f"Failed to log provider failure for symbol '{symbol}' to database: {e}",
                exc_info=True,
            )


# Convenience function for quick validation
def run_bootstrap_diagnostic(
    db_session: Session,
    symbols: List[str],
    provider: str = "yfinance",
) -> Dict[str, Any]:
    """
    Run bootstrap diagnostic on a list of symbols.

    Args:
        db_session: SQLAlchemy session.
        symbols: List of symbols to validate.
        provider: Market data provider to use.

    Returns:
        Summary dictionary from validate_symbols.
    """
    diagnostic = BootstrapDiagnostic(db_session)
    return diagnostic.validate_symbols(symbols, provider=provider)


# Example usage (for testing)
if __name__ == "__main__":
    # This is just a demo; remove or adapt for actual use.
    import sys
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # For demo, we'll use an in-memory SQLite database.
    # In reality, you would use your actual database URL.
    engine = create_engine("sqlite:///:memory:")
    # We would need to create the tables; for demo we skip.
    # Instead, we'll just show how it would be called.
    print("This is a bootstrap diagnostic engine.")
    print("To use, import and call run_bootstrap_diagnostic with a session and symbol list.")