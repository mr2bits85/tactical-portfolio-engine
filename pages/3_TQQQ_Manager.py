"""
Tactical Portfolio Engine - Leveraged ETF Manager
SOXL and TQQQ strategy dashboards.
"""
import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from strategy_service import StrategyService
from market_data_service import MarketDataService
from auth import get_current_user
import pandas as pd
import numpy as np

# Import macro gating decorator
from macro_gating import require_fresh_macro_data

# Page configuration
st.set_page_config(
    page_title="Leveraged ETF Manager",
    page_icon="📊",
    layout="wide"
)

# Load custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Get current user
current_user = get_current_user()

# Page header
st.title("📊 Leveraged ETF Manager")
st.caption("SOXL and TQQQ strategy dashboards")

# User info
if current_user:
    st.sidebar.success(f"Logged in as: {current_user}")
else:
    st.sidebar.warning("Running in development mode")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between different views")

# Main content
tab1, tab2 = st.tabs(["📈 SOXL Manager", "🚀 TQQQ Manager"])

with tab1:
    st.header("SOXL Strategy - Based on SOXX")

    # Initialize services
    @st.cache_resource
    def get_services():
        # Import the get_services function from app.py to get the cached services with proper DB session
        from app import get_services as get_app_services
        strategy_service, market_data_service, global_context_service = get_app_services()
        return strategy_service, market_data_service, global_context_service

    try:
        strategy_service, market_data_service, global_context_service = get_services()
        # NOTE: rename variable to avoid conflict
    except Exception as e:
        st.error(f"Error initializing services: {str(e)}")
        st.stop()

    # Define a function to fetch and compute SOXX data, gated by macro data freshness
    @require_fresh_macro_data()
    def get_soxx_data(session):
        # All services are available via closure (same session)
        # Fetch historical data for SOXX (1 year for EMA/ADX calculation)
        soxx_hist_data = market_data_service.get_historical_data("SOXX", period="1y", interval="1d")
        if soxx_hist_data is None or soxx_hist_data.empty:
            raise ValueError("Failed to fetch SOXX historical data")

        # Calculate EMAs on SOXX close prices
        soxx_close = soxx_hist_data['Close']
        ema_45 = soxx_close.ewm(span=45, adjust=False).mean().iloc[-1]
        ema_200 = soxx_close.ewm(span=200, adjust=False).mean().iloc[-1]
        soxx_price = soxx_close.iloc[-1]
        soxx_prev_close = soxx_close.iloc[-2] if len(soxx_close) > 1 else soxx_price
        soxx_price_change_pct = ((soxx_price - soxx_prev_close) / soxx_prev_close) * 100

        # Calculate EMA changes for SOXX
        ema_45_prev = soxx_close.ewm(span=45, adjust=False).mean().iloc[-2] if len(soxx_close) > 1 else ema_45
        ema_200_prev = soxx_close.ewm(span=200, adjust=False).mean().iloc[-2] if len(soxx_close) > 1 else ema_200
        ema_45_change_pct = ((ema_45 - ema_45_prev) / ema_45_prev) * 100 if ema_45_prev != 0 else 0
        ema_200_change_pct = ((ema_200 - ema_200_prev) / ema_200_prev) * 100 if ema_200_prev != 0 else 0

        # Calculate ADX for SOXX (proper calculation)
        try:
            # Calculate True Range and Directional Movement for ADX
            high = soxx_hist_data['High']
            low = soxx_hist_data['Low']
            close = soxx_hist_data['Close']

            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Directional Movement
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low

            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

            # Smooth the values (typically 14-period)
            tr_ma = tr.rolling(window=14).mean()
            plus_dm_ma = pd.Series(plus_dm).rolling(window=14).mean()
            minus_dm_ma = pd.Series(minus_dm).rolling(window=14).mean()

            # Calculate DI values
            plus_di = 100 * (plus_dm_ma / tr_ma)
            minus_di = 100 * (minus_dm_ma / tr_ma)

            # Calculate DX and ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx_value = dx.rolling(window=14).mean().iloc[-1]

            # Handle potential NaN values
            if pd.isna(adx_value):
                adx_value = 25.0  # fallback
        except Exception as e:
            raise RuntimeError(f"Error calculating ADX for SOXX: {e}")

        # Determine SOXL signal based on EMA crossover and ADX filter
        # Bullish signal: EMA45 > EMA200 AND ADX > 20
        # Bearish signal: EMA45 < EMA200 AND ADX > 20
        # Neutral: ADX <= 20 (no strong trend)
        if adx_value > 20:
            if ema_45 > ema_200:
                signal = "BULLISH"
                signal_strength = "STRONG" if adx_value > 25 else "MODERATE"
            else:
                signal = "BEARISH"
                signal_strength = "STRONG" if adx_value > 25 else "MODERATE"
        else:
            signal = "NEUTRAL"
            signal_strength = "WEAK"

        # Get SOXL data (5 days for price and change)
        soxl_hist_data = market_data_service.get_historical_data("SOXL", period="5d", interval="1d")
        if soxl_hist_data is None or soxl_hist_data.empty:
            raise ValueError("Failed to fetch SOXL historical data")

        soxl_price = soxl_hist_data['Close'].iloc[-1]
        soxl_prev = soxl_hist_data['Close'].iloc[-2] if len(soxl_hist_data) > 1 else soxl_price
        soxl_price_change_pct = ((soxl_price - soxl_prev) / soxx_prev_close) * 100  # Wait, should be soxl_prev

        # Actually compute correctly:
        soxl_price_change_pct = ((soxl_price - soxl_prev) / soxl_prev) * 100 if soxl_prev != 0 else 0.0

        # Return all needed data
        return {
            "soxx_hist_data": soxx_hist_data,
            "soxx_close": soxx_close,
            "ema_45": ema_45,
            "ema_200": ema_200,
            "soxx_price": soxx_price,
            "soxx_price_change_pct": soxx_price_change_pct,
            "ema_45_change_pct": ema_45_change_pct,
            "ema_200_change_pct": ema_200_change_pct,
            "adx_value": adx_value,
            "signal": signal,
            "signal_strength": signal_strength,
            "soxl_hist_data": soxl_hist_data,
            "soxl_price": soxl_price,
            "soxl_price_change_pct": soxl_price_change_pct
        }

    try:
        # Execute the guarded function
        with st.spinner("Fetching real-time SOXX data for EMA/ADX calculation..."):
            soxx_result = get_soxx_data(market_data_service.session)

        if soxx_result is None:
            st.error("Macro data is stale or unavailable. Cannot compute SOXL signal.")
            st.stop()

        # Extract results
        soxx_hist_data = soxx_result["soxx_hist_data"]
        soxx_close = soxx_result["soxx_close"]
        ema_45 = soxx_result["ema_45"]
        ema_200 = soxx_result["ema_200"]
        soxx_price = soxx_result["soxx_price"]
        soxx_price_change_pct = soxx_result["soxx_price_change_pct"]
        ema_45_change_pct = soxx_result["ema_45_change_pct"]
        ema_200_change_pct = soxx_result["ema_200_change_pct"]
        adx_value = soxx_result["adx_value"]
        signal = soxx_result["signal"]
        signal_strength = soxx_result["signal_strength"]
        soxl_hist_data = soxx_result["soxl_hist_data"]
        soxl_price = soxx_result["soxl_price"]
        soxl_price_change_pct = soxx_result["soxl_price_change_pct"]

        # SOXL Strategy Explanation
        st.subheader("🎯 Strategy Overview")
        st.write("""
        The SOXL strategy uses EMA crossovers on SOXX (Semiconductor Holders Index) to generate signals:
        - **Bullish Signal**: 45-day EMA crosses above 200-day EMA, with ADX > 20 (strong trend)
        - **Bearish Signal**: 45-day EMA crosses below 200-day EMA, with ADX > 20 (strong trend)
        - **Neutral/No Signal**: ADX <= 20 (weak or no trend)

        SOXL attempts to provide 3x daily leverage of the SOXX index.
        """)

        # Current Signals Display
        col1, col2, col3 = st.columns(3)
        with col1:
            if signal == "BULLISH":
                st.markdown(f'<p><span style="color: green; font-size: 1.5em;">🟢</span> <strong>SIGNAL: {signal}</strong></p>', unsafe_allow_html=True)
            elif signal == "BEARISH":
                st.markdown(f'<p><span style="color: red; font-size: 1.5em;">🔴</span> <strong>SIGNAL: {signal}</strong></p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p><span style="color: orange; font-size: 1.5em;">🟡</strong> <strong>SIGNAL: {signal}</strong></p>', unsafe_allow_html=True)
        with col2:
            st.metric("ADX (SOXX)", f"{adx_value:.1f}",
                     delta="Strong Trend" if adx_value > 25 else "Moderate Trend" if adx_value > 20 else "Weak Trend")
        with col3:
            st.metric("Signal Strength", signal_strength)

        # Key Metrics
        st.subheader("📊 Key Metrics")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        with metric_col1:
            st.metric("SOXX Price", f"${soxx_price:.2f}", f"{soxx_price_change_pct:+.1f}%")
        with metric_col2:
            st.metric("SOXL Price (3x)", f"${soxl_price:.2f}", f"{soxl_price_change_pct:+.1f}%")
        with metric_col3:
            st.metric("SOXX 45-Day EMA", f"${ema_45:.2f}", f"{ema_45_change_pct:+.1f}%")
        with metric_col4:
            st.metric("SOXX 200-Day EMA", f"${ema_200:.2f}", f"{ema_200_change_pct:+.1f}%")

        # EMA Crossover Chart
        st.subheader("📈 EMA Crossover Chart (SOXX)")
        if not soxx_hist_data.empty:
            # Prepare chart data with calculated EMAs
            chart_data = pd.DataFrame({
                'Date': soxx_hist_data.index,
                'SOXX': soxx_hist_data['Close'],
                'EMA_45': soxx_hist_data['Close'].ewm(span=45, adjust=False).mean(),
                'EMA_200': soxx_hist_data['Close'].ewm(span=200, adjust=False).mean()
            })
            st.line_chart(chart_data.set_index('Date')[['SOXX', 'EMA_45', 'EMA_200']])

        else:
            # This should not happen because we checked for empty data above, but just in case
            st.info("No data available to display chart.")

        # Trading Recommendation
        st.subheader("💡 Trading Recommendation")

        if signal == "BULLISH":
            st.success(f"**RECOMMENDATION: CONSIDER LONG SOXL**")
            st.write(f"""
            - SOXX 45-day EMA (${ema_45:.2f}) is above 200-day EMA (${ema_200:.2f}) - bullish crossover
            - ADX is {adx_value:.1f} indicating {'strong' if adx_value > 25 else 'moderate'} trend strength
            - Consider entering long SOXL positions with appropriate risk management
            """)
        elif signal == "BEARISH":
            st.error(f"**RECOMMENDATION: CONSIDER SHORT/AVOID SOXL**")
            st.write(f"""
            - SOXX 45-day EMA (${ema_45:.2f}) is below 200-day EMA (${ema_200:.2f}) - bearish crossover
            - ADX is {adx_value:.1f} indicating {'strong' if adx_value > 25 else 'moderate'} trend strength
            - Consider avoiding or reducing SOXL exposure, or look for short opportunities
            """)
        else:
            st.warning(f"**RECOMMENDATION: HOLD/WAIT FOR CLEAR SIGNAL**")
            st.write(f"""
            - ADX is {adx_value:.1f} indicating weak or no trend (ADX <= 20)
            - EMA crossover signals are not reliable in ranging markets
            - Consider waiting for stronger trend development before taking positions
            """)

        # Additional Context
        with st.expander("📊 Detailed Analysis"):
            st.write(f"""
            **SOXX Technical Analysis:**
            - Current Price: ${soxx_price:.2f} ({soxx_price_change_pct:+.1f}%)
            - 45-Day EMA: ${ema_45:.2f} ({ema_45_change_pct:+.1f}%)
            - 200-Day EMA: ${ema_200:.2f} ({ema_200_change_pct:+.1f}%)
            - EMA Relationship: {'Bullish (45 > 200)' if ema_45 > ema_200 else 'Bearish (45 < 200)'}
            - ADX (Trend Strength): {adx_value:.1f} ({'Strong' if adx_value > 25 else 'Moderate' if adx_value > 20 else 'Weak'})

            **SOXL Implications (3x Leveraged):**
            - Approximate Price: ${soxl_price:.2f} ({soxl_price_change_pct:+.1f}%)
            - Leveraged moves will be approximately 3x SOXX daily moves
            """)

    except Exception as e:
        st.error(f"Error processing SOXX data: {str(e)}")
        st.info("Please check that all required services are properly configured.")

with tab2:
    st.header("TQQQ Manager - Dynamic 3-Tier EMA Strategy")

    # Initialize services
    @st.cache_resource
    def get_services():
        # Import the get_services function from app.py to get the cached services with proper DB session
        from app import get_services as get_app_services
        strategy_service, market_data_service, global_context_service = get_app_services()
        return strategy_service, market_data_service, global_context_service

    try:
        strategy_service, market_data_service, global_context_service = get_services()
    except Exception as e:
        st.error(f"Error initializing services: {str(e)}")
        st.stop()

    # Define a function to fetch and compute TQQQ data, gated by macro data freshness
    @require_fresh_macro_data()
    def get_tqqq_data(session):
        # All services are available via closure
        # Get historical data for QQQ (1 year for EMA/ADX calculation)
        qqq_hist_data = market_data_service.get_historical_data("QQQ", period="1y", interval="1d")
        # Get recent data for TQQQ (5 days for price and change)
        tqqq_hist_data = market_data_service.get_historical_data("TQQQ", period="5d", interval="1d")

        if qqq_hist_data is None or qqq_hist_data.empty or tqqq_hist_data is None or tqqq_hist_data.empty:
            raise ValueError("Failed to fetch QQQ or TQQQ historical data")

        # Calculate EMAs on QQQ close prices
        qqq_close = qqq_hist_data['Close']
        ema_45 = qqq_close.ewm(span=45, adjust=False).mean().iloc[-1]
        ema_230 = qqq_close.ewm(span=230, adjust=False).mean().iloc[-1]
        # price change percentage for QQQ (for reference)
        qqq_price = qqq_close.iloc[-1]
        qqq_prev_close = qqq_close.iloc[-2] if len(qqq_close) > 1 else qqq_price
        qqq_price_change_pct = ((qqq_price - qqq_prev_close) / qqq_prev_close) * 100 if qqq_prev_close != 0 else 0.0

        # Calculate EMA changes (approximate) for QQQ
        ema_45_prev = qqq_close.ewm(span=45, adjust=False).mean().iloc[-2] if len(qqq_close) > 1 else ema_45
        ema_230_prev = qqq_close.ewm(span=230, adjust=False).mean().iloc[-2] if len(qqq_close) > 1 else ema_230
        ema_45_change_pct = ((ema_45 - ema_45_prev) / ema_45_prev) * 100 if ema_45_prev != 0 else 0
        ema_230_change_pct = ((ema_230 - ema_230_prev) / ema_230_prev) * 100 if ema_230_prev != 0 else 0

        # Calculate exposure tier: sum of active EMA signals based on QQQ price vs EMA
        # Tier 0: price <= EMA45 AND price <= EMA230 -> 0 signals
        # Tier 1: price > EMA45 XOR price > EMA230 -> 1 signal
        # Tier 2: price > EMA45 AND price > EMA230 -> 2 signals
        active_signals = 0
        if qqq_price > ema_45:
            active_signals += 1
        if qqq_price > ema_230:
            active_signals += 1

        # Use active_signals as the exposure tier (0, 1, or 2)
        exposure_tier = active_signals

        # TQQQ price and change
        tqqq_price = tqqq_hist_data['Close'].iloc[-1]
        tqqq_prev = tqqq_hist_data['Close'].iloc[-2] if len(tqqq_hist_data) > 1 else tqqq_price
        tqqq_price_change_pct = ((tqqq_price - tqqq_prev) / tqqq_prev) * 100 if tqqq_prev != 0 else 0.0

        # Get ADX for filtering (proper calculation)
        try:
            # Calculate True Range and Directional Movement for ADX
            high = qqq_hist_data['High']
            low = qqq_hist_data['Low']
            close = qqq_hist_data['Close']

            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Directional Movement
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low

            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

            # Smooth the values (typically 14-period)
            tr_ma = tr.rolling(window=14).mean()
            plus_dm_ma = pd.Series(plus_dm).rolling(window=14).mean()
            minus_dm_ma = pd.Series(minus_dm).rolling(window=14).mean()

            # Calculate DI values
            plus_di = 100 * (plus_dm_ma / tr_ma)
            minus_di = 100 * (minus_dm_ma / tr_ma)

            # Calculate DX and ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx_value = dx.rolling(window=14).mean().iloc[-1]

            # Handle potential NaN values
            if pd.isna(adx_value):
                adx_value = 25.0  # fallback
        except Exception as e:
            raise RuntimeError(f"Error calculating ADX for QQQ: {e}")

        # Determine recommendation based on QQQ signals from legacy logic
        # Track the last known tier in session state to compare with current signals
        if 'last_tier' not in st.session_state:
            st.session_state.last_tier = exposure_tier  # Initialize to current calculated tier

        current_tier = st.session_state.last_tier  # This would come from user's current position in a real system

        # Apply TQQQ rules
        if active_signals < current_tier:
            # Trend Breakdown
            action = "SELL"
            action_type = "sell"
            reason = f"Active uptrend signals ({active_signals}) < current tier ({current_tier})"
            rec_box = "rec-box-red"
        elif active_signals > current_tier and adx_value < 20:
            # Wait (Filtered Uptrend)
            action = "WAIT (FILTERED)"
            action_type = "wait"
            reason = f"Active uptrend signals ({active_signals}) > current tier ({current_tier}) but ADX ({adx_value:.1f}) < 20"
            rec_box = "rec-box-orange"
        elif active_signals > current_tier and adx_value >= 20:
            # Trend Up + Strong ADX
            action = "BUY"
            action_type = "buy"
            reason = f"Active uptrend signals ({active_signals}) > current tier ({current_tier}) AND ADX ({adx_value:.1f}) >= 20"
            rec_box = "rec-box-green"
        else:
            # Conditions Unchanged (active_signals == current_tier)
            action = "HOLD"
            action_type = "hold"
            reason = f"Active uptrend signals ({active_signals}) == current tier ({current_tier})"
            rec_box = "rec-box-grey"

        # Return all needed data
        return {
            "qqq_hist_data": qqq_hist_data,
            "qqq_close": qqq_close,
            "ema_45": ema_45,
            "ema_230": ema_230,
            "qqq_price": qqq_price,
            "qqq_price_change_pct": qqq_price_change_pct,
            "ema_45_change_pct": ema_45_change_pct,
            "ema_230_change_pct": ema_230_change_pct,
            "adx_value": adx_value,
            "exposure_tier": exposure_tier,
            "tqqq_hist_data": tqqq_hist_data,
            "tqqq_price": tqqq_price,
            "tqqq_price_change_pct": tqqq_price_change_pct,
            "action": action,
            "action_type": action_type,
            "reason": reason,
            "rec_box": rec_box
        }

    try:
        # Execute the guarded function
        with st.spinner("Fetching real-time QQQ data for EMA/ADX and TQQQ price..."):
            tqqq_result = get_tqqq_data(market_data_service.session)

        if tqqq_result is None:
            st.error("Macro data is stale or unavailable. Cannot compute TQQQ signal.")
            st.stop()

        # Extract results
        qqq_hist_data = tqqq_result["qqq_hist_data"]
        qqq_close = tqqq_result["qqq_close"]
        ema_45 = tqqq_result["ema_45"]
        ema_230 = tqqq_result["ema_230"]
        qqq_price = tqqq_result["qqq_price"]
        qqq_price_change_pct = tqqq_result["qqq_price_change_pct"]
        ema_45_change_pct = tqqq_result["ema_45_change_pct"]
        ema_230_change_pct = tqqq_result["ema_230_change_pct"]
        adx_value = tqqq_result["adx_value"]
        exposure_tier = tqqq_result["exposure_tier"]
        tqqq_hist_data = tqqq_result["tqqq_hist_data"]
        tqqq_price = tqqq_result["tqqq_price"]
        tqqq_price_change_pct = tqqq_result["tqqq_price_change_pct"]
        action = tqqq_result["action"]
        action_type = tqqq_result["action_type"]
        reason = tqqq_result["reason"]
        rec_box = tqqq_result["rec_box"]

        # TQQQ Strategy Explanation
        st.subheader("🎯 Strategy Overview")
        st.write("""
        The TQQQ Manager uses a dynamic 3-tier exposure system based on EMA signals:
        - **Tier 0 (0% Exposure)**: Price below both 45-Day and 230-Day EMAs (0 active signals)
        - **Tier 1 (50% Exposure)**: Price above exactly one EMA (1 active signal)
        - **Tier 2 (100% Exposure)**: Price above both 45-Day and 230-Day EMAs (2 active signals)

        The system also considers ADX strength to filter signals.
        """)

        # New: Tier and Recommendation section
        col1, col2 = st.columns(2)
        with col1:
            # Determine tier meaning
            if exposure_tier == 0:
                tier_meaning = "Below both EMAs"
            elif exposure_tier == 1:
                tier_meaning = "Above one EMA"
            else: # exposure_tier == 2
                tenor_meaning = "Above both EMAs"
            st.metric(label="Tier", value=exposure_tier, help=tier_meaning)
        with col2:
            st.metric(label="Recommendation", value=action)

            # Then, the metrics row: QQQ Price, TQQQ Price, QQQ 45-Day EMA, QQQ 230-Day EMA, QQQ ADX
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("QQQ Price", f"${qqq_price:.2f}", f"{qqq_price_change_pct:+.1f}%")
            with col2:
                st.metric("TQQQ Price", f"${tqqq_price:.2f}", f"{tqqq_price_change_pct:+.1f}%")
            with col3:
                st.metric("QQQ 45-Day EMA", f"${ema_45:.2f}", f"{ema_45_change_pct:+.1f}%")
            with col4:
                st.metric("QQQ 230-Day EMA", f"${ema_230:.2f}", f"{ema_230_change_pct:+.1f}%")
            with col5:
                st.metric("QQQ ADX", f"{adx_value:.1f}")

        # EMA Crossover Chart with real data (based on QQQ)
        st.subheader("📈 EMA Crossover Chart (QQQ)")
        if not qqq_hist_data.empty:
            # Prepare chart data with calculated EMAs
            chart_data = pd.DataFrame({
                'Date': qqq_hist_data.index,
                'QQQ': qqq_hist_data['Close'],
                'EMA_45': qqq_hist_data['Close'].ewm(span=45, adjust=False).mean(),
                'EMA_230': qqq_hist_data['Close'].ewm(span=230, adjust=False).mean()
            })
            st.line_chart(chart_data.set_index('Date')[['QQQ', 'EMA_45', 'EMA_230']])
        else:
            # This should not happen because we checked for empty data above, but just in case
            st.info("No data available to display chart.")

        # Action buttons based on QQQ signals
        st.subheader("⚡ Recommended Action (Based on QQQ Signals)")

        # We already determined the action above, so just display it with styling
        if action == "BUY":
            st.success(f"**RECOMMENDATION: {action}**")
        elif action == "SELL":
            st.error(f"**RECOMMENDATION: {action}**")
        elif action == "WAIT (FILTERED)":
            st.warning(f"**RECOMMENDATION: {action}**")
        else:  # HOLD
            st.info(f"**RECOMMENDATION: {action}**")

        st.write(f"- **Reason**: {reason}")

        # TQQQ Rules Info
        st.subheader("📋 Active TQQQ Rules Context")
        st.write(f"""
        **Current Calculation**:
        - TQQQ Price: ${tqqq_price:.2f}
        - 45-Day EMA (QQQ): ${ema_45:.2f} (QQQ Price > EMA45: {'YES' if qqq_price > ema_45 else 'NO'})
        - 230-Day EMA (QQQ): ${ema_230:.2f} (QQQ Price > EMA230: {'YES' if qqq_price > ema_230 else 'NO'})
        - Active EMA Signals: {exposure_tier} (0, 1, or 2)
        - Current Position Tier: {exposure_tier} (0, 1, or 2) [Note: This is the last known tier from session state]
        - ADX Value: {adx_value:.1f}

        **Applied Rule**: {action}
        - **Calculation**: {reason}
        """)

    except Exception as e:
        st.error(f"Error processing TQQQ data: {str(e)}")
        st.info("Please check that all required services are properly configured.")

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))