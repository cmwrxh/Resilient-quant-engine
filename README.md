# resilient-quant-engine (RQE) — by @cmwrxh

<p align="left">
  <img src="assets/rqe-emblem.png" width="220"/>
</p>

A reliability-first crypto trading engine designed around a **portfolio of trading edges** with strong safety, monitoring, and deployment practices.

---

# 🚀 Overview

RQE runs multiple trading strategies within a controlled, observable, and risk-gated environment:

### Strategies
- **Trend Following**
  - Time-series momentum
  - Volatility-aware signal gating

- **Pairs Statistical Arbitrage**
  - Spread mean reversion
  - Time-based exit safety

- **Funding Carry**
  - Signal framework for perp funding arbitrage
  - Execution optional (MVP mode)

---

# 🛡 Core Principles

### Execution Safety
- Slippage guardrails  
- Conservative sizing  
- Idempotent execution design  

### Risk Modeling
- Daily stop-loss  
- Daily take-profit  
- Maximum notional exposure  
- Maximum trades per day  
- Volatility shock halts  

### Monitoring
- Prometheus metrics  
- SQLite audit trail  
- Daily runtime state tracking  

> Default runtime mode = **Paper Trading**  
> Live trading modules exist but are disabled until `MODE=live`.

---

# ⚡ Quickstart (Paper)

## 1️⃣ Create Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
