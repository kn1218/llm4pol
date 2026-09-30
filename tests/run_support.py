"""Fixtures shared by the run-management tests (Phase 4, plan 04-01).

A plain module beside ``conftest.py`` (``tests/`` has no ``__init__.py``; pytest puts the
directory on ``sys.path``, so it is imported as ``run_support``). Every value is invented: the
ids, times and hashes below name no data row and no real run.

The time and the random token are injected everywhere (RESEARCH Pattern 1), so a ledger built
from these constants is byte-identical from one run to the next.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

FIXED_NOW = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
FIXED_TOKEN = "00000000"
FIXED_RUN_ID = "20260101T000000Z-00000000"
FIXED_TS = "2026-01-01T00:00:00Z"
FIXED_CODE_SHA = "0" * 40

SNAPSHOT_ID = "polyomics:general_polymers@041e5834"


def constant_clock() -> Callable[[], datetime]:
    """A clock that always reads ``FIXED_NOW``."""

    def clock() -> datetime:
        return FIXED_NOW

    return clock


def charter_problem(iterations: int, candidates_per_beam: int, beams: int) -> dict[str, Any]:
    """The charter section 7 problem spec, with ``schema_version`` 1 and the two thresholds."""
    return {
        "schema_version": 1,
        "objective": {"property": "thermal_conductivity", "direction": "max"},
        "constraints": [
            {"property": "dielectric_const_dc", "op": "<=", "value": 2.6},
            {"property": "tg", "op": ">=", "value": 400.0},
        ],
        "form": "constrained_single",
        "budget": {
            "iterations": iterations,
            "candidates_per_beam": candidates_per_beam,
            "beams": beams,
        },
        "table": SNAPSHOT_ID,
        "seed": 0,
    }
