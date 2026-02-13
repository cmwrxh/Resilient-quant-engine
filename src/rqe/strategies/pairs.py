from dataclasses import dataclass
from collections import deque
import math
import time


@dataclass
class PairsSignal:
    action: str  # enter_long_spread | enter_short_spread | exit | hold
    z: float


class PairsMeanReversion:
    def __init__(self, lookback: int, z_enter: float, z_exit: float, max_hold_min: int) -> None:
        self.lookback = lookback
        self.z_enter = z_enter
        self.z_exit = z_exit
        self.max_hold_min = max_hold_min

        self.spread = deque(maxlen=lookback)
        self.in_pos = False
        self.side = None
        self.enter_ts = 0.0

    def _stats(self):
        xs = list(self.spread)
        m = sum(xs) / len(xs)
        v = sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)
        return m, math.sqrt(v) if v > 0 else 0.0

    def on_prices(self, a: float, b: float) -> PairsSignal:
        s = math.log(max(1e-9, a)) - math.log(max(1e-9, b))
        self.spread.append(s)

        if len(self.spread) < self.lookback:
            return PairsSignal("hold", 0.0)

        m, sd = self._stats()
        if sd == 0:
            return PairsSignal("hold", 0.0)

        z = (s - m) / sd

        # time stop
        if self.in_pos and (time.time() - self.enter_ts) > self.max_hold_min * 60:
            self.in_pos = False
            self.side = None
            return PairsSignal("exit", z)

        if not self.in_pos:
            if z >= self.z_enter:
                self.in_pos = True
                self.side = "short_spread"
                self.enter_ts = time.time()
                return PairsSignal("enter_short_spread", z)

            if z <= -self.z_enter:
                self.in_pos = True
                self.side = "long_spread"
                self.enter_ts = time.time()
                return PairsSignal("enter_long_spread", z)

            return PairsSignal("hold", z)

        # exit
        if self.side == "long_spread" and z >= -self.z_exit:
            self.in_pos = False
            self.side = None
            return PairsSignal("exit", z)

        if self.side == "short_spread" and z <= self.z_exit:
            self.in_pos = False
            self.side = None
            return PairsSignal("exit", z)

        return PairsSignal("hold", z)
