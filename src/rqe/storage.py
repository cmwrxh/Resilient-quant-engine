import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS fills(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  mode TEXT NOT NULL,
  strategy TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  fee REAL NOT NULL,
  pnl REAL NOT NULL,
  note TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily(
  day TEXT PRIMARY KEY,
  trades INTEGER NOT NULL,
  realized_pnl_usd REAL NOT NULL,
  halted INTEGER NOT NULL
);
"""


def _day_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _ts_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class DailyState:
    day: str
    trades: int
    realized_pnl_usd: float
    halted: int


class Store:
    def __init__(self, path: str) -> None:
        self.path = path
        with sqlite3.connect(self.path) as con:
            con.executescript(SCHEMA)

    def get_daily(self) -> DailyState:
        d = _day_utc()
        with sqlite3.connect(self.path) as con:
            row = con.execute(
                "SELECT day,trades,realized_pnl_usd,halted FROM daily WHERE day=?",
                (d,),
            ).fetchone()
            if row:
                return DailyState(*row)
            con.execute(
                "INSERT INTO daily(day,trades,realized_pnl_usd,halted) VALUES(?,?,?,?)",
                (d, 0, 0.0, 0),
            )
            return DailyState(d, 0, 0.0, 0)

    def update_daily(self, trades: int, realized_pnl_usd: float, halted: int) -> None:
        d = _day_utc()
        with sqlite3.connect(self.path) as con:
            con.execute(
                "UPDATE daily SET trades=?, realized_pnl_usd=?, halted=? WHERE day=?",
                (trades, realized_pnl_usd, halted, d),
            )

    def log_fill(
        self,
        mode: str,
        strategy: str,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        fee: float,
        pnl: float,
        note: str,
    ) -> None:
        with sqlite3.connect(self.path) as con:
            con.execute(
                "INSERT INTO fills(ts,mode,strategy,symbol,side,qty,price,fee,pnl,note) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (_ts_utc(), mode, strategy, symbol, side, qty, price, fee, pnl, note),
            )
