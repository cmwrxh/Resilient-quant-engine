from dataclasses import dataclass
from typing import Dict


@dataclass
class Weights:
    trend: float
    pairs: float
    funding: float


@dataclass
class Alloc:
    by_strategy_usd: Dict[str, float]


def normalize_weights(w: Weights) -> Weights:
    s = max(1e-9, w.trend + w.pairs + w.funding)
    return Weights(w.trend / s, w.pairs / s, w.funding / s)


def allocate(notional_usd: float, w: Weights) -> Alloc:
    w = normalize_weights(w)
    return Alloc(
        {
            "trend": notional_usd * w.trend,
            "pairs": notional_usd * w.pairs,
            "funding": notional_usd * w.funding,
        }
    )
