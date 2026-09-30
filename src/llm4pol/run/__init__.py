"""Run management (charter section 6 row ``run``; charter section 13 M3).

A campaign leaves a record under ``experiments/<run-id>/``: an append-only ledger, a problem
spec, and summaries derived from the ledger alone. This package owns that record. It may import
``llm4pol.evaluate`` and ``llm4pol.data`` and never ``llm4pol.loop`` or ``llm4pol.llm`` (the
``[tool.importlinter]`` contract of CONTEXT D-06, kept by the ``import-linter`` step of
``scripts/check.py``).

The package root re-exports the public names of ``ids``, ``jsonio``, ``config``, ``ledger``,
``selector``, ``reduce`` and ``summary`` (the function ``reduce`` is reached as ``llm4pol.run.reduce.reduce``:
exporting it here would shadow the submodule) and imports no dataframe, parquet or array library
(RESEARCH F-28, Pattern 4). ``population`` and ``resume``, which read the candidate table, are
imported by the ``run`` verb only, so ``replay`` never loads them.
"""

from __future__ import annotations

from llm4pol.run.config import (
    META_NAME,
    PROVIDER_KEY_NAMES,
    Budget,
    CodeIdentity,
    CodeIdentityError,
    Constraint,
    MetaError,
    Objective,
    ProblemSpec,
    ProblemSpecError,
    RunExists,
    build_meta,
    code_identity,
    create_run_dir,
    load_problem_spec,
    parse_problem_spec,
    provider_key_configured,
    validate_meta,
    write_meta,
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
    event_key,
    event_record,
    header_record,
    parse_bytes,
    read,
)
from llm4pol.run.reduce import (
    COLUMNS,
    RESULTS_NAME,
    SUMMARY_NAME,
    USAGE_NAME,
    Outputs,
    Reduced,
    ReduceError,
    Row,
    render_csv,
    render_outputs,
    render_usage,
    result_sha256,
    usage_of,
    write_outputs,
)
from llm4pol.run.selector import PlanError, PlanSelector, Selection, Selector
from llm4pol.run.summary import summary_of

__all__ = [
    "COLUMNS",
    "EVENT_KINDS",
    "LEDGER_NAME",
    "META_NAME",
    "PROVIDER_KEY_NAMES",
    "RESULTS_NAME",
    "RUN_ID_PATTERN",
    "SUMMARY_NAME",
    "USAGE_NAME",
    "Budget",
    "Clock",
    "CodeIdentity",
    "CodeIdentityError",
    "Constraint",
    "Event",
    "Header",
    "Ledger",
    "LedgerError",
    "LedgerFormatError",
    "LedgerIntegrityError",
    "MetaError",
    "Objective",
    "Outputs",
    "PlanError",
    "PlanSelector",
    "ProblemSpec",
    "ProblemSpecError",
    "ReduceError",
    "Reduced",
    "Row",
    "RunExists",
    "RunIdError",
    "Selection",
    "Selector",
    "StrictJsonError",
    "TornTail",
    "append",
    "build_meta",
    "canonical_bytes",
    "code_identity",
    "create",
    "create_run_dir",
    "event_key",
    "event_record",
    "format_ts",
    "header_record",
    "load_problem_spec",
    "loads_strict",
    "new_run_id",
    "parse_bytes",
    "parse_problem_spec",
    "pretty_bytes",
    "provider_key_configured",
    "random_token",
    "read",
    "render_csv",
    "render_outputs",
    "render_usage",
    "require_run_id",
    "result_sha256",
    "summary_of",
    "usage_of",
    "utc_now",
    "validate_meta",
    "write_meta",
    "write_outputs",
]
