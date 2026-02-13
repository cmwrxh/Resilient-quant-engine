from dataclasses import dataclass
import time


@dataclass
class FundingSignal:
    action: str  # hold | enable | disable
    funding: float


class FundingCarry:
    """Signal-only starter (execution can be added later with perps + hedge)."""

    def __init__(self, funding_min: float, hold_hrs: int) -> None:
        self.funding_min = funding_min
        self.hold_hrs = hold_hrs
        self.enabled = False
        self.until = 0.0

    def on_funding(self, funding_rate: float) -> FundingSignal:
        now = time.time()

        if self.enabled and now < self.until:
            return FundingSignal("hold", funding_rate)

        if funding_rate >= self.funding_min:
            self.enabled = True
            self.until = now + self.hold_hrs * 3600
            return FundingSignal("enable", funding_rate)

        self.enabled = False
        return FundingSignal("disable", funding_rate)
