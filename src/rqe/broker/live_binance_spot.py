"""
LIVE SPOT EXECUTION (ToS-safe, official endpoints, idempotent clientOrderId).

This file is provided for completeness, but live mode is OFF by default.

You are responsible for:
- enabling trade-only API keys (no withdrawals)
- understanding fees and order rules
- sizing conservatively
"""

import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from dataclasses import dataclass


@dataclass
class LiveFill:
    order_id: int
    status: str
    side: str
    qty: float
    price: float


class RateLimiter:
    def __init__(self, rps: float = 8.0) -> None:
        self.min_dt = 1.0 / max(0.1, rps)
        self.last = 0.0

    def wait(self) -> None:
        now = time.time()
        dt = now - self.last
        if dt < self.min_dt:
            time.sleep(self.min_dt - dt)
        self.last = time.time()


class BinanceSpotLive:
    BASE = "https://api.binance.com"

    def __init__(self, api_key: str, api_secret: str, rps: float = 8.0) -> None:
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.rl = RateLimiter(rps=rps)

    def _sign(self, params: dict) -> dict:
        qs = urlencode(params, doseq=True)
        sig = hmac.new(self.api_secret, qs.encode(), hashlib.sha256).hexdigest()
        params["signature"] = sig
        return params

    def _headers(self) -> dict:
        return {"X-MBX-APIKEY": self.api_key}

    def place_limit(self, symbol: str, side: str, qty: float, price: float, client_order_id: str) -> LiveFill:
        self.rl.wait()
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": f"{qty:.8f}",
            "price": f"{price:.2f}",
            "newClientOrderId": client_order_id,
            "timestamp": int(time.time() * 1000),
        }
        signed = self._sign(params)
        r = requests.post(f"{self.BASE}/api/v3/order", headers=self._headers(), params=signed, timeout=5)
        r.raise_for_status()
        j = r.json()
        return LiveFill(
            order_id=int(j["orderId"]),
            status=j["status"],
            side=side,
            qty=float(qty),
            price=float(price),
        )

    def cancel(self, symbol: str, client_order_id: str) -> dict:
        self.rl.wait()
        params = {"symbol": symbol, "origClientOrderId": client_order_id, "timestamp": int(time.time() * 1000)}
        signed = self._sign(params)
        r = requests.delete(f"{self.BASE}/api/v3/order", headers=self._headers(), params=signed, timeout=5)
        r.raise_for_status()
        return r.json()
