from dataclasses import dataclass
from prometheus_client import Counter, Gauge, start_http_server

TRADES = Counter("rqe_trades_total", "Total trades", ["mode", "strategy"])
HALTS = Counter("rqe_halts_total", "Total halts", ["reason"])
PNL = Gauge("rqe_realized_pnl_usd", "Realized PnL USD")
LAT_MS = Gauge("rqe_api_latency_ms", "API latency ms")
SLIP = Gauge("rqe_slippage_bps", "Last slippage bps")
STATE = Gauge("rqe_halted", "Halted flag (1/0)")


@dataclass
class MetricsRuntime:
    started: bool = False


runtime = MetricsRuntime()


def start(port: int) -> None:
    if runtime.started:
        return
    start_http_server(port)
    runtime.started = True
