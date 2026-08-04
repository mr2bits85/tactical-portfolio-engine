from sqlalchemy import Integer, String, Float, DateTime, Date, Boolean, Text, JSON, func
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

class BrokerageAccounts(Base):
    __tablename__ = 'brokerage_accounts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to users.id
    broker_name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., Fidelity, E-Trade
    account_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # Matches Fidelity's string identifier

class PortfolioSnapshots(Base):
    __tablename__ = 'portfolio_snapshots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to brokerage_accounts.id
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    last_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    basis: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    earnings_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    div_ex_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    capture_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class OptionInstruments(Base):
    __tablename__ = 'option_instruments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occ_symbol: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    shares_per_contract: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    cash_deliverable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    strike: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expiration: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    option_type: Mapped[Optional[String]] = mapped_column(String(10), nullable=True)
    delta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gamma: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    theta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vega: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rho: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class TickerQuantRatings(Base):
    __tablename__ = 'ticker_quant_ratings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class MarketRegime(Base):
    __tablename__ = 'market_regime'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anchor_symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    indicator_name: Mapped[str] = mapped_column(String(50), nullable=False)
    indicator_value: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

class TickerMappings(Base):
    __tablename__ = 'ticker_mappings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    broker_name: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_symbol: Mapped[str] = mapped_column(String(20), nullable=False)

class AdjustedOptionDefinitions(Base):
    __tablename__ = 'adjusted_option_definitions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occ_symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    shares_per_contract: Mapped[int] = mapped_column(Integer, nullable=False)
    cash_deliverable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)