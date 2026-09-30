"""Strict JSON in two byte forms (CONTEXT D-02; RESEARCH F-29, F-39, Pattern 2).

``canonical_bytes`` is the form of a ledger line: sorted keys, the separators ``,`` and ``:``
with no space, one trailing LF. ``pretty_bytes`` is the form of every tracked JSON file:
indent 2, sorted keys, the item separator ``,`` and the key separator ``: `` (colon, space),
one trailing LF. Both are UTF-8, refuse non-finite numbers and never emit a CR, so the bytes
are identical on Windows and Linux.

``loads_strict`` is the only reader: ``json.loads`` accepts ``NaN`` and ``Infinity``, turns
``1e999`` into ``inf``, lets the last of a repeated key win (F-39) and fails with a bare
``ValueError`` on a very long integer or ``RecursionError`` on deep nesting, so all are refused
here as ``StrictJsonError``; so is text that cannot be written as UTF-8 (a lone surrogate).

This module imports the standard library only.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any

MAX_INTEGER_CHARS = 64  # a run record holds seeds, counts and sequence numbers, never a bignum


class StrictJsonError(ValueError):
    """A value that cannot be written or a text that cannot be read as strict JSON."""


def _dumps(record: Mapping[str, Any], **options: Any) -> bytes:
    try:
        text = json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False, **options)
        return (text + "\n").encode("utf-8")
    except (ValueError, TypeError, RecursionError) as exc:  # UnicodeEncodeError is a ValueError
        raise StrictJsonError(f"not representable as strict JSON: {exc}") from exc


def canonical_bytes(record: Mapping[str, Any]) -> bytes:
    """One ledger line: no spaces, sorted keys, UTF-8, one trailing LF."""
    return _dumps(record, separators=(",", ":"))


def pretty_bytes(record: Mapping[str, Any]) -> bytes:
    """A tracked JSON file: indent 2, item separator ``,``, key separator ``: ``, one LF."""
    return _dumps(record, indent=2, separators=(",", ": "))


def _refuse_constant(name: str) -> float:
    raise StrictJsonError(f"non-finite JSON constant {name}")


def _refuse_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise StrictJsonError(f"non-finite JSON number {text[:24]}")
    return value


def _bounded_int(text: str) -> int:
    if len(text) > MAX_INTEGER_CHARS:
        raise StrictJsonError(f"integer of {len(text)} characters exceeds {MAX_INTEGER_CHARS}")
    return int(text)


def _refuse_repeated_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        repeated = sorted({key for key in keys if keys.count(key) > 1})
        raise StrictJsonError(f"repeated key {repeated[0]!r}")
    return dict(pairs)


def loads_strict(text: str) -> Any:
    """Parse ``text``; refuse a non-finite number, a very long integer and a repeated key."""
    try:
        return json.loads(
            text,
            parse_constant=_refuse_constant,
            parse_float=_refuse_float,
            parse_int=_bounded_int,
            object_pairs_hook=_refuse_repeated_keys,
        )
    except StrictJsonError:
        raise
    except (ValueError, RecursionError) as exc:  # JSONDecodeError is a ValueError
        raise StrictJsonError(f"invalid JSON: {exc}") from exc
