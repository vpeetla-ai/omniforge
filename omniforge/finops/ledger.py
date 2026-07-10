
"""In-repo FinOps ledger — no agent-finops dependency."""
from __future__ import annotations

from omniforge.models import RoutingDecision


class BudgetLedger:
    def __init__(self, budget_usd: float) -> None:
        self.budget_usd = budget_usd
        self.spent = 0.0
        self.halted = False

    def record(self, decision: RoutingDecision) -> None:
        self.spent += decision.cost_usd
        if self.spent > self.budget_usd:
            self.halted = True

    @property
    def remaining(self) -> float:
        return max(0.0, self.budget_usd - self.spent)
