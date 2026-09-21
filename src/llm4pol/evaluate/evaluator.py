"""The evaluator: one request in, one response out, through one ``Backend`` (CONTEXT D-01, D-02, D-04).

Decision order per (candidate, property) -- RESEARCH Pattern 1: ``unsupported``
is decided from the registry before the cache or the backend is consulted (so
an unregistered key on an unknown candidate is ``unsupported``, never
``missing``, and never reaches the cache); then the cache; then the backend,
which distinguishes ``candidate_unknown`` from ``value_absent``; any exception
raised inside ``backend.lookup`` becomes ``error`` with the exception class
name as ``reason`` (retryable, never cached).

Ordering and count (D-01): results follow the request's candidate order,
then property order, so ``len(results)`` equals the sum of ``len(properties)``
over the batch.

Two phases per request (RESEARCH Pattern 4): phase 1 computes every result
(cache hits first, then lookups) and queues the new ``ok`` / ``missing``
results; phase 2 compares the request's ``evals`` with what the meter has
left under ``evals_limit`` and raises ``BudgetExceeded`` before anything is
committed, else commits the queue to the cache and charges the meter.

Charging (D-04, R-2): ``evals`` counts distinct candidates per request --
one eval on a candidate's first non-cached ``ok`` result in the request,
zero on its later properties (the loop's 400-eval arithmetic counts
candidates, not properties). ``unsupported``, ``missing``, ``error`` and
every cache hit cost nothing; ``cpu_hours`` is 0.0 for the table. The
response ``cost`` is the sum.
"""

from __future__ import annotations

import dataclasses

from llm4pol.evaluate.budget import BudgetExceeded, BudgetMeter
from llm4pol.evaluate.cache import CacheKey, JsonlCache, key_for
from llm4pol.evaluate.contract import (
    Backend,
    Cost,
    EvalRequest,
    EvalResponse,
    EvalResult,
    Lookup,
)
from llm4pol.evaluate.registry import PropertyTable

_CACHEABLE: frozenset[str] = frozenset({"ok", "missing"})


class Evaluator:
    """Answers ``EvalRequest``s through ``backend``, deciding ``unsupported`` from ``properties``.

    ``cache`` defaults to a fresh in-memory ``JsonlCache()`` (persistence only
    when the caller passes a ``JsonlCache(path)``); ``meter`` to ``BudgetMeter()``;
    ``evals_limit`` ``None`` means no limit. All five are public attributes;
    ``meter`` is replaced (never mutated) when a request commits.

    Charging edges (D-04 literal reading; RESEARCH Pitfall 5, Open Question 2):
    a candidate listed twice inside one request is not a cache hit -- the
    commit happens after the request -- but its second entry is charged 0 by
    the per-request ``charged`` set; a new property of an already-cached
    candidate in a later request is a fresh ``ok`` and is charged 1 again.
    """

    def __init__(
        self,
        backend: Backend,
        properties: PropertyTable,
        *,
        cache: JsonlCache | None = None,
        meter: BudgetMeter | None = None,
        evals_limit: int | None = None,
    ) -> None:
        self.backend = backend
        self.properties = properties
        self.cache = cache if cache is not None else JsonlCache()
        self.meter = meter if meter is not None else BudgetMeter()
        self.evals_limit = evals_limit

    def evaluate(self, request: EvalRequest) -> EvalResponse:
        """Every (candidate, property) of the batch, in request order, charged per candidate.

        Raises ``BudgetExceeded`` -- with nothing cached and the meter
        unchanged -- when ``evals_limit`` is set and the request's distinct
        uncached ``ok`` candidates would exceed ``meter.remaining(evals_limit)``.
        """
        charged: set[str] = set()
        results: list[EvalResult] = []
        queued: list[tuple[CacheKey, EvalResult]] = []
        for entry in request.batch:
            for key in entry.properties:
                if not self.properties.supported(key):
                    results.append(self._fresh(entry.candidate_id, key, Lookup("unsupported"), 0))
                    continue
                cache_key = key_for(entry.candidate_id, key, self.backend)
                hit = self.cache.get(cache_key)
                if hit is not None:
                    results.append(dataclasses.replace(hit, cached=True, cost=Cost(0, 0.0)))
                    continue
                lookup = self._lookup(entry.candidate_id, key)
                evals = 1 if lookup.status == "ok" and entry.candidate_id not in charged else 0
                if evals:
                    charged.add(entry.candidate_id)
                result = self._fresh(entry.candidate_id, key, lookup, evals)
                results.append(result)
                if lookup.status in _CACHEABLE:
                    queued.append((cache_key, result))

        total = Cost(
            evals=sum(result.cost.evals for result in results),
            cpu_hours=sum(result.cost.cpu_hours for result in results),
        )
        if self.evals_limit is not None:
            remaining = self.meter.remaining(self.evals_limit)
            if total.evals > remaining:
                raise BudgetExceeded(
                    requested=total.evals, remaining=remaining, limit=self.evals_limit
                )
        self.cache.put_many(queued)
        self.meter = self.meter.charge(total)
        return EvalResponse(
            run_id=request.run_id,
            iteration=request.iteration,
            results=tuple(results),
            cost=total,
        )

    def _fresh(self, candidate_id: str, key: str, lookup: Lookup, evals: int) -> EvalResult:
        return EvalResult.from_lookup(
            candidate_id, key, lookup, self.backend, cost=Cost(evals, 0.0)
        )

    def _lookup(self, candidate_id: str, key: str) -> Lookup:
        try:
            return self.backend.lookup(candidate_id, key)
        except Exception as exc:  # noqa: BLE001 -- every backend failure is the `error` status (D-02)
            return Lookup("error", reason=type(exc).__name__)
