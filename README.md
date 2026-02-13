# resilient-quant-engine (RQE) — by @cmwrxh

A reliability-first crypto trading engine that runs a **portfolio of edges**:

- **Trend following** (time-series momentum; volatility-aware gating)
- **Pairs stat-arb** (spread mean reversion with time stops)
- **Funding carry** (signal-only MVP; execution optional)

Wrapped in:

- **Execution safety**: slippage guardrails, conservative sizing, idempotent order intent concept
- **Risk modeling**: daily stop-loss / take-profit, max notional, max trades/day, volatility shock halts
- **Monitoring**: Prometheus metrics + SQLite audit log + daily state

> Paper mode is the default. Live trading modules exist but are **OFF** unless you explicitly set `MODE=live`.

---

## Quickstart (Paper)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c "from dotenv import load_dotenv; load_dotenv(); import sys; sys.path.append('src'); from rqe.engine import run; run()"
