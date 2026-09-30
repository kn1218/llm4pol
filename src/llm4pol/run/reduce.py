"""The reducer: the events of a ledger -> ``results.csv``, ``usage.json``, ``run_summary.json``.

``reduce`` is a pure function of a parsed ``Ledger``: no clock, no file, no table. It returns one
``Row`` per ``selection`` or ``no_match`` event, in ledger order, and per population in the order
of the ``run_opened`` payload (ADR-0008 item 4; CONTEXT R-2, R-3). The objective key, its direction,
the constraint operators and their thresholds come from the problem spec in the ledger header;
nothing here names a property or a number. ``usage_of`` sums the recorded costs: ``evals`` as an
integer and ``cpu_hours`` with ``math.fsum``, two currencies no expression here adds, multiplies or
compares (A-3); ``tokens`` and ``usd`` are 0 until Phase 6.

``render_outputs`` is the one rendering for every caller: from the bytes of a ledger it gives the
bytes of the three files, each mapping checked against its schema before anything is written
(D-39), and their hashes; ``run_summary.json`` is built by ``llm4pol.run.summary``. Floats are
``repr`` and integers ``str``, LF only, so the bytes are identical on Windows and Linux (RESEARCH
F-27, F-29). The module imports the standard library, ``jsonschema`` and the ``llm4pol`` modules
``evaluate.contract``, ``run.atomic``, ``run.config``, ``run.jsonio``, ``run.ledger`` and
``run.summary``, no
dataframe, parquet or array library (RESEARCH F-28, Pattern 4); the only files it opens are the
outputs of ``write_outputs``, written through ``llm4pol.run.atomic``.
"""

from __future__ import annotations

import csv
import functools
import hashlib
import io
import math
import operator
import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import astuple, dataclass
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema.exceptions import best_match

from llm4pol.evaluate.contract import EvalResult
from llm4pol.run import atomic
from llm4pol.run.config import SCHEMA_DIR, ProblemSpec
from llm4pol.run.jsonio import loads_strict, pretty_bytes
from llm4pol.run.ledger import LEDGER_NAME, Event, Ledger, LedgerIntegrityError, parse_bytes
from llm4pol.run.summary import summary_of

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
USAGE_NAME = "usage.json"
SUMMARY_NAME = "run_summary.json"
USAGE_SCHEMA_PATH = SCHEMA_DIR / "run-usage.json"
SUMMARY_SCHEMA_PATH = SCHEMA_DIR / "run-summary.json"
USAGE_SCHEMA_VERSION = 1

# The vocabulary of the problem spec schema; what is compared with comes from the ledger header.
_Compare = Callable[[float, float], bool]
_OPERATORS: dict[str, _Compare] = {"<=": operator.le, ">=": operator.ge}
_AT_LEAST_AS_GOOD: dict[str, _Compare] = {"max": operator.ge, "min": operator.le}
_STRICTLY_WORSE: dict[str, _Compare] = {"max": operator.lt, "min": operator.gt}
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
        """The values in the order of ``COLUMNS``, the order the fields are declared in."""
        return astuple(self)


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
    ranked = sorted(feasible, reverse=_BEST_IS_LARGEST[problem.objective.direction])
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
    opened = [event for event in events if event.event == "run_opened"]
    return tuple(_reference(problem, p) for p in opened[0].payload["populations"]) if opened else ()


_ByCandidate = dict[tuple[int, str, str], dict[str, EvalResult]]


def _results_by_candidate(events: Sequence[Event]) -> _ByCandidate:
    """The results of every ``evaluation`` event, by (iteration, beam, candidate) and property."""
    grouped: _ByCandidate = {}
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
    results: _ByCandidate,
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
    if isinstance(value, float) and not math.isfinite(value):
        raise ReduceError(f"a non-finite number cannot be written to {RESULTS_NAME}")
    return "" if value is None else (repr(value) if isinstance(value, float) else str(value))


def render_csv(reduced: Reduced) -> bytes:
    """The bytes of ``results.csv``: header and rows, LF only, UTF-8 without a byte order mark."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in reduced.rows:
        writer.writerow([_cell(value) for value in row.cells()])
    return buffer.getvalue().encode("utf-8")


def _costs_agree(recorded: Mapping[str, Any], results: Sequence[EvalResult]) -> bool:
    """The event cost is the sum of its result costs: ``evals`` exactly, ``cpu_hours`` to 1e-12.

    The evaluator adds the hours as a running float sum and ``fsum`` is exact, so no bit for bit.
    """
    same_evals = int(recorded["evals"]) == sum(r.cost.evals for r in results)
    same_hours = math.isclose(
        float(recorded["cpu_hours"]),
        math.fsum(r.cost.cpu_hours for r in results),
        rel_tol=1e-12,
        abs_tol=1e-15,
    )
    return same_evals and same_hours


def usage_of(ledger: Ledger) -> dict[str, Any]:
    """The five keys of ``usage.json``, summed from the ``evaluation`` events of ``ledger``.

    ``evals`` is the integer sum of the recorded result costs and ``cpu_hours`` their ``fsum``,
    never combined (A-3, CONTEXT D-04); ``tokens`` and ``usd`` stay 0 until Phase 6. An event
    whose cost is not the sum of its results raises ``LedgerIntegrityError``.
    """
    evals = 0
    hours: list[float] = []
    for event in ledger.events:
        if event.event != "evaluation":
            continue
        results = [EvalResult.from_json(item) for item in event.payload["results"]]
        if not _costs_agree(event.payload["cost"], results):
            raise LedgerIntegrityError(
                f"seq {event.seq}: the cost of the evaluation event is not the sum of its results"
            )
        evals += sum(r.cost.evals for r in results)
        hours.extend(r.cost.cpu_hours for r in results)
    return {
        "schema_version": USAGE_SCHEMA_VERSION,
        "evals": evals,
        "cpu_hours": math.fsum(hours),
        "tokens": 0,
        "usd": 0.0,
    }


@functools.cache
def _validator(schema_path: Path) -> Any:
    return jsonschema.Draft202012Validator(loads_strict(schema_path.read_text(encoding="utf-8")))


def _render_checked(mapping: Mapping[str, Any], schema_path: Path, what: str) -> bytes:
    """``pretty_bytes`` of ``mapping`` once its schema accepts it, else ``ReduceError``."""
    error = best_match(_validator(schema_path).iter_errors(mapping))
    if error is not None:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise ReduceError(
            f"{what} mapping refused by {schema_path.name}: {pointer}: {error.message}"
        )
    return pretty_bytes(mapping)


def render_usage(ledger: Ledger) -> bytes:
    """The bytes of ``usage.json``; ``ReduceError`` when the mapping is not what the schema allows."""
    return _render_checked(usage_of(ledger), USAGE_SCHEMA_PATH, "usage")


@dataclass(frozen=True, slots=True)
class Outputs:
    """The three reduced files of one ledger as bytes, the hashes they carry, and its state."""

    results: bytes
    usage: bytes
    summary: bytes
    ledger_sha256: str
    results_sha256: str
    closed: bool

    def files(self) -> dict[str, bytes]:
        return {RESULTS_NAME: self.results, USAGE_NAME: self.usage, SUMMARY_NAME: self.summary}


def result_sha256(results: bytes, usage: bytes, summary: bytes) -> str:
    """The sha256 of the three reduced files laid end to end in this order (CONTEXT D-03)."""
    return hashlib.sha256(results + usage + summary).hexdigest()


def render_outputs(ledger_bytes: bytes) -> Outputs:
    """Parse ``ledger_bytes`` with every check of ``read``, reduce, and render the three files."""
    parsed = parse_bytes(ledger_bytes)
    if not parsed.events:
        raise ReduceError("the ledger holds a header and no event: there is nothing to summarise")
    reduced = reduce(parsed)
    results = render_csv(reduced)
    ledger_sha, results_sha = (hashlib.sha256(raw).hexdigest() for raw in (ledger_bytes, results))
    mapping = summary_of(parsed, reduced.rows, ledger_sha256=ledger_sha, results_sha256=results_sha)
    return Outputs(
        results=results,
        usage=render_usage(parsed),
        summary=_render_checked(mapping, SUMMARY_SCHEMA_PATH, "summary"),
        ledger_sha256=ledger_sha,
        results_sha256=results_sha,
        closed=parsed.closed,
    )


def write_outputs(run_dir: Path, outputs: Outputs | None = None) -> dict[str, str]:
    """Reduce the ledger of ``run_dir`` (or take ``outputs``) and write the files that are absent.

    All three are rendered, and each mapping is checked against its schema, before a file is
    opened. A file that is present must hold the same bytes, else ``LedgerIntegrityError``, and
    that is checked for all three before any is written; nothing is ever overwritten. Returns the
    sha256 by file name.
    """
    files = (outputs or render_outputs((run_dir / LEDGER_NAME).read_bytes())).files()
    for name, data in files.items():
        present = run_dir / name
        if present.exists() and present.read_bytes() != data:
            raise LedgerIntegrityError(f"{name} differs from what the ledger reduces to")
    for name, data in files.items():
        target = run_dir / name
        if not target.exists():
            atomic.write_new(target, data)
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
