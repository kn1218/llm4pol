"""Fixtures shared by the run-management tests (Phase 4, plan 04-01).

A plain module beside ``conftest.py`` (``tests/`` has no ``__init__.py``; pytest puts the
directory on ``sys.path``, so it is imported as ``run_support``). Every value is invented: the
ids, times and hashes below name no data row and no real run.

The time and the random token are injected everywhere (RESEARCH Pattern 1), so a ledger built
from these constants is byte-identical from one run to the next.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
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


# --------------------------------------------------------------------------
# The reference and budget campaigns of plan 04-05, derived by hand from the fixture of
# ``conftest._CORE`` (see the plan objective). Both run under the fixed identity above, so the
# ledger and ``results.csv`` are byte-identical from one run to the next.
# --------------------------------------------------------------------------

UNKNOWN = "0123456789abcdef"  # well formed and absent from the candidate table

# Two iterations, two beams each: 17 events after the header, five `evals`, budget limit 12.
REFERENCE_PLAN: dict[str, Any] = {
    "schema_version": 1,
    "iterations": [
        {
            "iteration": 1,
            "beams": [
                {"beam": "full", "candidates": [PE, PS]},
                {"beam": "random", "candidates": [POM, PVF, UNKNOWN]},
            ],
        },
        {
            "iteration": 2,
            "beams": [
                {"beam": "full", "candidates": [PE, PP_ISO]},
                {"beam": "chem", "candidates": []},
            ],
        },
    ],
}
REFERENCE_KINDS = [
    "run_opened",
    "iteration_opened",
    "selection",
    "evaluation",
    "evaluation",
    "selection",
    "evaluation",
    "evaluation",
    "evaluation",
    "iteration_closed",
    "iteration_opened",
    "selection",
    "evaluation",
    "evaluation",
    "no_match",
    "iteration_closed",
    "run_closed",
]
_RESULTS_HEADER = (
    b"iteration,beam,population,n_selected,n_ok,median_objective,feasible_frac,"
    b"n_population,pct_of_population,hits_top10,hits_top1\n"
)
REFERENCE_RESULTS_CSV = _RESULTS_HEADER + (
    b"1,full,check_tc,2,2,0.235,0.0,4,75.0,0,0\n"
    b"1,full,readme_triple,2,2,0.235,0.0,4,75.0,0,0\n"
    b"1,random,check_tc,3,1,0.22,0.0,4,75.0,0,0\n"
    b"1,random,readme_triple,3,1,0.22,0.0,4,75.0,0,0\n"
    b"2,full,check_tc,2,2,0.2575,0.5,4,75.0,1,1\n"
    b"2,full,readme_triple,2,2,0.2575,0.5,4,75.0,1,1\n"
    b"2,chem,check_tc,0,0,,,4,,0,0\n"
    b"2,chem,readme_triple,0,0,,,4,,0,0\n"
)
REFERENCE_RESULTS_SHA256 = "0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6"

# One iteration, one beam of three candidates, budget limit 2: PS is refused.
BUDGET_PLAN: dict[str, Any] = {
    "schema_version": 1,
    "iterations": [{"iteration": 1, "beams": [{"beam": "full", "candidates": [PE, PP_ISO, PS]}]}],
}
BUDGET_RESULTS_CSV = _RESULTS_HEADER + (
    b"1,full,check_tc,3,2,0.2575,0.3333333333333333,4,75.0,1,1\n"
    b"1,full,readme_triple,3,2,0.2575,0.3333333333333333,4,75.0,1,1\n"
)
BUDGET_RESULTS_SHA256 = "23f046d9a90fcfad19ff5963610210885ef4d7e558c8acaaec9bec9dc0c73062"


def fixed_run(root: Path, experiments: Path, plan: dict[str, Any], problem: dict[str, Any]) -> Path:
    """Open and drive one run under the fixed identity; return its run directory."""
    from llm4pol.run import config, resume, selector  # deferred: ledger tests import this module

    spec = config.parse_problem_spec(problem)
    chosen = selector.PlanSelector.from_payload(plan, spec)
    run_dir = resume.open_run(
        experiments,
        spec,
        chosen,
        root=root,
        now=FIXED_NOW,
        token=FIXED_TOKEN,
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
    )
    resume.drive(run_dir, root=root, selector=chosen, clock=constant_clock())
    return run_dir


def reference_run(root: Path, experiments: Path) -> Path:
    """The uninterrupted reference campaign: 17 events, five ``evals``, 453 bytes of results."""
    return fixed_run(root, experiments, REFERENCE_PLAN, charter_problem(2, 3, 2))


def budget_run(root: Path, experiments: Path) -> Path:
    """The budget scenario: six events, ended by a recorded refusal of PS."""
    return fixed_run(root, experiments, BUDGET_PLAN, charter_problem(1, 1, 2))


def cut_run(source_dir: Path, target_experiments: Path, k: int) -> Path:
    """A new run directory holding ``meta.json`` and the header plus the first ``k`` events."""
    lines = (source_dir / "ledger.jsonl").read_bytes().split(b"\n")[:-1]
    target = target_experiments / source_dir.name
    target.mkdir(parents=True)
    (target / "meta.json").write_bytes((source_dir / "meta.json").read_bytes())
    (target / "ledger.jsonl").write_bytes(b"".join(line + b"\n" for line in lines[: k + 1]))
    return target


# --------------------------------------------------------------------------
# Plan 04-07: the column definitions and the two currencies, proven on ledgers built by hand.
# Like the builders above these import nothing of ``llm4pol.run``.
# --------------------------------------------------------------------------

# Typed from the derivation of the plan objective (five evaluation events charged 1, 1, 1, 1, 0,
# 0, 1 make `evals` 5; the table backend costs no compute; no provider is called before Phase 6),
# not copied from an output: seven lines, 89 bytes, the key separator is a colon and a space.
REFERENCE_USAGE_JSON = (
    b"{\n"
    b'  "cpu_hours": 0.0,\n'
    b'  "evals": 5,\n'
    b'  "schema_version": 1,\n'
    b'  "tokens": 0,\n'
    b'  "usd": 0.0\n'
    b"}\n"
)
REFERENCE_USAGE_SHA256 = "bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa"


def canonical_line(record: dict[str, Any]) -> bytes:
    """One ledger line in the canonical form: sorted keys, no spaces, one LF."""
    return (
        json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def problem_variant(
    *,
    direction: str = "max",
    eps_max: float = 2.6,
    tg_min: float = 400.0,
    iterations: int = 2,
    candidates_per_beam: int = 3,
    beams: int = 2,
) -> dict[str, Any]:
    """The charter problem with another direction or other thresholds."""
    problem = charter_problem(iterations, candidates_per_beam, beams)
    problem["objective"]["direction"] = direction
    problem["constraints"][0]["value"] = eps_max
    problem["constraints"][1]["value"] = tg_min
    return problem


def recorded_event_lines(run_dir: Path) -> list[bytes]:
    """The event lines of a run, each with its LF, header left out."""
    lines = (run_dir / "ledger.jsonl").read_bytes().split(b"\n")[:-1]
    return [line + b"\n" for line in lines[1:]]


def ledger_under(problem: dict[str, Any], event_lines: list[bytes]) -> bytes:
    """A header for ``problem`` joined with recorded event lines: the same events, another problem."""
    return canonical_line(valid_header(problem)) + b"".join(event_lines)


def candidate_ids(count: int) -> list[str]:
    """``count`` distinct well-formed ids that name no table row."""
    return [f"{index:016x}" for index in range(1, count + 1)]


def population_payload(
    name: str,
    objective: list[float | None],
    eps: list[float | None] | None = None,
    tg: list[float | None] | None = None,
) -> dict[str, Any]:
    """A population for the charter problem; the constraint arrays default to feasible values."""
    size = len(objective)
    return {
        "name": name,
        "objective": list(objective),
        "constraints": {
            "dielectric_const_dc": list(eps) if eps is not None else [2.0] * size,
            "tg": list(tg) if tg is not None else [500.0] * size,
        },
    }


def feasible_population(name: str, m: int) -> dict[str, Any]:
    """``m`` members, every one feasible, with objectives 1.0, 2.0, ..., m.0."""
    return population_payload(name, [float(value) for value in range(1, m + 1)])


def _hand_result(
    candidate: str, key: str, value: float | None, evals: int, cpu_hours: float
) -> dict[str, Any]:
    result = valid_result(candidate, key, 0.0 if value is None else value, evals=evals)
    result["cost"] = valid_cost(evals, cpu_hours)
    if value is None:
        result.update(
            status="missing",
            value=None,
            unit=None,
            n_replicates=None,
            spread=None,
            reason="value_absent",
        )
    return result


def hand_ledger(
    problem: dict[str, Any],
    populations: list[dict[str, Any]],
    selected: list[str],
    evaluated: dict[str, dict[str, float | None]],
    *,
    cpu_hours: float = 0.0,
    closed: bool = True,
) -> bytes:
    """A one-iteration, one-beam ledger built by hand.

    ``evaluated`` maps a selected candidate to its value per property (``None`` is a ``missing``
    result); a selected candidate that is absent from it has no evaluation event. The first result
    that has a value carries the charge of the event: one evaluation and ``cpu_hours``.
    """
    events: list[tuple[str, int, dict[str, Any]]] = [
        ("run_opened", 0, {"primary": populations[0]["name"], "populations": populations}),
        ("iteration_opened", 1, {}),
        ("selection", 1, {"beam": "full", "candidates": list(selected)}),
    ]
    for candidate in selected:
        if candidate not in evaluated:
            continue
        results = []
        charged = False
        for key, value in evaluated[candidate].items():
            pays = value is not None and not charged
            charged = charged or pays
            results.append(
                _hand_result(candidate, key, value, 1 if pays else 0, cpu_hours if pays else 0.0)
            )
        events.append(
            (
                "evaluation",
                1,
                {
                    "beam": "full",
                    "candidate_id": candidate,
                    "results": results,
                    "cost": valid_cost(1 if charged else 0, cpu_hours if charged else 0.0),
                },
            )
        )
    if closed:
        events.append(("iteration_closed", 1, {}))
        events.append(("run_closed", 0, {"reason": "completed"}))
    lines = [canonical_line(valid_header(problem))]
    for seq, (kind, iteration, payload) in enumerate(events, start=1):
        lines.append(canonical_line(valid_event(kind, seq, iteration=iteration, payload=payload)))
    return b"".join(lines)
