"""
Risk management: decides HOW MUCH to trade, not WHETHER to trade.
Keeping this separate from the strategy means you can't accidentally
bet the whole account on one signal.
"""

from dataclasses import dataclass


@dataclass
class RiskManager:
    risk_per_trade: float   # fraction of equity risked per trade, e.g. 0.02
    stop_loss_pct: float
    take_profit_pct: float

    def position_size(self, equity: float, entry_price: float) -> float:
        """
        Returns quantity to buy, sized so that if the stop loss is hit,
        the loss equals risk_per_trade * equity — not the whole position.
        """
        risk_amount = equity * self.risk_per_trade
        stop_distance = entry_price * self.stop_loss_pct
        if stop_distance <= 0:
            return 0.0
        qty = risk_amount / stop_distance
        # Never size a position larger than the account can actually pay for
        max_affordable_qty = equity / entry_price
        return max(0.0, min(qty, max_affordable_qty))

    def stop_loss_price(self, entry_price: float, side: str) -> float:
        return entry_price * (1 - self.stop_loss_pct) if side == "BUY" \
            else entry_price * (1 + self.stop_loss_pct)

    def take_profit_price(self, entry_price: float, side: str) -> float:
        return entry_price * (1 + self.take_profit_pct) if side == "BUY" \
            else entry_price * (1 - self.take_profit_pct)
