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


# --------------------------------------------------------------------------
# Ledger builders (plan 04-01, task 2): hand-built records, fixture ids only. They import
# nothing of ``llm4pol.run`` so a ledger test never rests on the code it is checking.
# --------------------------------------------------------------------------

CANDIDATE_A = "7ec8cb49ff317efc"
CANDIDATE_B = "b3a635a55e1a6645"
CANDIDATE_C = "81b997b85ccd2069"

EVENT_KINDS = (
    "run_opened",
    "iteration_opened",
    "selection",
    "evaluation",
    "no_match",
    "iteration_closed",
    "run_closed",
)


def valid_header(problem: dict[str, Any] | None = None) -> dict[str, Any]:
    """A valid ledger header line for the tracer problem (thresholds 2.6 and 400.0)."""
    body = problem if problem is not None else charter_problem(1, 3, 2)
    return {
        "schema_version": 1,
        "run_id": FIXED_RUN_ID,
        "problem": body,
        "provenance": {
            "seed": body["seed"],
            "snapshot": SNAPSHOT_ID,
            "registry_version": "v1",
            "selector": "plan:sha256:" + "0" * 64,
            "code_git_sha": FIXED_CODE_SHA,
        },
    }


def valid_cost(evals: int = 1, cpu_hours: float = 0.0) -> dict[str, Any]:
    return {"evals": evals, "cpu_hours": cpu_hours}


def valid_result(
    candidate_id: str = CANDIDATE_A,
    property_key: str = "thermal_conductivity",
    value: float = 0.315,
    *,
    evals: int = 1,
) -> dict[str, Any]:
    """A valid ``ok`` result of the evaluator response schema (invented value)."""
    return {
        "candidate_id": candidate_id,
        "property": property_key,
        "status": "ok",
        "value": value,
        "unit": "W/(m K)",
        "n_replicates": 2,
        "spread": 0.01,
        "backend": "table",
        "source": SNAPSHOT_ID,
        "provenance_tier": "md_simulated",
        "cached": False,
        "cost": valid_cost(evals),
    }


def valid_payload(kind: str) -> dict[str, Any]:
    """A valid payload of each of the seven M3 event kinds."""
    if kind == "run_opened":
        return {
            "primary": "check_tc",
            "populations": [
                {
                    "name": name,
                    "objective": [0.155, 0.18, 0.2, 0.315],
                    "constraints": {
                        "dielectric_const_dc": [2.2, 2.3, 2.5, 2.6],
                        "tg": [250.0, 260.0, 300.0, 410.0],
                    },
                }
                for name in ("check_tc", "readme_triple")
            ],
        }
    if kind == "selection":
        return {"beam": "full", "candidates": [CANDIDATE_A, CANDIDATE_B]}
    if kind == "evaluation":
        return {
            "beam": "full",
            "candidate_id": CANDIDATE_A,
            "results": [valid_result()],
            "cost": valid_cost(),
        }
    if kind == "no_match":
        return {"beam": "chem"}
    if kind == "run_closed":
        return {"reason": "completed"}
    if kind in ("iteration_opened", "iteration_closed"):
        return {}
    raise ValueError(f"unknown event kind {kind!r}")


def valid_event(
    kind: str,
    seq: int = 1,
    *,
    iteration: int | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A valid event of ``kind``; run-scoped kinds sit at iteration 0, the others at 1."""
    run_scoped = kind in ("run_opened", "run_closed")
    return {
        "seq": seq,
        "ts": FIXED_TS,
        "run_id": FIXED_RUN_ID,
        "iteration": iteration if iteration is not None else (0 if run_scoped else 1),
        "event": kind,
        "payload": payload if payload is not None else valid_payload(kind),
    }


def one_event_of_each_kind() -> list[dict[str, Any]]:
    """Seven valid events, ``seq`` 1..7, one per kind in the order of ``EVENT_KINDS``."""
    return [valid_event(kind, seq) for seq, kind in enumerate(EVENT_KINDS, start=1)]


# --------------------------------------------------------------------------
# The tracer of plan 04-02: the six fixture candidates of ``conftest._CORE`` and the plan and
# results the tracer run must produce. The ids are pinned to the candidate table once, by
# ``test_the_fixture_ids_are_the_candidates_of_the_synthetic_table`` in ``test_run_cli.py``.
# --------------------------------------------------------------------------

PE = "7ec8cb49ff317efc"  # `*CC*` / none
PP_ISO = "d751b16095852737"  # `*CC(*)C` / isotactic
PP_ATA = "c3da5668f5a82772"  # `*CC(*)C` / atactic
PS = "b3a635a55e1a6645"  # `*CC(*)c1ccccc1` / atactic
POM = "81b997b85ccd2069"  # `*CO*` / none, no thermal conductivity
PVF = "d24805b4ce4c381c"  # `*CC(*)F` / none, no Tg

# Iteration 1: beam `full` holds three candidates, beam `chem` matches nothing.
TRACER_PLAN: dict[str, Any] = {
    "schema_version": 1,
    "iterations": [
        {
            "iteration": 1,
            "beams": [
                {"beam": "full", "candidates": [PE, PP_ISO, PS]},
                {"beam": "chem", "candidates": []},
            ],
        }
    ],
}

# Hand-derived from the served medians of the fixture (plan 04-02, objective): 301 bytes, LF only.
TRACER_RESULTS_CSV = (
    b"iteration,beam,population,n_selected,n_ok,median_objective,feasible_frac,"
    b"n_population,pct_of_population,hits_top10,hits_top1\n"
    b"1,full,check_tc,3,3,0.2,0.3333333333333333,4,50.0,1,1\n"
    b"1,full,readme_triple,3,3,0.2,0.3333333333333333,4,50.0,1,1\n"
    b"1,chem,check_tc,0,0,,,4,,0,0\n"
    b"1,chem,readme_triple,0,0,,,4,,0,0\n"
)
TRACER_RESULTS_SHA256 = "bbd59e21275bb7357f83d679ae67ce339dd30c83a126019e833ccff77941be14"
