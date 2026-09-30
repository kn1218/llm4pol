"""Run management (charter section 6 row ``run``; charter section 13 M3).

A campaign leaves a record under ``experiments/<run-id>/``: an append-only ledger, a problem
spec, and summaries derived from the ledger alone. This package owns that record. It may import
``llm4pol.evaluate`` and ``llm4pol.data`` and never ``llm4pol.loop`` or ``llm4pol.llm`` (the
``[tool.importlinter]`` contract of CONTEXT D-06, kept by the ``import-linter`` step of
``scripts/check.py``).

The package root re-exports the public names of ``ids``, ``jsonio``, ``config`` and ``ledger``
and imports no dataframe, parquet or array library (RESEARCH F-28, Pattern 4).
"""

from __future__ import annotations

from llm4pol.run.config import (
    Budget,
    Constraint,
    Objective,
    ProblemSpec,
    ProblemSpecError,
    RunExists,
    create_run_dir,
    load_problem_spec,
    parse_problem_spec,
)
from llm4pol.run.ids import (
    RUN_ID_PATTERN,
    Clock,
    RunIdError,
    format_ts,
    new_run_id,
    random_token,
    require_run_id,
    utc_now,
)
from llm4pol.run.jsonio import StrictJsonError, canonical_bytes, loads_strict, pretty_bytes
from llm4pol.run.ledger import (
    EVENT_KINDS,
    LEDGER_NAME,
    Event,
    Header,
    Ledger,
    LedgerError,
    LedgerFormatError,
    LedgerIntegrityError,
    TornTail,
    append,
    create,
    event_record,
    header_record,
    parse_bytes,
    read,
)

__all__ = [
    "EVENT_KINDS",
    "LEDGER_NAME",
    "RUN_ID_PATTERN",
    "Budget",
    "Clock",
    "Constraint",
    "Event",
    "Header",
    "Ledger",
    "LedgerError",
    "LedgerFormatError",
    "LedgerIntegrityError",
    "Objective",
    "ProblemSpec",
    "ProblemSpecError",
    "RunExists",
    "RunIdError",
    "StrictJsonError",
    "TornTail",
    "append",
    "canonical_bytes",
    "create",
    "create_run_dir",
    "event_record",
    "format_ts",
    "header_record",
    "load_problem_spec",
    "loads_strict",
    "new_run_id",
    "parse_bytes",
    "parse_problem_spec",
    "pretty_bytes",
    "random_token",
    "read",
    "require_run_id",
    "utc_now",
]
