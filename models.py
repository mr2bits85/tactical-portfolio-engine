from sqlalchemy import Integer, String, Float, DateTime, Date, Boolean, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
import datetime


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default='user')  # admin or user
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())


class UserTickerSettings(Base):
    __tablename__ = 'user_ticker_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to users.id
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., Core, Income, Growth, Momentum
    custom_stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship (optional)
    # user: Mapped["Users"] = relationship("Users", back_populates="ticker_settings")


class BrokerageAccounts(Base):
    __tablename__ = 'brokerage_accounts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to users.id
    broker_name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., Fidelity, E-Trade
    account_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # hashed account number for security


class TransactionLots(Base):
    __tablename__ = 'transaction_lots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # portfolio_id: Mapped[int] = mapped_column(Integer, nullable=False)  # We don't have a portfolio table? Maybe we link to user? Or we can have a portfolio per user? Let's see the ledger: it says portfolio_id but we don't have a portfolio table. We might need to create a portfolio table? However, the ledger doesn't list a portfolio table. We'll leave it as a foreign key to a portfolio table that we might create later? Or we can link to user_id? Let's re-examine the ledger.

    # According to the ledger: transaction_lots has portfolio_id. We don't have a portfolio table defined. We might need to create one? Or perhaps portfolio_id is the user_id? Let's think: each user can have multiple portfolios? The ledger doesn't specify. We'll assume that portfolio_id is a foreign key to a portfolio table that we will create in the future? But the task says to build the base model structures for all Tay 1, 2, and 3 tables. We don't see a portfolio table in the ledger. We'll leave portfolio_id as an integer for now and note that it might be a foreign key to a portfolio table that we will define later? Alternatively, we can remove it and link to user_id? Let's check the ledger again:

    # Table: transaction_lots
    # Description: Granular tax-lot tracking for *active open positions*. Future-proofed for choices beyond equities.
    # Key Fields: id (Serial PK), portfolio_id, symbol, asset_type (EQUITY/OPTION), quantity, purchase_price, purchase_date

    # We don't have a portfolio table. We'll create a portfolio table? But it's not in the ledger. We'll assume that portfolio_id is the user_id? Or we can create a portfolio table later? Since the task is to build the base models for the tables listed, we will only create the tables that are explicitly listed. We'll add portfolio_id as an integer and note that it should be a foreign key to a portfolio table (to be created). However, to avoid having a dangling foreign key, we can leave it as an integer without a foreign key for now and then adjust later.

    # Alternatively, we can see that the ledger does not have a portfolio table, so maybe portfolio_id is a mistake? Or it's the user_id? We'll assume it's the user_id for now and rename? But we must follow the ledger.

    # Let's keep portfolio_id as an integer and we will add a foreign key to a portfolio table if we create one later. For now, we'll leave it as an integer.

    portfolio_id: Mapped[int] = mapped_column(Integer, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EQUITY/OPTION
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)


class PortfolioSnapshots(Base):
    __tablename__ = 'portfolio_snapshots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to brokerage_accounts.id
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EQUITY/OPTION
    total_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    capture_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)


class TransactionHistory(Base):
    __tablename__ = 'transaction_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to brokerage_accounts.id
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY/SELL
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    execution_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    realized_gain_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class UserTargetWatchlists(Base):
    __tablename__ = 'user_target_watchlists'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to users.id
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    custom_buy_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_monitored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())


class RecommendationActions(Base):
    __tablename__ = 'recommendation_actions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to users.id
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., BUY, SELL, HOLD
    recommended_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    custom_action_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TickerMetadata(Base):
    __tablename__ = 'ticker_metadata'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class TickerPricesLive(Base):
    __tablename__ = 'ticker_prices_live'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class TickerIndicators(Base):
    __tablename__ = 'ticker_indicators'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    rsi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sma_50: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sma_100: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    atr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # We can add more indicators as needed
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class OptionInstruments(Base):
    __tablename__ = 'option_instruments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occ_symbol: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)  # OCC symbol
    shares_per_contract: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    cash_deliverable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # for cash-settled options
    # We can add more fields like strike, expiration, option_type, etc. as per the ledger? The ledger only mentions standardized OCC strings and Greeks. We'll add Greeks as separate columns.
    strike: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expiration: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    option_type: Mapped[Optional[String]] = mapped_column(String(10), nullable=True)  # 'call' or 'put'
    # Greeks
    delta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gamma: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    theta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vega: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rho: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class TickerQuantRatings(Base):
    __tablename__ = 'ticker_quant_ratings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    # We don't have the specific metrics from Seeking Alpha, so we'll leave it as a JSONB for flexibility
    # Or we can define specific columns? The ledger says: Houses uploaded Seeking Alpha metric data linked across asset views.
    # We'll use a JSONB column to store the metrics.
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class MarketRegime(Base):
    __tablename__ = 'market_regime'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anchor_symbol: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g., QQQ, SPY, VIX
    indicator_name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'price', 'rsi', etc.
    indicator_value: Mapped[Float] = mapped_column(Float, nullable=False)
    calculated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())


class TickerMappings(Base):
    __tablename__ = 'ticker_mappings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    broker_name: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    # We can add a unique constraint on (broker_name, raw_symbol)
    __table_args__ = (
        # UniqueConstraint('broker_name', 'raw_symbol', name='_broker_raw_uc'),
    )


class AdjustedOptionDefinitions(Base):
    __tablename__ = 'adjusted_option_definitions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occ_symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    shares_per_contract: Mapped[int] = mapped_column(Integer, nullable=False)
    cash_deliverable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class SystemNotifications(Base):
    __tablename__ = 'system_notifications'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'provider_fetch_failed', 'unmapped_symbol', 'data_discrepancy'
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSONB for flexible metadata
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())