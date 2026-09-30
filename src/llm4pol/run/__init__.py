"""Run management (charter section 6 row ``run``; charter section 13 M3).

A campaign leaves a record under ``experiments/<run-id>/``: an append-only ledger, a problem
spec, and summaries derived from the ledger alone. This package owns that record. It may import
``llm4pol.evaluate`` and ``llm4pol.data`` and never ``llm4pol.loop`` or ``llm4pol.llm`` (the
``[tool.importlinter]`` contract of CONTEXT D-06, kept by the ``import-linter`` step of
``scripts/check.py``).

The package root re-exports the names of the modules built so far -- ``ids``, ``jsonio`` and
``config`` -- and imports no dataframe, parquet or array library (RESEARCH F-28, Pattern 4).
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

__all__ = [
    "RUN_ID_PATTERN",
    "Budget",
    "Clock",
    "Constraint",
    "Objective",
    "ProblemSpec",
    "ProblemSpecError",
    "RunExists",
    "RunIdError",
    "StrictJsonError",
    "canonical_bytes",
    "create_run_dir",
    "format_ts",
    "load_problem_spec",
    "loads_strict",
    "new_run_id",
    "parse_problem_spec",
    "pretty_bytes",
    "random_token",
    "require_run_id",
    "utc_now",
]
