"""The campaign driver: open a run, drive it, continue it from its ledger (RUN-01..RUN-03; ADR-0008).

``open_run`` refuses a problem that names another snapshot than the registry, reads the source
hash from the candidate parquet before anything is created, validates ``meta.json`` before the
run directory exists, and then creates the directory, ``meta.json`` and the ledger header.

``drive`` is the one campaign code path, for a fresh run and a resumed one (Pattern 3). It reads
the problem from the ledger header, derives the state from the recorded events (``rebuild_state``)
and walks every iteration, skipping each event whose key is recorded: the ledger is append-only,
so the events of an interrupted iteration stay and the run continues at the first key not yet
recorded (Pitfall 5). An ``evaluation`` event is one candidate's one-candidate request (ADR-0008
item 5) and carries the response cost; nothing here prices a result. The evaluator gets a
memory-only ``JsonlCache()`` and the rebuilt meter, so nothing but the ledger survives a restart
(ADR-0008 item 1). A budget refusal is recorded as ``run_closed``.

``resume`` reads the ledger first, so a torn tail or an integrity error stops it before a table is
opened, then refuses a header that names other code, snapshot, registry version or selector
(ADR-0008 item 7). No function here shortens or rewrites the ledger.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from llm4pol.data import snapshot
from llm4pol.data.registry import Registry
from llm4pol.evaluate import (
    Backend,
    BatchEntry,
    BudgetExceeded,
    BudgetMeter,
    EvalRequest,
    EvalResult,
    Evaluator,
    JsonlCache,
    PropertyTable,
)
from llm4pol.evaluate.backends.table import TableBackend
from llm4pol.evaluate.cache import key_for
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
from llm4pol.run.ledger import (
    LEDGER_NAME,
    Event,
    EventKey,
    Ledger,
    LedgerIntegrityError,
    append,
    create,
    event_key,
    event_record,
    header_record,
    read,
)
from llm4pol.run.population import PopulationError
from llm4pol.run.selector import Selector, SequenceMismatch, verify_replay

__all__ = [
    "DriveError",
    "Outcome",
    "RunRefused",
    "RunState",
    "SequenceMismatch",
    "drive",
    "open_run",
    "rebuild_state",
    "resume",
]


class DriveError(RuntimeError):
    """A selector that is not the one the ledger header records."""


class RunRefused(LedgerIntegrityError):
    """The header names other code, snapshot, registry version or selector than the running ones."""


@dataclass(frozen=True, slots=True)
class Outcome:
    """What a driven run leaves behind: its cost in two currencies, its results hash, its end."""

    run_id: str
    evals: int
    cpu_hours: float
    results_sha256: str
    status: str  # `completed` or `budget_exhausted`: the reason of the recorded run_closed
    appended: int  # events this call appended; 0 for a run that was already closed
    closing: Mapping[str, Any]  # the payload of run_closed


@dataclass(frozen=True, slots=True)
class RunState:
    """Everything a restart needs, derived from the recorded events and from nothing else."""

    recorded: frozenset[EventKey]
    selections: Mapping[tuple[int, str], tuple[str, ...]]
    cache: JsonlCache
    meter: BudgetMeter


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


def rebuild_state(ledger: Ledger, backend: Backend) -> RunState:
    """The cache, the meter and the recorded keys, from the ``evaluation`` events alone (Pattern 3).

    Every recorded result goes back through ``EvalResult.from_json``; ``evals`` are summed as
    integers and ``cpu_hours`` with ``math.fsum``; a result that was not a cache hit and has
    status ``ok`` or ``missing`` is stored, as the evaluator stored it. Nothing is priced here.
    """
    cache = JsonlCache()
    evals = 0
    hours: list[float] = []
    selections: dict[tuple[int, str], tuple[str, ...]] = {}
    for event in ledger.events:
        if event.event in ("selection", "no_match"):
            beam = (event.iteration, str(event.payload["beam"]))
            selections[beam] = tuple(event.payload.get("candidates", ()))
        if event.event != "evaluation":
            continue
        for item in event.payload["results"]:
            result = EvalResult.from_json(item)
            evals += result.cost.evals
            hours.append(result.cost.cpu_hours)
            if not result.cached and result.status in ("ok", "missing"):
                cache.put_many([(key_for(result.candidate_id, result.property, backend), result)])
    return RunState(
        recorded=frozenset(event_key(event) for event in ledger.events),
        selections=selections,
        cache=cache,
        meter=BudgetMeter(evals=evals, cpu_hours=math.fsum(hours)),
    )


class _Recorder:
    """Appends events to one ledger with the next ``seq`` and the clock's ``ts``, keeping them."""

    def __init__(self, path: Path, run_id: str, clock: Clock, recorded: Sequence[Event]) -> None:
        self._path = path
        self.run_id = run_id
        self._clock = clock
        self.events: list[Event] = list(recorded)

    def emit(self, iteration: int, kind: str, payload: Mapping[str, Any]) -> Event:
        record = event_record(
            len(self.events) + 1, format_ts(self._clock()), self.run_id, iteration, kind, payload
        )
        append(self._path, record)
        event = Event.from_json(record)
        self.events.append(event)
        return event


def _history_before(events: Sequence[Event], iteration: int) -> tuple[Event, ...]:
    """The events recorded before ``iteration`` opened: what the selector is given."""
    for position, event in enumerate(events):
        if event.event == "iteration_opened" and event.iteration == iteration:
            return tuple(events[:position])
    return tuple(events)


def _evaluate_one(
    recorder: _Recorder,
    evaluator: Evaluator,
    problem: ProblemSpec,
    iteration: int,
    beam: str,
    candidate: str,
) -> None:
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
            "beam": beam,
            "candidate_id": candidate,
            "results": [r.to_json() for r in response.results],
            "cost": response.cost.to_json(),
        },
    )


def _drive_iteration(
    recorder: _Recorder,
    evaluator: Evaluator,
    state: RunState,
    selector: Selector,
    problem: ProblemSpec,
    iteration: int,
) -> None:
    history = _history_before(recorder.events, iteration)
    if ("iteration_opened", iteration) not in state.recorded:
        recorder.emit(iteration, "iteration_opened", {})
    for chosen in selector.select(problem, iteration, history):
        if (iteration, chosen.beam) not in state.selections:
            if not chosen.candidates:
                recorder.emit(iteration, "no_match", {"beam": chosen.beam})
                continue
            recorder.emit(
                iteration, "selection", {"beam": chosen.beam, "candidates": list(chosen.candidates)}
            )
        for candidate in chosen.candidates:
            if ("evaluation", iteration, chosen.beam, candidate) not in state.recorded:
                _evaluate_one(recorder, evaluator, problem, iteration, chosen.beam, candidate)
    if ("iteration_closed", iteration) not in state.recorded:
        recorder.emit(iteration, "iteration_closed", {})


def _cost(events: Sequence[Event]) -> tuple[int, float]:
    costs = [e.payload["cost"] for e in events if e.event == "evaluation"]
    return sum(int(c["evals"]) for c in costs), math.fsum(float(c["cpu_hours"]) for c in costs)


def _finish(run_dir: Path, events: Sequence[Event], appended: int) -> Outcome:
    """Write ``results.csv`` (or check the one present) and describe the closed run."""
    sums = reduce.write_outputs(run_dir)
    closing = events[-1].payload
    evals, cpu_hours = _cost(events)
    return Outcome(
        run_id=events[-1].run_id,
        evals=evals,
        cpu_hours=cpu_hours,
        results_sha256=sums[reduce.RESULTS_NAME],
        status=str(closing["reason"]),
        appended=appended,
        closing=closing,
    )


def _run_to_close(
    recorder: _Recorder,
    evaluator: Evaluator,
    state: RunState,
    selector: Selector,
    problem: ProblemSpec,
) -> None:
    try:
        for iteration in range(1, problem.budget.iterations + 1):
            _drive_iteration(recorder, evaluator, state, selector, problem, iteration)
        recorder.emit(0, "run_closed", {"reason": "completed"})
    except BudgetExceeded as refused:
        payload = {
            "reason": "budget_exhausted",
            "requested": refused.requested,
            "remaining": refused.remaining,
            "limit": refused.limit,
        }
        recorder.emit(0, "run_closed", payload)


def drive(run_dir: Path, *, root: Path, selector: Selector, clock: Clock) -> Outcome:
    """Bring the run of ``run_dir`` to its close from whatever prefix its ledger records."""
    path = run_dir / LEDGER_NAME
    recorded = read(path)
    if recorded.header.selector != selector.identity:
        raise DriveError("the selector is not the one the ledger header records")
    verify_replay(recorded, selector)
    if recorded.closed:
        return _finish(run_dir, recorded.events, appended=0)
    problem = recorded.problem
    properties = PropertyTable.load()
    backend = TableBackend(
        snapshot.candidates_parquet(snapshot.processed_dir(root)), properties=properties
    )
    state = rebuild_state(recorded, backend)
    evaluator = Evaluator(
        backend,
        properties,
        cache=state.cache,
        meter=state.meter,
        evals_limit=problem.evals_limit,
    )
    recorder = _Recorder(path, recorded.header.run_id, clock, recorded.events)
    if ("run_opened", 0) not in state.recorded:
        _open_ledger(recorder, root, problem, properties.registry)
    _run_to_close(recorder, evaluator, state, selector, problem)
    return _finish(run_dir, recorder.events, appended=len(recorder.events) - len(recorded.events))


def _open_ledger(recorder: _Recorder, root: Path, problem: ProblemSpec, registry: Registry) -> None:
    populations = population.capture(root, problem, registry)
    recorder.emit(
        0,
        "run_opened",
        {
            "primary": population.PRIMARY_POPULATION,
            "populations": [p.to_json() for p in populations],
        },
    )


def resume(
    run_dir: Path, *, root: Path, selector: Selector, code: CodeIdentity, clock: Clock
) -> Outcome:
    """Continue the run of ``run_dir`` under the code, snapshot and selector that opened it.

    The ledger is read first; then the header is compared with the running code in a fixed order
    and the first difference raises ``RunRefused``. There is no argument that relaxes a check.
    """
    recorded = read(run_dir / LEDGER_NAME)
    registry = PropertyTable.load().registry
    header = recorded.header
    for field, found, running in (
        ("provenance.snapshot", header.snapshot, registry.snapshot),
        ("provenance.registry_version", header.registry_version, registry.registry_version),
        ("provenance.code_git_sha", header.code_git_sha, code.sha),
        ("provenance.selector", header.selector, selector.identity),
    ):
        if found != running:
            raise RunRefused(
                f"{field}: the ledger records {found!r}, the running code has {running!r}"
            )
    return drive(run_dir, root=root, selector=selector, clock=clock)
