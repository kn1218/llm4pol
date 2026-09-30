"""The reducer: the events of a ledger -> the rows of ``results.csv`` (ADR-0008 item 4; CONTEXT R-2, R-3).

``reduce`` is a pure function of a parsed ``Ledger``: no clock, no file, no table. It returns one
``Row`` per ``selection`` or ``no_match`` event, in ledger order, and per population in the order
of the ``run_opened`` payload, so ``replay`` re-derives every number from the ledger alone
(RUN-04). The objective key, its direction, the constraint operators and their thresholds are
read from the problem spec in the ledger header; nothing in this module names a property or a
number (RESEARCH anti-pattern). The definitions are the column table of ADR-0008 item 4.

``render_csv`` writes LF-terminated UTF-8 with floats as ``repr`` and integers as ``str``, so the
bytes are identical on Windows and Linux (RESEARCH F-27, F-29). The module imports the standard
library, ``llm4pol.run.ledger``, ``llm4pol.run.config`` and ``llm4pol.evaluate.contract`` only,
and no dataframe, parquet or array library (RESEARCH F-28, Pattern 4).
"""

from __future__ import annotations

import csv
import hashlib
import io
import operator
import os
import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llm4pol.evaluate.contract import EvalResult
from llm4pol.run.config import ProblemSpec
from llm4pol.run.ledger import LEDGER_NAME, Event, Ledger, LedgerIntegrityError, read

COLUMNS: tuple[str, ...] = (
    "iteration",
    "beam",
    "population",
    "n_selected",
    "n_ok",
    "median_objective",
    "feasible_frac",
    "n_population",
    "pct_of_population",
    "hits_top10",
    "hits_top1",
)
RESULTS_NAME = "results.csv"

# The vocabulary of the problem spec schema: two constraint operators, two directions. What a
# direction or an operator is compared with always comes from the problem in the ledger header.
_OPERATORS: dict[str, Callable[[float, float], bool]] = {"<=": operator.le, ">=": operator.ge}
_AT_LEAST_AS_GOOD: dict[str, Callable[[float, float], bool]] = {
    "max": operator.ge,
    "min": operator.le,
}
_STRICTLY_WORSE: dict[str, Callable[[float, float], bool]] = {
    "max": operator.lt,
    "min": operator.gt,
}
_BEST_IS_LARGEST: dict[str, bool] = {"max": True, "min": False}
_TOP10_DIVISOR = 10
_TOP1_DIVISOR = 100


class ReduceError(ValueError):
    """A ledger that cannot be reduced: rows to report but no population to report them against."""


@dataclass(frozen=True, slots=True)
class Row:
    """One line of ``results.csv``: an iteration, a beam and a population."""

    iteration: int
    beam: str
    population: str
    n_selected: int
    n_ok: int
    median_objective: float | None
    feasible_frac: float | None
    n_population: int
    pct_of_population: float | None
    hits_top10: int | None
    hits_top1: int | None

    def cells(self) -> tuple[object, ...]:
        return (
            self.iteration,
            self.beam,
            self.population,
            self.n_selected,
            self.n_ok,
            self.median_objective,
            self.feasible_frac,
            self.n_population,
            self.pct_of_population,
            self.hits_top10,
            self.hits_top1,
        )


@dataclass(frozen=True, slots=True)
class Reduced:
    """The rows of one ledger, in the order ``results.csv`` lists them."""

    rows: tuple[Row, ...]


@dataclass(frozen=True, slots=True)
class _Reference:
    """A population reduced to what a row needs: objective values, and the feasible members."""

    name: str
    values: tuple[float, ...]
    feasible: tuple[float, ...]  # objectives of the feasible members, best first
    thresholds: tuple[float, float] | None  # top-10 % and top-1 % thresholds; None when m is 0


def _holds(problem: ProblemSpec, values: Mapping[str, float | None]) -> bool:
    """Every constraint has a value and satisfies its operator against its threshold."""
    for constraint in problem.constraints:
        value = values.get(constraint.property)
        if value is None or not _OPERATORS[constraint.op](value, constraint.value):
            return False
    return True


def _better_first(problem: ProblemSpec, values: Iterable[float]) -> list[float]:
    return sorted(values, reverse=_BEST_IS_LARGEST[problem.objective.direction])


def _reference(problem: ProblemSpec, population: Mapping[str, Any]) -> _Reference:
    objective: Sequence[float | None] = population["objective"]
    constraints: Mapping[str, Sequence[float | None]] = population["constraints"]
    values: list[float] = []
    feasible: list[float] = []
    for index, value in enumerate(objective):
        if value is None:
            continue
        values.append(value)
        cells = {key: array[index] for key, array in constraints.items()}
        if _holds(problem, cells):
            feasible.append(value)
    ranked = _better_first(problem, feasible)
    thresholds = None
    if ranked:
        m = len(ranked)
        top10 = (m + _TOP10_DIVISOR - 1) // _TOP10_DIVISOR
        top1 = (m + _TOP1_DIVISOR - 1) // _TOP1_DIVISOR
        thresholds = (ranked[top10 - 1], ranked[top1 - 1])
    return _Reference(
        name=str(population["name"]),
        values=tuple(values),
        feasible=tuple(ranked),
        thresholds=thresholds,
    )


def _references(problem: ProblemSpec, events: Sequence[Event]) -> tuple[_Reference, ...]:
    for event in events:
        if event.event == "run_opened":
            return tuple(_reference(problem, p) for p in event.payload["populations"])
    return ()


def _results_by_candidate(
    events: Sequence[Event],
) -> dict[tuple[int, str, str], dict[str, EvalResult]]:
    """The results of every ``evaluation`` event, by (iteration, beam, candidate) and property."""
    grouped: dict[tuple[int, str, str], dict[str, EvalResult]] = {}
    for event in events:
        if event.event != "evaluation":
            continue
        payload = event.payload
        key = (event.iteration, str(payload["beam"]), str(payload["candidate_id"]))
        results = [EvalResult.from_json(item) for item in payload["results"]]
        grouped.setdefault(key, {}).update({r.property: r for r in results})
    return grouped


def _ok_value(result: EvalResult | None) -> float | None:
    if result is None or result.status != "ok":
        return None
    return result.value


def _percent_worse(problem: ProblemSpec, reference: _Reference, median: float) -> float:
    """``100 * n_worse / n_population``: an integer product, then one division."""
    is_worse = _STRICTLY_WORSE[problem.objective.direction]
    worse = sum(1 for value in reference.values if is_worse(value, median))
    return 100 * worse / len(reference.values)


def _row(
    problem: ProblemSpec,
    iteration: int,
    beam: str,
    selected: Sequence[str],
    results: Mapping[tuple[int, str, str], dict[str, EvalResult]],
    reference: _Reference,
) -> Row:
    objective_key = problem.objective.property
    objectives: list[float] = []
    hits_pool: list[float] = []
    n_feasible = 0
    for candidate in selected:
        by_property = results.get((iteration, beam, candidate), {})
        value = _ok_value(by_property.get(objective_key))
        constraints = {
            c.property: _ok_value(by_property.get(c.property)) for c in problem.constraints
        }
        feasible = _holds(problem, constraints)
        n_feasible += 1 if feasible else 0
        if value is not None:
            objectives.append(value)
            if feasible:
                hits_pool.append(value)
    median = statistics.median(objectives) if objectives else None
    hits: tuple[int, int] | None = None
    if reference.thresholds is not None:
        as_good = _AT_LEAST_AS_GOOD[problem.objective.direction]
        top10, top1 = reference.thresholds
        hits = (
            sum(1 for v in hits_pool if as_good(v, top10)),
            sum(1 for v in hits_pool if as_good(v, top1)),
        )
    pct = None
    if median is not None and reference.values:
        pct = _percent_worse(problem, reference, median)
    return Row(
        iteration=iteration,
        beam=beam,
        population=reference.name,
        n_selected=len(selected),
        n_ok=len(objectives),
        median_objective=median,
        feasible_frac=n_feasible / len(selected) if selected else None,
        n_population=len(reference.values),
        pct_of_population=pct,
        hits_top10=None if hits is None else hits[0],
        hits_top1=None if hits is None else hits[1],
    )


def reduce(ledger: Ledger) -> Reduced:
    """One row per selection or no-match event and population; a pure function of ``ledger``."""
    problem = ledger.problem
    events = ledger.events
    reported = [e for e in events if e.event in ("selection", "no_match")]
    references = _references(problem, events)
    if reported and not references:
        raise ReduceError("the ledger reports selections but holds no run_opened populations")
    results = _results_by_candidate(events)
    rows: list[Row] = []
    for event in reported:
        beam = str(event.payload["beam"])
        selected = tuple(event.payload.get("candidates", ()))
        rows.extend(
            _row(problem, event.iteration, beam, selected, results, reference)
            for reference in references
        )
    return Reduced(rows=tuple(rows))


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def render_csv(reduced: Reduced) -> bytes:
    """The bytes of ``results.csv``: header and rows, LF only, UTF-8 without a byte order mark."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in reduced.rows:
        writer.writerow([_cell(value) for value in row.cells()])
    return buffer.getvalue().encode("utf-8")


def write_outputs(run_dir: Path) -> dict[str, str]:
    """Reduce the ledger of ``run_dir`` and write ``results.csv`` when it is absent.

    A file that is present must hold the same bytes, else ``LedgerIntegrityError``; nothing is
    ever overwritten. Returns the sha256 by file name.
    """
    data = render_csv(reduce(read(run_dir / LEDGER_NAME)))
    target = run_dir / RESULTS_NAME
    if target.exists():
        if target.read_bytes() != data:
            raise LedgerIntegrityError(f"{RESULTS_NAME} differs from what the ledger reduces to")
    else:
        with target.open("xb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
    return {RESULTS_NAME: hashlib.sha256(data).hexdigest()}
