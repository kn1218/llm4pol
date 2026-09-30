"""The Phase 4 tracer: problem spec -> run -> ledger -> replay -> results.csv (plan 04-02).

One path through every layer of ``llm4pol.run`` on the synthetic candidate table, driven through
``python -m llm4pol.run`` (RUN-01, RUN-02, RUN-04; CONTEXT D-01, D-07, D-39, R-1..R-8; ADR-0008
items 2-5 and 8). Every id and value is an invented fixture fact of ``conftest._CORE``; the six
ids of ``run_support`` are pinned to the candidate table once, so they are never copied blindly.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import pyarrow.parquet as pq
import pytest

from conftest import REPO_ROOT
from llm4pol.data import snapshot
from llm4pol.run import __main__ as cli
from llm4pol.run import config, ids, jsonio, ledger, reduce, resume, selector
from run_support import (
    FIXED_CODE_SHA,
    FIXED_NOW,
    FIXED_RUN_ID,
    FIXED_TOKEN,
    PE,
    POM,
    PP_ATA,
    PP_ISO,
    PS,
    PVF,
    TRACER_PLAN,
    TRACER_RESULTS_CSV,
    TRACER_RESULTS_SHA256,
    charter_problem,
    constant_clock,
)

SRC = REPO_ROOT / "src"
SCHEMAS = REPO_ROOT / "protocol" / "schemas"
RUN_PACKAGE = SRC / "llm4pol" / "run"
PROPERTY_ORDER = ["thermal_conductivity", "dielectric_const_dc", "tg"]
TRACER_KINDS = [
    "run_opened",
    "iteration_opened",
    "selection",
    "evaluation",
    "evaluation",
    "evaluation",
    "no_match",
    "iteration_closed",
    "run_closed",
]
META_KEYS = {
    "schema_version",
    "run_id",
    "created_at",
    "problem",
    "code_git_sha",
    "dirty",
    "prompt_versions",
    "provider",
    "model",
    "seed",
    "snapshot",
    "snapshot_sha256",
    "registry_version",
    "selector",
    "provider_key_configured",
}


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _child_env() -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"}


def _module(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm4pol.run", *args],
        cwd=REPO_ROOT,
        env=_child_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


@dataclass(frozen=True)
class Tracer:
    """The run of the tracer test: where it lives and what it printed."""

    run_id: str
    run_dir: Path
    experiments: Path
    root: Path
    problem_path: Path
    plan_path: Path
    stdout: str


def _tracer_files(tmp_path: Path) -> tuple[Path, Path]:
    problem = _write_json(tmp_path / "problem.json", charter_problem(1, 3, 2))
    plan = _write_json(tmp_path / "plan.json", TRACER_PLAN)
    return problem, plan


@pytest.fixture
def tracer(synthetic_candidates: Path, tmp_path: Path) -> Tracer:
    problem, plan = _tracer_files(tmp_path)
    experiments = tmp_path / "experiments"
    done = _module(
        "run",
        "--problem",
        str(problem),
        "--selector",
        "plan",
        "--plan",
        str(plan),
        "--root",
        str(synthetic_candidates),
        "--experiments",
        str(experiments),
    )
    assert done.returncode == 0, done.stderr
    first = done.stdout.splitlines()[0]
    assert first.startswith("run_id: ")
    run_id = first.removeprefix("run_id: ")
    return Tracer(
        run_id=run_id,
        run_dir=experiments / run_id,
        experiments=experiments,
        root=synthetic_candidates,
        problem_path=problem,
        plan_path=plan,
        stdout=done.stdout,
    )


def test_the_fixture_ids_are_the_candidates_of_the_synthetic_table(
    synthetic_candidates: Path,
) -> None:
    table = pq.read_table(
        snapshot.candidates_parquet(snapshot.processed_dir(synthetic_candidates))
    ).to_pandas()
    found = {
        row["candidate_id"]: (row["canonical_psmiles"], row["tacticity"])
        for _, row in table.iterrows()
    }
    assert found[PE] == ("*CC*", "none")
    assert found[PP_ISO] == ("*CC(*)C", "isotactic")
    assert found[PP_ATA] == ("*CC(*)C", "atactic")
    assert found[PS] == ("*CC(*)c1ccccc1", "atactic")
    assert found[POM] == ("*CO*", "none")
    assert found[PVF] == ("*CC(*)F", "none")


def test_tracer_run_then_replay_through_the_module_entry_point(
    tracer: Tracer, tmp_path: Path
) -> None:
    assert ids.RUN_ID_PATTERN.fullmatch(tracer.run_id)
    assert sorted(p.name for p in tracer.run_dir.iterdir()) == [
        "ledger.jsonl",
        "meta.json",
        "results.csv",
        "run_summary.json",
        "usage.json",
    ]

    raw = (tracer.run_dir / ledger.LEDGER_NAME).read_bytes()
    assert raw.endswith(b"\n") and raw.count(b"\n") == 10 and b"\r" not in raw
    parsed = ledger.read(tracer.run_dir / ledger.LEDGER_NAME)
    header = json.loads(raw.split(b"\n")[0])
    assert set(header) == {"schema_version", "run_id", "problem", "provenance"}
    assert set(header["provenance"]) == {
        "seed",
        "snapshot",
        "registry_version",
        "selector",
        "code_git_sha",
    }
    assert [e.event for e in parsed.events] == TRACER_KINDS
    assert [e.seq for e in parsed.events] == list(range(1, 10))
    assert [e.iteration for e in parsed.events] == [0, 1, 1, 1, 1, 1, 1, 1, 0]

    evaluations = [e.payload for e in parsed.events if e.event == "evaluation"]
    assert [p["candidate_id"] for p in evaluations] == [PE, PP_ISO, PS]
    assert {p["beam"] for p in evaluations} == {"full"}
    for payload in evaluations:
        assert [r["property"] for r in payload["results"]] == PROPERTY_ORDER
    evals = sum(r["cost"]["evals"] for p in evaluations for r in p["results"])
    hours = sum(r["cost"]["cpu_hours"] for p in evaluations for r in p["results"])
    assert (evals, hours) == (3, 0.0)
    assert sum(p["cost"]["evals"] for p in evaluations) == 3
    assert sum(p["cost"]["cpu_hours"] for p in evaluations) == 0.0

    assert "evals: 3" in tracer.stdout.splitlines()
    assert "cpu_hours: 0.0" in tracer.stdout.splitlines()
    assert f"results_sha256: {TRACER_RESULTS_SHA256}" in tracer.stdout.splitlines()
    written = (tracer.run_dir / "results.csv").read_bytes()
    assert written == TRACER_RESULTS_CSV and len(written) == 301
    assert hashlib.sha256(written).hexdigest() == TRACER_RESULTS_SHA256

    before = {p.name: p.read_bytes() for p in tracer.run_dir.iterdir()}
    out = tmp_path / "replayed"
    replayed = _module(
        "replay",
        "--run",
        tracer.run_id,
        "--experiments",
        str(tracer.experiments),
        "--out",
        str(out),
    )
    assert replayed.returncode == 0, replayed.stderr
    assert f"results_sha256: {TRACER_RESULTS_SHA256}" in replayed.stdout.splitlines()
    assert (out / "results.csv").read_bytes() == TRACER_RESULTS_CSV
    assert {p.name: p.read_bytes() for p in tracer.run_dir.iterdir()} == before


def test_meta_is_validated_written_once_and_holds_no_key_value(
    tracer: Tracer, tmp_path: Path
) -> None:
    meta_path = tracer.run_dir / config.META_NAME
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    schema = json.loads((SCHEMAS / "run-meta.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(meta)
    assert set(meta) == META_KEYS
    metadata = pq.read_schema(
        snapshot.candidates_parquet(snapshot.processed_dir(tracer.root))
    ).metadata
    assert meta["schema_version"] == 1 and meta["run_id"] == tracer.run_id
    assert meta["prompt_versions"] == {} and meta["provider"] is None and meta["model"] is None
    assert meta["seed"] == 0
    assert meta["snapshot"] == "polyomics:general_polymers@041e5834"
    assert meta["registry_version"] == "v1"
    assert meta["snapshot_sha256"] == metadata[b"llm4pol.source_sha256"].decode("utf-8")
    assert re.fullmatch(r"[0-9a-f]{40}", meta["code_git_sha"])
    assert isinstance(meta["dirty"], bool) and isinstance(meta["provider_key_configured"], bool)
    assert meta["selector"].startswith("plan:sha256:")
    assert meta["problem"] == charter_problem(1, 3, 2)
    assert meta_path.read_bytes() == jsonio.pretty_bytes(meta)

    with pytest.raises(FileExistsError):
        config.write_meta(tracer.run_dir, meta)
    assert meta_path.read_bytes() == jsonio.pretty_bytes(meta)

    for broken in (
        {k: v for k, v in meta.items() if k != "seed"},
        {**meta, "extra": 1},
        {**meta, "dirty": "false"},
    ):
        target = tmp_path / f"broken-{len(broken)}-{broken.get('dirty')!s}"
        target.mkdir()
        with pytest.raises(config.MetaError):
            config.write_meta(target, broken)
        assert list(target.iterdir()) == []

    assert config.provider_key_configured({"OPENAI_API_KEY": "sk-not-a-real-value"}) is True
    assert config.provider_key_configured({}) is False
    built = config.build_meta(
        run_id=FIXED_RUN_ID,
        created_at="2026-01-01T00:00:00Z",
        problem=config.parse_problem_spec(charter_problem(1, 3, 2)),
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
        snapshot=meta["snapshot"],
        snapshot_sha256=meta["snapshot_sha256"],
        registry_version="v1",
        selector="plan:sha256:" + "0" * 64,
        environ={"GEMINI_API_KEY": "value-that-must-not-be-written"},
    )
    assert built["provider_key_configured"] is True
    assert "value-that-must-not-be-written" not in jsonio.pretty_bytes(built).decode("utf-8")


@pytest.mark.parametrize(
    "case",
    [
        "form_pareto",
        "no_schema_version",
        "other_snapshot",
        "plan_two_iterations",
        "plan_repeated_beam",
    ],
)
def test_run_refuses_an_invalid_problem_or_plan_with_exit_2_and_creates_nothing(
    case: str,
    synthetic_candidates: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    problem = charter_problem(1, 3, 2)
    plan = copy.deepcopy(TRACER_PLAN)
    if case == "form_pareto":
        problem["form"] = "pareto"
    elif case == "no_schema_version":
        del problem["schema_version"]
    elif case == "other_snapshot":
        problem["table"] = "polyomics:general_polymers@deadbeef"
    elif case == "plan_two_iterations":
        plan["iterations"].append({"iteration": 2, "beams": [{"beam": "full", "candidates": [PE]}]})
    else:
        plan["iterations"][0]["beams"][1]["beam"] = "full"
    experiments = tmp_path / "experiments"
    capsys.readouterr()
    code = cli.main(
        [
            "run",
            "--problem",
            str(_write_json(tmp_path / "problem.json", problem)),
            "--selector",
            "plan",
            "--plan",
            str(_write_json(tmp_path / "plan.json", plan)),
            "--root",
            str(synthetic_candidates),
            "--experiments",
            str(experiments),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == "ERROR: input refused\n"
    assert captured.err.startswith("detail:")
    assert not experiments.exists() or list(experiments.iterdir()) == []


@pytest.mark.parametrize("run_id", ["../escape", "20260101T000000Z-0000000", "nothing-here"])
def test_replay_refuses_a_malformed_or_unknown_run_id(
    run_id: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    assert cli.main(["replay", "--run", run_id, "--experiments", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == "ERROR: input refused\n" and captured.err.startswith("detail:")
    assert list(tmp_path.iterdir()) == []


def test_replay_returns_4_when_results_csv_holds_other_bytes(
    tracer: Tracer, capsys: pytest.CaptureFixture[str]
) -> None:
    (tracer.run_dir / "results.csv").write_bytes(TRACER_RESULTS_CSV + b"9,x\n")
    capsys.readouterr()
    args = ["replay", "--run", tracer.run_id, "--experiments", str(tracer.experiments)]
    assert cli.main(args) == 4
    assert capsys.readouterr().out.splitlines()[-1] == "ERROR: ledger integrity check failed"


def test_a_request_beyond_the_evals_limit_exits_3_and_records_the_refusal(
    synthetic_candidates: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plan = copy.deepcopy(TRACER_PLAN)
    plan["iterations"][0]["beams"] = [{"beam": "full", "candidates": [PE, PP_ISO]}]
    experiments = tmp_path / "experiments"
    capsys.readouterr()
    code = cli.main(
        [
            "run",
            "--problem",
            str(_write_json(tmp_path / "problem.json", charter_problem(1, 1, 1))),
            "--selector",
            "plan",
            "--plan",
            str(_write_json(tmp_path / "plan.json", plan)),
            "--root",
            str(synthetic_candidates),
            "--experiments",
            str(experiments),
        ]
    )
    captured = capsys.readouterr()
    assert code == 3
    assert captured.out.splitlines()[-1] == "BUDGET: evaluation budget exhausted"
    assert captured.err.startswith("detail:")
    (run_dir,) = list(experiments.iterdir())
    record = ledger.read(run_dir / ledger.LEDGER_NAME)
    assert [e.event for e in record.events][-3:] == ["selection", "evaluation", "run_closed"]
    assert record.closed and record.events[-1].payload["reason"] == "budget_exhausted"


def _library_run(root: Path, tmp_path: Path, plan: dict[str, Any] | None = None) -> Path:
    problem = config.parse_problem_spec(charter_problem(1, 3, 2))
    chosen = selector.PlanSelector.from_payload(plan or TRACER_PLAN, problem)
    run_dir = resume.open_run(
        tmp_path / "experiments",
        problem,
        chosen,
        root=root,
        now=FIXED_NOW,
        token=FIXED_TOKEN,
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
    )
    resume.drive(run_dir, root=root, selector=chosen, clock=constant_clock())
    return run_dir


def test_run_opened_carries_both_populations_sorted_and_without_ids(
    synthetic_candidates: Path, tmp_path: Path
) -> None:
    run_dir = _library_run(synthetic_candidates, tmp_path)
    assert run_dir.name == FIXED_RUN_ID
    raw = (run_dir / ledger.LEDGER_NAME).read_bytes()
    parsed = ledger.parse_bytes(raw)
    opened = parsed.events[0]
    assert opened.event == "run_opened"
    assert opened.payload["primary"] == "check_tc"
    assert [p["name"] for p in opened.payload["populations"]] == ["check_tc", "readme_triple"]
    for population in opened.payload["populations"]:
        assert population["objective"] == [0.155, 0.18, 0.2, 0.315]
        assert population["constraints"]["dielectric_const_dc"] == [
            2.6100000000000003,
            2.25,
            2.2,
            2.335,
        ]
        assert population["constraints"]["tg"] == [377.5, 400.0, 450.0, 262.5]
    assert not re.search(rb'"[0-9a-f]{16}"', raw.split(b"\n")[1])

    problem = config.parse_problem_spec(charter_problem(1, 3, 2))
    plan = selector.PlanSelector.from_payload(TRACER_PLAN, problem)
    assert parsed.header.selector == plan.identity
    assert re.fullmatch(r"plan:sha256:[0-9a-f]{64}", plan.identity)
    other = copy.deepcopy(TRACER_PLAN)
    other["iterations"][0]["beams"][0]["candidates"][2] = PP_ATA
    assert selector.PlanSelector.from_payload(other, problem).identity != plan.identity


def test_replay_loads_no_dataframe_library(synthetic_candidates: Path, tmp_path: Path) -> None:
    run_dir = _library_run(synthetic_candidates, tmp_path)
    script = (
        "import sys\n"
        "from llm4pol.run import __main__ as cli\n"
        f"code = cli.main(['replay', '--run', {run_dir.name!r}, '--experiments', "
        f"{str(run_dir.parent)!r}])\n"
        "print(sorted(m for m in ('numpy', 'pandas', 'pyarrow') if m in sys.modules))\n"
        "sys.exit(code)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        env=_child_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines()[-1] == "[]"
    assert f"results_sha256: {TRACER_RESULTS_SHA256}" in done.stdout.splitlines()


def test_reduce_is_a_pure_function_of_the_ledger(
    synthetic_candidates: Path, tmp_path: Path
) -> None:
    run_dir = _library_run(synthetic_candidates, tmp_path)
    parsed = ledger.read(run_dir / ledger.LEDGER_NAME)
    first = reduce.render_csv(reduce.reduce(parsed))
    assert first == reduce.render_csv(reduce.reduce(parsed)) == TRACER_RESULTS_CSV
    assert first.decode("utf-8").splitlines()[0].split(",") == list(reduce.COLUMNS)
    before = (run_dir / "results.csv").read_bytes()
    sums = reduce.write_outputs(run_dir)
    assert set(sums) == {"results.csv", "run_summary.json", "usage.json"}
    assert sums["results.csv"] == TRACER_RESULTS_SHA256
    assert (run_dir / "results.csv").read_bytes() == before  # compared, never rewritten
    (run_dir / "results.csv").write_bytes(before + b"9,x\n")
    with pytest.raises(ledger.LedgerIntegrityError):
        reduce.write_outputs(run_dir)
    assert (run_dir / "results.csv").read_bytes() == before + b"9,x\n"


def test_plan_selector_refuses_a_plan_that_its_schema_or_the_budget_refuses(
    tmp_path: Path,
) -> None:
    problem = config.parse_problem_spec(charter_problem(2, 3, 2))
    with pytest.raises(selector.PlanError):
        selector.PlanSelector.from_payload(TRACER_PLAN, problem)  # iteration 2 is missing
    gap = copy.deepcopy(TRACER_PLAN)
    gap["iterations"][0]["iteration"] = 2
    with pytest.raises(selector.PlanError):
        selector.PlanSelector.from_payload(gap, config.parse_problem_spec(charter_problem(1, 3, 2)))
    for bad in ("ABC", "full\n", ""):
        broken = copy.deepcopy(TRACER_PLAN)
        broken["iterations"][0]["beams"][0]["beam"] = bad
        with pytest.raises(selector.PlanError):
            selector.PlanSelector.from_payload(
                broken, config.parse_problem_spec(charter_problem(1, 3, 2))
            )
    repeated = tmp_path / "plan.json"
    repeated.write_text('{"schema_version": 1, "schema_version": 1, "iterations": []}', "utf-8")
    with pytest.raises(selector.PlanError):
        selector.PlanSelector.from_file(
            repeated, config.parse_problem_spec(charter_problem(1, 3, 2))
        )
    assert isinstance(
        selector.PlanSelector.from_payload(
            TRACER_PLAN, config.parse_problem_spec(charter_problem(1, 3, 2))
        ),
        selector.Selector,
    )


def test_the_new_schemas_are_valid_and_the_meta_problem_is_the_problem_spec_body() -> None:
    for name in ("selection-plan.json", "run-meta.json"):
        schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
    meta = json.loads((SCHEMAS / "run-meta.json").read_text(encoding="utf-8"))
    spec = json.loads((SCHEMAS / "problem-spec.json").read_text(encoding="utf-8"))
    body = {k: v for k, v in spec.items() if k not in ("$schema", "$id", "title", "description")}
    assert meta["$defs"]["problem"] == body
    assert set(meta["required"]) == META_KEYS
    assert "charter section 4 A-5" in meta["description"]
    refs = re.findall(r'"\$ref":\s*"([^"]*)"', json.dumps(meta))
    assert refs and all(ref.startswith("#/") for ref in refs)


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_the_static_prohibitions_of_the_plan_hold() -> None:
    modules = sorted(p.name for p in RUN_PACKAGE.glob("*.py"))
    assert modules == [
        "__init__.py",
        "__main__.py",
        "atomic.py",
        "config.py",
        "ids.py",
        "jsonio.py",
        "ledger.py",
        "lock.py",
        "population.py",
        "records.py",
        "redaction.py",
        "reduce.py",
        "resume.py",
        "selector.py",
        "strictschema.py",
        "summary.py",
    ]
    assert all(
        len(p.read_text(encoding="utf-8").splitlines()) <= 400 for p in RUN_PACKAGE.glob("*.py")
    )
    assert not (SRC / "llm4pol" / "loop").exists() and not (SRC / "llm4pol" / "llm").exists()

    reduce_imports = {name.split(".")[0] for name in _imports(RUN_PACKAGE / "reduce.py")}
    assert not reduce_imports & {"numpy", "pandas", "pyarrow"}
    init_imports = _imports(RUN_PACKAGE / "__init__.py")
    assert not any(name.endswith((".population", ".resume")) for name in init_imports)

    reduce_text = (RUN_PACKAGE / "reduce.py").read_text(encoding="utf-8")
    for literal in ("thermal_conductivity", "dielectric_const_dc", "tg", "2.6", "400"):
        assert not re.search(rf'["\'\s(]{re.escape(literal)}["\'\s),]', reduce_text), literal
    resume_text = (RUN_PACKAGE / "resume.py").read_text(encoding="utf-8")
    assert "JsonlCache()" in resume_text and "JsonlCache(path" not in resume_text
