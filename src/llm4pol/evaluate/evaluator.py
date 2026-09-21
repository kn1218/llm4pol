"""The evaluator: one request in, one response out, through one ``Backend`` (CONTEXT D-01, D-02, D-04).

Decision order per (candidate, property) -- RESEARCH Pattern 1: ``unsupported``
is decided from the registry before the backend is consulted (so an
unregistered key on an unknown candidate is ``unsupported``, never
``missing``); the backend distinguishes ``candidate_unknown`` from
``value_absent``; any exception raised inside ``backend.lookup`` becomes
``error`` with the exception class name as ``reason`` (retryable).

Ordering and count (D-01): results follow the request's candidate order,
then property order, so ``len(results)`` equals the sum of ``len(properties)``
over the batch.

Charging (D-04, R-2): ``evals`` counts distinct candidates per request --
one eval on a candidate's first ``ok`` result in the request, zero on its
later properties (the loop's 400-eval arithmetic counts candidates, not
properties). ``unsupported``, ``missing`` and ``error`` cost nothing;
``cpu_hours`` is 0.0 for the table. The response ``cost`` is the sum.
Plan 03-02 adds the cache, the budget meter and ``evals_limit`` here.
"""

from __future__ import annotations

from llm4pol.evaluate.contract import (
    Backend,
    Cost,
    EvalRequest,
    EvalResponse,
    EvalResult,
    Lookup,
)
from llm4pol.evaluate.registry import PropertyTable


class Evaluator:
    """Answers ``EvalRequest``s through ``backend``, deciding ``unsupported`` from ``properties``."""

    def __init__(self, backend: Backend, properties: PropertyTable) -> None:
        self._backend = backend
        self._properties = properties

    @property
    def backend(self) -> Backend:
        return self._backend

    def evaluate(self, request: EvalRequest) -> EvalResponse:
        """Every (candidate, property) of the batch, in request order, charged per candidate."""
        charged: set[str] = set()
        results: list[EvalResult] = []
        for entry in request.batch:
            for key in entry.properties:
                lookup = self._lookup(entry.candidate_id, key)
                evals = 1 if lookup.status == "ok" and entry.candidate_id not in charged else 0
                if evals:
                    charged.add(entry.candidate_id)
                results.append(
                    EvalResult.from_lookup(
                        entry.candidate_id, key, lookup, self._backend, cost=Cost(evals, 0.0)
                    )
                )
        total = Cost(
            evals=sum(result.cost.evals for result in results),
            cpu_hours=sum(result.cost.cpu_hours for result in results),
        )
        return EvalResponse(
            run_id=request.run_id,
            iteration=request.iteration,
            results=tuple(results),
            cost=total,
        )

    def _lookup(self, candidate_id: str, key: str) -> Lookup:
        if not self._properties.supported(key):
            return Lookup("unsupported")
        try:
            return self._backend.lookup(candidate_id, key)
        except Exception as exc:  # noqa: BLE001 -- every backend failure is the `error` status (D-02)
            return Lookup("error", reason=type(exc).__name__)
