import os
from pydantic import BaseModel


def _s(k: str, d: str) -> str:
    return os.getenv(k, d)


class Settings(BaseModel):
    mode: str = _s("MODE", "paper")

    binance_api_key: str = _s("BINANCE_API_KEY", "")
    binance_api_secret: str = _s("BINANCE_API_SECRET", "")

    symbol_spot: str = _s("SYMBOL_SPOT", "BTCUSDT")
    symbol_perp: str = _s("SYMBOL_PERP", "BTCUSDT")

    max_notional_usd: float = float(_s("MAX_NOTIONAL_USD", "100"))
    max_daily_loss_pct: float = float(_s("MAX_DAILY_LOSS_PCT", "0.02"))
    daily_take_profit_pct: float = float(_s("DAILY_TAKE_PROFIT_PCT", "0.03"))
    max_trades_per_day: int = int(_s("MAX_TRADES_PER_DAY", "20"))
    max_slippage_bps: float = float(_s("MAX_SLIPPAGE_BPS", "15"))
    max_api_latency_ms: int = int(_s("MAX_API_LATENCY_MS", "800"))
    halt_on_vol_spike: int = int(_s("HALT_ON_VOL_SPIKE", "1"))
    vol_spike_mult: float = float(_s("VOL_SPIKE_MULT", "3.0"))

    w_trend: float = float(_s("W_TREND", "0.35"))
    w_pairs: float = float(_s("W_PAIRS", "0.35"))
    w_funding: float = float(_s("W_FUNDING", "0.30"))

    trend_fast: int = int(_s("TREND_FAST", "50"))
    trend_slow: int = int(_s("TREND_SLOW", "200"))
    trend_vol_target_pct: float = float(_s("TREND_VOL_TARGET_PCT", "0.007"))

    pair_a: str = _s("PAIR_A", "BTCUSDT")
    pair_b: str = _s("PAIR_B", "ETHUSDT")
    pair_lookback: int = int(_s("PAIR_LOOKBACK", "240"))
    pair_z_enter: float = float(_s("PAIR_Z_ENTER", "2.2"))
    pair_z_exit: float = float(_s("PAIR_Z_EXIT", "0.7"))
    pair_max_hold_min: int = int(_s("PAIR_MAX_HOLD_MIN", "240"))

    funding_min: float = float(_s("FUNDING_MIN", "0.0005"))
    funding_hold_hrs: int = int(_s("FUNDING_HOLD_HRS", "8"))

    loop_seconds: float = float(_s("LOOP_SECONDS", "2"))
    log_level: str = _s("LOG_LEVEL", "INFO")
    db_path: str = _s("DB_PATH", "./rqe.sqlite")
    metrics_port: int = int(_s("METRICS_PORT", "9108"))
