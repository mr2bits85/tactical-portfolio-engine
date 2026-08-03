# Phase 2 Investigation: Ingestion Pipeline & Normalization

This document investigates each task in Phase 2 of the Project Ledger to verify completion status, locate primary code, and outline testing procedures.

## Task 2.1: Build a robust CSV parser targeting broker-provided files. Ensure records parse `asset_type` fields seamlessly.

- **Completion Status**: Yes (Implemented)
- **Primary Code Location**: `csv_parser.py` - `BrokerCSVParser` class
- **How to Test in App**:
  1. Prepare a sample CSV file with broker data (e.g., Fidelity or E-Trade format) containing columns for symbol, quantity, price, date, and optionally asset type.
  2. Use the parser via `create_fidelity_parser()` or `create_e_trade_parser()` to parse the file.
  3. Verify that the returned list of dictionaries includes correct asset_type (EQUITY/OPTION) for each row.
  4. Check that the parser handles missing asset_type column by inferring from other columns (e.g., presence of strike/expiration).
  5. Test edge cases: missing values, different date formats, numeric values with commas.

## Task 2.2: Option Regex Normalization: Implement regex parsing `^([A-Z0-9]+)\s+(\d{2}/\d{2}/\d{4})\s+(\d+\.\d+)\s+([CP])$` to handle non-standard broker symbols (Supports formats like `SQQQ2`, `VISN1`).

- **Completion Status**: No (Not Implemented)
- **Primary Code Location**: Not found in codebase.
- **How to Test in App**:
  1. This regex appears intended to parse raw option strings from a source (possibly notes or alternative feeds) that contain the underlying symbol, expiration date, strike price, and call/put indicator in a single string.
  2. To test, one would need to integrate this regex into a service that processes such strings (e.g., when extracting option data from user notes or alternative data feeds).
  3. Since no implementation exists, testing is not currently possible. Implementation would involve creating a utility function that applies the regex to input strings and returns parsed components (symbol, date, strike, put/call).

## Task 2.3: Bootstrap & Diagnostic Task: Write a test engine that validates raw CSV strings against data providers. Route mapping failures to `system_notifications.metadata`.

- **Completion Status**: Partial (Implemented provider validation but missing mapping validation)
- **Primary Code Location**: `bootstrap_diagnostic.py` - `BootstrapDiagnostic` class and `run_bootstrap_diagnostic` function
- **How to Test in App**:
  1. The current implementation validates symbols against market data providers (yfinance) and logs failures to `system_notifications` with category `provider_fetch_failed`.
  2. However, it does not validate raw CSV strings against the `ticker_mappings` table to check for missing mappings.
  3. To test the existing functionality:
     - Ensure yfinance is installed (`pip install yfinance`).
     - Obtain a database session (e.g., via the app's context).
     - Call `run_bootstrap_diagnostic(session, ['AAPL', 'MSFT', 'INVALID'])`.
     - Check the `system_notifications` table for entries with `category='provider_fetch_failed'` for the invalid symbol.
  4. To test the missing mapping validation:
     - There is currently no way to test because the mapping lookup step is absent.
     - Implementation would require: before validating a symbol against the provider, check if the raw symbol (from CSV) has a mapping in `ticker_mappings`. If not, log a `mapping_failure` notification with metadata containing the raw symbol and broker context.

## Task 2.4: Build the core processing engine to commit verified data chunks to `transaction_lots` and `portfolio_snapshots`.

- **Completion Status**: Yes (Implemented)
- **Primary Code Location**: `data_processor.py` - `process_transaction_lots` and `process_portfolio_snapshots` functions
- **How to Test in App**:
  1. Prepare a list of dictionaries representing transaction lots (with keys: portfolio_id, symbol, asset_type, quantity, purchase_price, purchase_date) and portfolio snapshots (account_id, symbol, asset_type, total_quantity, capture_date).
  2. Obtain a database session.
  3. Call `process_transaction_lots(session, lots_data)` and verify that rows are inserted into the `transaction_lots` table.
  4. Call `process_portfolio_snapshots(session, snapshots_data)` and verify insertion into `portfolio_snapshots`.
  5. Test error handling by providing invalid data (e.g., missing required fields, duplicate primary keys) and ensure errors are logged and transactions rolled back.

## Task 2.5: Build the Drift Engine: Compare physical reality (CSV totals) with recorded lots. If data points diverge (< $0.0001 shares or < $0.01), mark for review. Supersede historical drift records upon clean CSV updates.

- **Completion Status**: Yes (Implemented)
- **Primary Code Location**: `drift_engine.py` - `DriftEngine` class and `run_drift_check` function
- **How to Test in App**:
  1. Set up a test scenario with known database lots for an account/symbol.
  2. Provide a CSV total quantity that differs from the database sum by a known amount (both within and outside thresholds).
  3. Call `run_drift_check(session, account_id, symbol, csv_total_quantity, csv_total_value)`.
  4. Verify that:
     - If difference is within thresholds (quantity < 0.0001 shares, value < $0.01), no notification is created and any existing unresolved drift notification for the same account/symbol is marked as resolved.
     - If difference exceeds thresholds, a new `system_notifications` entry with `category='data_discrepancy'` is created, containing metadata with the differences.
  5. Test edge cases: missing CSV total value, zero database totals, negative quantities.

## Summary of Findings

- Tasks 2.1, 2.4, and 2.5 are fully implemented.
- Task 2.2 (Option Regex Normalization) is not implemented at all.
- Task 2.3 (Bootstrap & Diagnostic Task) is partially implemented: it validates symbols against data providers but does not check for missing symbol mappings via the `ticker_mappings` table. The mapping validation step is missing.