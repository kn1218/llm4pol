"""The run ledger: a header line, durable appends, a strict reader (RUN-02; CONTEXT D-02, D-03).

``ledger.jsonl`` is one canonical JSON object per LF-terminated line: the header first, then
events with the envelope ``seq, ts, run_id, iteration, event, payload``. Every line is
validated against ``protocol/schemas/ledger-event.json`` before it is written and after it is
read, so nothing reaches the file or the caller unvalidated (threats T-04-03..T-04-05).

Writing (RESEARCH Pattern 2, Code Example 1): ``create`` opens the file exclusively in binary
mode; ``append`` writes one complete line in one call and fsyncs. After every append the
previous bytes are a strict prefix of the file (A-6) and the file holds no CR.

Reading works on bytes (F-36): the file must end in LF (``TornTail`` names the offset of the
last LF and the bytes after it), every line is parsed strictly (no repeated key, no non-finite
constant, F-39), line 1 must be a header, every later line an event whose ``seq`` equals its
line index and whose ``run_id`` equals the header's.

The module imports the standard library, ``jsonschema``, ``llm4pol.run.jsonio``,
``llm4pol.run.config``, ``llm4pol.run.ids`` and ``llm4pol.data.snapshot`` only.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema.exceptions import best_match

from llm4pol.run import ids
from llm4pol.run.config import SCHEMA_DIR, ProblemSpec, ProblemSpecError, parse_problem_spec
from llm4pol.run.jsonio import StrictJsonError, canonical_bytes, loads_strict

LEDGER_NAME = "ledger.jsonl"
LEDGER_SCHEMA_PATH = SCHEMA_DIR / "ledger-event.json"

EVENT_KINDS: tuple[str, ...] = (
    "run_opened",
    "iteration_opened",
    "selection",
    "evaluation",
    "no_match",
    "iteration_closed",
    "run_closed",
)

_LF = b"\n"


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


# --------------------------------------------------------------------------
# Typed records
# --------------------------------------------------------------------------


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


# --------------------------------------------------------------------------
# Schema validation: the header line and the event lines have one validator each
# --------------------------------------------------------------------------


@functools.cache
def _validator(part: str) -> Any:
    """The Draft 2020-12 validator of ``#/$defs/<part>`` of ``ledger-event.json`` (built once)."""
    schema = loads_strict(LEDGER_SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$defs": schema["$defs"],
            "$ref": f"#/$defs/{part}",
        }
    )


def _check(record: object, part: str, where: str) -> None:
    error = best_match(_validator(part).iter_errors(record))
    if error is not None:
        pointer = "/" + "/".join(str(item) for item in error.absolute_path)
        raise LedgerFormatError(f"{where}: {pointer}: {error.message}")


def _line_bytes(record: Mapping[str, Any], part: str, where: str) -> bytes:
    """Validate ``record`` and return its canonical line; nothing is written by the caller first."""
    _check(record, part, where)
    try:
        return canonical_bytes(record)
    except StrictJsonError as exc:
        raise LedgerFormatError(f"{where}: {exc}") from exc


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------


def _write(path: Path, mode: str, data: bytes) -> None:
    with path.open(mode) as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())


def create(path: Path, header: Mapping[str, Any]) -> None:
    """Create the ledger with its header line; ``LedgerError`` when the file exists (A-6)."""
    data = _line_bytes(header, "header", "header")
    try:
        _write(path, "xb", data)
    except FileExistsError as exc:
        raise LedgerError("ledger exists; use replay") from exc


def _refuse_torn_tail(path: Path) -> None:
    """Refuse to append to a file whose last byte is not LF (Pitfall 2), reading one byte."""
    try:
        with path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            if fh.tell() == 0:
                raise LedgerError("ledger is empty")
            fh.seek(-1, os.SEEK_END)
            last = fh.read(1)
    except FileNotFoundError as exc:
        raise LedgerError("ledger does not exist") from exc
    if last != _LF:
        _refuse_missing_lf(path.read_bytes(), str(path))


def append(path: Path, event: Mapping[str, Any]) -> None:
    """Append one event as one complete LF-terminated line, then fsync.

    The record is validated first, and the ledger must exist and end in LF: a record that
    fails the schema raises ``LedgerFormatError`` before the file is opened.
    """
    data = _line_bytes(event, "event", "event")
    _refuse_torn_tail(path)
    _write(path, "ab", data)


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------


def _refuse_missing_lf(raw: bytes, where: str) -> None:
    if raw.endswith(_LF):
        return
    last = raw.rfind(_LF)
    raise TornTail(
        f"{where}: the final line is not terminated by LF",
        last_lf_offset=last,
        trailing_bytes=len(raw) - last - 1,
    )


def _parse_line(line: bytes, where: str) -> Any:
    try:
        return loads_strict(line.decode("utf-8"))
    except (UnicodeDecodeError, StrictJsonError) as exc:
        raise LedgerFormatError(f"{where}: {exc}") from exc


def parse_bytes(raw: bytes, *, source: str = "ledger") -> Ledger:
    """Parse the bytes of a ledger with every check ``read`` makes."""
    if not raw:
        raise LedgerFormatError(f"{source}: empty ledger, no header line")
    _refuse_missing_lf(raw, source)
    lines = raw.split(_LF)[:-1]
    header_line = _parse_line(lines[0], f"{source}:1")
    _check(header_line, "header", f"{source}:1")
    try:
        header = Header.from_json(header_line)
        ids.require_run_id(header.run_id)
    except (ProblemSpecError, ids.RunIdError) as exc:
        raise LedgerFormatError(f"{source}:1: {exc}") from exc
    events: list[Event] = []
    for index, line in enumerate(lines[1:], start=1):
        where = f"{source}:{index + 1}"
        record = _parse_line(line, where)
        _check(record, "event", where)
        event = Event.from_json(record)
        if event.run_id != header.run_id:
            raise LedgerIntegrityError(f"{where}: run_id {event.run_id} is not the header's")
        if event.seq != index:
            raise LedgerIntegrityError(f"{where}: seq {event.seq} is not its line index {index}")
        events.append(event)
    return Ledger(header=header, events=tuple(events))


def read(path: Path) -> Ledger:
    """Read ``path`` as bytes and return the ledger, or raise a ``LedgerError`` subclass."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise LedgerError(f"{path}: ledger does not exist") from exc
    return parse_bytes(raw, source=str(path))
