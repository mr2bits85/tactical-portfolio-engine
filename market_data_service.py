"""
Core MarketDataService for fetching market data using yfinance with tenacity
exponential backoff and jitter for resilience.
"""
import logging
import time
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

try:
    import yfinance as yf
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    _yfinance_available = True
    _tenacity_available = True
except ImportError:
    _yfinance_available = False
    _tenacity_available = False

from models import TickerPricesLive, TickerIndicators, TickerMetadata

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Service for fetching and caching market data from yfinance with automatic
    retry mechanism using tenacity.
    """

    def __init__(self, session: Session):
        """
        Initialize the MarketDataService with a database session.

        Args:
            session: SQLAlchemy session for caching data.
        """
        self.session = session
        if not _yfinance_available:
            logger.error("yfinance library not installed. MarketDataService will not function.")
        if not _tenacity_available:
            logger.warning("tenacity library not installed. Retry mechanism will not be available.")

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),  # Retry on any exception
    )
    def _fetch_ticker_data_with_retry(self, symbol: str) -> Optional[yf.Ticker]:
        """
        Fetch ticker data from yfinance with exponential backoff retry.

        Args:
            symbol: The ticker symbol to fetch.

        Returns:
            yf.Ticker object or None if failed after retries.
        """
        if not _yfinance_available:
            return None
        try:
            ticker = yf.Ticker(symbol.upper().strip())
            # We'll do a light operation to verify the ticker exists
            # Fast info is available in newer yfinance versions
            _ = ticker.fast_info  # This will trigger a fetch
            return ticker
        except Exception as e:
            logger.warning(f"Attempt failed for symbol {symbol}: {e}")
            raise  # Re-raise to trigger tenacity retry

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the current price for a symbol with retry mechanism.

        Args:
            symbol: The ticker symbol.

        Returns:
            Current price as float, or None if unavailable.
        """
        try:
            ticker = self._fetch_ticker_data_with_retry(symbol)
            if ticker is None:
                return None
            # Try fast_info first (faster)
            try:
                price = ticker.fast_info.get('last_price')
                if price is not None:
                    return float(price)
            except (AttributeError, KeyError):
                pass
            # Fallback to history
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            return None
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol} after retries: {e}")
            return None

    def get_ticker_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed ticker information with retry mechanism.

        Args:
            symbol: The ticker symbol.

        Returns:
            Dictionary with ticker info, or None if unavailable.
        """
        try:
            ticker = self._fetch_ticker_data_with_retry(symbol)
            if ticker is None:
                return None
            info = ticker.info
            if info:
                # Extract commonly used fields
                return {
                    'symbol': info.get('symbol'),
                    'shortName': info.get('shortName'),
                    'longName': info.get('longName'),
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                    'marketCap': info.get('marketCap'),
                    'currency': info.get('currency'),
                    'exchange': info.get('exchange'),
                    'quoteType': info.get('quoteType'),
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get ticker info for {symbol} after retries: {e}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Optional[Any]:
        """
        Get historical price data with retry mechanism.

        Args:
            symbol: The ticker symbol.
            period: Data period (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max").
            interval: Data interval (e.g., "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo").

        Returns:
            DataFrame with historical data, or None if unavailable.
        """
        try:
            ticker = self._fetch_ticker_data_with_retry(symbol)
            if ticker is None:
                return None
            hist = ticker.history(period=period, interval=interval)
            if hist.empty:
                return None
            return hist
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol} after retries: {e}")
            return None

    def cache_current_price(self, symbol: str) -> bool:
        """
        Fetch and cache the current price for a symbol in the ticker_prices_live table.

        Args:
            symbol: The ticker symbol to cache.

        Returns:
            True if successfully cached, False otherwise.
        """
        try:
            price = self.get_current_price(symbol)
            if price is None:
                logger.warning(f"No price data available for {symbol}")
                return False

            # Check if we already have a recent entry (within last 5 minutes)
            from sqlalchemy import select
            from datetime import datetime, timedelta

            cutoff_time = datetime.now() - timedelta(minutes=5)
            stmt = select(TickerPricesLive).where(
                TickerPricesLive.symbol == symbol.upper(),
                TickerPricesLive.updated_at >= cutoff_time
            )
            existing = self.session.execute(stmt).scalar_one_or_none()

            if existing:
                # Update existing record
                existing.price = price
                existing.updated_at = datetime.now()
                logger.debug(f"Updated price for {symbol} to {price}")
            else:
                # Insert new record
                price_record = TickerPricesLive(
                    symbol=symbol.upper(),
                    price=price
                )
                self.session.add(price_record)
                logger.debug(f"Inserted new price record for {symbol}: {price}")

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to cache price for {symbol}: {e}", exc_info=True)
            return False

    def cache_multiple_prices(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Cache current prices for multiple symbols.

        Args:
            symbols: List of ticker symbols.

        Returns:
            Dictionary mapping symbol to success boolean.
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.cache_current_price(symbol)
        return results

    def get_cached_price(self, symbol: str) -> Optional[float]:
        """
        Get the cached price for a symbol from the database (if recent).

        Args:
            symbol: The ticker symbol.

        Returns:
            Cached price as float, or None if not cached or stale.
        """
        try:
            from sqlalchemy import select
            from datetime import datetime, timedelta

            cutoff_time = datetime.now() - timedelta(minutes=5)
            stmt = select(TickerPricesLive.price).where(
                TickerPricesLive.symbol == symbol.upper(),
                TickerPricesLive.updated_at >= cutoff_time
            )
            result = self.session.execute(stmt).scalar_one_or_none()
            return float(result) if result is not None else None
        except Exception as e:
            logger.error(f"Failed to get cached price for {symbol}: {e}")
            return None


# Convenience functions for quick use
def get_market_data_service(session: Session) -> MarketDataService:
    """
    Factory function to create a MarketDataService instance.

    Args:
        session: SQLAlchemy session.

    Returns:
        MarketDataService instance.
    """
    return MarketDataService(session)


def fetch_and_cache_price(session: Session, symbol: str) -> bool:
    """
    Convenience function to fetch and cache a single symbol's price.

    Args:
        session: SQLAlchemy session.
        symbol: Ticker symbol.

    Returns:
        True if successful, False otherwise.
    """
    service = MarketDataService(session)
    return service.cache_current_price(symbol)


# Example usage (for testing)
if __name__ == "__main__":
    # This is just a demo; remove or adapt for actual use.
    print("MarketDataService for fetching market data with tenacity retry.")
    print("To use, import and create an instance with a SQLAlchemy session.")