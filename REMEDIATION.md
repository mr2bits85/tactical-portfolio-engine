# Critical Architecture Remediation: Data Pipeline & Hydration

## Goal
The application is currently failing to utilize the `MarketDataService` for live data. It relies on mock data in `app.py` and bypasses the service layer in `pages/3_TQQQ_Manager.py`. This plan wires the established data services to the Streamlit frontend.

## Step 1: Eradicate Mock Data
- [ ] In `app.py`, completely remove the try/except block generating mock data for SPY, QQQ, and VIX.
- [ ] In `pages/3_TQQQ_Manager.py`, remove all direct `yfinance` imports and direct API calls.

## Step 2: Implement On-Demand Hydration Trigger
- [ ] In `app.py`, locate the "Refresh All Data" button logic. 
- [ ] Update the button logic so that clicking it directly calls `global_context_service.update_anchor_metrics()`.
- [ ] Implement a Streamlit caching mechanism (e.g., `@st.cache_data(ttl=300)`) attached to a function that runs `global_context_service.update_anchor_metrics()` when the application initially loads or when the cache expires (5-minute TTL).

## Step 3: Wire Frontend to the Database
- [ ] In `app.py`, replace the mock variable assignments with calls to `global_context_service.get_latest_indicator(symbol, "price")`. 
- [ ] Calculate the daily change percentage mathematically and format it for the `st.metric` UI components.

## Step 4: Enforce Service Layer in TQQQ Manager
- [ ] Refactor `pages/3_TQQQ_Manager.py` so that all price and EMA data fetches route exclusively through the initialized `MarketDataService` and `GlobalContextService`.

## Step 5: Activate Macro Gating
- [ ] Apply the currently unused `@require_fresh_macro_data` decorator (from `macro_gating.py`) to the core signal-generation functions. 
- [ ] Ensure the application explicitly blocks or flags trading logic in the UI if the anchor data fails to hydrate.