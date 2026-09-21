"""The evaluator's result cache (CONTEXT D-04, R-4; RESEARCH Pattern 5, Code Example 4).

Keyed by ``(candidate_id, property, backend, source)``: a result for another
backend or another snapshot is a miss, never a hit (threat T-03-07). An
in-memory dict, optionally persisted to an append-only JSONL file -- one
canonical JSON object per line, LF-only on every platform (F-33), key order
independent (F-35), NaN refused (F-34) -- and replayed on construction when
the path exists. Every replayed record goes back through
``EvalResult.from_json``, so a tampered or truncated line is a loud
``CacheError`` naming the path and the line number, never a silent skip.

The cache is a derived artifact: the Phase 4 ledger is the durable record.
Persistence is one append per request, flushed and nothing more (F-36).
Nothing in this module decides what is cached or how much a result costs:
the ``Evaluator`` queues only ``ok`` / ``missing`` results (never ``error``,
never ``unsupported``), stored records keep ``cached: false``, and a hit is
marked ``cached: true`` with a zero cost on return (R-4).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from llm4pol.evaluate.contract import Backend, EvalResult

CacheKey = tuple[str, str, str, str]


class CacheError(RuntimeError):
    """A cache file line that cannot be replayed (``<path>:<lineno>: <message>``)."""


def key_for(candidate_id: str, property_key: str, backend: Backend) -> CacheKey:
    """The cache key of one lookup through ``backend`` (D-04)."""
    return (candidate_id, property_key, backend.name, backend.source)


def canonical_line(key: CacheKey, result: EvalResult) -> str:
    """The one JSONL line of a stored record: sorted keys, no spaces, LF, no NaN."""
    record = {"key": list(key), "result": result.to_json()}
    return (
        json.dumps(
            record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
        + "\n"
    )


class JsonlCache:
    """A dict of ``EvalResult`` by ``CacheKey``, replayed from and appended to ``path``."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._records: dict[CacheKey, EvalResult] = {}
        if path is not None and path.exists():
            self._records = _replay(path)

    @property
    def path(self) -> Path | None:
        return self._path

    def __len__(self) -> int:
        return len(self._records)

    def get(self, key: CacheKey) -> EvalResult | None:
        """The stored result for ``key`` (still ``cached: false``), or ``None``."""
        return self._records.get(key)

    def put_many(self, items: Iterable[tuple[CacheKey, EvalResult]]) -> None:
        """Store every item, then append them to ``path`` in one flushed write (R-4)."""
        new = list(items)
        if not new:
            return
        self._records = {**self._records, **dict(new)}
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as fh:
            for key, result in new:
                fh.write(canonical_line(key, result))
            fh.flush()


def _replay(path: Path) -> dict[CacheKey, EvalResult]:
    """Read every line of ``path`` back into records; ``CacheError`` on the first bad line."""
    records: dict[CacheKey, EvalResult] = {}
    with path.open("r", encoding="utf-8", newline="\n") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                key, result = _parse_record(line)
            except ValueError as exc:
                raise CacheError(f"{path}:{lineno}: {exc}") from exc
            records[key] = result
    return records


def _parse_record(line: str) -> tuple[CacheKey, EvalResult]:
    """One stored line -> ``(key, result)``; ``ValueError`` on any shape or type defect."""
    record = json.loads(line)  # JSONDecodeError is a ValueError
    if not isinstance(record, dict) or set(record) != {"key", "result"}:
        raise ValueError("record must be an object with exactly the keys 'key' and 'result'")
    key = record["key"]
    if not isinstance(key, list) or len(key) != 4 or not all(isinstance(part, str) for part in key):
        raise ValueError("key must be a list of four strings")
    return (key[0], key[1], key[2], key[3]), EvalResult.from_json(record["result"])
