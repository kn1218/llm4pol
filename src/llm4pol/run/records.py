"""The records of a run ledger: its refusals, its header, events and the ledger read back.

Plain data and builders with no file and no schema (RUN-02; CONTEXT D-02). ``llm4pol.run.ledger``
owns reading and writing and re-exports every name here, so callers import from either.

The module imports the standard library, ``llm4pol.run.config`` only.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from llm4pol.run.config import ProblemSpec, parse_problem_spec

EVENT_KINDS: tuple[str, ...] = (
    "run_opened",
    "iteration_opened",
    "selection",
    "evaluation",
    "no_match",
    "iteration_closed",
    "run_closed",
)


class LedgerError(RuntimeError):
    """Any refusal of the ledger; the subclasses name what was wrong."""


class TornTail(LedgerError):
    """The file does not end in LF: a line was cut short or an append was interrupted.

    ``last_lf_offset`` is the byte offset of the last LF (-1 when the file holds none) and
    ``trailing_bytes`` the number of bytes after it. Nothing is repaired here.
    """

    def __init__(self, message: str, *, last_lf_offset: int, trailing_bytes: int) -> None:
        super().__init__(message)
        self.last_lf_offset = last_lf_offset
        self.trailing_bytes = trailing_bytes


class LedgerFormatError(LedgerError):
    """A line that is not strict JSON, fails the schema, or sits in the wrong place."""


class LedgerIntegrityError(LedgerError):
    """Lines that are each valid but do not belong together: a ``seq`` gap, a foreign run."""


@dataclass(frozen=True, slots=True)
class Header:
    """The first line: the problem and the provenance the run was opened with."""

    run_id: str
    problem: ProblemSpec
    seed: int
    snapshot: str
    registry_version: str
    selector: str
    code_git_sha: str
    schema_version: int = 1

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "problem": self.problem.to_json(),
            "provenance": {
                "seed": self.seed,
                "snapshot": self.snapshot,
                "registry_version": self.registry_version,
                "selector": self.selector,
                "code_git_sha": self.code_git_sha,
            },
        }

    @classmethod
    def from_json(cls, record: Mapping[str, Any]) -> Header:
        """Build from a record the header schema has accepted."""
        provenance = record["provenance"]
        return cls(
            schema_version=int(record["schema_version"]),
            run_id=str(record["run_id"]),
            problem=parse_problem_spec(record["problem"]),
            seed=int(provenance["seed"]),
            snapshot=str(provenance["snapshot"]),
            registry_version=str(provenance["registry_version"]),
            selector=str(provenance["selector"]),
            code_git_sha=str(provenance["code_git_sha"]),
        )


@dataclass(frozen=True, slots=True)
class Event:
    """One event line: the envelope and its payload."""

    seq: int
    ts: str
    run_id: str
    iteration: int
    event: str
    payload: Mapping[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "ts": self.ts,
            "run_id": self.run_id,
            "iteration": self.iteration,
            "event": self.event,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_json(cls, record: Mapping[str, Any]) -> Event:
        """Build from a record the event schema has accepted."""
        return cls(
            seq=int(record["seq"]),
            ts=str(record["ts"]),
            run_id=str(record["run_id"]),
            iteration=int(record["iteration"]),
            event=str(record["event"]),
            payload=record["payload"],
        )


@dataclass(frozen=True, slots=True)
class Ledger:
    """A ledger read back: the header and the events in order."""

    header: Header
    events: tuple[Event, ...]

    @property
    def problem(self) -> ProblemSpec:
        return self.header.problem

    @property
    def closed(self) -> bool:
        """True once a ``run_closed`` event has been recorded."""
        return any(event.event == "run_closed" for event in self.events)


def header_record(
    run_id: str,
    problem: ProblemSpec,
    *,
    selector: str,
    code_git_sha: str,
    snapshot: str,
    registry_version: str,
) -> dict[str, Any]:
    """The header line of a run; the provenance ``seed`` is the problem's seed."""
    return Header(
        run_id=run_id,
        problem=problem,
        seed=problem.seed,
        snapshot=snapshot,
        registry_version=registry_version,
        selector=selector,
        code_git_sha=code_git_sha,
    ).to_json()


def event_record(
    seq: int, ts: str, run_id: str, iteration: int, kind: str, payload: Mapping[str, Any]
) -> dict[str, Any]:
    """The envelope of one event; the schema, not this function, decides whether it is valid."""
    return {
        "seq": seq,
        "ts": ts,
        "run_id": run_id,
        "iteration": iteration,
        "event": kind,
        "payload": dict(payload),
    }


EventKey = tuple[str | int, ...]


def event_key(event: Event) -> EventKey:
    """What identifies an event: a ledger holds each key once (RUN-03, RESEARCH Pattern 3).

    A ``selection`` and a ``no_match`` share one key space, so a beam has one or the other.
    """
    payload = event.payload
    if event.event in ("selection", "no_match"):
        return ("beam", event.iteration, str(payload["beam"]))
    if event.event == "evaluation":
        return ("evaluation", event.iteration, str(payload["beam"]), str(payload["candidate_id"]))
    return (event.event, event.iteration)
