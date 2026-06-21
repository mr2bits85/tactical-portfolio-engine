"""
Macro logic gating to automatically freeze or suppress volatile strategy signals
across the platform if anchor data is stale or failed.
"""
import logging
import time
from typing import Callable, Any, Optional, List
from functools import wraps

from sqlalchemy.orm import Session

from .global_context_service import GlobalContextService

logger = logging.getLogger(__name__)


class MacroGatingError(Exception):
    """Exception raised when macro data is not available for gating."""
    pass


def require_fresh_macro_data(
    max_age_minutes: int = 5,
    anchor_symbols: Optional[List[str]] = None,
    fail_open: bool = False,
    default_return: Any = None
):
    """
    Decorator to gate function execution based on freshness of macro anchor data.
    If anchor data is stale or unavailable, the decorated function will not execute
    (or will return a default value, depending on fail_open setting).

    Args:
        max_age_minutes: Maximum age in minutes for data to be considered fresh.
        anchor_symbols: List of anchor symbols to check (default: ["SPY", "QQQ", "VIX"]).
        fail_open: If True, allow execution even if data is stale (default: False).
        default_return: Value to return if gating prevents execution and fail_open is False.

    Returns:
        Decorator function that gates execution based on macro data freshness.
    """
    if anchor_symbols is None:
        anchor_symbols = ["SPY", "QQQ", "VIX"]

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract session from args or kwargs
            session = None
            # Look for a Session object in args
            for arg in args:
                if isinstance(arg, Session):
                    session = arg
                    break
            # If not found in args, check kwargs
            if session is None:
                session = kwargs.get('session')

            if session is None:
                logger.warning(
                    "No SQLAlchemy session found for macro gating. "
                    "Proceeding with execution (fail_open behavior)."
                )
                if fail_open:
                    return func(*args, **kwargs)
                else:
                    return default_return

            try:
                # Create GlobalContextService to check data freshness
                context_service = GlobalContextService(session)

                # Check if all required anchor symbols have fresh data
                all_fresh = True
                for symbol in anchor_symbols:
                    if not context_service.is_anchor_data_fresh(symbol, max_age_minutes):
                        all_fresh = False
                        logger.warning(
                            f"Anchor data for {symbol} is stale or unavailable. "
                            f"Macro gating preventing execution of {func.__name__}."
                        )
                        break

                if all_fresh or fail_open:
                    # Data is fresh enough, or we're failing open
                    return func(*args, **kwargs)
                else:
                    # Data is stale and we're not failing open
                    logger.info(
                        f"Macro gating prevented execution of {func.__name__} "
                        f"due to stale anchor data."
                    )
                    return default_return

            except Exception as e:
                logger.error(
                    f"Error during macro gating check for {func.__name__}: {e}",
                    exc_info=True
                )
                # In case of error, decide based on fail_open
                if fail_open:
                    logger.warning("Proceeding with execution due to fail_open=True")
                    return func(*args, **kwargs)
                else:
                    return default_return
        return wrapper
    return decorator


def macro_data_available(
    session: Session,
    max_age_minutes: int = 5,
    anchor_symbols: Optional[List[str]] = None
) -> bool:
    """
    Check if macro anchor data is fresh and available.

    Args:
        session: SQLAlchemy session.
        max_age_minutes: Maximum age in minutes for data to be considered fresh.
        anchor_symbols: List of anchor symbols to check.

    Returns:
        True if all anchor data is fresh, False otherwise.
    """
    if anchor_symbols is None:
        anchor_symbols = ["SPY", "QQQ", "VIX"]

    try:
        context_service = GlobalContextService(session)
        for symbol in anchor_symbols:
            if not context_service.is_anchor_data_fresh(symbol, max_age_minutes):
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking macro data availability: {e}", exc_info=True)
        return False


def get_macro_data_status(
    session: Session,
    anchor_symbols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get detailed status of macro anchor data.

    Args:
        session: SQLAlchemy session.
        anchor_symbols: List of anchor symbols to check.

    Returns:
        Dictionary with status information for each symbol.
    """
    if anchor_symbols is None:
        anchor_symbols = ["SPY", "QQQ", "VIX"]

    status = {
        "overall": True,
        "symbols": {},
        "timestamp": time.time()
    }

    try:
        context_service = GlobalContextService(session)
        for symbol in anchor_symbols:
            is_fresh = context_service.is_anchor_data_fresh(symbol)
            latest_price = context_service.get_latest_indicator(symbol, "price")
            status["symbols"][symbol] = {
                "fresh": is_fresh,
                "latest_price": latest_price,
                "last_checked": time.time()
            }
            if not is_fresh:
                status["overall"] = False
    except Exception as e:
        logger.error(f"Error getting macro data status: {e}", exc_info=True)
        status["overall"] = False
        status["error"] = str(e)

    return status


class MacroGate:
    """
    Context manager for gating blocks of code based on macro data freshness.
    """

    def __init__(
        self,
        session: Session,
        max_age_minutes: int = 5,
        anchor_symbols: Optional[List[str]] = None,
        fail_open: bool = False
    ):
        """
        Initialize the macro gate.

        Args:
            session: SQLAlchemy session.
            max_age_minutes: Maximum age in minutes for data to be considered fresh.
            anchor_symbols: List of anchor symbols to check.
            fail_open: If True, allow execution even if data is stale.
        """
        self.session = session
        self.max_age_minutes = max_age_minutes
        self.anchor_symbols = anchor_symbols or ["SPY", "QQQ", "VIX"]
        self.fail_open = fail_open
        self.session_provided = session is not None

    def __enter__(self):
        """Enter the context and check macro data freshness."""
        if not self.session_provided:
            raise ValueError("No SQLAlchemy session provided for MacroGate")

        self.context_service = GlobalContextService(self.session)
        self.all_fresh = True
        self.stale_symbols = []

        for symbol in self.anchor_symbols:
            if not self.context_service.is_anchor_data_fresh(symbol, self.max_age_minutes):
                self.all_fresh = False
                self.stale_symbols.append(symbol)

        if not self.all_fresh and not self.fail_open:
            logger.warning(
                f"Macro gate entering blocked state due to stale data: {self.stale_symbols}"
            )
        elif not self.all_fresh and self.fail_open:
            logger.warning(
                f"Macro gate entering warn state due to stale data (fail_open): {self.stale_symbols}"
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        pass

    def proceed(self) -> bool:
        """
        Check if execution should proceed based on gate state.

        Returns:
            True if execution should proceed, False otherwise.
        """
        return self.all_fresh or self.fail_open

    def get_stale_symbols(self) -> List[str]:
        """Get list of symbols with stale data."""
        return self.stale_symbols.copy()


# Convenience decorator for strategies that should be gated by macro data
def guard_strategy_execution(
    max_age_minutes: int = 5,
    anchor_symbols: Optional[List[str]] = None
):
    """
    Decorator specifically for strategy functions that should not execute
    if macro anchor data is stale.

    This is a convenience wrapper around require_fresh_macro_data with
    fail_open=False and default_return=None.

    Args:
        max_age_minutes: Maximum age in minutes for data to be considered fresh.
        anchor_symbols: List of anchor symbols to check.

    Returns:
        Decorator function.
    """
    return require_fresh_macro_data(
        max_age_minutes=max_age_minutes,
        anchor_symbols=anchor_symbols,
        fail_open=False,
        default_return=None
    )


# Example usage (for testing)
if __name__ == "__main__":
    # This is just a demo; remove or adapt for actual use.
    print("Macro logic gating for freezing strategies when anchor data is stale.")
    print("To use, import the decorators or MacroGate class.")