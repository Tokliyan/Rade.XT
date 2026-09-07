"""
Runs a strategy over historical candles and reports how it would have
performed. Use this to sanity-check an idea BEFORE ever running it live,
paper or otherwise.

Caveat that matters more than any of the code: it's very easy to tune a
strategy until it looks great on one historical window and then watch it
fail on new data (overfitting). A good backtest is necessary, not
sufficient.
"""

from dataclasses import dataclass
import pandas as pd

from broker import PaperBroker
from risk_manager import RiskManager


@dataclass
class BacktestResult:
    final_equity: float
    starting_equity: float
    total_return_pct: float
    num_trades: int
    max_drawdown_pct: float

    def summary(self) -> str:
        return (
            f"Start equity:   ${self.starting_equity:,.2f}\n"
            f"Final equity:   ${self.final_equity:,.2f}\n"
            f"Total return:   {self.total_return_pct:+.2f}%\n"
            f"Trades taken:   {self.num_trades}\n"
            f"Max drawdown:   {self.max_drawdown_pct:.2f}%"
        )


def run_backtest(df: pd.DataFrame, agent_config, symbol: str, log_path: str = "backtest_log.csv") -> BacktestResult:
    """
    agent_config: an AgentConfig from config.py (uses .strategy, .starting_balance,
    .fee_pct, .risk_per_trade, .stop_loss_pct, .take_profit_pct)
    """
    strategy = agent_config.strategy
    broker = PaperBroker(starting_balance=agent_config.starting_balance, fee_pct=agent_config.fee_pct, log_path=log_path)
    risk = RiskManager(agent_config.risk_per_trade, agent_config.stop_loss_pct, agent_config.take_profit_pct)

    equity_curve = []
    position_side = None
    entry_price = None
    trades = 0

    for i in range(30, len(df)):
        window = df.iloc[: i + 1]
        price = window["close"].iloc[-1]
        ts = window.index[-1]
        signal = strategy.generate_signal(window)

        if position_side == "BUY":
            sl = risk.stop_loss_price(entry_price, "BUY")
            tp = risk.take_profit_price(entry_price, "BUY")
            if price <= sl or price >= tp:
                qty = broker.positions.get(symbol, 0.0)
                broker.execute(ts, symbol, "SELL", qty, price)
                position_side, entry_price = None, None
                trades += 1

        if signal == "BUY" and position_side is None:
            equity = broker.equity({symbol: price})
            qty = risk.position_size(equity, price)
            broker.execute(ts, symbol, "BUY", qty, price)
            position_side, entry_price = "BUY", price
            trades += 1
        elif signal == "SELL" and position_side == "BUY":
            qty = broker.positions.get(symbol, 0.0)
            broker.execute(ts, symbol, "SELL", qty, price)
            position_side, entry_price = None, None
            trades += 1

        equity_curve.append(broker.equity({symbol: price}))

    final_price = df["close"].iloc[-1]
    final_equity = broker.equity({symbol: final_price})

    series = pd.Series(equity_curve)
    running_max = series.cummax()
    drawdown = (series - running_max) / running_max
    max_dd = drawdown.min() * 100 if len(drawdown) else 0.0

    return BacktestResult(
        final_equity=final_equity,
        starting_equity=agent_config.starting_balance,
        total_return_pct=(final_equity / agent_config.starting_balance - 1) * 100,
        num_trades=trades,
        max_drawdown_pct=abs(max_dd),
    )
