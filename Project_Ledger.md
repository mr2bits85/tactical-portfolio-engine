# Project Blueprint: Tactical Portfolio Engine

## 1. System Architecture & UI Specifications

### 1.1 Infrastructure & Deployment
* **Infrastructure**: Google Cloud Platform (GCP).
* **Runtime**: Cloud Run (Dockerized Python/Streamlit).
* **Scale Target**: Minimal footprint optimized entirely for a small user base of approximately 2 active users.
* **Database**: Cloud SQL (PostgreSQL).
* **CI/CD**: Git-triggered builds via Cloud Build. Manual migrations are managed via Alembic using a specific `MIGRATE=true` build flag to preserve environmental isolation.

### 1.2 Authentication & Identity (Native Cloud Run IAP)
* **Mechanism**: Native Google Identity-Aware Proxy (IAP) enabled directly on the Cloud Run service instance. No external HTTPS Load Balancer or Serverless Network Endpoint Group (NEG) is utilized.
* **Identity Injection**: Native IAP provides the verified user's identity via the standard `x-goog-authenticated-user-email` header.
* **Local Development Fallback**: A `get_current_user()` utility checks for the IAP header; if missing, it defaults to a `DEV_USER_EMAIL` environment variable.
* **JIT Provisioning**: The app automatically creates a `users` record on the first successful IAP-authenticated request from a whitelisted email. The primary developer email must be manually elevated to `role='admin'` via direct SQL to enable cross-user resolution and global mapping capabilities.

### 1.3 Secret Management
* **Storage**: All sensitive data (API Keys, DB Credentials) are stored in **Google Secret Manager**.
* **Access**: Cloud Run service account uses `Secret Manager Secret Accessor` roles; no `.env` files are stored in production code.

### 1.4 Frontend Code Quality & Styling
* **No Inline Styling**: Complete ban on inline CSS injections or hardcoded style strings inside Streamlit Python code blocks.
* **Centralized Stylesheet**: The layout loads a single, external stylesheet (`assets/style.css`) at the application root. Component styling uses structured Markdown elements wrapped in containers utilizing strict CSS classes or IDs for a reliable, alterable visual theme.
* **Strict Typing**: All backend code must implement full Python type hinting, use highly explicit variable names (avoiding generic abbreviations), and pass immutable data structures or standardized Pydantic models between service layers.

---

## 2. Consolidated Database Schema (Future-Proofed)

### Tier 1: Identity & Transactional (User Data)
| Table | Description | Key Fields |
| :--- | :--- | :--- |
| **`users`** | Profile and role management. | `id`, `email`, `role` (admin/user), `created_at` |
| **`user_ticker_settings`** | Personal strategy (category) per symbol. | `user_id`, `symbol`, `category`, `custom_stop_loss`, `notes` |
| **`brokerage_accounts`** | Data source tracking (Fidelity, E-Trade). | `id`, `user_id`, `broker_name`, `account_hash` |
| **`transaction_lots`** | Granular tax-lot tracking for *active open positions*. Future-proofed for choices beyond equities. | `id` (Serial PK), `portfolio_id`, `symbol`, `asset_type` (EQUITY/OPTION), `quantity`, `purchase_price`, `purchase_date` |
| **`portfolio_snapshots`** | Point-in-time "Physical Reality" from uploaded broker CSV. | `id`, `account_id`, `symbol`, `asset_type`, `total_quantity`, `capture_date` |
| **`transaction_history`** | *[FUTURE PROOF]* Historical log of all closed trades to calculate cumulative symbol gains. | `id`, `account_id`, `symbol`, `action` (BUY/SELL), `quantity`, `price`, `execution_date`, `realized_gain_loss`, `notes` |
| **`user_target_watchlists`** | *[FUTURE PROOF]* Customizable tracking list for current or watched asset targets. | `id`, `user_id`, `symbol`, `custom_buy_target`, `is_monitored` (Boolean), `created_at` |
| **`recommendation_actions`** | *[FUTURE PROOF]* Logs when a user acknowledges or acts on a strategy signal. | `id`, `user_id`, `symbol`, `action_type`, `recommended_price`, `custom_action_details`, `timestamp`, `notes` |

### Tier 2: Global Market Data & Macro Regime
* **`ticker_metadata`**: Static asset info (`symbol`, `name`, `sector`).
* **`ticker_prices_live`**: Current stock metrics with 1-5 minute updates (`symbol`, `price`, `updated_at`).
* **`ticker_indicators`**: Pre-calculated technical indicators (`symbol`, `rsi`, `macd`, `sma_50`, `sma_100`, `atr`).
* **`option_instruments`**: Standardized OCC strings and Greeks.
* **`ticker_quant_ratings`**: *[FUTURE PROOF]* Houses uploaded Seeking Alpha metric data linked across asset views.
* **`market_regime`**: Single row per macro asset (QQQ, SPY, VIX) to evaluate broader market conditions efficiently (`anchor_symbol`, `indicator_name`, `indicator_value`, `calculated_at`).

### Tier 3: Support Tables
| Table | Description | Key Fields |
| :--- | :--- | :--- |
| **`ticker_mappings`** | **Global**: Maps variable broker export strings directly to provider data standards. | `broker_name`, `raw_symbol`, `provider_symbol` |
| **`adjusted_option_definitions`**| Manual overrides for non-standard contracts. | `id`, `occ_symbol`, `shares_per_contract`, `cash_deliverable` |
| **`system_notifications`** | Log of failed provider fetches, unmapped symbols, or structural data discrepancies. | `id`, `category`, `is_resolved`, `metadata` (JSONB) |

---

## 3. Phased Development Roadmap

### Phase 1: Database & Security Foundations
* **Objective**: Establish the core runtime, database connections, and secure auth layers.
* **Tasks**:
  1. Build the base SQLAlchemy model structures for all Tier 1, 2, and 3 schemas.
  2. Implement the Secret Manager loading logic to securely provision runtime configurations.
  3. Create the `get_current_user()` module for native IAP headers and JIT provisioning.

### Phase 2: Ingestion Pipeline & Normalization
* **Objective**: Parse broker data streams safely, map irregular symbols, and handle structural tracking differences.
* **Tasks**:
  1. Build a robust CSV parser targeting broker-provided files. Ensure records parse `asset_type` fields seamlessly.
  2. **Option Regex Normalization**: Implement regex parsing `^([A-Z0-9]+)\s+(\d{2}/\d{2}/\d{4})\s+(\d+\.\d+)\s+([CP])$` to handle non-standard broker symbols (Supports formats like `SQQQ2`, `VISN1`).
  3. **Bootstrap & Diagnostic Task**: Write a test engine that validates raw CSV strings against data providers. Route mapping failures to `system_notifications.metadata`.
  4. Build the core processing engine to commit verified data chunks to `transaction_lots` and `portfolio_snapshots`.
  5. Build the **Drift Engine**: Compare physical reality (CSV totals) with recorded lots. If data points diverge ($< 0.0001$ shares or $< \$0.01$), mark for review. Supersede historical drift records upon clean CSV updates.

### Phase 3: Market Data & Background Services
* **Objective**: Establish reliable data hydration routines while working within provider request limits.
* **Tasks**:
  1. Build the core `MarketDataService` calling third-party APIs (`yfinance`), utilizing the `tenacity` retry framework with Exponential Backoff + Jitter (Initial: 1s, Max: 60s). Cloud Run Jobs via Cloud Scheduler preferred for batching.
  2. Implement safe batch-resilience ingestion structure using scoped try-except blocks.
  3. Build the `GlobalContextService` (**Anchor First Pattern**). Update macro tickers (SPY, QQQ, VIX) directly into the `market_regime` table before portfolio evaluation. Suppress Momentum/Growth signals if this fetch fails.

### Phase 4: Strategy Engines & Dynamic UI Layouts
* **Objective**: Transform historical calculation rules into dynamic frontend dashboards.
* **Tasks**:
  1. **Legacy Refactor**: Port `logic_rules.py` math into a type-hinted `StrategyService` class.
  2. **Standardized Outputs & Tax Awareness**: Ensure `StrategyService` returns a standardized Recommendation JSON object (target_price, stop_price, logic_name, is_alert, status_color) and utilizes `purchase_date` to identify Short-Term vs. Long-Term tax status.
  3. **Adjusted Options Engine**: Integrate overrides from `adjusted_option_definitions` for non-standard contracts (`shares_per_contract`, `cash_deliverable`) and explicitly tag them as **[ADJUSTED]** in the UI.
  4. **TQQQ/TMF Manager Implementation**: Treat exposure tiers as real-time calculated values on page load to prevent state drift. Calculate using: `Exposure Tier = Sum(Active EMA Signals)` based on 45-day and 230-day EMAs.
  5. Implement dynamic states on the TQQQ dashboard (Bullish, Cautious, Bearish) with explicit visual prompts and targeted stop-on-quote recommendations.

### Phase 5: Resolution Center & Admin Controls
* **Objective**: Provide centralized monitoring, diagnostics, and data control panels.
* **Tasks**:
  1. Build the **Action Center Dashboard** (`app.py`) for priority signals and trailing targets.
  2. Build the **Resolution Center interface** mapping inbox tasks.
  3. Provide admin panels for global overrides into `ticker_mappings`.

---

## 4. Streamlit Frontend Sitemap

The application will follow this explicit multi-page architecture:
* **`app.py` (Action Center)**: Priority Buy/Sell/Trail signals and core dashboard.
* **`pages/1_Portfolio.py`**: Holdings, Tax-lots, and Drift indicators.
* **`pages/2_Resolution_Center.py`**: Manual fixes for all data issues (Mapping, Drift, Adjusted Options).
* **`pages/3_TQQQ_Manager.py`**: Dynamic 3-tier EMA strategy dashboard.
* **`pages/4_Discovery.py`**: Watchlist and Entry Analysis.
* **`pages/5_Settings.py`**: Admin controls and System Health.