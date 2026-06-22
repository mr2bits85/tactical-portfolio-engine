# Testing Plan for Tactical Portfolio Engine

This document outlines each feature of the application to be tested. Follow the format for each feature and fill in the Notes/Results section as you test.

---

Feature: Action Center Dashboard - Main interface showing market overview, priority signals, recent actions, and quick actions
How to Test: 
    Location - Home page (app.py)
    How to Test - Verify that the page loads without errors, displays SPY/QQQ/VIX metrics, shows priority signals tabs (Buy/Sell/Trail), recent actions tables, and quick action buttons are functional.
    Desired Outcome - All components load correctly, tabs switch without error, buttons trigger appropriate feedback (success/info messages), no JavaScript or Python errors appear in console.
Notes/Results:

---

Feature: Portfolio Holdings - View current holdings, tax-lot details, and drift indicators
How to Test: 
    Location - Navigate to Portfolio Holdings page (pages/1_Portfolio.py)
    How to Test - Check that the three tabs (Holdings, Tax-Lots, Drift Indicators) display sample data tables with correct column headers and that the tables are responsive (width='stretch'). Ensure no errors appear.
    Desired Outcome - Each tab shows a dataframe with appropriate sample data, tables stretch to container width, and interaction (sorting, if enabled) works.
Notes/Results:

---

Feature: Discovery Page - Watchlist management and entry analysis
How to Test: 
    Location - Discovery page (pages/4_Discovery.py)
    How to Test - Test the Watchlist tab: add a symbol via the form, verify it appears in the watchlist table, use refresh/analyze/clear buttons. Test the Entry Analysis tab: enter a symbol, click Analyze, verify technical/fundamental/strategy tabs load with sample data, and test watchlist actions from analysis tab.
    Desired Outcome - Form submissions succeed, tables update, buttons provide feedback (success/info), analysis tabs display sample data without errors.
Notes/Results:

---

Feature: TQQQ Manager - Dynamic 3-tier EMA strategy dashboard
How to Test: 
    Location - TQQQ Manager page (pages/3_TQQQ_Manager.py)
    How to Test - Verify the page loads and shows TQQQ price, EMA lines, ADX value, and active signals. Test the BUY/HOLD/SELL buttons (they should be disabled/enabled based on logic). Check that the dynamic state rendering components update based on market state (Bullish/Cautious/Bearish) and show appropriate stop-loss/target metrics.
    Desired Outcome - All metrics display correctly, buttons respond to state changes, state-specific components appear, no runtime errors.
Notes/Results:

---

Feature: Resolution Center - Symbol Mapping Issues tab
How to Test: 
    Location - Resolution Center page, Symbol Mapping tab (pages/2_Resolution_Center.py)
    How to Test - Run the bootstrap diagnostic (Refresh Diagnostics or Run Full Validation), verify the sample mapping issues table displays with Issue ID, Broker Symbol, Provider Symbol, etc. Test action buttons (Mark as Resolved, Notify Team, Export to CSV). Test the manual mapping form: select broker, enter symbols, submit, verify success message and form clears.
    Desired Outcome - Diagnostic runs without error, table shows sample data, action buttons give appropriate feedback, form validation works (error on missing fields, success on valid input), and submitted mapping appears as a success message.
Notes/Results:

---

Feature: Resolution Center - Drift Issues tab
How to Test: 
    Location - Resolution Center page, Drift Issues tab (pages/2_Resolution_Center.py)
    How to Test - Click Refresh Drift Scan, verify sample drift issues table displays with Issue ID, Account, Symbol, CSV/DB Quantities, Difference, Severity, etc. Test action buttons (Accept CSV as Correct, Accept DB as Correct, Enter Custom Values, Export to CSV). Test the drift resolution form: select symbol/account, enter quantities, choose action, fill notes, submit.
    Desired Outcome - Scan completes without error, table displays sample data, action buttons trigger success/info messages, form validates and submits successfully with appropriate success message.
Notes/Results:

---

Feature: Resolution Center - Adjusted Options tab
How to Test: 
    Location - Resolution Center page, Adjusted Options tab (pages/2_Resolution_Center.py)
    How to Test - Refresh options data, verify sample adjusted options table displays with Issue ID, OCC Symbol, Shares per Contract, Cash Deliverable, etc. Test action buttons (View Details, Export to CSV, Validate Contract). Test the add form: enter OCC symbol, underlying, option type, shares, strike, expiration, cash deliverable, description, submit.
    Desired Outcome - Data refresh works, table shows sample data, action buttons give feedback, form validates required fields and shows success on submit.
Notes/Results:

---

Feature: Admin Control Panels - System Settings tab
How to Test: 
    Location - Settings page (pages/5_Settings.py), System Settings tab
    How to Test - Adjust theme, default timeframe, enable notifications, set data refresh interval, enable cache, set cache TTL, toggle feature flags (TQQQ Manager, Advanced Charting, Paper Trading, API Access, Data Export, Backtesting). Click Save Settings button.
    Desired Outcome - All controls are interactive, Save Settings button shows success message, no errors occur.
Notes/Results:

---

Feature: Admin Control Panels - API Keys tab
How to Test: 
    Location - Settings page, API Keys tab
    How to Test - View the API keys table, click Add/Update API Key expander, select a service, enter an API key (can be dummy), optional description, click Save API Key. Test Yahoo Finance and Test All Connections buttons.
    Desired Outcome - Table displays sample data, expander opens/closes, form submission shows success (if key provided), test buttons show success/info messages.
Notes/Results:

---

Feature: Admin Control Panels - Database tab
How to Test: 
    Location - Settings page, Database tab
    How to Test - View connection information table, adjust pool settings (min/max connections, timeout, max retries), run maintenance tasks (Clean Old Logs, Update Statistics, Rebuild Indexes, Backup Database), click Save Database Settings.
    Desired Outcome - Tables show sample data, input controls accept values, maintenance task buttons show success messages, save button shows success.
Notes/Results:

---

Feature: Admin Control Panels - Symbol Translation Overrides tab
How to Test: 
    Location - Settings page, Symbol Mappings tab (new fourth tab)
    How to Test - View current symbol mappings table, click Add New Mapping button to open form, fill in broker name (select or custom), raw symbol, provider symbol, optional notes, submit. Test Export to CSV, Import from CSV, and Clear All Mappings buttons (note: Clear will show warning). Verify success messages and form clearing.
    Desired Outcome - Table displays sample mappings, add form validates required fields, submit shows success and clears form, export/import/clear buttons give appropriate feedback.
Notes/Results:

---
