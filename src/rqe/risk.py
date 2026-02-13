from dataclasses import dataclass


@dataclass
class RiskCfg:
    max_notional_usd: float
    max_daily_loss_pct: float
    daily_take_profit_pct: float
    max_trades_per_day: int
    max_slippage_bps: float
    max_api_latency_ms: int
    halt_on_vol_spike: bool
    vol_spike_mult: float


@dataclass
class RiskState:
    equity_usd: float
    trades_today: int
    realized_pnl_usd: float
    halted: bool


class RiskManager:
    def __init__(self, cfg: RiskCfg) -> None:
        self.cfg = cfg

    def daily_limits_ok(self, st: RiskState) -> tuple[bool, str]:
        if st.halted:
            return False, "halted"

        if st.trades_today >= self.cfg.max_trades_per_day:
            return False, "max_trades_per_day"

        loss_limit = -abs(self.cfg.max_daily_loss_pct) * st.equity_usd
        if st.realized_pnl_usd <= loss_limit:
            return False, "daily_stop_loss"

        tp_limit = abs(self.cfg.daily_take_profit_pct) * st.equity_usd
        if st.realized_pnl_usd >= tp_limit:
            return False, "daily_take_profit"

        return True, "ok"

    def cap_notional(self, desired_usd: float) -> float:
        return min(desired_usd, self.cfg.max_notional_usd)
