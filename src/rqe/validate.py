from dataclasses import dataclass


@dataclass
class ValidationResult:
    ok: bool
    reason: str


class Validator:
    """
    Constant revalidation:
    - if volatility shock, stop mean reversion/pairs
    - if edge decays, size down

    Intentionally simple and robust.
    """

    def __init__(self, vol_spike_mult: float) -> None:
        self.vol_spike_mult = vol_spike_mult

    def vol_spike(self, vol_now: float, vol_baseline: float) -> ValidationResult:
        if vol_baseline <= 0:
            return ValidationResult(True, "no_baseline")
        if vol_now >= self.vol_spike_mult * vol_baseline:
            return ValidationResult(False, "vol_spike")
        return ValidationResult(True, "ok")
