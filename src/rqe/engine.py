import time
import logging
from dataclasses import dataclass
from collections import deque

from rich.console import Console

from .config import Settings
from .log import setup as setup_logging
from .storage import Store
from .metrics import start as start_metrics, TRADES, HALTS, PNL, SLIP, STATE
from .exchange.binance_public import BinancePublic
from .risk import RiskManager, RiskCfg, RiskState
from .validate import Validator
from .portfolio import Weights, allocate
from .broker.paper import PaperBroker
from .strategies.trend import TrendFollowing
from .strategies.pairs import PairsMeanReversion
from .strategies.funding import FundingCarry

log = logging.getLogger("rqe.engine")
console = Console()


@dataclass
class Runtime:
    equity_usd: float = 1000.0  # paper equity baseline (edit later)
    halted: bool = False
    vol_baseline: float = 0.0
    returns_window: deque = deque(maxlen=240)
    last_price: float = 0.0


def _realized_vol(returns):
    if len(returns) < 30:
        return 0.0
    m = sum(returns) / len(returns)
    v = sum((x - m) ** 2 for x in returns) / max(1, len(returns) - 1)
    return v**0.5


def run() -> None:
    s = Settings()

    setup_logging(s.log_level)
    start_metrics(s.metrics_port)

    store = Store(s.db_path)
    pub = BinancePublic()

    risk = RiskManager(
        RiskCfg(
            max_notional_usd=s.max_notional_usd,
            max_daily_loss_pct=s.max_daily_loss_pct,
            daily_take_profit_pct=s.daily_take_profit_pct,
            max_trades_per_day=s.max_trades_per_day,
            max_slippage_bps=s.max_slippage_bps,
            max_api_latency_ms=s.max_api_latency_ms,
            halt_on_vol_spike=bool(s.halt_on_vol_spike),
            vol_spike_mult=s.vol_spike_mult,
        )
    )

    validator = Validator(vol_spike_mult=s.vol_spike_mult)

    trend = TrendFollowing(s.trend_fast, s.trend_slow)
    pairs = PairsMeanReversion(s.pair_lookback, s.pair_z_enter, s.pair_z_exit, s.pair_max_hold_min)
    funding = FundingCarry(s.funding_min, s.funding_hold_hrs)

    broker = PaperBroker()  # default (paper)
    rt = Runtime()

    console.print(f"[bold]RQE[/bold] mode={s.mode} metrics_port={s.metrics_port}")

    while True:
        daily = store.get_daily()
        rt.halted = bool(daily.halted)

        STATE.set(1 if rt.halted else 0)
        PNL.set(daily.realized_pnl_usd)

        # ===== Market data (public REST price; WebSocket upgrade later) =====
        t_spot = pub.price(s.symbol_spot)
        p = t_spot.price

        if rt.last_price > 0:
            r = (p - rt.last_price) / rt.last_price
            rt.returns_window.append(r)
        rt.last_price = p

        # volatility model (shock detection)
        vol_now = _realized_vol(rt.returns_window)
        if rt.vol_baseline == 0.0 and vol_now > 0:
            rt.vol_baseline = vol_now
        if vol_now > 0 and rt.vol_baseline > 0:
            rt.vol_baseline = 0.98 * rt.vol_baseline + 0.02 * vol_now

        # risk state
        st = RiskState(
            equity_usd=rt.equity_usd,
            trades_today=daily.trades,
            realized_pnl_usd=daily.realized_pnl_usd,
            halted=rt.halted,
        )

        ok, reason = risk.daily_limits_ok(st)
        if not ok:
            if not rt.halted:
                HALTS.labels(reason=reason).inc()
                store.update_daily(daily.trades, daily.realized_pnl_usd, 1)
                console.print(f"[red]HALT[/red] reason={reason}")
            time.sleep(s.loop_seconds)
            continue

        # volatility shock gate
        vres = validator.vol_spike(vol_now, rt.vol_baseline)
        if (not vres.ok) and risk.cfg.halt_on_vol_spike:
            HALTS.labels(reason=vres.reason).inc()
            store.update_daily(daily.trades, daily.realized_pnl_usd, 1)
            console.print(
                f"[red]HALT[/red] reason={vres.reason} vol_now={vol_now:.6f} base={rt.vol_baseline:.6f}"
            )
            time.sleep(s.loop_seconds)
            continue

        # ===== Portfolio allocation =====
        alloc = allocate(
            risk.cap_notional(s.max_notional_usd),
            Weights(s.w_trend, s.w_pairs, s.w_funding),
        ).by_strategy_usd

        # ===== Strategy 1: Trend (trade spot) =====
        tsig = trend.on_price(p)
        if tsig.action in ("buy", "flat"):
            slip_bps = min(10.0, risk.cfg.max_slippage_bps)
            usd = alloc["trend"]
            qty = usd / p if usd > 0 else 0.0

            if tsig.action == "buy" and qty > 0:
                fill = broker.buy(qty, p, slip_bps=slip_bps)
                SLIP.set(fill.slippage_bps)
                store.log_fill(
                    s.mode,
                    "trend",
                    s.symbol_spot,
                    "buy",
                    fill.qty,
                    fill.price,
                    fill.fee,
                    0.0,
                    f"strength={tsig.strength:.6f}",
                )
                daily.trades += 1
                TRADES.labels(mode=s.mode, strategy="trend").inc()

            if tsig.action == "flat":
                fill = broker.flatten(p)
                SLIP.set(fill.slippage_bps)
                store.log_fill(
                    s.mode,
                    "trend",
                    s.symbol_spot,
                    "flat",
                    fill.qty,
                    fill.price,
                    fill.fee,
                    fill.pnl,
                    "trend_exit",
                )
                daily.trades += 1
                daily.realized_pnl_usd += fill.pnl
                TRADES.labels(mode=s.mode, strategy="trend").inc()

        # ===== Strategy 2: Pairs stat-arb (signal-only, paper proxy) =====
        a = pub.price(s.pair_a).price
        b = pub.price(s.pair_b).price
        psig = pairs.on_prices(a, b)

        if psig.action in ("enter_long_spread", "enter_short_spread", "exit"):
            slip_bps = min(12.0, risk.cfg.max_slippage_bps)
            usd = alloc["pairs"]
            qty = usd / a if usd > 0 else 0.0

            if psig.action in ("enter_long_spread", "enter_short_spread") and qty > 0:
                side = "buy" if psig.action == "enter_long_spread" else "sell"
                fill = broker.buy(qty, a, slip_bps) if side == "buy" else broker.sell(qty, a, slip_bps)
                SLIP.set(fill.slippage_bps)
                store.log_fill(
                    s.mode,
                    "pairs",
                    s.pair_a,
                    side,
                    fill.qty,
                    fill.price,
                    fill.fee,
                    fill.pnl,
                    f"z={psig.z:.3f}",
                )
                daily.trades += 1
                daily.realized_pnl_usd += fill.pnl
                TRADES.labels(mode=s.mode, strategy="pairs").inc()

            if psig.action == "exit":
                fill = broker.flatten(a)
                SLIP.set(fill.slippage_bps)
                store.log_fill(
                    s.mode,
                    "pairs",
                    s.pair_a,
                    "flat",
                    fill.qty,
                    fill.price,
                    fill.fee,
                    fill.pnl,
                    f"exit z={psig.z:.3f}",
                )
                daily.trades += 1
                daily.realized_pnl_usd += fill.pnl
                TRADES.labels(mode=s.mode, strategy="pairs").inc()

        # ===== Strategy 3: Funding carry (signal-only MVP) =====
        f_rate = 0.0
        fsig = funding.on_funding(f_rate)
        store.log_fill(
            s.mode,
            "funding",
            s.symbol_perp,
            fsig.action,
            0.0,
            0.0,
            0.0,
            0.0,
            f"funding={fsig.funding}",
        )

        # persist day state
        store.update_daily(daily.trades, daily.realized_pnl_usd, 0)
        PNL.set(daily.realized_pnl_usd)

        log.info(
            "px=%.2f pnl=%.2f trades=%d vol=%.6f base=%.6f trend=%s pairs=%s",
            p,
            daily.realized_pnl_usd,
            daily.trades,
            vol_now,
            rt.vol_baseline,
            tsig.action,
            psig.action,
        )

        time.sleep(s.loop_seconds)
