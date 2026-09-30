"""The selector protocol and the plan-file selector (ADR-0008 item 8; CONTEXT R-8).

A selector answers one question: which candidates does each beam of iteration ``i`` select?
``llm4pol.run`` owns the protocol; Phase 5 adds the deterministic selector in ``llm4pol.loop``,
which imports it from here, and ``llm4pol.run`` never imports ``llm4pol.loop``.

``PlanSelector`` is a complete implementation, not a stub: it replays a plan read from a file
(``protocol/schemas/selection-plan.json``). The plan is read strictly (no repeated key, no
non-finite constant), validated against its schema, and then checked against the problem: the
iterations must be numbered 1 to ``problem.budget.iterations`` without a gap, and a beam name
must be unique inside an iteration (threat T-04-07). Its ``identity`` is
``plan:sha256:<hex>`` over the canonical bytes of the payload, recorded in the ledger header.

The module imports the standard library, ``jsonschema``, ``llm4pol.run.config``,
``llm4pol.run.jsonio``, ``llm4pol.run.ledger`` and ``llm4pol.run.strictschema`` only.
"""

from __future__ import annotations

import functools
import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

from jsonschema.exceptions import best_match

from llm4pol.run.config import SCHEMA_DIR, ProblemSpec
from llm4pol.run.jsonio import StrictJsonError, canonical_bytes, loads_strict
from llm4pol.run.ledger import Event, Ledger, LedgerIntegrityError
from llm4pol.run.strictschema import validator_class

PLAN_SCHEMA_PATH = SCHEMA_DIR / "selection-plan.json"
IDENTITY_PREFIX = "plan:sha256:"

# The schema patterns end in `$`, which Python's `re.search` lets match before a final LF; the
# same two patterns are matched again here with `fullmatch`.
_BEAM_NAME = re.compile(r"[a-z][a-z0-9_]*")
_CANDIDATE_ID = re.compile(r"[0-9a-f]{16}")


class PlanError(ValueError):
    """A plan the schema or the problem refuses (the message names the JSON pointer)."""


class SequenceMismatch(LedgerIntegrityError):
    """A recorded event sequence that the selector does not reproduce (CONTEXT D-03 item 3)."""


@dataclass(frozen=True, slots=True)
class Selection:
    """One beam of one iteration: its name and the ordered ids it selects (empty: no match)."""

    beam: str
    candidates: tuple[str, ...]


@runtime_checkable
class Selector(Protocol):
    """What a run needs from whatever chooses the candidates."""

    @property
    def identity(self) -> str:
        """A stable name for this selector and its configuration, recorded in the header."""
        ...

    def select(
        self, problem: ProblemSpec, iteration: int, history: Sequence[Event]
    ) -> Sequence[Selection]:
        """The ordered selections of ``iteration``; ``history`` is every event recorded before it."""
        ...


@functools.cache
def _plan_validator() -> Any:
    return validator_class()(loads_strict(PLAN_SCHEMA_PATH.read_text("utf-8")))


def _check_schema(payload: object) -> None:
    error = best_match(_plan_validator().iter_errors(payload))
    if error is not None:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise PlanError(f"{pointer}: {error.message}")


def _check_against_problem(payload: Mapping[str, Any], problem: ProblemSpec) -> None:
    numbers = [item["iteration"] for item in payload["iterations"]]
    expected = list(range(1, problem.budget.iterations + 1))
    if numbers != expected:
        raise PlanError(
            f"/iterations: expected iterations {expected[0]}..{expected[-1]} in order, "
            f"the plan has {numbers}"
        )
    for index, item in enumerate(payload["iterations"]):
        names = [beam["beam"] for beam in item["beams"]]
        for position, beam in enumerate(item["beams"]):
            where = f"/iterations/{index}/beams/{position}"
            if not _BEAM_NAME.fullmatch(beam["beam"]):
                raise PlanError(f"{where}/beam: not a beam name")
            if names.count(beam["beam"]) > 1:
                raise PlanError(f"{where}/beam: beam {beam['beam']!r} repeats in one iteration")
            for spot, candidate in enumerate(beam["candidates"]):
                if not _CANDIDATE_ID.fullmatch(candidate):
                    raise PlanError(f"{where}/candidates/{spot}: not a candidate id")


class PlanSelector:
    """Replays a validated plan: iteration ``i`` selects exactly what the plan lists."""

    def __init__(self, payload: object, problem: ProblemSpec) -> None:
        _check_schema(payload)
        fields = cast(Mapping[str, Any], payload)  # the schema admits objects only
        _check_against_problem(fields, problem)
        try:
            digest = hashlib.sha256(canonical_bytes(fields)).hexdigest()
        except StrictJsonError as exc:
            raise PlanError(f"the plan is not strict JSON: {exc}") from exc
        self._identity = f"{IDENTITY_PREFIX}{digest}"
        self._by_iteration: dict[int, tuple[Selection, ...]] = {
            int(item["iteration"]): tuple(
                Selection(beam=str(beam["beam"]), candidates=tuple(beam["candidates"]))
                for beam in item["beams"]
            )
            for item in fields["iterations"]
        }

    @classmethod
    def from_payload(cls, payload: object, problem: ProblemSpec) -> PlanSelector:
        """Build from a parsed plan; ``PlanError`` when the schema or the problem refuses it."""
        return cls(payload, problem)

    @classmethod
    def from_file(cls, path: Path, problem: ProblemSpec) -> PlanSelector:
        """Read ``path`` strictly, then ``from_payload``; any defect is ``PlanError``."""
        try:
            payload = loads_strict(path.read_text(encoding="utf-8"))
        except (StrictJsonError, UnicodeDecodeError) as exc:
            raise PlanError(f"{path.name}: {exc}") from exc
        return cls.from_payload(payload, problem)

    @property
    def identity(self) -> str:
        return self._identity

    def select(
        self, problem: ProblemSpec, iteration: int, history: Sequence[Event]
    ) -> Sequence[Selection]:
        """The plan's selections of ``iteration``; the plan ignores the history."""
        try:
            return self._by_iteration[iteration]
        except KeyError as exc:
            raise PlanError(f"the plan has no iteration {iteration}") from exc


def _shape(
    kind: str, beam: Any = None, candidates: Sequence[str] = (), candidate: Any = None
) -> tuple[Any, ...]:
    """What a selector decides about an event: its kind, beam, candidates and candidate."""
    return (kind, beam, tuple(candidates), candidate)


def _recorded_shape(event: Event) -> tuple[Any, ...]:
    payload = event.payload
    return _shape(
        event.event, payload.get("beam"), payload.get("candidates", ()), payload.get("candidate_id")
    )


def _expected(chosen: Sequence[Selection]) -> list[tuple[Any, ...]]:
    """The events one iteration records for ``chosen``, in order (ADR-0008 item 5)."""
    shapes = [_shape("iteration_opened")]
    for selection in chosen:
        if not selection.candidates:
            shapes.append(_shape("no_match", selection.beam))
            continue
        shapes.append(_shape("selection", selection.beam, selection.candidates))
        shapes.extend(
            _shape("evaluation", selection.beam, candidate=c) for c in selection.candidates
        )
    shapes.append(_shape("iteration_closed"))
    return shapes


def verify_replay(recorded: Ledger, selector: Selector) -> None:
    """Each recorded iteration is a prefix of what ``selector`` gives; nothing is appended here.

    The selector is asked for every iteration the ledger opened, given the events recorded before
    it, and the events of that iteration (a closing ``run_closed`` aside) must be the first events
    of the sequence it implies: same beams in the same order, same candidates in the same order
    (CONTEXT D-03 item 3; RESEARCH F-04). ``SequenceMismatch`` names the first difference.
    """
    events = recorded.events
    starts = [i for i, event in enumerate(events) if event.event == "iteration_opened"]
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(events)
        iteration = events[start].iteration
        found = [_recorded_shape(e) for e in events[start:end] if e.event != "run_closed"]
        expected = _expected(selector.select(recorded.problem, iteration, tuple(events[:start])))
        if found != expected[: len(found)]:
            at = next(i for i, (a, b) in enumerate(zip_longest(found, expected)) if a != b)
            gives = expected[at] if at < len(expected) else "no further event"
            raise SequenceMismatch(
                f"iteration {iteration}: the ledger records {found[at]} at its position {at + 1}, "
                f"the selector gives {gives}"
            )
