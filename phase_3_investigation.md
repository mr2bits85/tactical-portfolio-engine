# Phase 3 Investigation: Market Data & Background Services

This document investigates each task in Phase 3 of the Project Ledger to verify completion status, locate primary code, and outline testing procedures.

## Task 3.1: Build the core `MarketDataService` calling third-party APIs (`yfinance`), utilizing the `tenacity` retry framework with Exponential Backoff + Jitter (Initial: 1s, Max: 60s). Cloud Run Jobs via Cloud Scheduler preferred for batching.

- **Completion Status**: Yes (Implemented)
- **Primary Code Location**: `market_data_service.py` - `MarketDataService` class
- **How to Test in App**:
  1. Ensure `yfinance` and `tenacity` are installed (`pip install yfinance tenacity`).
  2. Obtain a database session (e.g., via the app's context or by creating a session factory).
  3. Instantiate `MarketDataService(session)`.
  4. Call `get_current_price('AAPL')` and verify it returns a float (or None if the symbol is invalid or service unavailable).
  5. Test the retry mechanism by simulating a temporary network failure (e.g., by mocking `yfinance.Ticker` to raise an exception initially then succeed).
  6. Verify that the service caches prices in the `ticker_prices_live` table via `cache_current_price`.
  7. Check that `get_cached_price` returns the cached value if recent (within 5 minutes) and None if stale.
  8. Test batch pricing with `cache_multiple_prices`.

## Task 3.2: Implement safe batch-resilience ingestion structure using scoped try-except blocks.

- **Completion Status**: Yes (Implemented)
- **Primary Code Location**: `batch_resilient.py` - `resilient_batch` decorator, `resilient_processor` decorator, and `BatchProcessor` class
- **How to Test in App**:
  1. Create a function that processes an item and may fail (e.g., a function that divides by zero for certain inputs).
  2. Apply the `@resilient_batch(default_return=None, log_errors=True)` decorator to a function that processes a list of items.
  3. Call the decorated function with a mixed list of valid and invalid items.
  4. Verify that:
     - The function returns a list of results with the same length as the input.
     - Failed items return the `default_return` value (None).
     - Errors are logged (check log output).
     - The batch processing continues despite individual failures.
  5. Test the `resilient_processor` decorator similarly, which adds retry logic with exponential backoff.
  6. Test the `BatchProcessor` class by instantiating it with a processing function and calling `process_batch`.

## Task 3.3: Build the `GlobalContextService` (**Anchor First Pattern**). Update macro tickers (SPY, QQQ, VIX) directly into the `market_regime` table before portfolio evaluation. Suppress Momentum/Growth signals if this fetch fails.

- **Completion Status**: Partial (Implemented data storage but signal suppression not yet connected)
- **Primary Code Location**: 
  - Data storage: `global_context_service.py` - `GlobalContextService` class
  - Signal suppression mechanism: `macro_gating.py` - `require_fresh_macro_data` decorator and `MacroGate` class
- **How to Test in App**:
  1. **Testing Data Storage (Part 1)**:
     - Ensure `yfinance` is installed.
     - Obtain a database session.
     - Instantiate `GlobalContextService(session)`.
     - Call `update_anchor_metrics()` and verify that it returns a dictionary with results for each anchor symbol.
     - Check the `market_regime` table for new entries with `anchor_symbol` in ('SPY', 'QQQ', 'VIX') and `indicator_name` = 'price' (or other indicators if extended).
     - Verify that calling the method again updates existing recent entries (within 5 minutes) rather than duplicating.
     - Test `get_latest_indicator('SPY', 'price')` to retrieve the cached value.
  2. **Testing Signal Suppression (Part 2)**:
     - The `GlobalContextService` does not currently suppress signals directly; this is intended to be handled by integrating the macro gating with strategy evaluation.
     - To test the suppression mechanism:
       a. Use the `require_fresh_macro_data` decorator on a sample function that simulates signal generation.
       b. Provide a database session where the `market_regime` table has no recent entries for the anchor symbols (or stale entries).
       - Call the decorated function and verify it returns the `default_return` (or does not execute if `fail_open=False`).
       c. Populate the `market_regime` table with fresh data (within `max_age_minutes`) and verify the function executes normally.
       d. Test the `MacroGate` context manager similarly.
     - However, as of the current codebase, the strategy evaluation (`StrategyService.evaluate_*_rules`) is not wrapped with macro gating, and the context passed to the strategy evaluation does not appear to be populated with data from `market_regime` (e.g., `QQQ_ADX_14`). This connection is missing.
     - To fully test the intended behavior, one would need to:
        1. Ensure that before evaluating strategy rules, the application fetches the latest macro indicators from `market_regime` (via `GlobalContextService`) and includes them in the context dictionary.
        2. Apply the `require_fresh_macro_data` decorator (or use `MacroGate`) to the strategy evaluation functions, setting `fail_open=False` and an appropriate `default_return` (e.g., returning a signal to hold or suppress).
        3. Verify that when macro data is stale (or fetch fails), the strategy evaluation returns suppressed signals (e.g., no buy/sell signals for Momentum/Growth categories).
     - A specific test case:
        - Simulate a failure to fetch macro data (e.g., by temporarily disabling the database connection or emptying the `market_regime` table).
        - Attempt to evaluate a Momentum strategy context (which currently includes a check for `QQQ_ADX_14 < 20`).
        - Without the macro data in the context, the `QQQ_ADX_14` key would be missing, causing a KeyError or defaulting to None (depending on how the context is built). The current `StrategyService` does not handle missing keys gracefully in all places (e.g., `context.get('QQQ_ADX_14', 0)` would return 0 if missing, which would trigger the suppression because 0 < 20). This is a partial accidental protection but not robust.
        - The intended design is likely to have the macro data available in the context when fresh, and to short-circuit the evaluation entirely when macro data is stale (returning a suppression signal without evaluating the strategy rules).

## Summary of Findings

- **Task 3.1**: Fully implemented. The `MarketDataService` provides robust data fetching with retry and caching.
- **Task 3.2**: Fully implemented. The `batch_resilient.py` module provides decorators and a class for resilient batch processing.
- **Task 3.3**: Partially implemented.
  - The `GlobalContextService` successfully updates the `market_regime` table with anchor symbol data (price and potentially other indicators).
  - The `macro_gating.py` module provides the tools (`require_fresh_macro_data` decorator and `MacroGate` class) to gate execution based on macro data freshness.
  - However, the integration between the `GlobalContextService` (data storage) and the signal suppression (via `macro_gating`) is not yet connected in the application flow. Specifically:
    - The strategy evaluation functions (`StrategyService.evaluate_*_rules`) are not decorated with macro gating.
    - The context passed to strategy evaluation does not appear to be systematically enriched with data from `market_regime` (e.g., `QQQ_ADX_14`, `SPY_RSI_14`, etc.).
    - As a result, the automatic suppression of Momentum/Growth signals when macro data fetch fails is not currently active.
  - To complete this task, the application needs to:
    1. Create a service or function that, before evaluating strategies, queries the `market_regime` table for the latest indicator values for the anchor symbols and adds them to the context dictionary (using predefined keys like `QQQ_ADX_14`, `SPY_RSI_14`, etc.).
    2. Apply the `require_fresh_macro_data` decorator (or equivalent logic) to the strategy evaluation entry points, ensuring that if macro data is stale or unavailable, the strategy evaluation returns a suppressed signal (e.g., `(0, 0, 'MACRO_DATA_STALE')` for buy/sell evaluations).

## Recommendations for Completion

To fully complete Task 3.3:

1. **Create a Context Builder Service**: Implement a function or class that, given a database session, retrieves the latest indicators from `market_regime` for the anchor symbols and returns a dictionary mapping indicator names to values (e.g., `{'QQQ_ADX_14': 25.5, 'SPY_RSI_14': 58.2, ...}`). This service should handle missing data gracefully (e.g., return None or a default if an indicator is not available).

2. **Integrate Macro Gating**: 
   - Decorate the strategy evaluation methods (or the functions that call them) with `@require_fresh_macro_data(fail_open=False, default_return=(0, 0, 'MACRO_DATA_STALE'))` for buy/sell evaluations, or implement similar logic inside a wrapper.
   - Alternatively, modify the application flow to check macro data freshness before proceeding to the macro data is stale, skip strategy evaluation and return a signal indicating that trading is suspended due to unstable market conditions.

3. **Update Strategy Service (Optional)**: Enhance the `StrategyService` to optionally accept a pre-built context (or fetch macro data internally) and to have a built-in check for macro data availability that overrides individual rule evaluations.

By implementing these steps, the system will achieve the goal of suppressing Momentum/Growth signals when the anchor data fetch fails, as specified in the Project Ledger.