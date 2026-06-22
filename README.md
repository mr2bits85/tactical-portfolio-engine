# Tactical Portfolio Engine

A high-precision Stock Portfolio Manager built with Python and Streamlit for Google Cloud Platform deployment.

## Overview

Tactical Portfolio Engine is a comprehensive portfolio management system designed to help traders and investors monitor market data, execute strategies, resolve data issues, and manage system configurations. The application follows a structured, phase-by-phase architecture and is deployed on Google Cloud Run using Cloud SQL for data persistence.

## Features

### 🎯 Action Center Dashboard (Main Interface)
- Real-time market overview (SPY, QQQ, VIX metrics)
- Priority signals dashboard with buy/sell/trail signals
- Recent actions and alerts system
- Quick action buttons for common operations
- Service integration (Strategy, Market Data, Global Context)

### 📊 Portfolio Holdings
- View current holdings with P/L calculations
- Tax-lot details tracking
- Drift indicators monitoring
- Interactive data tables with sorting and filtering

### 🔍 Discovery Page
- Watchlist management with add/remove functionality
- Price refresh and analysis tools
- Entry analysis with technical, fundamental, and strategy tabs
- Symbol search and evaluation capabilities

### ⚙️ TQQQ Manager
- Dynamic 3-tier EMA strategy dashboard
- Real-time EMA calculations (45-day and 230-day)
- Market state detection (Bullish, Cautious, Bearish)
- Actionable recommendations based on TQQQ rules
- Dynamic stop-loss and target calculations
- Visual state indicators and components

### 🔧 Resolution Center
**Active inbox for monitoring and resolving data issues:**
- **Symbol Mapping Issues**: View and fix failed symbol mappings with bootstrap diagnostics
- **Lot Drift Anomalies**: Monitor and resolve discrepancies between CSV and database lot data
- **Adjusted Options Management**: Handle non-standard options contracts
- Interactive resolution workflows with metrics, severity indicators, and timestamp tracking
- Export capabilities for further analysis

### ⚙️ Admin Control Panels
- System configuration settings (theme, timeframe, notifications, etc.)
- API key management for market data providers
- Database connection and pool settings
- Maintenance tasks (logs cleanup, statistics update, index rebuild, backup)
- **Symbol Translation Overrides**: Manage global symbol translation overrides in the ticker_mappings master table
- Add/edit/delete broker-to-provider symbol mappings with validation
- CSV import/export functionality for mapping data

## System Architecture

### Core Components
1. **MarketDataService** - Fetches market data using yfinance with tenacity exponential backoff and jitter
2. **StrategyService** - Implements Core, Income, Growth, and Momentum strategy logic
3. **GlobalContextService** - Implements "Anchor First" pattern for macro indices ($SPY, $QQQ, $VIX)
4. **BootstrapDiagnostic** - Validates market data provider connectivity and routes errors to system notifications
5. **DataProcessor** - Safely commits verified data chunks to transaction_lots and portfolio_snapshots
6. **DriftEngine** - Calculates discrepancies between physical reality (CSV) and database lots
7. **MacroGating** - Automatically freezes or suppresses volatile strategy signals based on macro data freshness

### Data Models
The application uses SQLAlchemy ORM with the following key tables:
- Users & UserTickerSettings
- BrokerageAccounts
- TransactionLots & PortfolioSnapshots
- TransactionHistory
- UserTargetWatchlists & RecommendationActions
- TickerMetadata, TickerPricesLive, TickerIndicators
- OptionInstruments, TickerQuantRatings
- MarketRegime, TickerMappings
- AdjustedOptionDefinitions
- SystemNotifications

## Technology Stack

### Backend
- Python 3.12
- Streamlit >=1.35.0 (web framework)
- Pandas >=2.2.0 & NumPy >=1.26.0 (data processing)
- YFinance >=0.2.40 & Tenacity >=9.0.0 (market data with retry logic)
- SQLAlchemy >=2.0.0,<3.0.0 (ORM)
- Google Cloud Secret Manager >=2.20.0 (secure configuration)

### Deployment
- Google Cloud Run (container orchestration)
- Google Cloud SQL PostgreSQL (database)
- Google Cloud Secret Manager (secrets management)
- Docker (containerization)
- Artifact Registry (image storage)

## Installation & Setup

### Local Development
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tactical-portfolio-engine
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (copy .env.example to .env and configure):
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Initialize the database:
   ```bash
   alembic upgrade head
   ```

5. Run the application:
   ```bash
   streamlit run app.py
   ```

### Docker Deployment
1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. Access the application at http://localhost:8501

### Google Cloud Run Deployment
1. Build and push the Docker image:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/tpe-repo/tactical-portfolio-engine
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy tactical-portfolio-engine \
     --image gcr.io/PROJECT_ID/tpe-repo/tactical-portfolio-engine \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. Set up Cloud SQL connection and Secret Manager integration as per CLAUDE.md

## Usage Guidelines

### Getting Started
1. Access the application at the deployed URL or locally at http://localhost:8501
2. Log in (in development mode, uses DEV_USER_EMAIL fallback)
3. Navigate through the sidebar to access different modules:
   - Action Center Dashboard (home)
   - Portfolio Holdings
   - Discovery
   - TQQQ Manager
   - Resolution Center
   - Settings (admin only)

### Key Workflows
1. **Market Monitoring**: Use Action Center Dashboard for real-time signals
2. **Portfolio Review**: Check Portfolio Holdings for current positions and P/L
3. **Strategy Evaluation**: Use TQQQ Manager for EMA-based strategy decisions
4. **Symbol Research**: Use Discovery page for watchlist management and analysis
5. **Issue Resolution**: Use Resolution Center to fix data discrepancies
6. **System Administration**: Use Settings page (admin only) for configuration management

## Configuration

### Environment Variables
Key environment variables (set in .env or Cloud Run):
- `TACTICAL_DATABASE_URL`: PostgreSQL connection string
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `DEV_USER_EMAIL`: Development user email fallback
- `USER_WHITELIST`: Comma-separated list of allowed emails (optional)

### Secret Manager
For production, store sensitive configuration in Google Cloud Secret Manager:
- Database credentials
- API keys for market data providers
- Other sensitive tokens

## Development

### Code Structure
- `app.py`: Main Action Center Dashboard
- `pages/`: Streamlit multipage application components
- `*.py` files in root: Core services and utilities
- `assets/style.css`: Centralized styling
- `archive/logic_rules.py`: Legacy strategy logic (reference)
- `models.py`: SQLAlchemy ORM models
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container configuration
- `docker-compose.yml`: Local development setup

### Contributing
1. Follow the existing code style and conventions
2. Maintain 100% full Python type hinting across custom service classes
3. Avoid inline CSS strings; use structural CSS classes/IDs in assets/style.css
4. Use highly explicit, descriptive naming conventions
5. Run validation tests after making adjustments
6. Update STATUS.md to reflect completed work

## Project Phases

The application was developed following a structured 5-phase approach:

### Phase 1: Database & Security Foundations
- Base SQLAlchemy model structures
- Google Secret Manager loading utility
- get_current_user() module with IAP/DEV_USER_EMAIL fallback
- Just-In-Time (JIT) user provisioning service

### Phase 2: Ingestion Pipeline & Normalization
- Broker CSV parser with asset_type extraction
- Bootstrap diagnostic engine for market data validation
- Data processing engine for transaction_lots and portfolio_snapshots
- Drift Engine for CSV/database lot discrepancy detection

### Phase 3: Market Data & Background Services
- MarketDataService with yfinance and tenacity retry logic
- Batch-resilient wrapper logic for ingestion batches
- GlobalContextService implementing "Anchor First" pattern
- Macro logic gating for volatile market conditions

### Phase 4: Strategy Engines & Dynamic UI Layouts
- Refactored StrategyService from legacy logic_rules.py
- Multi-page Streamlit directory architecture with centralized CSS
- TQQQ Manager Engine using 45-day and 230-day EMA tiers
- Dynamic front-end state rendering components for TQQQ Dashboard

### Phase 5: Resolution Center & Admin Controls
- Action Center Dashboard for high-priority trading signals
- Interactive Resolution Center UI for symbol mappings and drift issues
- Admin Control panels for global symbol translation overrides in ticker_mappings

## Future Enhancements

Potential areas for future development:
1. Advanced strategy implementations beyond Core/Income/Growth/Momentum
2. Enhanced backtesting capabilities
3. Improved alerting and notification systems
4. Mobile-responsive design improvements
5. Additional technical indicators and analysis tools
6. Portfolio optimization and risk management features
7. Integration with additional data sources and brokers
8. Automated report generation and export capabilities
9. Multi-user collaboration and sharing features
10. Advanced charting and visualization options

## License

This project is proprietary and confidential. All rights reserved.

## Contact

For questions or support regarding the Tactical Portfolio Engine, please refer to the project documentation or contact the development team.