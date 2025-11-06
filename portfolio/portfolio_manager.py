from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
import os


@dataclass
class Position:
    symbol: str
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl_realized: float = 0.0
    closed: bool = False
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None


class PortfolioManager:
    def __init__(self,
                 initial_cash: float = 1000,
                 max_risk_per_trade: float = 0.02,
                 default_stop: float = 0.02,
                 default_tp: float = 0.05,
                 fee_rate: float = 0.0005):

        self.cash = float(initial_cash)
        self.initial_cash = float(initial_cash)
        self.max_risk_per_trade = float(max_risk_per_trade)
        self.default_stop = float(default_stop)
        self.default_tp = float(default_tp)
        self.fee_rate = float(fee_rate)

        self.positions: Dict[str, Position] = {}
        self.trade_history = []             # list of buy/sell trade dicts
        self.portfolio_snapshots = []       # list of portfolio snapshot dicts (total_value etc)
        self.unrealized_pnl = 0.0

    # --- Risk Management ---
    def _calc_risk_budget(self):
        return self.initial_cash * self.max_risk_per_trade

    def size_from_risk(self, symbol: str, entry_price: float, stop_loss_pct: Optional[float] = None):
        sl = stop_loss_pct if stop_loss_pct is not None else self.default_stop
        if sl <= 0:
            raise ValueError("stop_loss_pct must be > 0 for risk sizing")
        risk_budget = self._calc_risk_budget()
        risk_per_unit = entry_price * sl
        raw_qty = risk_budget / risk_per_unit
        max_affordable_qty = self.cash / entry_price
        qty = min(raw_qty, max_affordable_qty)
        return round(max(qty, 0.0), 8)

    # --- Trading Operations ---
    def open_position(self, symbol: str, entry_price: float, quantity: float,
                      stop_loss_pct: Optional[float] = None,
                      take_profit_pct: Optional[float] = None,
                      now=None):

        now = now or datetime.utcnow()
        if quantity <= 0:
            return None

        fee = entry_price * quantity * self.fee_rate
        cost = entry_price * quantity + fee

        if cost > self.cash:
            # not enough cash
            return None

        sl = stop_loss_pct if stop_loss_pct is not None else self.default_stop
        tp = take_profit_pct if take_profit_pct is not None else self.default_tp

        pos = Position(
            symbol=symbol,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=now,
            stop_loss=entry_price * (1 - sl),
            take_profit=entry_price * (1 + tp)
        )

        self.positions[symbol] = pos
        self.cash -= cost

        self.trade_history.append({
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "action": "BUY",
            "price": entry_price,
            "quantity": quantity,
            "fee": round(fee, 8),
            "cash_after": round(self.cash, 8)
        })
        return pos

    def close_position(self, symbol: str, exit_price: float, now=None):
        now = now or datetime.utcnow()
        pos = self.positions.get(symbol)
        if not pos:
            return None

        fee = exit_price * pos.quantity * self.fee_rate
        proceeds = exit_price * pos.quantity - fee
        cost_basis = pos.entry_price * pos.quantity + pos.entry_price * pos.quantity * self.fee_rate
        pnl = proceeds - cost_basis
        self.cash += proceeds

        pos.exit_price = exit_price
        pos.exit_time = now
        pos.closed = True
        pos.pnl_realized = round(pnl, 8)

        self.trade_history.append({
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "action": "SELL",
            "price": exit_price,
            "quantity": pos.quantity,
            "fee": round(fee, 8),
            "pnl": round(pnl, 8),
            "cash_after": round(self.cash, 8)
        })

        # remove from open positions
        del self.positions[symbol]
        return pos

    # --- Monitoring ---
    def mark_to_market(self, market_prices: Dict[str, float], record_snapshot: bool = False):
        """
        Update unrealized_pnl and optionally append a portfolio snapshot record.
        market_prices: {'BTCUSDT': price, ...}
        If record_snapshot=True it will append a snapshot containing total_value, cash and unrealized_pnl.
        """
        unreal = 0.0
        for s, pos in self.positions.items():
            if s not in market_prices:
                continue
            price = float(market_prices[s])
            unreal += (price - pos.entry_price) * pos.quantity

        self.unrealized_pnl = round(unreal, 8)

        if record_snapshot:
            total_value = self.portfolio_value(market_prices)
            snapshot = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "cash": round(self.cash, 8),
                "unrealized_pnl": round(self.unrealized_pnl, 8),
                "total_value": round(total_value, 8),
                "open_positions": len(self.positions)
            }
            # append snapshot
            self.portfolio_snapshots.append(snapshot)

        return self.unrealized_pnl

    def check_stops_and_tps(self, market_prices: Dict[str, float], now=None):
        """Automatically close positions that hit SL or TP."""
        now = now or datetime.utcnow()
        closed = []
        for s, pos in list(self.positions.items()):
            price = market_prices.get(s)
            if price is None:
                continue
            if pos.stop_loss is not None and price <= pos.stop_loss:
                closed.append(("STOP", s, price))
                self.close_position(s, price, now=now)
            elif pos.take_profit is not None and price >= pos.take_profit:
                closed.append(("TP", s, price))
                self.close_position(s, price, now=now)
        return closed

    # --- Summary ---
    def portfolio_value(self, market_prices: Dict[str, float]):
        total = self.cash
        for s, pos in self.positions.items():
            price = float(market_prices.get(s, pos.entry_price))
            total += pos.quantity * price
        return round(total, 8)

    def summary(self, prices: dict):
        total_value = self.portfolio_value(prices)
        roi = (total_value - self.initial_cash) / self.initial_cash * 100
        return {
            "cash": round(self.cash, 2),
            "total_value": round(total_value, 2),
            "roi_%": round(roi, 2),
            "open_positions": len(self.positions),
            "unrealized_pnl": round(self.unrealized_pnl, 2)
        }

    # --- Logging ---
    def save_history_csv(self, path="portfolio_trades.csv"):
        """
        Saves:
          - trade_history -> path (CSV)
          - portfolio_snapshots -> same_dir/portfolio_snapshots_<timestamp>.csv
        """
        # make dir
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        # save trades (even if empty, keep columns consistent)
        trades_cols = ["timestamp", "symbol", "action", "price", "quantity", "fee", "pnl", "cash_after"]
        if not self.trade_history:
            trades_df = pd.DataFrame(columns=trades_cols)
            print("⚠️ No trades recorded — saving empty trade history file.")
        else:
            trades_df = pd.DataFrame(self.trade_history)
            # ensure all columns exist
            for c in trades_cols:
                if c not in trades_df.columns:
                    trades_df[c] = None

        trades_df.to_csv(path, index=False)
        print(f"🪵 Trade history saved to: {path}")

        # save portfolio snapshots
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshots_path = os.path.join(os.path.dirname(path) or ".", f"portfolio_snapshots_{ts}.csv")
        if not self.portfolio_snapshots:
            snapshots_df = pd.DataFrame(columns=["timestamp", "cash", "unrealized_pnl", "total_value", "open_positions"])
            print("⚠️ No portfolio snapshots recorded — saving empty snapshot file.")
        else:
            snapshots_df = pd.DataFrame(self.portfolio_snapshots)

        snapshots_df.to_csv(snapshots_path, index=False)
        print(f"🪵 Portfolio snapshots saved to: {snapshots_path}")