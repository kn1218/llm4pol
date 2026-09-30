"""``run_summary.json``, the full ``replay`` and the pinned fixture ledger (plan 04-08).

Guards RUN-04 (charter section 13 M3 exit criterion (2)), ADR-0008 items 6 and 7 and its second
guard, ADR-0007 and D-39. The expected summary is typed from the hand table of the plan objective
(``run_support.reference_summary``), not copied from an output, and the four pinned sha256 values
are two hand-derived (``results.csv`` and ``usage.json``) and two recorded when the fixture was
generated (the ledger and the rendered summary). Every id and value is an invented fixture fact.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from conftest import REPO_ROOT, UNKNOWN_CANDIDATE_ID, make_synthetic_root
from history_secret_scan import PATTERNS, _matches
from llm4pol.data import load, snapshot
from llm4pol.evaluate import PropertyTable
from llm4pol.evaluate.backends.table import TableBackend
from llm4pol.run import __main__ as cli
from llm4pol.run import jsonio, ledger, reduce
from run_support import (
    FIXED_CODE_SHA,
    FIXED_RUN_ID,
    PE,
    POM,
    PP_ATA,
    PP_ISO,
    PS,
    PVF,
    REFERENCE_LEDGER_SHA256,
    REFERENCE_LEDGER_SIZE,
    REFERENCE_RESULTS_CSV,
    REFERENCE_RESULTS_SHA256,
    REFERENCE_SUMMARY_SHA256,
    REFERENCE_SUMMARY_SIZE,
    REFERENCE_USAGE_JSON,
    REFERENCE_USAGE_SHA256,
    TRACER_PLAN,
    budget_run,
    charter_problem,
    cut_run,
    fixed_run,
    reference_run,
    reference_summary,
    reference_summary_json,
)

SCHEMA_PATH = REPO_ROOT / "protocol" / "schemas" / "run-summary.json"
EXAMPLE_PATH = REPO_ROOT / "protocol" / "examples" / "run-summary.example.json"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "run" / "reference-ledger.jsonl"
SRC = REPO_ROOT / "src"
RUN_PACKAGE = SRC / "llm4pol" / "run"

# The hand-derived pair of the third truth, typed in the plan objective.
RESULTS_SHA256 = "0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6"
USAGE_SHA256 = "bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa"
REDUCED_NAMES = (reduce.RESULTS_NAME, reduce.USAGE_NAME, reduce.SUMMARY_NAME)
FIVE_FILES = sorted(["meta.json", "ledger.jsonl", "usage.json", "results.csv", "run_summary.json"])
SUMMARY_KEYS = {
    "schema_version",
    "run_id",
    "status",
    "completed_iterations",
    "primary_population",
    "trends",
    "ledger_sha256",
    "results_sha256",
}


@pytest.fixture(scope="module")
def table_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = make_synthetic_root(tmp_path_factory.mktemp("replay-table"))
    load.load(root)
    return root


@pytest.fixture(scope="module")
def reference(table_root: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    return reference_run(table_root, tmp_path_factory.mktemp("replay-reference") / "experiments")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _summary_validator() -> Any:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _replay(
    capsys: pytest.CaptureFixture[str], run_dir: Path, *extra: str
) -> tuple[int, list[str]]:
    capsys.readouterr()
    code = cli.main(["replay", "--run", run_dir.name, "--experiments", str(run_dir.parent), *extra])
    return code, capsys.readouterr().out.splitlines()


def _copy(source: Path, experiments: Path) -> Path:
    target = experiments / source.name
    shutil.copytree(source, target)
    return target


def _bytes_of(directory: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir())}


def test_run_summary_holds_what_adr_0008_names(reference: Path) -> None:
    raw = (reference / reduce.SUMMARY_NAME).read_bytes()
    parsed = json.loads(raw)
    assert list(_summary_validator().iter_errors(parsed)) == []
    assert set(parsed) == SUMMARY_KEYS
    assert parsed == reference_summary()
    assert [(t["beam"], t["population"]) for t in parsed["trends"]] == [
        (beam, population)
        for beam in ("full", "random", "chem")
        for population in ("check_tc", "readme_triple")
    ]
    assert all(
        set(point) == {"iteration", "value"}
        for trend in parsed["trends"]
        for series in (trend["percentile_trend"], trend["count_trend"])
        for point in series
    )
    chem = [t for t in parsed["trends"] if t["beam"] == "chem"]
    assert [t["percentile_trend"] for t in chem] == [[{"iteration": 2, "value": None}]] * 2
    assert [t["count_trend"] for t in chem] == [[{"iteration": 2, "value": 0}]] * 2
    assert parsed["ledger_sha256"] == _sha((reference / ledger.LEDGER_NAME).read_bytes())
    assert parsed["results_sha256"] == RESULTS_SHA256
    assert raw == jsonio.pretty_bytes(parsed) == reference_summary_json()


def test_summary_schema_pins_names_and_types(
    reference: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = _summary_validator()
    good = reference_summary()
    assert list(validator.iter_errors(good)) == []

    def refused(mapping: dict[str, Any]) -> bool:
        return any(True for _ in validator.iter_errors(mapping))

    def with_point(trends_key: str, point: object) -> dict[str, Any]:
        trends = json.loads(json.dumps(good["trends"]))
        trends[0][trends_key] = [point]
        return good | {"trends": trends}

    refusals = {
        "a key removed": {k: v for k, v in good.items() if k != "status"},
        "an extra key": good | {"created_at": "2026-01-01T00:00:00Z"},
        "status done": good | {"status": "done"},
        "completed_iterations as a float": good | {"completed_iterations": 1.5},
        "completed_iterations negative": good | {"completed_iterations": -1},
        "a trend point without iteration": with_point("percentile_trend", {"value": 1.0}),
        "iteration 0": with_point("count_trend", {"iteration": 0, "value": 1}),
        "a count as a float": with_point("count_trend", {"iteration": 1, "value": 2.5}),
        "a negative count": with_point("count_trend", {"iteration": 1, "value": -1}),
        "a percentile as a string": with_point("percentile_trend", {"iteration": 1, "value": "x"}),
        "a 63-character hash": good | {"ledger_sha256": "a" * 63},
        "an upper-case hash": good | {"results_sha256": "A" * 64},
        "schema_version 2": good | {"schema_version": 2},
        "an empty primary population": good | {"primary_population": ""},
        "a malformed run id": good | {"run_id": "20260101T000000Z-0000000"},
    }
    for name, mapping in refusals.items():
        assert refused(mapping), name

    # `write_outputs` applies the schema before a file is opened
    target = cut_run(reference, tmp_path / "experiments", 17)
    monkeypatch.setattr(reduce, "summary_of", lambda *_a, **_k: good | {"status": "done"})
    with pytest.raises(reduce.ReduceError, match="summary"):
        reduce.write_outputs(target)
    assert sorted(p.name for p in target.iterdir()) == ["ledger.jsonl", "meta.json"]


def test_a_closed_run_directory_holds_five_files(
    reference: Path, table_root: Path, tmp_path: Path
) -> None:
    assert sorted(p.name for p in reference.iterdir()) == FIVE_FILES
    budget = budget_run(table_root, tmp_path / "experiments")
    assert sorted(p.name for p in budget.iterdir()) == FIVE_FILES
    summary = json.loads((budget / reduce.SUMMARY_NAME).read_text(encoding="utf-8"))
    assert list(_summary_validator().iter_errors(summary)) == []
    assert (summary["status"], summary["completed_iterations"]) == ("budget_exhausted", 0)
    assert summary["primary_population"] == "check_tc"
    assert [(t["beam"], t["population"]) for t in summary["trends"]] == [
        ("full", "check_tc"),
        ("full", "readme_triple"),
    ]


def test_replay_regenerates_the_three_files_byte_identical(
    reference: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"
    before = _bytes_of(reference)
    code, lines = _replay(capsys, reference, "--out", str(out))
    assert code == 0
    assert sorted(p.name for p in out.iterdir()) == sorted(REDUCED_NAMES)
    for name in REDUCED_NAMES:
        assert (out / name).read_bytes() == (reference / name).read_bytes(), name
    assert _bytes_of(reference) == before
    ledger_bytes = (reference / ledger.LEDGER_NAME).read_bytes()
    assert lines[-3:-1] == [
        f"ledger_sha256: {_sha(ledger_bytes)}",
        f"results_sha256: {RESULTS_SHA256}",
    ]
    expected = _sha(b"".join((reference / name).read_bytes() for name in REDUCED_NAMES))
    assert lines[-1] == f"result_sha256: {expected}"
    assert (
        reduce.result_sha256(
            (reference / reduce.RESULTS_NAME).read_bytes(),
            (reference / reduce.USAGE_NAME).read_bytes(),
            (reference / reduce.SUMMARY_NAME).read_bytes(),
        )
        == expected
    )


@pytest.mark.parametrize("name", REDUCED_NAMES)
def test_replay_refuses_a_file_that_differs(
    name: str, reference: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = _copy(reference, tmp_path / "experiments")
    data = (run_dir / name).read_bytes()
    (run_dir / name).write_bytes(bytes([data[0] ^ 1]) + data[1:])
    before = _bytes_of(run_dir)
    out = tmp_path / "out"

    code, lines = _replay(capsys, run_dir, "--out", str(out))

    assert code == 4
    assert lines[-1] == "ERROR: ledger integrity check failed"
    assert not any(line.startswith("result_sha256:") for line in lines)
    assert _bytes_of(run_dir) == before
    assert not out.exists()


def test_replay_writes_what_is_absent_on_a_closed_run_and_nothing_into_an_open_one(
    reference: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    closed = cut_run(reference, tmp_path / "closed", 17)
    code, lines = _replay(capsys, closed)
    assert code == 0 and lines[-1].startswith("result_sha256: ")
    for name in REDUCED_NAMES:
        assert (closed / name).read_bytes() == (reference / name).read_bytes(), name

    partial = cut_run(reference, tmp_path / "partial", 17)
    (partial / reduce.USAGE_NAME).write_bytes((reference / reduce.USAGE_NAME).read_bytes())
    code, _ = _replay(capsys, partial)
    assert code == 0
    assert sorted(p.name for p in partial.iterdir()) == FIVE_FILES

    open_run = cut_run(reference, tmp_path / "open", 9)
    before = _bytes_of(open_run)
    code, lines = _replay(capsys, open_run)
    assert code == 0 and lines[-1].startswith("result_sha256: ")
    assert _bytes_of(open_run) == before

    out = tmp_path / "open-out"
    code, _ = _replay(capsys, open_run, "--out", str(out))
    assert code == 0 and _bytes_of(open_run) == before
    assert sorted(p.name for p in out.iterdir()) == sorted(REDUCED_NAMES)
    summary = json.loads((out / reduce.SUMMARY_NAME).read_text(encoding="utf-8"))
    assert list(_summary_validator().iter_errors(summary)) == []
    assert (summary["status"], summary["completed_iterations"]) == ("open", 0)


def test_committed_fixture_ledger_reduces_to_the_pinned_bytes() -> None:
    raw = FIXTURE_PATH.read_bytes()
    assert (len(raw), _sha(raw)) == (REFERENCE_LEDGER_SIZE, REFERENCE_LEDGER_SHA256)

    outputs = reduce.render_outputs(raw)

    assert outputs.results == REFERENCE_RESULTS_CSV
    assert _sha(outputs.results) == RESULTS_SHA256 == REFERENCE_RESULTS_SHA256
    assert outputs.usage == REFERENCE_USAGE_JSON
    assert _sha(outputs.usage) == USAGE_SHA256 == REFERENCE_USAGE_SHA256
    assert (len(outputs.summary), _sha(outputs.summary)) == (
        REFERENCE_SUMMARY_SIZE,
        REFERENCE_SUMMARY_SHA256,
    )
    assert outputs.summary == reference_summary_json()
    assert outputs.summary == EXAMPLE_PATH.read_bytes()
    assert (outputs.ledger_sha256, outputs.results_sha256) == (
        REFERENCE_LEDGER_SHA256,
        RESULTS_SHA256,
    )
    assert outputs.closed is True


def test_committed_fixture_ledger_equals_a_fresh_reference_run(reference: Path) -> None:
    assert (reference / ledger.LEDGER_NAME).read_bytes() == FIXTURE_PATH.read_bytes()


def test_committed_fixture_holds_fixture_ids_and_invented_values_only(table_root: Path) -> None:
    raw = FIXTURE_PATH.read_bytes()
    assert raw.count(b"\n") == 18 and b"\r" not in raw
    allowed = {PE, PP_ISO, PP_ATA, PS, POM, PVF, UNKNOWN_CANDIDATE_ID}
    tokens = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])", raw.decode("utf-8")))
    assert tokens and tokens <= allowed

    parsed = ledger.parse_bytes(raw)
    assert parsed.header.code_git_sha == FIXED_CODE_SHA == "0" * 40
    assert parsed.header.run_id == FIXED_RUN_ID

    backend = TableBackend(
        snapshot.candidates_parquet(snapshot.processed_dir(table_root)),
        properties=PropertyTable.load(),
    )
    seen = 0
    for event in parsed.events:
        if event.event != "evaluation":
            continue
        for result in event.payload["results"]:
            served = backend.lookup(result["candidate_id"], result["property"])
            assert result["status"] == served.status
            assert result["value"] == (served.value if served.status == "ok" else None)
            seen += 1
    assert seen == 21


def test_replay_and_usage_need_no_table_and_no_dataframe_library(tmp_path: Path) -> None:
    experiments = tmp_path / "experiments"
    run_dir = experiments / FIXED_RUN_ID
    run_dir.mkdir(parents=True)
    (run_dir / ledger.LEDGER_NAME).write_bytes(FIXTURE_PATH.read_bytes())
    work = tmp_path / "empty"
    work.mkdir()
    script = (
        "import json, sys\n"
        "from llm4pol.run import __main__ as cli\n"
        f"common = ['--run', {FIXED_RUN_ID!r}, '--experiments', {str(experiments)!r}]\n"
        "codes = [cli.main(['replay', *common]), cli.main(['usage', *common])]\n"
        "loaded = sorted(m for m in ('numpy', 'pandas', 'pyarrow') if m in sys.modules)\n"
        "print(json.dumps({'codes': codes, 'loaded': loaded}))\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", script],
        cwd=work,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout.splitlines()[-1]) == {"codes": [0, 0], "loaded": []}
    assert sorted(p.name for p in run_dir.iterdir()) == sorted([ledger.LEDGER_NAME, *REDUCED_NAMES])
    assert list(work.iterdir()) == []


def test_no_written_file_matches_a_scanner_class(
    reference: Path, table_root: Path, tmp_path: Path
) -> None:
    tracer = fixed_run(table_root, tmp_path / "experiments", TRACER_PLAN, charter_problem(1, 3, 2))
    checked = 0
    for run_dir in (reference, tracer):
        assert sorted(p.name for p in run_dir.iterdir()) == FIVE_FILES
        for path in run_dir.iterdir():
            text = path.read_text(encoding="utf-8")
            for pattern in PATTERNS:
                assert list(_matches(pattern, text)) == [], f"{pattern.name} in {path.name}"
            checked += 1
    assert checked == 10


def _imported(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names.add(module)
            names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


def test_reduced_modules_import_no_dataframe_library() -> None:
    for name in ("reduce.py", "ledger.py", "jsonio.py", "summary.py"):
        roots = {n.split(".")[0] for n in _imported(RUN_PACKAGE / name)}
        assert not roots & {"numpy", "pandas", "pyarrow"}, name
    init = _imported(RUN_PACKAGE / "__init__.py")
    assert not any(n.endswith((".population", ".resume")) for n in init)
