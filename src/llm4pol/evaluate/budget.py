"""The budget meter: two currencies, counted separately (charter section 4 A-3; CONTEXT D-04).

``BudgetMeter`` carries ``evals`` (an integer count of charged candidates)
and ``cpu_hours`` (a float, 0.0 for the ``table`` backend, set by M9) as two
separate fields. This package never merges the two into one number: no
attribute, method or arithmetic here combines them, and the guard test
``tests/test_evaluate_cache_budget.py::test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies``
reads this module's source to keep it so. Only ``evals`` is limited at M2
(``remaining`` / ``exhausted``); ``cpu_hours`` is summed and reported.

The meter is frozen (the coding-style immutability rule): ``charge`` returns
a new meter and the ``Evaluator`` replaces its reference after a request
commits (RESEARCH Pattern 6). ``BudgetExceeded`` is the structured refusal
the evaluator raises *before* committing anything when a request's distinct
uncached ``ok`` candidates would exceed the remaining limit (Pattern 4); it
is never a per-result status.
"""

from __future__ import annotations

from dataclasses import dataclass

from llm4pol.evaluate.contract import Cost


@dataclass(frozen=True, slots=True)
class BudgetMeter:
    """What has been spent so far, in two currencies that stay apart."""

    evals: int = 0
    cpu_hours: float = 0.0

    def charge(self, cost: Cost) -> BudgetMeter:
        """A new meter with ``cost`` spent on top of this one."""
        return BudgetMeter(evals=self.evals + cost.evals, cpu_hours=self.cpu_hours + cost.cpu_hours)

    def remaining(self, evals_limit: int) -> int:
        """How many ``evals`` are left under ``evals_limit`` (never negative)."""
        return max(evals_limit - self.evals, 0)

    def exhausted(self, evals_limit: int) -> bool:
        """Whether ``evals_limit`` leaves no ``evals``."""
        return self.remaining(evals_limit) == 0


class BudgetExceeded(RuntimeError):
    """A request refused because it would exceed the ``evals`` limit; nothing was committed."""

    def __init__(self, requested: int, remaining: int, limit: int) -> None:
        self.requested = requested
        self.remaining = remaining
        self.limit = limit
        super().__init__(f"requested {requested} evals, {remaining} remaining of limit {limit}")
