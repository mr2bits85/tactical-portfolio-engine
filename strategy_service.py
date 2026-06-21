"""
Modern, type-hinted StrategyService class refactored from legacy logic_rules.py.
Contains all mathematical models and rule evaluation logic for portfolio strategies.
"""
from dataclasses import dataclass
from typing import Callable, Any, List, Dict, Tuple, Optional
import pandas as pd


@dataclass
class Rule:
    """Represents a trading rule with conditions and evaluations."""
    # The human readable name/title of the rule, e.g. "🔴 Breakdown (Price < 100DMA -5%)"
    name: str
    scenario: str  # The scenario that triggers the rule, e.g. "Price falls below 95% of the 100-Day Moving Average"
    action: str  # The recommended action: "MARKET SELLNOW", "STOP ON QUOTE", "MARKET BUY"
    calculation: str  # The mathematical formula or logic, e.g. "100-Day MT * 0.95"
    # A sentence that brings together the action, scenario, and calculation
    calculated_action: str
    # Lambda that evaluates to True if the rule applies
    condition: Callable[[dict], bool]
    # Lambda that computes the final values when the rule applies
    evaluate: Callable[[dict], Any]


class StrategyService:
    """
    Modern service for evaluating portfolio strategy rules.
    Refactored from legacy logic_rules.py with full type hinting.
    """

    def __init__(self):
        """Initialize all strategy rules."""
        # Initialize all rule sets
        self._initialize_all_rules()

    # --- HELPER FUNCTIONS ---

    def _atr_floor_pct(self, ctx: dict, tier_pct: float, atr_multiplier: float = 2.0) -> float:
        """Return the effective trailing %, applying an ATR floor so volatile stocks aren't stopped out on noise."""
        price = ctx.get('price', 0)
        atr = ctx.get('ATR_14', 0)
        if price > 0 and atr > 0:
            atr_pct = (atr_multiplier * atr / price) * 100
            return max(tier_pct, atr_pct)
        return tier_pct

    def _ts_msg(self, ctx: dict, base_pct: float, atr_mult: float, reason_text: str) -> str:
        """
        Calculates the ATR-floored percentage and its exact dollar equivalent,
        returning a cleanly formatted string for the UI.
        """
        price = ctx.get('price', 0)

        # 1. Get the final percentage using your existing helper
        final_pct = self._atr_floor_pct(ctx, base_pct, atr_mult)

        # 2. Calculate the exact dollar amount of that percentage
        dollar_amt = price * (final_pct / 100.0)

        # 3. Return the combined display string
        return f"Set Trailing Stop of {final_pct:.1f}% (${dollar_amt:.2f}). {reason_text}"

    def is_falling_knife(self, context: dict) -> bool:
        """Pre-filter: returns True if the stock is in a falling knife condition.
        When True, ALL buy and re-entry signals should be suppressed."""
        slope = context.get('SMA_50_slope', 0)
        rsi = context.get('RSI_14', 50)
        if slope < 0 and rsi < 30:
            return True
        if slope < -5.0:
            return True
        return False

    # --- RULE INITIALIZATION ---

    def _initialize_all_rules(self) -> None:
        """Initialize all strategy rules."""
        # GROWTH STRATEGY
        self.GROWTH_BUY_RULES: List[Rule] = [
            Rule(
                name="📈 Strong Uptrend Pullback (20 EMA)",
                scenario="Price is more than 15% above the 50 Day SMA, indicating a strong uptrend where the 50 SMA is too far away to be a useful entry. The 50 SMA slope is positive (uptrend confirmed) and RSI is between 30 and 70.",
                action="SET BUY LIMIT",
                calculation="20 Day EMA (pullback entry for strong uptrends)",
                calculated_action="Set a buy limit at the 20 Day EMA to catch a pullback in a strong uptrend.",
                condition=lambda ctx: (
                    ctx.get('SMA_50_slope', 0) > 0
                    and ctx.get('price', 0) > ctx.get('MA_50', 0) * 1.15
                    and 30 <= ctx.get('RSI_14', 50) <= 70
                    and ctx.get('MA_50', 0) > 0
                ),
                evaluate=lambda ctx: (
                    ctx.get('EMA_20', 0),
                    max(
                        ctx.get('EMA_20', 0) - (2 * ctx.get('ATR_14', 0)
                                                ) if ctx.get('ATR_14', 0) > 0 else ctx.get('EMA_20', 0) * 0.92,
                        ctx.get('EMA_20', 0) * (1 - 0.10)
                    ),
                    "Strong Uptrend Pullback (20 EMA)"
                )
            ),
            Rule(
                name="✅ Healthy Dip (50 Day SMA)",
                scenario="50 SMA slope is positive (uptrend confirmed) and RSI is below 50 (pulling back). This is the ideal dip-buying scenario — buying into a confirmed uptrend during a temporary pullback.",
                action="SET BUY LIMIT",
                calculation="50 Day SMA",
                calculated_action="Set a buy limit at the 50 Day SMA to buy a healthy dip in an uptrend.",
                condition=lambda ctx: (
                    ctx.get('SMA_50_slope', 0) > 0
                    and ctx.get('RSI_14', 50) < 50
                    and ctx.get('MA_50', 0) > 0
                    and ctx.get('MACD_line', 0) > ctx.get('MACD_signal', 0)
                ),
                evaluate=lambda ctx: (
                    ctx.get('MA_50', 0),
                    max(
                        ctx.get('MA_50', 0) - (2 * ctx.get('ATR_14', 0)
                                               ) if ctx.get('ATR_14', 0) > 0 else ctx.get('MA_50', 0) * 0.90,
                        ctx.get('MA_50', 0) * (1 - 0.12)
                    ),
                    "Healthy Dip (50 Day SMA)"
                ),
            ),
        ]

        self.GROWTH_SELL_RULES: List[Rule] = [
            Rule(
                name="⚠️ Trend Exhaustion (MACD Bearish Cross)",
                scenario="The stock has a gain_pct of >= 20% (locking in profits) AND the MACD line crosses below the MACD signal line.",
                action="TRAILING STOP %",
                calculation="max(8%, 2.0 * ATR%)",
                calculated_action="Set an ATR-floored percentage trailing stop. MACD momentum is breaking down; protect profits.",
                condition=lambda ctx: ctx.get('gain_pct', 0) >= 20 and ctx.get('MACD_line', 0) < ctx.get('MACD_signal', 0),
                evaluate=lambda ctx: (
                    "⚠️ Trend Exhaustion (MACD Bearish Cross)",
                    self._atr_floor_pct(ctx, 8.0, 2.0),
                    self._ts_msg(ctx, 8.0, 2.0, "MACD momentum is breaking down; protect profits."),
                    "TRAILING STOP %", False, 'neutral'
                )
            )
        ]

        # MOMENTUM STRATEGY
        self.MOMENTUM_BUY_RULES: List[Rule] = [
            Rule(
                name="🚀 Breakout Entry (52W High + Strong ADX)",
                scenario="Price is within 2% of the 52-Week High AND ADX is above 20, confirming strong trend behind the breakout. This filters out false breakouts in weak/choppy markets.",
                action="SET BUY LIMIT",
                calculation="52-Week High (ADX > 20 confirmation required)",
                calculated_action="Set a buy limit at the 52-Week High for a confirmed momentum breakout.",
                condition=lambda ctx: (
                    ctx.get('price', 0) >= ctx.get('High_52', 0) * 0.98
                    and ctx.get('ADX_14', 0) > 20
                    and ctx.get('High_52', 0) > 0
                    and ctx.get('MACD_line', 0) > ctx.get('MACD_signal', 0)
                ),
                evaluate=lambda ctx: (
                    ctx.get('High_52', 0),
                    max(
                        ctx.get('High_52', 0) - (2 * ctx.get('ATR_14', 0)
                                                 ) if ctx.get('ATR_14', 0) > 0 else ctx.get('High_52', 0) * 0.92,
                        ctx.get('High_52', 0) * (1 - 0.10)
                    ),
                    "Breakout Entry (52W High + Strong ADX)"
                ),
            ),
        ]

        self.MOMENTUM_SELL_RULES: List[Rule] = [
            Rule(
                name="⚠️ Momentum Exhaustion (MACD Bearish Cross)",
                scenario="The stock has a gain_pct of >= 15% (sitting on profits) AND the MACD line crosses below the MACD signal line (bearish signal).",
                action="TRAILING STOP %",
                calculation="max(5%, 1.5 * ATR / Price)",
                calculated_action="Set a tight 5% trailing stop. MACD momentum is breaking down.",
                condition=lambda ctx: ctx.get('gain_pct', 0) >= 15 and ctx.get(
                    'MACD_line', 0) < ctx.get('MACD_signal', 0),
                evaluate=lambda ctx: (
                    "⚠️ Momentum Exhaustion (MACD Bearish Cross)",
                    self._atr_floor_pct(ctx, 5.0, 1.5),
                    f"Set tight 5% Trailing Stop ({self._atr_floor_pct(ctx, 5.0, 1.5):.1f}%, ATR-adjusted). MACD momentum is breaking down.",
                    "TRAILING STOP %", False, 'neutral'
                )
            )
        ]

        # CORE STRATEGY
        self.CORE_BUY_RULES: List[Rule] = [
            Rule(
                name="✅ Value Entry (100 Day SMA)",
                scenario="50 SMA slope is positive or flat (no active downtrend). Standard deep value entry at the 100 Day SMA.",
                action="SET BUY LIMIT",
                calculation="100 Day SMA",
                calculated_action="Set a buy limit at the 100 Day SMA for a deep value entry in a stable trend.",
                condition=lambda ctx: (
                    ctx.get('SMA_50_slope', 0) >= 0
                    and ctx.get('MA_100', 0) > 0
                ),
                evaluate=lambda ctx: (
                    ctx.get('MA_100', 0),
                    max(
                        ctx.get('MA_100', 0) - (3 * ctx.get('ATR_14', 0)
                                                ) if ctx.get('ATR_14', 0) > 0 else ctx.get('MA_100', 0) * 0.90,
                        ctx.get('MA_100', 0) * (1 - 0.15)
                    )
                ),
            )
        ],

        self.CORE_SELL_RULES: List[Rule] = [
            Rule(
                name="⚠️ Fundamental Review Alert",
                scenario="Price has fallen 20% or more from the 52-Week High. This may indicate a fundamental change in the company's outlook. Analyze whether the company still deserves Core status.",
                action="REVIEW ALERT",
                calculation="52-Week High * 0.80",
                calculated_action="Alert: Analyze company fundamentals. Determine if the core investment thesis is still intact.",
                condition=lambda ctx: ctx.get('price', 0) < (
                    ctx.get('High_52', 0) * 0.80) and ctx.get('High_52', 0) > 0,
                evaluate=lambda ctx: ("⚠️ Fundamental Review Alert", ctx.get(
                    'High_52', 0) * 0.80, "REVIEW FUNDAMENTALS. Price dropped 20%+ from highs. Is the thesis still intact?", "REVIEW ALERT", True, 'sell')
            )
        ]

        # INCOME STRATEGY
        self.INCOME_BUY_RULES: List[Rule] = [
            Rule(
                name="✅ Value Entry (100 Day SMA)",
                scenario="50 SMA slope is positive or flat (no active downtrend). Standard deep value entry at the 100 Day SMA.",
                action="SET BUY LIMIT",
                calculation="100 Day SMA",
                calculated_action="Set a buy limit at the 100 Day SMA for a deep value entry in a stable trend.",
                condition=lambda ctx: (
                    ctx.get('SMA_50_slope', 0) >= 0
                    and ctx.get('MA_100', 0) > 0
                ),
                evaluate=lambda ctx: (
                    ctx.get('MA_100', 0),
                    max(
                        ctx.get('MA_100', 0) - (3 * ctx.get('ATR_14', 0)
                                                ) if ctx.get('ATR_14', 0) > 0 else ctx.get('MA_100', 0) * 0.90,
                        ctx.get('MA_100', 0) * (1 - 0.15)
                    )
                ),
            ),
        ]

        self.INCOME_SELL_RULES: List[Rule] = [
            Rule(
                name="✅ Income Monitoring",
                scenario="Default state for income stocks. No fundamental alerts or major breakdowns are active.",
                action="TRAILING STOP %",
                calculation="10.0%",
                calculated_action="Set a standard 10% trailing stop to protect income position.",
                condition=lambda ctx: True,
                evaluate=lambda ctx: (
                    "✅ Income Monitoring",
                    10.0,
                    self._ts_msg(ctx, 10.0, 0, "Maintain position."),
                    "TRAILING STOP %", False, 'neutral'
                )
            )
        ]

        # TQQQ MANAGER
        self.TQQQ_RULES: List[Rule] = [
            Rule(
                name="Trend Breakdown",
                scenario="Active uptrend signals (Price > 45 Day EMA or 230 Day EMA) are fewer than the current exposure tier.",
                action="SELL",
                calculation="Active Uptrend Signals < Current Tier",
                calculated_action="Immediately Sell because active uptrend signals are fewer than the current exposure tier.",
                condition=lambda ctx: ctx.get(
                    'active_signals', 0) < ctx.get('current_tier', 0),
                evaluate=lambda ctx: ("Trend Breakdown", "SELL",
                                      "rec-box-red", ctx.get('active_signals', 0))
            ),
            Rule(
                name="Trend Up + Strong ADX",
                scenario="Active uptrend signals are greater than current tier, and the ADX indicator is strong (>= 20).",
                action="BUY",
                calculation="Active Uptrend Signals > Current Tier AND ADX >= 20",
                calculated_action="Immediately Buy because uptrend signals are present and ADX is strong.",
                condition=lambda ctx: ctx.get('active_signals', 0) > ctx.get(
                    'current_tier', 0) and ctx.get('adx', 0) >= 20,
                evaluate=lambda ctx: ("Trend Up + Strong ADX.", "BUY",
                                      "rec-box-green", ctx.get('active_signals', 0))
            )
        ]

        # RE-ENTRY RULES (simplified)
        self.GROWTH_REENTRY_RULES: List[Rule] = [
            Rule(
                name="📗 Trend Reclaim (50 SMA Rising)",
                scenario="After a previous exit, price reclaims the 50 Day SMA AND the SMA 50 slope is positive (uptrend resuming).",
                action="RE-ENTER",
                calculation="Price > 50 Day SMA AND SMA 50 Slope > 0",
                calculated_action="Re-enter using the standard Growth Buy Point and Stop Loss rules.",
                condition=lambda ctx: ctx.get('price', 0) > ctx.get(
                    'MA_50', 0) > 0 and ctx.get('SMA_50_slope', 0) > 0,
                evaluate=lambda ctx: ("📗 Trend Reclaim", ctx.get(
                    'MA_50', 0), "Trend resumed. Re-enter using standard Buy Point rules.", "RE-ENTER", False, 'buy')
            )
        ]

        self.MOMENTUM_REENTRY_RULES: List[Rule] = [
            Rule(
                name="📗 New 52-Week High",
                scenario="After a previous exit, price makes a new 52-Week High — the ultimate breakout re-entry signal.",
                action="RE-ENTER",
                calculation="Price > 52-Week High",
                calculated_action="Re-enter using the standard Momentum Buy Point and Stop Loss rules.",
                condition=lambda ctx: ctx.get('price', 0) >= ctx.get('High_52', 0) > 0,
                evaluate=lambda ctx: ("📗 New 52-Week High", ctx.get('High_52', 0),
                                      "Breakout confirmed. Re-enter using standard Buy Point rules.", "RE-ENTER", False, 'buy')
            )
        ]

        self.CORE_REENTRY_RULES: List[Rule] = [
            Rule(
                name="📗 Value Reclaim (100 SMA + Uptrend)",
                scenario="After a previous exit, price reclaims the 100 Day SMA AND the SMA 50 slope is positive, confirming the downtrend has reversed.",
                action="RE-ENTER",
                calculation="Price > 100 Day SMA AND SMA 50 Slope > 0",
                calculated_action="Re-enter using the standard Core Buy Point and Stop Loss rules.",
                condition=lambda ctx: ctx.get('price', 0) > ctx.get(
                    'MA_100', 0) > 0 and ctx.get('SMA_50_slope', 0) > 0,
                evaluate=lambda ctx: ("📗 Value Reclaim", ctx.get(
                    'MA_100', 0), "Trend reversed. Re-enter using standard Buy Point rules.", "RE-ENTER", False, 'buy')
            )
        ]

        self.INCOME_REENTRY_RULES: List[Rule] = [
            Rule(
                name="📗 Value Reclaim (100 SMA + Uptrend)",
                scenario="After a previous exit, price reclaims the 100 Day SMA AND the SMA 50 slope is positive, confirming the downtrend has reversed.",
                action="RE-ENTER",
                calculation="Price > 100 Day SMA AND SMA 50 Slope > 0",
                calculated_action="Re-enter using the standard Core Buy Point and Stop Loss rules.",
                condition=lambda ctx: ctx.get('price', 0) > ctx.get(
                    'MA_100', 0) > 0 and ctx.get('SMA_50_slope', 0) > 0,
                evaluate=lambda ctx: ("📗 Value Reclaim", ctx.get(
                    'MA_100', 0), "Trend reversed. Re-enter using standard Buy Point rules.", "RE-ENTER", False, 'buy')
            )
        ]

    # --- EVALUATION METHODS ---

    def evaluate_buy_rules(self, category: str, context: dict) -> Tuple[float, float, str]:
        """
        Evaluate buy rules with falling knife pre-filter.
        Returns (buy_price, stop_price, logic_name).
        If falling knife detected, returns (0, 0, 'FALLING_KNIFE').
        """
        if self.is_falling_knife(context):
            return (0, 0, "FALLING_KNIFE")

        # Momentum-specific QQQ ADX check
        if category == 'Momentum' and context.get('QQQ_ADX_14', 0) < 20:
            return (0, 0, "CHOPPY MARKET - MOMENTUM SUPPRESSED")

        # Select appropriate rule set
        rules_map = {
            'Momentum': self.MOMENTUM_BUY_RULES,
            'Growth': self.GROWTH_BUY_RULES,
            'Core': self.CORE_BUY_RULES,
            'Income': self.INCOME_BUY_RULES
        }
        rules = rules_map.get(category, [])

        for rule in rules:
            if rule.condition(context):
                return rule.evaluate(context)

        return (0, 0, "No Data")

    def evaluate_sell_rules(self, category: str, context: dict) -> Tuple[str, float, str, str, bool, str]:
        """
        Evaluate sell rules.
        Returns (trigger, target, instruction, order_type, condition_met, action_type).
        """
        rules_map = {
            'Momentum': self.MOMENTUM_SELL_RULES,
            'Growth': self.GROWTH_SELL_RULES,
            'Core': self.CORE_SELL_RULES,
            'Income': self.INCOME_SELL_RULES
        }
        rules = rules_map.get(category, [])

        for rule in rules:
            if rule.condition(context):
                return rule.evaluate(context)

        return ("Uncategorized", 0, "No strategy defined.", "NONE", False, 'neutral')

    def evaluate_reentry_rules(self, category: str, context: dict) -> Tuple[str, float, str, str, bool, str]:
        """
        Evaluate re-entry rules for previously held tickers.
        Returns same format as sell rules: (trigger, target, instruction, order_type, condition_met, action_type).
        If falling knife, returns a suppression signal. If no rule matches, returns WAIT."""
        if self.is_falling_knife(context):
            return ("🔪 Falling Knife", 0, "Do not re-enter — price in active decline.", "DO NOT BUY", False, 'sell')

        if category == 'Momentum' and context.get('QQQ_ADX_14', 0) < 20:
            return ("⏳ Waiting", 0, "Momentum re-entry is suppressed. Broad market ADX (< 20) is too choppy.", "WAIT", False, 'neutral')

        rules_map = {
            'Momentum': self.MOMENTUM_REENTRY_RULES,
            'Growth': self.GROWTH_REENTRY_RULES,
            'Core': self.CORE_REENTRY_RULES,
            'Income': self.INCOME_REENTRY_RULES
        }
        rules = rules_map.get(category, [])

        for rule in rules:
            if rule.condition(context):
                trigger, original_target, instruction, order_type, cond_met, act_type = rule.evaluate(context)

                # Fetch the dynamic target from standard buy rules if condition met
                if act_type == 'buy' or cond_met:
                    buy_price, stop_price, buy_logic = self.evaluate_buy_rules(category, context)
                    if buy_price > 0:
                        instruction = f"{instruction} [Using: {buy_logic}]"
                        return (trigger, buy_price, instruction, order_type, cond_met, act_type)

                return (trigger, original_target, instruction, order_type, cond_met, act_type)

        # If no rule matches, determine the primary reason for waiting based on category
        wait_reason = "Continue monitoring."
        price = context.get('price', 0)
        sma50 = context.get('MA_50', 0)
        slope = context.get('SMA_50_slope', 0)

        if category == 'Growth':
            if price <= sma50:
                wait_reason = f"Price (${price:.2f}) is below the 50 SMA (${sma50:.2f})."
            elif slope <= 0:
                wait_reason = f"50 SMA slope ({slope:.2f}%) is not positive."

        elif category == 'Momentum':
            high52 = context.get('High_52', 0)
            adx = context.get('ADX_14', 0)
            if price < high52 * 0.98 and price <= sma50:
                wait_reason = f"Price (${price:.2f}) is below 50 SMA (${sma50:.2f}) and far from 52W High (${high52:.2f})."
            elif price > sma50 and adx < 20:
                wait_reason = f"Price > 50 SMA, but ADX ({adx:.1f}) is too weak (< 20)."

        elif category == 'Core' or category == 'Income':
            sma100 = context.get('MA_100', 0)
            if price <= sma100:
                wait_reason = f"Price (${price:.2f}) is below the 100 SMA (${sma100:.2f})."
            elif slope < 0:
                wait_reason = f"50 SMA slope ({slope:.2f}%) is actively declining."

        return ("⏳ Waiting", 0, f"No re-entry conditions met. {wait_reason}", "WAIT", False, 'neutral')

    def get_all_rules(self) -> Dict[str, Dict[str, List[Rule]]]:
        """Returns a structured dictionary of all rules for displaying."""
        return {
            "⚠️ Falling Knife Filter": {
                "Pre-Filter (Supersedes All Buy/Re-Entry Rules)": [],  # Simplified for display
            },
            "Watchlist": {
                "Growth – Buy Point & Stop Loss": self.GROWTH_BUY_RULES,
                "Momentum – Buy Point & Stop Loss": self.MOMENTUM_BUY_RULES,
                "Core – Buy Point & Stop Loss": self.CORE_BUY_RULES,
                "Income – Buy Point & Stop Loss": self.INCOME_BUY_RULES,
            },
            "Core": {
                "Buy Target": self.CORE_BUY_RULES,
                "Sell Target": self.CORE_SELL_RULES,
                "Re-Entry": self.CORE_REENTRY_RULES
            },
            "Income": {
                "Buy Target": self.INCOME_BUY_RULES,
                "Sell Target": self.INCOME_SELL_RULES,
                "Re-Entry": self.INCOME_REENTRY_RULES
            },
            "Growth": {
                "Buy Target": self.GROWTH_BUY_RULES,
                "Sell Target": self.GROWTH_SELL_RULES,
                "Re-Entry": self.GROWTH_REENTRY_RULES
            },
            "Momentum": {
                "Buy Target": self.MOMENTUM_BUY_RULES,
                "Sell Target": self.MOMENTUM_SELL_RULES,
                "Re-Entry": self.MOMENTUM_REENTRY_RULES
            },
            "TQQQ": {
                "Strategy": self.TQQQ_RULES,
                "Downside Protection": [],  # Simplified
                "Upside Opportunity": []    # Simplified
            }
        }


# Convenience function for backward compatibility
def get_strategy_service() -> StrategyService:
    """Factory function to create a StrategyService instance."""
    return StrategyService()


# Legacy function wrappers for compatibility with existing code
def evaluate_buy_rules(category: str, context: dict) -> Tuple[float, float, str]:
    """Legacy wrapper for evaluate_buy_rules."""
    service = get_strategy_service()
    return service.evaluate_buy_rules(category, context)


def evaluate_sell_rules(category: str, context: dict) -> Tuple[str, float, str, str, bool, str]:
    """Legacy wrapper for evaluate_sell_rules."""
    service = get_strategy_service()
    return service.evaluate_sell_rules(category, context)


def evaluate_reentry_rules(category: str, context: dict) -> Tuple[str, float, str, str, bool, str]:
    """Legacy wrapper for evaluate_reentry_rules."""
    service = get_strategy_service()
    return service.evaluate_reentry_rules(category, context)


def is_falling_knife(context: dict) -> bool:
    """Legacy wrapper for is_falling_knife."""
    service = get_strategy_service()
    return service.is_falling_knife(context)


# Example usage (for testing)
if __name__ == "__main__":
    # This is just a demo; remove or adapt for actual use.
    print("StrategyService refactored from legacy logic_rules.py")
    print("To use, instantiate StrategyService or use the convenience functions.")