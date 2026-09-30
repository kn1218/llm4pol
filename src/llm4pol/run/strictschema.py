"""JSON Schema validators that mean what the run schemas say (WR-02, WR-07).

The stock Draft 2020-12 validator differs from the schemas' intent in two ways. Its ``pattern``
uses ``re.search`` over a ``str`` pattern, so ``^...$`` also accepts a value that ends in an LF
(``$`` matches before it) and ``\\d`` matches any Unicode digit. Here ``pattern`` is a
``re.fullmatch`` with ``re.ASCII``: an anchored pattern accepts exactly the text it names, ASCII
only. Optionally ``integer`` counts only an ``int``, since the stock validator accepts ``2.0``,
and a canonical ledger writes ``2``.

The module imports the standard library and ``jsonschema`` only.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

import jsonschema
from jsonschema.exceptions import ValidationError

_BASE = jsonschema.Draft202012Validator


def _pattern(validator: Any, pattern: str, instance: object, schema: object) -> Iterator[Any]:
    if validator.is_type(instance, "string") and not re.fullmatch(pattern, str(instance), re.ASCII):
        yield ValidationError(f"{instance!r} does not match {pattern!r}")


def _is_integer(_checker: Any, instance: object) -> bool:
    return isinstance(instance, int) and not isinstance(instance, bool)


_ANCHORED = jsonschema.validators.extend(_BASE, validators={"pattern": _pattern})
_STRICT = jsonschema.validators.extend(
    _ANCHORED, type_checker=_BASE.TYPE_CHECKER.redefine("integer", _is_integer)
)


def validator_class(*, strict_integers: bool = False) -> Any:
    """The validator class: full-match ASCII patterns, and int-only integers when asked."""
    return _STRICT if strict_integers else _ANCHORED
