"""Strict JSON in two byte forms (CONTEXT D-02; RESEARCH F-29, F-39, Pattern 2).

``canonical_bytes`` is the form of a ledger line: sorted keys, the separators ``,`` and ``:``
with no space, one trailing LF. ``pretty_bytes`` is the form of every tracked JSON file:
indent 2, sorted keys, the item separator ``,`` and the key separator ``: `` (colon, space),
one trailing LF. Both are UTF-8, refuse non-finite numbers and never emit a CR, so the bytes
are identical on Windows and Linux.

``loads_strict`` is the only reader: ``json.loads`` accepts ``NaN`` and ``Infinity`` and lets
the last of a repeated key win (F-39), so both are refused here.

This module imports the standard library only.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


class StrictJsonError(ValueError):
    """A value that cannot be written or a text that cannot be read as strict JSON."""


def _dumps(record: Mapping[str, Any], **options: Any) -> bytes:
    try:
        text = json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False, **options)
    except (ValueError, TypeError) as exc:
        raise StrictJsonError(f"not representable as strict JSON: {exc}") from exc
    return (text + "\n").encode("utf-8")


def canonical_bytes(record: Mapping[str, Any]) -> bytes:
    """One ledger line: no spaces, sorted keys, UTF-8, one trailing LF."""
    return _dumps(record, separators=(",", ":"))


def pretty_bytes(record: Mapping[str, Any]) -> bytes:
    """A tracked JSON file: indent 2, item separator ``,``, key separator ``: ``, one LF."""
    return _dumps(record, indent=2, separators=(",", ": "))


def _refuse_constant(name: str) -> float:
    raise StrictJsonError(f"non-finite JSON constant {name}")


def _refuse_repeated_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        repeated = sorted({key for key in keys if keys.count(key) > 1})
        raise StrictJsonError(f"repeated key {repeated[0]!r}")
    return dict(pairs)


def loads_strict(text: str) -> Any:
    """Parse ``text``; refuse ``NaN``, ``Infinity``, ``-Infinity`` and a repeated key."""
    try:
        return json.loads(
            text, parse_constant=_refuse_constant, object_pairs_hook=_refuse_repeated_keys
        )
    except json.JSONDecodeError as exc:
        raise StrictJsonError(f"invalid JSON: {exc}") from exc
