import time
import requests
from dataclasses import dataclass

from ..metrics import LAT_MS


@dataclass
class Ticker:
    price: float
    latency_ms: float


class BinancePublic:
    BASE = "https://api.binance.com"

    def price(self, symbol: str) -> Ticker:
        t0 = time.time()
        r = requests.get(
            f"{self.BASE}/api/v3/ticker/price",
            params={"symbol": symbol},
            timeout=5,
        )
        r.raise_for_status()
        ms = (time.time() - t0) * 1000.0
        LAT_MS.set(ms)
        return Ticker(price=float(r.json()["price"]), latency_ms=ms)
