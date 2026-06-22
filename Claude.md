I am building a high-precision Stock Portfolio Manager named 'Tactical Portfolio Engine' using Python and Streamlit on GCP Cloud Run. You will use Alembic to handle table creation in Google Cloud SQL.  We are strictly following the structured, phase-by-phase architecture defined in the attached Project_Ledger.md file.

All progress on app development will be guided by and tracked through STATUS.md.  All development should follow the STATUS.md workflow.  Each item in the STATUS.md file must be worked on in order, and then STATUS.md must be updated to mark off completed steps or where work was left off and update progress before moving to the next item in the STATUS.md file.  

I have also attached our legacy `logic_rules.py` file, which contains the math algorithms for our legacy Core, Income, Growth, and Momentum strategy logic.



# Tactical Portfolio Engine - System Guardrails

## Core Execution Commands
- Run Streamlit App: `streamlit run app.py`
- Run DB Migrations: `alembic upgrade head`
- Execution Pattern: Always run validation tests after making adjustments.

## Strict Code Style Rules
- CRITICAL: Implement 100% full Python type hinting across all custom service classes.
- CRITICAL: Absolute ban on inline CSS strings within Streamlit text components. Custom visual layouts must map strictly to structural CSS classes or IDs managed inside `assets/style.css`.
- Variables and modules must implement highly explicit, descriptive naming conventions (completely avoid brief or generic abbreviations like `t_qty`).

## Deployment Architecture (GCP Reference)
- Project ID: active-trade-manager
- Deploy Region: us-central1
- Artifact Registry: us-central1-docker.pkg.dev/active-trade-manager/tpe-repo
- Cloud SQL Instance: active-trade-manager:us-central1:trade-db
- Target Database Name: tactical_portfolio_db
- Cloud Run Service Name: tactical-portfolio-engine
- Secret Manager Key: TACTICAL_DATABASE_URL=TACTICAL_DATABASE_URL:latest