from dataclasses import dataclass
from collections import deque


@dataclass
class TrendSignal:
    action: str  # buy | sell | hold | flat
    strength: float


class TrendFollowing:
    def __init__(self, fast: int, slow: int) -> None:
        self.fast = fast
        self.slow = slow
        self.prices = deque(maxlen=max(fast, slow))
        self.in_pos = False
        self.side = None

    def _ma(self, n: int) -> float:
        xs = list(self.prices)[-n:]
        return sum(xs) / max(1, len(xs))

    def on_price(self, price: float) -> TrendSignal:
        self.prices.append(price)
        if len(self.prices) < self.slow:
            return TrendSignal("hold", 0.0)

        f = self._ma(self.fast)
        s = self._ma(self.slow)
        strength = (f - s) / s

        if f > s and (not self.in_pos or self.side != "long"):
            self.in_pos = True
            self.side = "long"
            return TrendSignal("buy", strength)

        if f < s and self.in_pos and self.side == "long":
            self.in_pos = False
            self.side = None
            return TrendSignal("flat", strength)

        return TrendSignal("hold", strength)
