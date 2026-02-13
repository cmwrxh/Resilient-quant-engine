from dataclasses import dataclass


@dataclass
class Fill:
    side: str
    qty: float
    price: float
    fee: float
    pnl: float
    slippage_bps: float


class PaperBroker:
    def __init__(self, fee_bps: float = 10.0) -> None:
        self.fee_bps = fee_bps
        self.pos_qty = 0.0
        self.avg = 0.0
        self.realized = 0.0

    def _fee(self, notional: float) -> float:
        return notional * (self.fee_bps / 10_000.0)

    def buy(self, qty: float, price: float, slip_bps: float = 5.0) -> Fill:
        fill_px = price * (1 + slip_bps / 10_000.0)
        notional = qty * fill_px
        fee = self._fee(notional)

        new_qty = self.pos_qty + qty
        self.avg = ((self.avg * self.pos_qty) + (fill_px * qty)) / new_qty if new_qty else 0.0
        self.pos_qty = new_qty

        return Fill("buy", qty, fill_px, fee, 0.0, slip_bps)

    def sell(self, qty: float, price: float, slip_bps: float = 5.0) -> Fill:
        fill_px = price * (1 - slip_bps / 10_000.0)
        notional = qty * fill_px
        fee = self._fee(notional)

        pnl = 0.0
        if self.pos_qty > 0:
            close = min(qty, self.pos_qty)
            pnl = (fill_px - self.avg) * close - fee
            self.pos_qty -= close
            if self.pos_qty == 0:
                self.avg = 0.0
            self.realized += pnl
        else:
            pnl = -fee
            self.realized += pnl

        return Fill("sell", qty, fill_px, fee, pnl, slip_bps)

    def flatten(self, price: float) -> Fill:
        if self.pos_qty > 0:
            return self.sell(self.pos_qty, price, slip_bps=10.0)
        return Fill("flat", 0.0, price, 0.0, 0.0, 0.0)
