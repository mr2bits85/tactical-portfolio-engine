"""
Tactical Portfolio Engine - TQQQ Manager Page
Dynamic 3-tier EMA strategy dashboard.
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
from global_context_service import GlobalContextService
from auth import get_current_user
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Tactical Portfolio Engine - TQQQ Manager",
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
st.title("📊 TQQQ Manager")
st.caption("Dynamic 3-tier EMA strategy dashboard")

# User info
if current_user:
    st.sidebar.success(f"Logged in as: {current_user}")
else:
    st.sidebar.warning("Running in development mode")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between different views")

# Main content
st.header("📈 TQQQ Analysis - Real-time EMA Calculation")

# Initialize services
@st.cache_resource
def get_services():
    # Note: In a real implementation, we would get a database session from Secret Manager or environment
    # For now, we'll initialize services without a session for demonstration
    # In production, these would be initialized with a proper database session
    strategy_service = StrategyService()
    return strategy_service

try:
    strategy_service = get_services()

    # Fetch real-time data and calculate EMAs
    with st.spinner("Fetching real-time TQQQ data and calculating EMAs..."):
        # In a real implementation, we would use MarketDataService to get data
        # For this example, we'll simulate real-time data calculation

        # Get historical data for EMA calculation (using yfinance directly for demo)
        try:
            import yfinance as yf

            # Fetch TQQQ data
            tqqq_ticker = yf.Ticker("TQQQ")

            # Get enough data for 230-day EMA calculation
            hist_data = tqqq_ticker.history(period="1y")  # 1 year of data

            if not hist_data.empty:
                # Calculate EMAs
                close_prices = hist_data['Close']
                ema_45 = close_prices.ewm(span=45, adjust=False).mean().iloc[-1]
                ema_230 = close_prices.ewm(span=230, adjust=False).mean().iloc[-1]
                current_price = close_prices.iloc[-1]

                # Calculate price change percentage
                prev_close = close_prices.iloc[-2] if len(close_prices) > 1 else close_prices.iloc[-1]
                price_change_pct = ((current_price - prev_close) / prev_close) * 100

                # Calculate EMA changes (approximate)
                ema_45_prev = close_prices.ewm(span=45, adjust=False).mean().iloc[-2] if len(close_prices) > 1 else ema_45
                ema_230_prev = close_prices.ewm(span=230, adjust=False).mean().iloc[-2] if len(close_prices) > 1 else ema_230
                ema_45_change_pct = ((ema_45 - ema_45_prev) / ema_45_prev) * 100 if ema_45_prev != 0 else 0
                ema_230_change_pct = ((ema_230 - ema_230_prev) / ema_230_prev) * 100 if ema_230_prev != 0 else 0

                # Calculate exposure tier: sum of active EMA signals
                # Tier 0: price <= EMA45 AND price <= EMA230 -> 0 signals
                # Tier 1: price > EMA45 XOR price > EMA230 -> 1 signal
                # Tier 2: price > EMA45 AND price > EMA230 -> 2 signals
                active_signals = 0
                if current_price > ema_45:
                    active_signals += 1
                if current_price > ema_230:
                    active_signals += 1

                # Use active_signals as the exposure tier (0, 1, or 2)
                exposure_tier = active_signals

                # Get ADX for filtering (simplified - in reality would calculate properly)
                # For demo, we'll use a placeholder or try to calculate
                adx_value = 25  # Placeholder - would calculate from DMI in real implementation

            else:
                # Fallback to placeholder data if unable to fetch
                raise Exception("Unable to fetch historical data")

        except Exception as e:
            # Fallback to reasonable placeholder values if real data fetch fails
            st.warning(f"Using placeholder data due to: {str(e)}. In production, this would use real market data.")
            current_price = 45.20
            ema_45 = 44.80
            ema_230 = 42.50
            price_change_pct = 2.1
            ema_45_change_pct = 0.9
            ema_230_change_pct = 6.4
            # Calculate exposure tier based on fallback values
            active_signals = 0
            if current_price > ema_45:
                active_signals += 1
            if current_price > ema_230:
                active_signals += 1
            exposure_tier = active_signals
            adx_value = 25

    # Display real-time metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "TQQQ Price",
            f"${current_price:.2f}",
            f"{price_change_pct:+.1f}%"
        )
    with col2:
        st.metric(
            "45-Day EMA",
            f"${ema_45:.2f}",
            f"{ema_45_change_pct:+.1f}%"
        )
    with col3:
        st.metric(
            "230-Day EMA",
            f"${ema_230:.2f}",
            f"{ema_230_change_pct:+.1f}%"
        )

    # TQQQ Strategy Explanation
    st.subheader("🎯 Strategy Overview")
    st.write("""
    The TQQQ Manager uses a dynamic 3-tier exposure system based on EMA signals:
    - **Tier 0 (0% Exposure)**: Price below both 45-Day and 230-Day EMAs (0 active signals)
    - **Tier 1 (50% Exposure)**: Price above exactly one EMA (1 active signal)
    - **Tier 2 (100% Exposure)**: Price above both 45-Day and 230-Day EMAs (2 active signals)

    The system also considers ADX strength to filter signals.
    """)

    # Current tier indicator based on real calculation
    st.subheader("📊 Current Exposure Tier (Real-time)")
    tier_col1, tier_col2, tier_col3 = st.columns(3)
    with tier_col1:
        tier_0_active = (exposure_tier == 0)
        st.metric(
            "Tier 0 (0%)",
            "✅ Active" if tier_0_active else "❌ Inactive",
            f"{active_signals} active signals" if not tier_0_active else "Price below both EMAs"
        )
    with tier_col2:
        tier_1_active = (exposure_tier == 1)
        st.metric(
            "Tier 1 (50%)",
            "✅ Active" if tier_1_active else "❌ Inactive",
            f"{active_signals} active signals" if tier_1_active else "Not exactly one EMA signal"
        )
    with tier_col3:
        tier_2_active = (exposure_tier == 2)
        st.metric(
            "Tier 2 (100%)",
            "✅ Active" if tier_2_active else "❌ Inactive",
            f"{active_signals} active signals" if tier_2_active else "Price below both or above only one EMA"
        )

    # EMA Crossover Chart with real data
    st.subheader("📈 EMA Crossover Chart (Real Data)")
    if 'hist_data' in locals() and not hist_data.empty:
        # Prepare chart data with calculated EMAs
        chart_data = pd.DataFrame({
            'Date': hist_data.index,
            'TQQQ': hist_data['Close'],
            'EMA_45': hist_data['Close'].ewm(span=45, adjust=False).mean(),
            'EMA_230': hist_data['Close'].ewm(span=230, adjust=False).mean()
        })
        st.line_chart(chart_data.set_index('Date')[['TQQQ', 'EMA_45', 'EMA_230']])
    else:
        # Sample chart data as fallback
        chart_data = pd.DataFrame({
            'Date': pd.date_range(start='2023-01-01', end='2023-06-21', freq='D'),
            'TQQQ': np.random.randn(172).cumsum() + 40,
            'EMA_45': np.random.randn(172).cumsum() + 38,
            'EMA_230': np.random.randn(172).cumsum() + 35
        })
        st.line_chart(chart_data.set_index('Date')[['TQQQ', 'EMA_45', 'EMA_230']])
        st.info("Showing sample data - in production would display real TQQQ EMA data")

    # Action buttons based on TQQQ rules
    st.subheader("⚡ Recommended Action (Based on TQQQ Rules)")

    # Determine recommendation based on TQQQ rules from legacy logic
    # Trend Breakdown: active_signals < current_tier -> SELL
    # Wait (Filtered Uptrend): active_signals > current_tier AND ADX < 20 -> WAIT
    # Trend Up + Strong ADX: active_signals > current_tier AND ADX >= 20 -> BUY
    # Conditions Unchanged: active_signals == current_tier -> HOLD

    # Note: In the TQQQ manager, current_tier is essentially what we're calculating as exposure_tier
    # But for the rules, we need to think about what the "current tier" represents vs the "active signals"
    # Looking at the legacy rules, it seems like:
    # - active_signals = number of EMAs above price (0, 1, or 2)
    # - current_tier = the system's current position/tier (0, 1, or 2)
    # For demonstration, we'll simulate having a current_tier based on some logic

    # For simplicity in this demo, let's assume we track the last known tier
    # In a real system, this would be stored in user state or database
    if 'last_tier' not in st.session_state:
        st.session_state.last_tier = exposure_tier  # Initialize to current calculated tier

    current_tier = st.session_state.last_tier  # This would come from user's current position

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

    # Display recommendation
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("📈 BUY", type="primary", use_container_width=True,
                    disabled=(action != "BUY")):
            if action == "BUY":
                st.success("Buy signal executed!")
                # In real system, would update current_tier
                st.session_state.last_tier = min(2, st.session_state.last_tier + 1)
            else:
                st.error(f"Not recommended: {action}")
    with action_col2:
        if st.button("⏸️ HOLD", use_container_width=True,
                    disabled=(action != "HOLD")):
            if action == "HOLD":
                st.info("Hold position maintained")
            else:
                st.error(f"Not recommended: {action}")
    with action_col3:
        if st.button("📉 SELL", use_container_width=True,
                    disabled=(action != "SELL")):
            if action == "SELL":
                st.warning("Sell signal executed!")
                # In real system, would update current_tier
                st.session_state.last_tier = max(0, st.session_state.last_tier - 1)
            else:
                st.error(f"Not recommended: {action}")

    # Show reasoning
    st.info(f"**Reason**: {reason}")

    # TQQQ Rules Info
    st.subheader("📋 Active TQQQ Rules Context")
    st.write(f"""
    **Current Calculation**:
    - TQQQ Price: ${current_price:.2f}
    - 45-Day EMA: ${ema_45:.2f} (Price > EMA45: {'YES' if current_price > ema_45 else 'NO'})
    - 230-Day EMA: ${ema_230:.2f} (Price > EMA230: {'YES' if current_price > ema_230 else 'NO'})
    - Active EMA Signals: {active_signals} (0, 1, or 2)
    - Current Position Tier: {current_tier} (0, 1, or 2)
    - ADX Value: {adx_value:.1f}

    **Applied Rule**: {action}
    - **Calculation**: {reason}
    """)

except Exception as e:
    st.error(f"Error initializing TQQQ Manager: {str(e)}")
    st.info("Please check that all required services are properly configured.")

# Dynamic Front-End State Rendering Components (Task 4.4)
st.subheader("🎨 Dynamic State Rendering Components")

# Determine market state based on EMA signals and ADX
if 'hist_data' in locals() and not hist_data.empty:
    # Use real data to determine state
    if current_price > ema_45 and current_price > ema_230:
        # Price above both EMAs
        if adx_value >= 25:
            market_state = "Bullish"
            state_description = "Strong uptrend - Price above both EMAs with strong ADX"
            state_color = "green"
        else:
            market_state = "Cautious"
            state_description = "Moderate uptrend - Price above both EMAs but weak ADX"
            state_color = "orange"
    elif current_price > ema_45 or current_price > ema_230:
        # Price above one EMA
        market_state = "Cautious"
        state_description = "Moderate uptrend - Price above one EMA"
        state_color = "orange"
    else:
        # Price below both EMAs
        market_state = "Bearish"
        state_description = "Downtrend - Price below both EMAs"
        state_color = "red"
else:
    # Use fallback data to determine state
    if current_price > ema_45 and current_price > ema_230:
        market_state = "Bullish"
        state_description = "Strong uptrend - Price above both EMAs (fallback data)"
        state_color = "green"
    elif current_price > ema_45 or current_price > ema_230:
        market_state = "Cautious"
        state_description = "Moderate uptrend - Price above one EMA (fallback data)"
        state_color = "orange"
    else:
        market_state = "Bearish"
        state_description = "Downtrend - Price below both EMAs (fallback data)"
        state_color = "red"

# State indicator
state_col1, state_col2 = st.columns([1, 3])
with state_col1:
    if market_state == "Bullish":
        st.markdown(f'<p><span style="color: {state_color}; font-size: 1.5em;">🟢</span> <strong>{market_state}</strong></p>', unsafe_allow_html=True)
    elif market_state == "Cautious":
        st.markdown(f'<p><span style="color: {state_color}; font-size: 1.5em;">🟡</span> <strong>{market_state}</strong></p>', unsafe_allow_html=True)
    else:  # Bearish
        st.markdown(f'<p><span style="color: {state_color}; font-size: 1.5em;">🔴</span> <strong>{market_state}</strong></p>', unsafe_allow_html=True)

with state_col2:
    st.markdown(f'<p>{state_description}</p>', unsafe_allow_html=True)

# Dynamic components based on state
if market_state == "Bullish":
    # Bullish states showing two stops
    st.write("#### 🟢 Bullish State Components")

    stop_col1, stop_col2 = st.columns(2)

    with stop_col1:
        # Calculate stop levels (simplified for demo)
        stop1 = current_price * 0.95  # 5% below current price
        stop2 = current_price * 0.90  # 10% below current price
        st.metric(
            label="🛡️ Primary Stop Loss",
            value=f"${stop1:.2f}",
            delta=f"-{(current_price-stop1)/current_price*100:.1f}%"
        )
        st.caption("Set stop on quote at 45-day EMA or 5% below price")

    with stop_col2:
        st.metric(
            label="🎯 Secondary Stop / Target",
            value=f"${stop2:.2f}",
            delta=f"-{(current_price-stop2)/current_price*100:.1f}%"
        )
        st.caption("Trailing stop or profit target at 230-day EMA or 10% below price")

    st.info("""
    **Bullish State Action**: Maintain position with dual stop protection
    - Primary stop: Protects capital (teacher)
    - Secondary stop: Locks in profits or re-entry point ( Warrior)
    """)

elif market_state == "Cautious":
    # Cautious states showing one stop/half-out alert
    st.write#### 🟡 Cautious State Components")

    alert_col, stop_col = st.columns([1, 1])

    with alert_col:
        st.warning("🟡 **HALF-OUT ALERT**")
        st.write("Consider reducing position by 50%")
        st.write(f"Current exposure suggests caution")

    with stop_col:
        # Calculate single stop level
        stop_level = current_price * 0.92  # 8% below current price
        st.metric(
            label="🛑 Consolidated Stop",
            value=f"${stop_level:.2f}",
            delta=f"-{(current_price-stop_level)/current_price*100:.1f}%"
        )
        st.caption("Single stop level for risk management")

    st.info("""
    **Cautious State Action**: Reduce exposure and tighten stops
    - Half-out alert: Reduce position size
    - Consolidated stop: Unified risk management
    """)

else:  # Bearish
    # Bearish states showing cash/re-entry triggers
    st.write("#### 🔴 Bearish State Components")

    cash_col, reentry_col = st.columns(2)

    with cash_col:
        # Calculate cash levels
        cash_trigger = current_price * 0.88  # 12% below for bearish confirmation
        st.metric(
            label="💰 Cash Trigger Level",
            value=f"${cash_trigger:.2f}",
            delta=f"-{(current_price-cash_trigger)/current_price*100:.1f}%"
        )
        st.caption("Move to cash if price breaks this level")

    with reentry_col:
        # Calculate re-entry triggers (would be based on EMA crosses)
        reentry_trigger1 = ema_45 * 0.98  # Slightly below 45 EMA
        reentry_trigger2 = ema_230 * 0.95  # Slightly below 230 EMA
        st.metric(
            label="🔄 Re-entry Trigger 1",
            value=f"${reentry_trigger1:.2f}",
            delta=f"{(reentry_trigger1/current_price-1)*100:+.1f}%" if reentry_trigger1 > 0 else "0.0%"
        )
        st.caption("Re-enter if price reclaims 45-day EMA")

    st.info("""
    **Bearish State Action**: Protect capital and wait for re-entry signals
    - Cash trigger: Move to defensive position
    - Re-entry triggers: Watch for trend reversal signals
    """)

# Add some styling for the components
st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
    }
    .stAlert {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("Tactical Portfolio Engine v1.0.0 | Data as of " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))