# Tactical Portfolio Engine - Development Status

## Project Philosophy: Signal vs. Noise
The previous iteration of this app was over-engineered. We are doing a "Soft Reset" of the frontend and logic layers while preserving the GCP/Cloud SQL infrastructure. 
**Core Mandates:**
1. **No Caching Nightmares:** All prices must display a visible "Last Fetched" timestamp.
2. **Simple Uploads:** Uploading a CSV wipes the old portfolio state and becomes the new "Single Source of Truth." No complex transaction math.
3. **Admin First:** The primary developer account must have Admin access to fix mappings globally.

---

## Phase 1: The Purge & Admin Access
- [ ] **Step 1: Clean the UI Slate.** Delete all broken UI placeholders on the TQQQ, Core, and Momentum pages. Strip the app down to a basic navigation sidebar.
- [ ] **Step 2: Fix Admin Access.** Modify the database or the `get_current_user()` logic so the primary developer email is recognized as `role='admin'`. Ensure the Settings page is accessible.
- [ ] **Step 3: Global Symbol Mapping.** Build a simple UI on the Settings page to add/edit/delete ticker mappings (e.g., `BRK/B` to `BRK-B`). 

## Phase 2: Data Foundations & Uploads
- [ ] **Step 1: Reliable Market Data.** Rip out unreliable cached `yfinance` calls. Implement a strict on-demand fetcher that returns a price and a `timestamp`. Ensure this timestamp is rendered in the UI anywhere a price is shown.
- [ ] **Step 2: Tastytrade API Prep (Optional/Pending).** Scaffold the connection utilities for the Tastytrade API to replace `yfinance`.
- [ ] **Step 3: Fidelity CSV Upload.** Rebuild the upload manager. Logic: Read CSV -> Wipe current holdings for user -> Insert new holdings. 
- [ ] **Step 4: Quant Ratings Upload.** Build a CSV uploader for Seeking Alpha Quant Ratings.
- [ ] **Step 5: Quant Freshness.** Add logic to globally discard/ignore Quant Ratings where `upload_date` is older than 7 days.

## Phase 3: TQQQ Manager (MVP)
- [ ] **Step 1: Indicators.** Calculate current price, 45-day EMA, 235-day EMA, and ADX (using a strict threshold of 25 to confirm trends).
- [ ] **Step 2: Dashboard UI.** Build a clean dashboard displaying these 4 metrics clearly.
- [ ] **Step 3: Action Logic.** Display explicit "Bullish", "Bearish", or "Wait" signals based on the EMA crossovers and ADX > 25 rule.

## Phase 4: Core vs. Momentum
- [ ] **Step 1: Portfolio Segmentation.** Update the UI to parse the uploaded portfolio into two distinct buckets: "Core" and "Momentum".
- [ ] **Step 2: Core View.** Build the Core dashboard. Show price, daily performance, and Quant Rating (if < 7 days old). Add placeholders for future Health Score/Earnings integrations.
- [ ] **Step 3: Momentum View.** Build the Momentum dashboard. Integrate legacy `logic_rules.py` to calculate trailing stops and automated triggers.
- [ ] **Step 4: Trigger Tracking.** Add a UI checkbox next to Momentum recommendations allowing the user to mark "Order placed at broker."

## Phase 5: Options Strategy Engine (Future Vision)
- [ ] *Pending MVP Completion.* Will include grouping by underlying, unassigned leg alerts, strategy assignment (Wheel, Spreads, Butterflies), Profit/Loss charts using live Bid/Ask, and "Gatekeeper" logic (Moneyness, IVR > 60) for alternative pivot recommendations.