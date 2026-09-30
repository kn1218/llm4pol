"""Secret redaction for ``meta.json``: by key name and by the shape of a string value (WR-05; F-48).

``redact`` returns a copy of a mapping in which every secret-shaped key name holds ``REDACTED``
and so does every string value that has the shape of a credential. It is the second defence: the
closed ``run-meta.json`` schema is the first (no key of ``meta.json`` can hold an environment
value), and this covers the one open mapping the schema admits (``prompt_versions``) and what
Phase 6 adds (D-01).

Names are read after splitting camel case and ``-`` into ``_`` and lowering the case, so
``apiKey``, ``API-KEY`` and ``api_key`` are one name. ``secret``, ``password``, ``passwd``,
``credential(s)``, ``private_key`` and ``authorization`` redact as a segment anywhere in the
name; ``api_key``, ``access_key``, ``signing_key``, ``encryption_key``, ``token``, ``pwd``,
``auth`` and ``bearer`` only as the end of it, so ``tokens``, ``max_tokens`` and ``token_budget``
(usage numbers), ``key`` and ``author`` are kept (Pitfall 10).

The shapes are the ones of ``scripts/history_secret_scan.py`` in short form: an ``sk-`` key, a
GitHub, Hugging Face, Google, AWS or Slack token, a PEM private-key header and a ``Bearer``
credential, found anywhere in a string.

The module imports the standard library only.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

# The marker of CONTEXT D-01 that stands in for the value of a secret-shaped key name.
REDACTED = "***REDACTED***"

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SEPARATORS = re.compile(r"[-\s.]+")

_SEGMENT_ANYWHERE = re.compile(
    r"(?:^|_)(?:secret|password|passwd|credentials?|private_?key|authorization)(?:_|$)"
)
_SEGMENT_AT_END = re.compile(
    r"(?:^|_)(?:api_?key|(?:access|signing|encryption)_?key|token|pwd|auth|bearer)$"
)

_VALUE_SHAPES: tuple[re.Pattern[str], ...] = tuple(
    re.compile(shape)
    for shape in (
        r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{20,}",
        r"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{36,}",
        r"(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{20,}",
        r"(?<![A-Za-z0-9_])hf_[A-Za-z0-9]{30,}",
        r"(?<![A-Za-z0-9_])AIza[0-9A-Za-z_-]{35}",
        r"(?<![A-Za-z0-9_])A[KS]IA[0-9A-Z]{16}",
        r"(?<![A-Za-z0-9_])xox[bapsr]-[0-9A-Za-z-]{10,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY[A-Z ]*-----",
        r"(?i)(?<![A-Za-z0-9_])bearer\s+[A-Za-z0-9._~+/=-]{20,}",
    )
)


def _normalised(name: object) -> str:
    return _SEPARATORS.sub("_", _CAMEL_BOUNDARY.sub("_", str(name))).lower()


def is_secret_name(name: object) -> bool:
    """True when ``name`` reads as the name of a credential."""
    lowered = _normalised(name)
    return bool(_SEGMENT_ANYWHERE.search(lowered) or _SEGMENT_AT_END.search(lowered))


def is_secret_value(text: str) -> bool:
    """True when ``text`` holds something shaped like a credential."""
    return any(shape.search(text) for shape in _VALUE_SHAPES)


def redact(value: Any) -> Any:
    """A copy of ``value`` with secret-shaped key names and string values holding ``REDACTED``.

    Mappings and lists are followed to any depth (a tuple comes back as a list); the argument is
    never changed. The rules read names and string shapes only, so a number under ``tokens``
    survives.
    """
    if isinstance(value, Mapping):
        return {
            key: REDACTED if is_secret_name(key) else redact(item) for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [redact(item) for item in value]
    if isinstance(value, str) and is_secret_value(value):
        return REDACTED
    return value
