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
constant, F-39) and must equal the canonical bytes of what it parses to (no CR, no space, no
reordered key, no number written another way, no integer field written ``2.0``; WR-02), line 1
must be the only header, every later line an event whose ``seq`` equals its line index and whose
``run_id`` equals the header's. One pass over the events then checks
that no event key occurs twice, that the lifecycle is in order and that the populations of
``run_opened`` are parallel arrays (plan 04-05). Nothing here repairs or shortens a file.

The module imports the standard library, ``jsonschema``, ``llm4pol.run.jsonio``,
``llm4pol.run.config``, ``llm4pol.run.ids``, ``llm4pol.run.atomic``, ``llm4pol.run.records``,
``llm4pol.run.strictschema`` and ``llm4pol.data.snapshot`` only.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema.exceptions import best_match

from llm4pol.run import ids
from llm4pol.run.atomic import RecordWriteError, fsync_dir
from llm4pol.run.config import SCHEMA_DIR, ProblemSpecError
from llm4pol.run.jsonio import StrictJsonError, canonical_bytes, loads_strict
from llm4pol.run.records import (
    EVENT_KINDS,
    Event,
    EventKey,
    Header,
    Ledger,
    LedgerError,
    LedgerFormatError,
    LedgerIntegrityError,
    TornTail,
    event_key,
    event_record,
    header_record,
)
from llm4pol.run.strictschema import validator_class

__all__ = [
    "EVENT_KINDS",
    "LEDGER_NAME",
    "LEDGER_SCHEMA_PATH",
    "Event",
    "EventKey",
    "Header",
    "Ledger",
    "LedgerError",
    "LedgerFormatError",
    "LedgerIntegrityError",
    "TornTail",
    "append",
    "create",
    "event_key",
    "event_record",
    "header_record",
    "parse_bytes",
    "read",
]

LEDGER_NAME = "ledger.jsonl"
LEDGER_SCHEMA_PATH = SCHEMA_DIR / "ledger-event.json"

_LF = b"\n"
_TAIL_CHUNK = 1 << 16


def _check_populations(payload: Mapping[str, Any], where: str) -> None:
    names = [population["name"] for population in payload["populations"]]
    if payload["primary"] not in names or len(set(names)) != len(names):
        raise LedgerFormatError(f"{where}: primary {payload['primary']!r} is not one of {names}")
    for population in payload["populations"]:
        arrays = [population["objective"], *population["constraints"].values()]
        if len({len(array) for array in arrays}) != 1:
            raise LedgerFormatError(f"{where}: arrays of {population['name']!r} differ in length")


def _check_events(events: Sequence[Event], source: str) -> None:
    """One pass: the first event, no repeated key, nothing after run_closed, the lifecycle order."""
    seen: set[EventKey] = set()
    selected: dict[tuple[int, str], frozenset[str]] = {}
    open_iteration: int | None = None
    closed = 0
    for position, event in enumerate(events):
        where, kind, payload = f"{source}:{position + 2}", event.event, event.payload
        key = event_key(event)
        if position and events[position - 1].event == "run_closed":
            raise LedgerIntegrityError(f"{where}: {kind} follows run_closed")
        if key in seen:
            raise LedgerIntegrityError(f"{where}: duplicate event {key}")
        if not position and kind != "run_opened":
            raise LedgerIntegrityError(f"{where}: the first event is {kind}, not run_opened")
        seen.add(key)
        if kind == "run_opened":
            _check_populations(payload, where)
        elif kind == "iteration_opened":
            if open_iteration is not None or event.iteration != closed + 1:
                raise LedgerIntegrityError(
                    f"{where}: iteration {event.iteration} opens after {closed} closed, "
                    f"{open_iteration} open"
                )
            open_iteration = event.iteration
        elif kind != "run_closed":
            if event.iteration != open_iteration:
                raise LedgerIntegrityError(
                    f"{where}: {kind} of iteration {event.iteration} outside iteration {open_iteration}"
                )
            beam = (event.iteration, str(payload.get("beam", "")))
            if kind in ("selection", "no_match"):
                selected[beam] = frozenset(payload.get("candidates", ()))
            elif kind == "evaluation":
                if payload["candidate_id"] not in selected.get(beam, frozenset()):
                    raise LedgerIntegrityError(
                        f"{where}: evaluation of {payload['candidate_id']} has no selection naming it"
                    )
            else:
                closed, open_iteration = event.iteration, None


@functools.cache
def _validator(part: str) -> Any:
    """The Draft 2020-12 validator of ``#/$defs/<part>`` of ``ledger-event.json`` (built once)."""
    schema = loads_strict(LEDGER_SCHEMA_PATH.read_text(encoding="utf-8"))
    return validator_class(strict_integers=True)(
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
    """Validate ``record`` and return its canonical line."""
    _check(record, part, where)
    try:
        return canonical_bytes(record)
    except StrictJsonError as exc:
        raise LedgerFormatError(f"{where}: {exc}") from exc


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
    except OSError as exc:
        raise RecordWriteError(
            f"creating {path.name} failed: {exc}; the header may be partial"
        ) from exc
    fsync_dir(path.parent)  # the entry is durable too (WR-06)


def _last_line(path: Path) -> tuple[int, bytes, bool]:
    """The file size, its last line, and whether that line is the first (the header).

    Refuses a missing or empty file and a file whose last byte is not LF (Pitfall 2); only the
    bytes of the last line are read.
    """
    try:
        with path.open("rb") as fh:
            size = fh.seek(0, os.SEEK_END)
            if size == 0:
                raise LedgerError("ledger is empty")
            fh.seek(-1, os.SEEK_END)
            if fh.read(1) != _LF:
                _refuse_missing_lf(path.read_bytes(), str(path))
            start, block = size - 1, b""  # block holds bytes [start, size - 1)
            while start > 0:
                step = min(_TAIL_CHUNK, start)
                start -= step
                fh.seek(start)
                block = fh.read(step) + block
                if _LF in block:
                    break
    except FileNotFoundError as exc:
        raise LedgerError("ledger does not exist") from exc
    cut = block.rfind(_LF)
    return size, block[cut + 1 :], cut < 0 and start == 0


def _require_next(path: Path, event: Mapping[str, Any]) -> int:
    """Refuse an event that does not directly follow the recorded tail; return the file size."""
    size, line, first = _last_line(path)
    tail = _parse_line(line, f"{path}: last line")
    if not isinstance(tail, dict):
        raise LedgerFormatError(f"{path}: the last line is not an object")
    last = 0 if first else tail.get("seq")
    if (
        last != event["seq"] - 1
        or tail.get("event") == "run_closed"
        or tail.get("run_id") != event["run_id"]
    ):
        raise LedgerIntegrityError(
            f"append of seq {event['seq']} does not follow the recorded tail (seq {last}, "
            f"{tail.get('event', 'header')}) of run {tail.get('run_id')}"
        )
    return size


def append(path: Path, event: Mapping[str, Any]) -> None:
    """Append one validated event as one LF-terminated line, then fsync.

    A torn tail refuses, and so does an event whose ``seq`` is not the last ``seq`` plus one, one
    after ``run_closed`` and one of another run (CR-01, belt and braces beside the run lock).
    """
    data = _line_bytes(event, "event", "event")
    size = _require_next(path, event)
    try:
        _write(path, "ab", data)
    except OSError as exc:
        raise RecordWriteError(
            f"appending seq {event['seq']} to {path.name} failed: {exc}; the ledger may end in a "
            f"torn line after byte offset {size - 1}, which resume refuses",
            last_lf_offset=size - 1,
        ) from exc


def _refuse_missing_lf(raw: bytes, where: str) -> None:
    if raw.endswith(_LF):
        return
    last = raw.rfind(_LF)
    raise TornTail(
        f"{where}: the final line is not terminated by LF "
        f"(last LF at byte offset {last}, {len(raw) - last - 1} trailing bytes)",
        last_lf_offset=last,
        trailing_bytes=len(raw) - last - 1,
    )


def _parse_line(line: bytes, where: str) -> Any:
    try:
        return loads_strict(line.decode("utf-8"))
    except (UnicodeDecodeError, StrictJsonError) as exc:
        raise LedgerFormatError(f"{where}: {exc}") from exc


def _require_canonical(record: Any, line: bytes, where: str) -> None:
    """The line is exactly the canonical bytes of what it parses to: no CR, no space, no reorder."""
    try:
        canonical = canonical_bytes(record)
    except StrictJsonError as exc:
        raise LedgerFormatError(f"{where}: {exc}") from exc
    if canonical != line + _LF:
        raise LedgerFormatError(f"{where}: the line is not in canonical form")


def parse_bytes(raw: bytes, *, source: str = "ledger") -> Ledger:
    """Parse the bytes of a ledger with every check ``read`` makes."""
    if not raw:
        raise LedgerFormatError(f"{source}: empty ledger, no header line")
    _refuse_missing_lf(raw, source)
    lines = raw.split(_LF)[:-1]
    header_line = _parse_line(lines[0], f"{source}:1")
    _check(header_line, "header", f"{source}:1")
    _require_canonical(header_line, lines[0], f"{source}:1")
    try:
        header = Header.from_json(header_line)
        ids.require_run_id(header.run_id)
    except (ProblemSpecError, ids.RunIdError) as exc:
        raise LedgerFormatError(f"{source}:1: {exc}") from exc
    events: list[Event] = []
    for index, line in enumerate(lines[1:], start=1):
        where = f"{source}:{index + 1}"
        record = _parse_line(line, where)
        if isinstance(record, dict) and "provenance" in record and "event" not in record:
            raise LedgerFormatError(f"{where}: a second header")
        _check(record, "event", where)
        _require_canonical(record, line, where)
        event = Event.from_json(record)
        if event.run_id != header.run_id:
            raise LedgerIntegrityError(f"{where}: run_id {event.run_id} is not the header's")
        if event.seq != index:
            raise LedgerIntegrityError(f"{where}: seq {event.seq} is not its line index {index}")
        events.append(event)
    _check_events(events, source)
    return Ledger(header=header, events=tuple(events))


def read(path: Path) -> Ledger:
    """Read ``path`` as bytes and return the ledger, or raise a ``LedgerError`` subclass."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise LedgerError(f"{path}: ledger does not exist") from exc
    return parse_bytes(raw, source=str(path))
