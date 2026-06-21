"""
GlobalContextService implementing the "Anchor First" pattern.
Updates macro indices ($SPY, $QQQ, $VIX) and stores metrics in the market_regime table.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from .market_data_service import MarketDataService
from .models import MarketRegime

logger = logging.getLogger(__name__)


class GlobalContextService:
    """
    Service for managing global market context using an "Anchor First" approach.
    Fetches data for key market anchors (SPY, QQQ, VIX) and stores indicators
    in the market_regime table for use in strategy evaluation.
    """

    def __init__(self, session: Session):
        """
        Initialize the GlobalContextService with a database session.

        Args:
            session: SQLAlchemy session for caching data.
        """
        self.session = session
        self.market_data = MarketDataService(session)
        # Anchor symbols as defined in the ledger
        self.anchor_symbols = ["SPY", "QQQ", "VIX"]
        # Indicators to compute and store
        self.indicators_to_compute = ["price"]  # Can be extended

    def update_anchor_metrics(self) -> Dict[str, Any]:
        """
        Update metrics for all anchor symbols and store in market_regime table.
        This implements the "Anchor First" pattern.

        Returns:
            Dictionary with update results for each symbol.
        """
        results = {}
        for symbol in self.anchor_symbols:
            try:
                symbol_results = self._update_symbol_metrics(symbol)
                results[symbol] = symbol_results
                logger.info(f"Updated anchor metrics for {symbol}: {symbol_results}")
            except Exception as e:
                logger.error(f"Failed to update anchor metrics for {symbol}: {e}", exc_info=True)
                results[symbol] = {"error": str(e)}
        return results

    def _update_symbol_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Update metrics for a single anchor symbol.

        Args:
            symbol: The anchor symbol (e.g., "SPY").

        Returns:
            Dictionary of computed indicators.
        """
        # Fetch current price
        price = self.market_data.get_current_price(symbol)
        if price is None:
            raise ValueError(f"Could not fetch price for {symbol}")

        # Compute additional indicators (can be extended)
        indicators = {"price": price}

        # TODO: Add more indicators like moving averages, volatility, etc.
        # For example:
        # sma_50 = self._calculate_sma(symbol, 50)
        # if sma_50 is not None:
        #     indicators["sma_50"] = sma_50

        # Store each indicator in the market_regime table
        stored_indicators = {}
        for indicator_name, indicator_value in indicators.items():
            if indicator_value is not None:
                try:
                    self._store_indicator(symbol, indicator_name, indicator_value)
                    stored_indicators[indicator_name] = indicator_value
                except Exception as e:
                    logger.error(
                        f"Failed to store indicator {indicator_name} for {symbol}: {e}"
                    )

        return stored_indicators

    def _store_indicator(
        self,
        symbol: str,
        indicator_name: str,
        indicator_value: float
    ) -> None:
        """
        Store a single indicator value in the market_regime table.

        Args:
            symbol: The anchor symbol.
            indicator_name: Name of the indicator (e.g., "price", "rsi").
            indicator_value: The indicator value.
        """
        # Check if we already have a recent entry for this symbol/indicator
        # (within last 5 minutes) to avoid excessive writes
        from sqlalchemy import select
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(minutes=5)
        stmt = select(MarketRegime).where(
            MarketRegime.anchor_symbol == symbol.upper(),
            MarketRegime.indicator_name == indicator_name,
            MarketRegime.calculated_at >= cutoff_time
        )
        existing = self.session.execute(stmt).scalar_one_or_none()

        if existing:
            # Update existing record
            existing.indicator_value = indicator_value
            existing.calculated_at = datetime.now()
            logger.debug(
                f"Updated {indicator_name} for {symbol} to {indicator_value}"
            )
        else:
            # Insert new record
            regime_record = MarketRegime(
                anchor_symbol=symbol.upper(),
                indicator_name=indicator_name,
                indicator_value=indicator_value
            )
            self.session.add(regime_record)
            logger.debug(
                f"Inserted new {indicator_name} for {symbol}: {indicator_value}"
            )

        # Commit the transaction
        self.session.commit()

    def get_latest_indicator(
        self,
        symbol: str,
        indicator_name: str
    ) -> Optional[float]:
        """
        Get the latest value for a specific indicator from the market_regime table.

        Args:
            symbol: The anchor symbol.
            indicator_name: Name of the indicator.

        Returns:
            Latest indicator value, or None if not available.
        """
        try:
            from sqlalchemy import select
            from datetime import datetime, timedelta

            # Get the most recent value (within last 30 minutes to avoid stale data)
            cutoff_time = datetime.now() - timedelta(minutes=30)
            stmt = select(MarketRegime.indicator_value).where(
                MarketRegime.anchor_symbol == symbol.upper(),
                MarketRegime.indicator_name == indicator_name,
                MarketRegime.calculated_at >= cutoff_time
            ).order_by(MarketRegime.calculated_at.desc()).limit(1)

            result = self.session.execute(stmt).scalar_one_or_none()
            return float(result) if result is not None else None
        except Exception as e:
            logger.error(
                f"Failed to get latest indicator {indicator_name} for {symbol}: {e}"
            )
            return None

    def get_all_latest_indicators(self, symbol: str) -> Dict[str, float]:
        """
        Get all latest indicators for a symbol.

        Args:
            symbol: The anchor symbol.

        Returns:
            Dictionary of indicator names to values.
        """
        indicators = {}
        for indicator_name in self.indicators_to_compute:
            value = self.get_latest_indicator(symbol, indicator_name)
            if value is not None:
                indicators[indicator_name] = value
        return indicators

    def is_anchor_data_fresh(self, symbol: str, max_age_minutes: int = 5) -> bool:
        """
        Check if anchor data for a symbol is fresh enough to use.

        Args:
            symbol: The anchor symbol.
            max_age_minutes: Maximum age in minutes to consider data fresh.

        Returns:
            True if data is fresh, False otherwise.
        """
        try:
            from sqlalchemy import select
            from datetime import datetime, timedelta

            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            stmt = select(MarketRegime.id).where(
                MarketRegime.anchor_symbol == symbol.upper(),
                MarketRegime.calculated_at >= cutoff_time
            ).limit(1)

            result = self.session.execute(stmt).scalar_one_or_none()
            return result is not None
        except Exception as e:
            logger.error(
                f"Failed to check freshness for {symbol}: {e}"
            )
            return False

    def are_all_anchors_fresh(self, max_age_minutes: int = 5) -> bool:
        """
        Check if all anchor symbols have fresh data.

        Args:
            max_age_minutes: Maximum age in minutes to consider data fresh.

        Returns:
            True if all anchors are fresh, False otherwise.
        """
        for symbol in self.anchor_symbols:
            if not self.is_anchor_data_fresh(symbol, max_age_minutes):
                return False
        return True


# Convenience functions
def get_global_context_service(session: Session) -> GlobalContextService:
    """
    Factory function to create a GlobalContextService instance.

    Args:
        session: SQLAlchemy session.

    Returns:
        GlobalContextService instance.
    """
    return GlobalContextService(service)


def update_global_context(session: Session) -> Dict[str, Any]:
    """
    Convenience function to update global context for all anchor symbols.

    Args:
        session: SQLAlchemy session.

    Returns:
        Dictionary with update results.
    """
    service = GlobalContextService(session)
    return service.update_anchor_metrics()


# Example usage (for testing)
if __name__ == "__main__":
    # This is just a demo; remove or adapt for actual use.
    print("GlobalContextService for Anchor First pattern and macro indicators.")
    print("To use, import and create an instance with a SQLAlchemy session.")