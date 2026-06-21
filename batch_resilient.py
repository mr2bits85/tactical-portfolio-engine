"""
Batch-resilient wrapper logic to prevent single-ticker lookup failures
from halting ingestion batches.
Provides decorators and context managers for isolating failures in batch processing.
"""
import logging
import time
from typing import Callable, List, Any, TypeVar, Generic, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class BatchError(Exception):
    """Custom exception for batch processing errors."""
    def __init__(self, item: Any, exception: Exception):
        self.item = item
        self.exception = exception
        super().__init__(f"Error processing item {item}: {exception}")


def resilient_batch(
    default_return: Any = None,
    log_errors: bool = True,
    raise_on_error: bool = False,
    error_callback: Optional[Callable[[Any, Exception], None]] = None
):
    """
    Decorator to make a function resilient to errors when processing batches.
    Each item in the batch is processed independently, and errors are caught
    and logged without stopping the entire batch.

    Args:
        default_return: Value to return for failed items (default: None)
        log_errors: Whether to log errors (default: True)
        raise_on_error: Whether to raise an exception after processing batch if any errors occurred (default: False)
        error_callback: Optional callback function called with (item, exception) for each error

    Returns:
        Decorated function that processes batches resiliently
    """
    def decorator(func: Callable[[T], R]) -> Callable[[List[T]], List[R]]:
        @wraps(func)
        def wrapper(batch: List[T]) -> List[R]:
            results = []
            errors = []

            for i, item in enumerate(batch):
                try:
                    result = func(item)
                    results.append(result)
                except Exception as e:
                    if log_errors:
                        logger.warning(
                            f"Error processing batch item {i} ({item}): {e}",
                            exc_info=True
                        )
                    if error_callback:
                        try:
                            error_callback(item, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Error in error callback for item {item}: {callback_error}"
                            )
                    errors.append((item, e))
                    results.append(default_return)

            if errors and raise_on_error:
                # Raise a summary exception
                raise BatchError(
                    item=f"{len(errors)} errors in batch of {len(batch)} items",
                    exception=Exception(f"Batch processing failed with {len(errors)} errors")
                )

            return results
        return wrapper
    return decorator


def resilient_processor(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator that adds retry logic with exponential backoff to a function,
    making it resilient to transient failures.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        exceptions: Tuple of exception types to catch and retry on (default: (Exception,))

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> R:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )

            # If we get here, all retries failed
            raise last_exception
        return wrapper
    return decorator


class BatchProcessor(Generic[T, R]):
    """
    A class-based batch processor that combines resilience and retry logic.
    """

    def __init__(
        self,
        process_func: Callable[[T], R],
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        default_return: Any = None,
        log_errors: bool = True
    ):
        """
        Initialize the batch processor.

        Args:
            process_func: Function to process each item
            max_retries: Max retry attempts per item
            delay: Initial delay between retries
            backoff_factor: Delay multiplier after each retry
            default_return: Value to return for failed items
            log_errors: Whether to log errors
        """
        self.process_func = process_func
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.default_return = default_return
        self.log_errors = log_errors

    def process_item_with_retry(self, item: T) -> R:
        """
        Process a single item with retry logic.

        Args:
            item: The item to process

        Returns:
            Processed result or default_return if all retries fail
        """
        last_exception = None
        current_delay = self.delay

        for attempt in range(self.max_retries + 1):
            try:
                return self.process_func(item)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    if self.log_errors:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for item {item}: {e}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                    time.sleep(current_delay)
                    current_delay *= self.backoff_factor
                else:
                    if self.log_errors:
                        logger.error(
                            f"All {self.max_retries + 1} attempts failed for item {item}: {e}"
                        )

        return self.default_return

    def process_batch(self, batch: List[T]) -> List[R]:
        """
        Process a batch of items, each with independent retry logic.

        Args:
            batch: List of items to process

        Returns:
            List of processed results
        """
        results = []
        for i, item in enumerate(batch):
            try:
                result = self.process_item_with_retry(item)
                results.append(result)
            except Exception as e:
                if self.log_errors:
                    logger.error(
                        f"Unexpected error processing batch item {i} ({item}): {e}",
                        exc_info=True
                    )
                results.append(self.default_return)
        return results


# Pre-configured resilient wrappers for common market data operations
def make_resilient_price_fetcher(price_func: Callable[[str], Optional[float]]) -> Callable[[List[str]], List[Optional[float]]]:
    """
    Create a resilient batch price fetcher from a single price fetcher function.

    Args:
        price_func: Function that takes a symbol and returns a price or None

    Returns:
        Function that takes a list of symbols and returns list of prices
    """
    @resilient_batch(default_return=None, log_errors=True)
    def fetch_price(symbol: str) -> Optional[float]:
        return price_func(symbol)

    return fetch_price


def make_resilient_info_fetcher(info_func: Callable[[str], Optional[Dict[str, Any]]]) -> Callable[[List[str]], List[Optional[Dict[str, Any]]]]:
    """
    Create a resilient batch info fetcher from a single info fetcher function.

    Args:
        info_func: Function that takes a symbol and returns info dict or None

    Returns:
        Function that takes a list of symbols and returns list of info dicts
    """
    @resilient_batch(default_return=None, log_errors=True)
    def fetch_info(symbol: str) -> Optional[Dict[str, Any]]:
        return info_func(symbol)

    return fetch_info


# Example usage (for testing)
if __name__ == "__main__":
    # This is just a demo; remove or adapt for actual use.
    print("Batch-resilient wrapper logic for preventing single failures from halting batches.")
    print("To use, import the decorators or BatchProcessor class.")