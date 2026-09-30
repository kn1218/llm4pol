"""The campaign driver: open a run, then drive it to its close (RUN-01, RUN-02; CONTEXT R-7; Pattern 3).

``open_run`` refuses a problem that names another snapshot than the registry, reads the source
hash from the candidate parquet before anything is created (a missing table leaves no directory
behind), validates ``meta.json`` before the run directory exists, and then creates the directory,
writes ``meta.json`` and creates the ledger with its header. ``drive`` is the one campaign code
path: it reads the problem from the ledger header, appends ``run_opened`` with the captured
populations, and for each iteration asks the selector once and appends one event per beam and one
``evaluation`` event per candidate, each the response of a one-candidate request (ADR-0008 item 5).
The recorded cost is the response cost; nothing in this package computes a cost.

In this plan ``drive`` starts from a ledger that holds its header only; continuing a recorded
prefix, rebuilding the cache and meter from it, and closing on a budget refusal are plan 04-05.
The evaluator gets a memory-only ``JsonlCache()``: no cache file is written beside the ledger, so
the ledger stays the only state (RESEARCH anti-pattern). A ``BudgetExceeded`` from the evaluator
propagates; an append that raises ends the drive.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from llm4pol.data import snapshot
from llm4pol.data.registry import Registry
from llm4pol.evaluate import (
    BatchEntry,
    BudgetMeter,
    EvalRequest,
    Evaluator,
    JsonlCache,
    PropertyTable,
)
from llm4pol.evaluate.backends.table import TableBackend
from llm4pol.run import population, reduce
from llm4pol.run.config import (
    CodeIdentity,
    ProblemSpec,
    build_meta,
    create_run_dir,
    validate_meta,
    write_meta,
)
from llm4pol.run.ids import Clock, format_ts, new_run_id
from llm4pol.run.ledger import LEDGER_NAME, Event, append, create, event_record, header_record, read
from llm4pol.run.population import PopulationError
from llm4pol.run.selector import Selector


class DriveError(RuntimeError):
    """A ledger that ``drive`` cannot start from, or a selector that is not the one recorded."""


@dataclass(frozen=True, slots=True)
class Outcome:
    """What a driven run leaves behind: its cost, in two currencies, and its results hash."""

    run_id: str
    evals: int
    cpu_hours: float
    results_sha256: str


def open_run(
    experiments: Path,
    problem: ProblemSpec,
    selector: Selector,
    *,
    root: Path,
    now: datetime,
    token: str,
    code: CodeIdentity,
) -> Path:
    """Create ``experiments/<run id>/`` with ``meta.json`` and a ledger holding its header."""
    registry = PropertyTable.load().registry
    if problem.table != registry.snapshot:
        raise PopulationError(
            f"the problem names {problem.table!r}, the registry is {registry.snapshot!r}"
        )
    found, source_sha256 = population.candidate_metadata(root)
    if found != problem.table:
        raise PopulationError(f"candidate table is {found!r}, the problem names {problem.table!r}")
    run_id = new_run_id(now, token)
    meta = build_meta(
        run_id=run_id,
        created_at=format_ts(now),
        problem=problem,
        code=code,
        snapshot=registry.snapshot,
        snapshot_sha256=source_sha256,
        registry_version=registry.registry_version,
        selector=selector.identity,
    )
    validate_meta(meta)
    run_dir = create_run_dir(experiments, run_id)
    write_meta(run_dir, meta)
    create(
        run_dir / LEDGER_NAME,
        header_record(
            run_id,
            problem,
            selector=selector.identity,
            code_git_sha=code.sha,
            snapshot=registry.snapshot,
            registry_version=registry.registry_version,
        ),
    )
    return run_dir


class _Recorder:
    """Appends events to one ledger with the next ``seq`` and the clock's ``ts``, keeping them."""

    def __init__(self, path: Path, run_id: str, clock: Clock) -> None:
        self._path = path
        self.run_id = run_id
        self._clock = clock
        self.events: list[Event] = []

    def emit(self, iteration: int, kind: str, payload: Mapping[str, Any]) -> Event:
        record = event_record(
            len(self.events) + 1, format_ts(self._clock()), self.run_id, iteration, kind, payload
        )
        append(self._path, record)
        event = Event.from_json(record)
        self.events.append(event)
        return event


def _drive_iteration(
    recorder: _Recorder,
    evaluator: Evaluator,
    selector: Selector,
    problem: ProblemSpec,
    iteration: int,
) -> None:
    recorder.emit(iteration, "iteration_opened", {})
    for chosen in selector.select(problem, iteration, tuple(recorder.events)):
        if not chosen.candidates:
            recorder.emit(iteration, "no_match", {"beam": chosen.beam})
            continue
        recorder.emit(
            iteration, "selection", {"beam": chosen.beam, "candidates": list(chosen.candidates)}
        )
        for candidate in chosen.candidates:
            request = EvalRequest(
                run_id=recorder.run_id,
                iteration=iteration,
                batch=(BatchEntry(candidate, problem.property_keys()),),
            )
            response = evaluator.evaluate(request)
            recorder.emit(
                iteration,
                "evaluation",
                {
                    "beam": chosen.beam,
                    "candidate_id": candidate,
                    "results": [r.to_json() for r in response.results],
                    "cost": response.cost.to_json(),
                },
            )
    recorder.emit(iteration, "iteration_closed", {})


def _evaluator(root: Path, problem: ProblemSpec, registry: PropertyTable) -> Evaluator:
    backend = TableBackend(
        snapshot.candidates_parquet(snapshot.processed_dir(root)), properties=registry
    )
    return Evaluator(
        backend,
        registry,
        cache=JsonlCache(),
        meter=BudgetMeter(),
        evals_limit=problem.evals_limit,
    )


def _cost(events: list[Event]) -> tuple[int, float]:
    costs = [e.payload["cost"] for e in events if e.event == "evaluation"]
    return sum(int(c["evals"]) for c in costs), math.fsum(float(c["cpu_hours"]) for c in costs)


def drive(run_dir: Path, *, root: Path, selector: Selector, clock: Clock) -> Outcome:
    """Run every iteration of the problem in the ledger of ``run_dir``, then write ``results.csv``."""
    path = run_dir / LEDGER_NAME
    recorded = read(path)
    if recorded.events:
        raise DriveError("the ledger already holds events; continuing a run is `resume`")
    if recorded.header.selector != selector.identity:
        raise DriveError("the selector is not the one the ledger header records")
    problem = recorded.problem
    properties = PropertyTable.load()
    registry: Registry = properties.registry
    recorder = _Recorder(path, recorded.header.run_id, clock)
    populations = population.capture(root, problem, registry)
    recorder.emit(
        0,
        "run_opened",
        {
            "primary": population.PRIMARY_POPULATION,
            "populations": [p.to_json() for p in populations],
        },
    )
    evaluator = _evaluator(root, problem, properties)
    for iteration in range(1, problem.budget.iterations + 1):
        _drive_iteration(recorder, evaluator, selector, problem, iteration)
    recorder.emit(0, "run_closed", {"reason": "completed"})
    sums = reduce.write_outputs(run_dir)
    evals, cpu_hours = _cost(recorder.events)
    return Outcome(recorded.header.run_id, evals, cpu_hours, sums[reduce.RESULTS_NAME])
