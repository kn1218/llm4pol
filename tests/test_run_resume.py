"""Resume from the ledger alone (plan 04-05, task 2; RUN-02, RUN-03).

The ledger is the only state (ADR-0008 item 1): a run cut at any event boundary and resumed must
end in the bytes of the uninterrupted run, with no event recorded twice (charter section 13 M3
(1)). The reference campaign has 17 events after the header, so 18 boundaries are tested. Every
id and value is an invented fixture fact of ``conftest._CORE``; the run identity is fixed by
``run_support`` so the bytes are comparable.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any

import pytest

from conftest import make_synthetic_root
from llm4pol.data import load, snapshot
from llm4pol.evaluate import BatchEntry, EvalRequest, Evaluator, PropertyTable
from llm4pol.evaluate.backends.table import TableBackend
from llm4pol.evaluate.cache import key_for
from llm4pol.run import __main__ as cli
from llm4pol.run import config, jsonio, ledger, reduce, resume, selector
from run_support import (
    BUDGET_PLAN,
    BUDGET_RESULTS_CSV,
    BUDGET_RESULTS_SHA256,
    FIXED_CODE_SHA,
    PE,
    POM,
    PP_ATA,
    PP_ISO,
    PS,
    PVF,
    REFERENCE_KINDS,
    REFERENCE_PLAN,
    REFERENCE_RESULTS_CSV,
    REFERENCE_RESULTS_SHA256,
    REFERENCE_USAGE_JSON,
    UNKNOWN,
    budget_run,
    charter_problem,
    constant_clock,
    cut_run,
    reference_run,
    reference_summary_json,
)

FIXED_CODE = config.CodeIdentity(FIXED_CODE_SHA, False)
BOUNDARIES = range(len(REFERENCE_KINDS) + 1)  # 0 = the header alone, 17 = the complete ledger
PROPERTIES = ["thermal_conductivity", "dielectric_const_dc", "tg"]


@pytest.fixture(scope="module")
def table_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One synthetic repository root for the module: the runs only read its candidate table."""
    root = make_synthetic_root(tmp_path_factory.mktemp("resume-table"))
    load.load(root)
    return root


@pytest.fixture(scope="module")
def reference(table_root: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The run directory of the uninterrupted reference campaign."""
    return reference_run(table_root, tmp_path_factory.mktemp("reference") / "experiments")


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _reference_selector(plan: dict[str, Any] | None = None) -> selector.PlanSelector:
    problem = config.parse_problem_spec(charter_problem(2, 3, 2))
    return selector.PlanSelector.from_payload(plan or REFERENCE_PLAN, problem)


def _resume(
    run_dir: Path,
    root: Path,
    chosen: selector.PlanSelector | None = None,
    code: config.CodeIdentity = FIXED_CODE,
) -> resume.Outcome:
    return resume.resume(
        run_dir,
        root=root,
        selector=chosen if chosen is not None else _reference_selector(),
        code=code,
        clock=constant_clock(),
    )


def _bytes_of(run_dir: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(run_dir.iterdir())}


def _backend(root: Path) -> TableBackend:
    properties = PropertyTable.load()
    return TableBackend(
        snapshot.candidates_parquet(snapshot.processed_dir(root)), properties=properties
    )


def _rewrite_line(run_dir: Path, index: int, mutate: Any) -> None:
    """Replace line ``index`` of the ledger (0 = header) by ``mutate(record)``, canonical bytes."""
    path = run_dir / ledger.LEDGER_NAME
    lines = path.read_bytes().split(b"\n")[:-1]
    record = jsonio.loads_strict(lines[index].decode("utf-8"))
    mutate(record)
    lines[index] = jsonio.canonical_bytes(record).rstrip(b"\n")
    path.write_bytes(b"".join(line + b"\n" for line in lines))


def _cli_resume(run_dir: Path, root: Path, plan: Path) -> list[str]:
    return [
        "resume",
        "--run",
        run_dir.name,
        "--selector",
        "plan",
        "--plan",
        str(plan),
        "--root",
        str(root),
        "--experiments",
        str(run_dir.parent),
    ]


def test_reference_campaign_records_seventeen_events_and_five_evals(reference: Path) -> None:
    led = ledger.read(reference / ledger.LEDGER_NAME)
    assert [e.event for e in led.events] == REFERENCE_KINDS
    evaluations = [e.payload for e in led.events if e.event == "evaluation"]
    assert [p["candidate_id"] for p in evaluations] == [PE, PS, POM, PVF, UNKNOWN, PE, PP_ISO]
    assert [p["cost"]["evals"] for p in evaluations] == [1, 1, 1, 1, 0, 0, 1]
    assert sum(p["cost"]["evals"] for p in evaluations) == 5

    assert (
        all(r["cached"] for r in evaluations[5]["results"]) and len(evaluations[5]["results"]) == 3
    )
    assert not any(r["cached"] for p in evaluations[:5] for r in p["results"])

    def result(payload: dict[str, Any], key: str) -> dict[str, Any]:
        (found,) = [r for r in payload["results"] if r["property"] == key]
        return found

    pom, pvf, unknown = evaluations[2], evaluations[3], evaluations[4]
    assert (
        result(pom, "thermal_conductivity")["status"],
        result(pom, "thermal_conductivity")["reason"],
    ) == (
        "missing",
        "value_absent",
    )
    assert result(pom, "dielectric_const_dc")["status"] == "ok"  # POM is charged through it
    assert (result(pvf, "tg")["status"], result(pvf, "tg")["reason"]) == ("missing", "value_absent")
    assert [(r["status"], r.get("reason")) for r in unknown["results"]] == [
        ("missing", "candidate_unknown")
    ] * 3

    written = (reference / reduce.RESULTS_NAME).read_bytes()
    assert written == REFERENCE_RESULTS_CSV and len(written) == 453
    assert hashlib.sha256(written).hexdigest() == REFERENCE_RESULTS_SHA256


@pytest.mark.parametrize("k", BOUNDARIES)
def test_resume_at_every_event_boundary_is_byte_identical(
    k: int, table_root: Path, reference: Path, tmp_path: Path
) -> None:
    run_dir = cut_run(reference, tmp_path / "experiments", k)
    assert len((run_dir / ledger.LEDGER_NAME).read_bytes().split(b"\n")) == k + 2

    outcome = _resume(run_dir, table_root)

    assert (run_dir / ledger.LEDGER_NAME).read_bytes() == (
        reference / ledger.LEDGER_NAME
    ).read_bytes()
    assert (run_dir / reduce.RESULTS_NAME).read_bytes() == REFERENCE_RESULTS_CSV
    assert (run_dir / reduce.USAGE_NAME).read_bytes() == REFERENCE_USAGE_JSON
    assert (run_dir / reduce.SUMMARY_NAME).read_bytes() == reference_summary_json()
    resumed = ledger.read(run_dir / ledger.LEDGER_NAME)
    assert len(resumed.events) + 1 == 18
    keys = [ledger.event_key(event) for event in resumed.events]
    assert len(keys) == len(set(keys))
    assert (outcome.status, outcome.evals, outcome.appended) == ("completed", 5, 17 - k)
    assert outcome.results_sha256 == REFERENCE_RESULTS_SHA256


@pytest.mark.parametrize("k", BOUNDARIES)
def test_rebuilt_state_equals_the_recorded_spend(k: int, table_root: Path, reference: Path) -> None:
    lines = (reference / ledger.LEDGER_NAME).read_bytes().split(b"\n")[:-1]
    prefix = ledger.parse_bytes(b"".join(line + b"\n" for line in lines[: k + 1]))
    backend = _backend(table_root)

    state = resume.rebuild_state(prefix, backend)

    results = [r for e in prefix.events if e.event == "evaluation" for r in e.payload["results"]]
    assert state.meter.evals == sum(r["cost"]["evals"] for r in results)
    assert state.meter.cpu_hours == math.fsum(r["cost"]["cpu_hours"] for r in results)
    stored = [r for r in results if not r["cached"] and r["status"] in ("ok", "missing")]
    assert len(state.cache) == len({(r["candidate_id"], r["property"]) for r in stored})
    for item in stored:
        found = state.cache.get(key_for(item["candidate_id"], item["property"], backend))
        assert found is not None and found.cached is False and found.to_json() == item
    assert state.recorded == frozenset(ledger.event_key(e) for e in prefix.events)

    if k == 12:  # the selection of iteration 2 is recorded, its evaluations are not
        assert state.meter.evals == 4
        evaluator = Evaluator(
            backend,
            PropertyTable.load(),
            cache=state.cache,
            meter=state.meter,
            evals_limit=12,
        )
        answer = evaluator.evaluate(EvalRequest("r", 2, (BatchEntry(PE, tuple(PROPERTIES)),)))
        assert all(r.cached for r in answer.results) and answer.cost.evals == 0


def test_resume_appends_nothing_to_a_closed_run(
    table_root: Path, reference: Path, tmp_path: Path
) -> None:
    run_dir = tmp_path / "experiments" / reference.name
    shutil.copytree(reference, run_dir)
    before = _bytes_of(run_dir)

    outcome = _resume(run_dir, table_root)

    assert _bytes_of(run_dir) == before
    assert (outcome.status, outcome.appended, outcome.evals) == ("completed", 0, 5)
    (run_dir / reduce.RESULTS_NAME).write_bytes(REFERENCE_RESULTS_CSV + b"9,x\n")
    with pytest.raises(ledger.LedgerIntegrityError):
        _resume(run_dir, table_root)
    assert (run_dir / reduce.RESULTS_NAME).read_bytes() == REFERENCE_RESULTS_CSV + b"9,x\n"


def test_resume_refuses_a_torn_final_line(
    table_root: Path,
    reference: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_dir = cut_run(reference, tmp_path / "experiments", 8)
    path = run_dir / ledger.LEDGER_NAME
    whole = (reference / ledger.LEDGER_NAME).read_bytes().split(b"\n")
    torn = path.read_bytes() + whole[9][:20]  # the middle of event 9
    path.write_bytes(torn)
    plan = _write_json(tmp_path / "plan.json", REFERENCE_PLAN)
    capsys.readouterr()

    code = cli.main(_cli_resume(run_dir, table_root, plan))

    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == "ERROR: input refused\n"
    assert f"byte offset {len(torn) - 20 - 1}" in captured.err
    assert "20 trailing bytes" in captured.err
    assert path.read_bytes() == torn


def _header_defect(name: str) -> tuple[Any, config.CodeIdentity, tuple[str, ...]]:
    def snapshot_id(record: dict[str, Any]) -> None:
        record["provenance"]["snapshot"] = "polyomics:general_polymers@ffffffff"

    def registry(record: dict[str, Any]) -> None:
        record["provenance"]["registry_version"] = "v0"

    def nothing(record: dict[str, Any]) -> None:
        pass

    return {
        "snapshot": (
            snapshot_id,
            FIXED_CODE,
            ("provenance.snapshot", "ffffffff", "polyomics:general_polymers@041e5834"),
        ),
        "registry": (registry, FIXED_CODE, ("provenance.registry_version", "v0", "v1")),
        "code": (
            nothing,
            config.CodeIdentity("1" * 40, False),
            ("provenance.code_git_sha", "1" * 40, FIXED_CODE_SHA),
        ),
    }[name]


@pytest.mark.parametrize("name", ["snapshot", "registry", "code"])
def test_resume_refuses_a_different_snapshot_registry_version_or_code(
    name: str,
    table_root: Path,
    reference: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mutate, code, fragments = _header_defect(name)
    run_dir = cut_run(reference, tmp_path / "experiments", 5)
    _rewrite_line(run_dir, 0, mutate)
    before = _bytes_of(run_dir)

    with pytest.raises(resume.RunRefused) as refused:
        _resume(run_dir, table_root, code=code)
    for fragment in fragments:
        assert fragment in str(refused.value)
    assert _bytes_of(run_dir) == before

    monkeypatch.setattr(cli, "code_identity", lambda: code)
    plan = _write_json(tmp_path / "plan.json", REFERENCE_PLAN)
    capsys.readouterr()
    assert cli.main(_cli_resume(run_dir, table_root, plan)) == 4
    assert capsys.readouterr().out == "ERROR: ledger integrity check failed\n"
    assert _bytes_of(run_dir) == before


def test_resume_refuses_another_plan_or_a_doctored_selection(
    table_root: Path,
    reference: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_dir = cut_run(reference, tmp_path / "experiments", 3)  # through the first selection
    before = _bytes_of(run_dir)
    other_plan = copy.deepcopy(REFERENCE_PLAN)
    other_plan["iterations"][1]["beams"][0]["candidates"] = [PE, PP_ATA]
    other = _reference_selector(other_plan)
    assert other.identity != _reference_selector().identity

    with pytest.raises(resume.RunRefused, match="provenance.selector"):
        _resume(run_dir, table_root, other)
    assert _bytes_of(run_dir) == before

    def doctor(record: dict[str, Any]) -> None:
        record["payload"]["candidates"] = [PE, PP_ATA]

    _rewrite_line(run_dir, 3, doctor)
    before = _bytes_of(run_dir)
    assert ledger.read(run_dir / ledger.LEDGER_NAME).events[2].payload["candidates"] == [PE, PP_ATA]
    with pytest.raises(resume.SequenceMismatch, match="iteration 1"):
        _resume(run_dir, table_root)
    assert _bytes_of(run_dir) == before

    monkeypatch.setattr(cli, "code_identity", lambda: FIXED_CODE)
    plan = _write_json(tmp_path / "plan.json", REFERENCE_PLAN)
    capsys.readouterr()
    assert cli.main(_cli_resume(run_dir, table_root, plan)) == 4
    assert "ERROR: ledger integrity check failed" in capsys.readouterr().out
    assert _bytes_of(run_dir) == before


def test_budget_refusal_closes_the_run_and_exits_3(
    table_root: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiments = tmp_path / "experiments"
    problem = _write_json(tmp_path / "problem.json", charter_problem(1, 1, 2))
    plan = _write_json(tmp_path / "plan.json", BUDGET_PLAN)
    capsys.readouterr()
    code = cli.main(
        [
            "run",
            "--problem",
            str(problem),
            "--selector",
            "plan",
            "--plan",
            str(plan),
            "--root",
            str(table_root),
            "--experiments",
            str(experiments),
        ]
    )
    captured = capsys.readouterr()
    assert code == 3
    assert captured.out.splitlines()[-1] == "BUDGET: evaluation budget exhausted"
    assert captured.err.startswith("detail:")
    (run_dir,) = list(experiments.iterdir())
    led = ledger.read(run_dir / ledger.LEDGER_NAME)
    assert [e.event for e in led.events] == [
        "run_opened",
        "iteration_opened",
        "selection",
        "evaluation",
        "evaluation",
        "run_closed",
    ]
    assert led.events[-1].payload == {
        "reason": "budget_exhausted",
        "requested": 1,
        "remaining": 0,
        "limit": 2,
    }
    written = (run_dir / reduce.RESULTS_NAME).read_bytes()
    assert written == BUDGET_RESULTS_CSV and len(written) == 244
    assert hashlib.sha256(written).hexdigest() == BUDGET_RESULTS_SHA256

    before = _bytes_of(run_dir)
    resumed = cli.main(_cli_resume(run_dir, table_root, plan))
    assert resumed == 0 and _bytes_of(run_dir) == before

    uninterrupted = budget_run(table_root, tmp_path / "fixed")
    cut = cut_run(uninterrupted, tmp_path / "cut", 4)  # after the first evaluation
    assert len(ledger.read(cut / ledger.LEDGER_NAME).events) == 4
    spec = config.parse_problem_spec(charter_problem(1, 1, 2))
    outcome = resume.resume(
        cut,
        root=table_root,
        selector=selector.PlanSelector.from_payload(BUDGET_PLAN, spec),
        code=FIXED_CODE,
        clock=constant_clock(),
    )
    assert outcome.status == "budget_exhausted" and outcome.appended == 2
    assert (cut / ledger.LEDGER_NAME).read_bytes() == (
        uninterrupted / ledger.LEDGER_NAME
    ).read_bytes()
    assert (cut / reduce.RESULTS_NAME).read_bytes() == BUDGET_RESULTS_CSV


def test_cli_resume_reads_the_problem_from_the_header(
    table_root: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    experiments = tmp_path / "experiments"
    problem = _write_json(tmp_path / "problem.json", charter_problem(2, 3, 2))
    plan = _write_json(tmp_path / "plan.json", REFERENCE_PLAN)
    with pytest.raises(SystemExit) as usage:
        cli.main(["resume", "--run", "20260101T000000Z-00000000", "--problem", str(problem)])
    assert usage.value.code == 2

    capsys.readouterr()
    args = [
        "run",
        "--problem",
        str(problem),
        "--selector",
        "plan",
        "--plan",
        str(plan),
        "--root",
        str(table_root),
        "--experiments",
        str(experiments),
    ]
    assert cli.main(args) == 0
    run_id = capsys.readouterr().out.splitlines()[0].removeprefix("run_id: ")
    cut = cut_run(experiments / run_id, tmp_path / "second", 7)

    assert cli.main(_cli_resume(cut, table_root, plan)) == 0
    resumed = ledger.read(cut / ledger.LEDGER_NAME)
    assert [e.event for e in resumed.events] == REFERENCE_KINDS
    keys = [ledger.event_key(e) for e in resumed.events]
    assert len(keys) == len(set(keys))
    assert (cut / reduce.RESULTS_NAME).read_bytes() == REFERENCE_RESULTS_CSV


def test_the_prohibitions_of_the_plan_hold_in_the_source() -> None:
    """No path shortens or rewrites a ledger; ``resume`` has no argument that relaxes a check."""
    run_package = Path(resume.__file__).parent
    ledger_text = (run_package / "ledger.py").read_text(encoding="utf-8")
    assert sorted(set(re.findall(r'_write\(path, "(\w+)"', ledger_text))) == ["ab", "xb"]
    # `atomic.py` alone may replace and unlink, and only its own temporary file onto an absent
    # target (WR-03); the ledger modules never call `write_new`, so no ledger byte goes through it
    for name in ("ledger.py", "records.py", "lock.py"):
        assert "write_new" not in (run_package / name).read_text(encoding="utf-8"), name
    for module in run_package.glob("*.py"):
        if module.name == "atomic.py":
            continue
        text = module.read_text(encoding="utf-8")
        for forbidden in (".truncate(", ".unlink(", "os.remove(", "os.replace(", '"r+b"', '"wb"'):
            assert forbidden not in text, (module.name, forbidden)
    assert list(inspect.signature(resume.resume).parameters) == [
        "run_dir",
        "root",
        "selector",
        "code",
        "clock",
    ]
    resume_text = (run_package / "resume.py").read_text(encoding="utf-8")
    assert "JsonlCache()" in resume_text and "JsonlCache(path" not in resume_text
