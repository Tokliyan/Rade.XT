"""
Strategy layer.

A "strategy" is just a function: DataFrame of candles -> Signal.
Swap SmaCrossStrategy out for your own idea by matching the same
interface (a `generate_signal(df)` method returning "BUY"/"SELL"/"HOLD").

IMPORTANT: SmaCrossStrategy below is a well-known textbook example
(moving-average crossover), included so the bot has something to run
out of the box. It is not a profitable strategy on its own — on most
assets, most of the time, it roughly breaks even before fees and loses
after them. Treat it as a template to build on and backtest, not
something to trade with real money as-is.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class SmaCrossStrategy:
    fast_period: int = 10
    slow_period: int = 30

    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < self.slow_period + 1:
            return "HOLD"

        fast = df["close"].rolling(self.fast_period).mean()
        slow = df["close"].rolling(self.slow_period).mean()

        prev_diff = fast.iloc[-2] - slow.iloc[-2]
        curr_diff = fast.iloc[-1] - slow.iloc[-1]

        if prev_diff <= 0 and curr_diff > 0:
            return "BUY"
        if prev_diff >= 0 and curr_diff < 0:
            return "SELL"
        return "HOLD"


@dataclass
class RsiMeanReversionStrategy:
    """
    A second, genuinely different approach from SmaCrossStrategy: instead
    of following momentum, this bets that a price that's moved too far
    too fast will snap back. Same caveat as the other strategy — a
    reasonable template to test and refine, not a guaranteed edge.
    """
    period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0

    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < self.period + 1:
            return "HOLD"

        delta = df["close"].diff()
        gains = delta.clip(lower=0).rolling(self.period).mean()
        losses = (-delta.clip(upper=0)).rolling(self.period).mean()

        rs = gains / losses.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        last_rsi = rsi.iloc[-1]

        if pd.isna(last_rsi):
            return "HOLD"
        if last_rsi < self.oversold:
            return "BUY"
        if last_rsi > self.overbought:
            return "SELL"
        return "HOLD"
