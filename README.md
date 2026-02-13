# resilient-quant-engine (RQE) — by @cmwrxh

<p align="left">
  <img src="assets/rqe-emblem.png" width="220"/>
</p>

A reliability-first crypto trading engine that runs a **portfolio of edges**:

- **Trend following** (time-series momentum; volatility-aware gating)
- **Pairs stat-arb** (spread mean reversion with time stops)
- **Funding carry** (signal-only MVP; execution optional)

---

## Core Principles

- **Execution safety**
  - Slippage guardrails
  - Conservative sizing
  - Idempotent order intent design

- **Risk modeling**
  - Daily stop-loss / take-profit
  - Max notional exposure
  - Max trades per day
  - Volatility shock halts

- **Monitoring**
  - Prometheus metrics
  - SQLite audit log
  - Daily runtime state tracking

> Paper mode is the default.  
> Live trading modules exist but are **OFF** unless `MODE=live`.

---

# Quickstart (Paper Mode)

## 1️⃣ Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
