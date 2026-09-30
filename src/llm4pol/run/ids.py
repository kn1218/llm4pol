"""Run identity and the injected clock (RUN-01; CONTEXT D-01; RESEARCH Pattern 1, F-51).

A run id is ``<UTC YYYYMMDDTHHMMSSZ>-<8 lowercase hex>``: 25 characters, none of which
Windows forbids in a file name. The time and the random token are arguments of
``new_run_id`` -- production passes ``utc_now()`` and ``random_token()``, tests pass constants --
so two runs with the same seed can have identical ledgers only when both are fixed.

``require_run_id`` is the gate between text a caller supplies and a path under ``experiments/``
(threat T-04-02): it matches the whole text before anything is joined.
"""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

RUN_ID_PATTERN = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}")  # ASCII digits only (WR-07)
_TOKEN_PATTERN = re.compile(r"[0-9a-f]{8}")

RUN_ID_TIME_FORMAT = "%Y%m%dT%H%M%SZ"
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

Clock = Callable[[], datetime]


class RunIdError(ValueError):
    """Text that is not a run id, or a token or time that cannot make one."""


def utc_now() -> datetime:
    """The current time in UTC, to the second the run id and every event ``ts`` show."""
    return datetime.now(UTC).replace(microsecond=0)


def random_token() -> str:
    """Eight lowercase hex characters from the operating system's random source."""
    return secrets.token_hex(4)


def _utc(now: datetime) -> datetime:
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise RunIdError("the time must be timezone-aware and in UTC")
    return now.astimezone(UTC)


def format_ts(now: datetime) -> str:
    """The event timestamp form ``YYYY-MM-DDTHH:MM:SSZ``."""
    return _utc(now).strftime(TS_FORMAT)


def new_run_id(now: datetime, token: str) -> str:
    """``<UTC timestamp>-<token>``; the token must be 8 lowercase hex characters."""
    if not _TOKEN_PATTERN.fullmatch(token):
        raise RunIdError("the run id token must be 8 lowercase hex characters")
    return f"{_utc(now).strftime(RUN_ID_TIME_FORMAT)}-{token}"


def require_run_id(text: str) -> str:
    """Return ``text`` unchanged when it is a run id; ``RunIdError`` otherwise."""
    if not RUN_ID_PATTERN.fullmatch(text):
        raise RunIdError("not a run id (expected <UTC YYYYMMDDTHHMMSSZ>-<8 hex>)")
    return text
