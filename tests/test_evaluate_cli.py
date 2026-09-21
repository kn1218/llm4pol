"""The Phase 3 tracer: request JSON -> schema -> Evaluator -> TableBackend -> response JSON.

One path through every layer of ``llm4pol.evaluate`` on the 9-candidate
synthetic table (CONTEXT D-01, D-02, D-04, D-07; RESEARCH F-40), driven
through ``python -m llm4pol.evaluate`` in-process (F-45). Every id and value
below is an invented fixture fact of ``conftest.SYNTHETIC_ROWS``; the ids are
pinned to ``identity.candidate_id`` once so they are never copied blindly.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import jsonschema
import pandas as pd
import pytest

from conftest import REPO_ROOT, SYNTHETIC_EXAMPLE_REQUEST, UNKNOWN_CANDIDATE_ID
from llm4pol.data import identity, snapshot
from llm4pol.evaluate import __main__ as cli

RESPONSE_SCHEMA = REPO_ROOT / "protocol" / "schemas" / "eval-response.json"

EXPECTED_STATUSES = ["ok", "ok", "ok", "missing", "missing", "ok", "missing", "unsupported", "ok"]
EXPECTED_EVALS = [1, 0, 0, 0, 0, 1, 0, 0, 1]


def _write_request(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "request.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _flattened_batch(payload: dict[str, object]) -> list[tuple[str, str]]:
    batch: Any = payload["batch"]
    return [(entry["candidate_id"], key) for entry in batch for key in entry["properties"]]


def test_tracer_request_json_to_response_json_on_the_synthetic_root(
    synthetic_candidates: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The F-40 ids are the identity function's output, and the unknown id is
    # genuinely absent from the fixture's candidate frame.
    assert identity.candidate_id("*CC*", "none") == "7ec8cb49ff317efc"
    frame = pd.read_parquet(
        snapshot.candidates_parquet(snapshot.processed_dir(synthetic_candidates))
    ).set_index("candidate_id")
    assert UNKNOWN_CANDIDATE_ID not in frame.index

    request_path = _write_request(tmp_path, SYNTHETIC_EXAMPLE_REQUEST)
    capsys.readouterr()
    assert cli.main(["--request", str(request_path), "--root", str(synthetic_candidates)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""

    payload = json.loads(captured.out)
    schema = json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(payload)

    assert payload["run_id"] == "example-run"
    assert payload["iteration"] == 0
    results = payload["results"]
    assert len(results) == 9
    assert [r["status"] for r in results] == EXPECTED_STATUSES
    assert [(r["candidate_id"], r["property"]) for r in results] == _flattened_batch(
        SYNTHETIC_EXAMPLE_REQUEST
    )

    missing = [r for r in results if r["status"] == "missing"]
    assert [r["reason"] for r in missing] == ["value_absent", "value_absent", "candidate_unknown"]
    for r in results:
        if r["status"] in ("ok", "unsupported"):
            assert "reason" not in r, r

    assert [r["cost"]["evals"] for r in results] == EXPECTED_EVALS
    assert payload["cost"] == {"evals": 3, "cpu_hours": 0.0}

    for r in results:
        assert r["backend"] == "table"
        assert r["source"] == "polyomics:general_polymers@041e5834"
        assert r["provenance_tier"] == "md_simulated"
        assert r["cached"] is False

    first = results[0]
    assert math.isclose(first["value"], 0.32, rel_tol=0.0, abs_tol=1e-9)
    assert first["unit"] == "W/(m*K)"
    assert first["n_replicates"] == 3
    assert math.isclose(first["spread"], 0.02, rel_tol=0.0, abs_tol=1e-6)

    sixth = results[5]
    assert (sixth["candidate_id"], sixth["property"]) == (
        "d24805b4ce4c381c",
        "thermal_conductivity",
    )
    assert sixth["n_replicates"] == 1
    assert sixth["spread"] is None

    ninth = results[8]
    assert ninth["candidate_id"] == "b3a635a55e1a6645"
    assert ninth["n_replicates"] == 2
    assert math.isclose(ninth["spread"], 0.007071, rel_tol=0.0, abs_tol=1e-6)


_MALFORMED_ID: dict[str, object] = {
    "run_id": "example-run",
    "iteration": 0,
    "batch": [{"candidate_id": "ZZZZ", "properties": ["thermal_conductivity"]}],
}
_DUPLICATE_PROPERTIES: dict[str, object] = {
    "run_id": "example-run",
    "iteration": 0,
    "batch": [
        {
            "candidate_id": "7ec8cb49ff317efc",
            "properties": ["thermal_conductivity", "thermal_conductivity"],
        }
    ],
}


@pytest.mark.parametrize(
    "payload",
    [_MALFORMED_ID, _DUPLICATE_PROPERTIES],
    ids=["malformed-candidate-id", "duplicate-properties"],
)
def test_cli_exit_2_on_a_request_schema_failure(
    synthetic_candidates: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: dict[str, object],
) -> None:
    request_path = _write_request(tmp_path, payload)
    capsys.readouterr()
    assert cli.main(["--request", str(request_path), "--root", str(synthetic_candidates)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("ERROR:")


# --------------------------------------------------------------------------
# Exit codes 0 / 2 / 3 and --cache / --evals-limit (D-07, R-4; RESEARCH Code Example 5)
# --------------------------------------------------------------------------

_TWO_OK: dict[str, object] = {
    "run_id": "two-ok",
    "iteration": 0,
    "batch": [
        {"candidate_id": "7ec8cb49ff317efc", "properties": ["thermal_conductivity"]},
        {"candidate_id": "81b997b85ccd2069", "properties": ["thermal_conductivity"]},
        {"candidate_id": "b3a635a55e1a6645", "properties": ["tg"]},
    ],
}


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    capsys.readouterr()
    code = cli.main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _line_count(path: Path) -> int:
    return path.read_text(encoding="utf-8").count("\n")


@pytest.mark.parametrize(
    "case",
    [
        "absent-request",
        "bad-json",
        "schema-failure",
        "cache-is-a-directory",
        "malformed-cache-line",
    ],
)
def test_cli_exit_2_on_missing_request_bad_json_and_schema_failure(
    synthetic_candidates: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], case: str
) -> None:
    request_path = _write_request(tmp_path, SYNTHETIC_EXAMPLE_REQUEST)
    args = ["--root", str(synthetic_candidates)]
    if case == "absent-request":
        args += ["--request", str(tmp_path / "absent.json")]
    elif case == "bad-json":
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        args += ["--request", str(bad)]
    elif case == "schema-failure":
        args += ["--request", str(_write_request(tmp_path, _DUPLICATE_PROPERTIES))]
    elif case == "cache-is-a-directory":
        (tmp_path / "cache-dir").mkdir()
        args += ["--request", str(request_path), "--cache", str(tmp_path / "cache-dir")]
    else:
        cache = tmp_path / "cache.jsonl"
        # A first run persists the cache, then a malformed line is appended by hand.
        assert _run([*args, "--request", str(request_path), "--cache", str(cache)], capsys)[0] == 0
        with cache.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write("{not json\n")
        args += ["--request", str(request_path), "--cache", str(cache)]

    code, out, err = _run(args, capsys)
    assert code == 2
    assert out == ""
    assert err.startswith("ERROR:")


def test_cli_exit_3_when_evals_limit_would_be_exceeded_and_nothing_is_committed(
    synthetic_candidates: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = _write_request(tmp_path, _TWO_OK)
    cache = tmp_path / "cache.jsonl"
    common = [
        "--request",
        str(request_path),
        "--root",
        str(synthetic_candidates),
        "--cache",
        str(cache),
    ]

    code, out, err = _run([*common, "--evals-limit", "1"], capsys)
    assert code == 3
    assert out == ""
    assert err.startswith("BUDGET:")
    assert "2" in err and "1" in err
    assert not cache.exists()

    code, out, err = _run([*common, "--evals-limit", "2"], capsys)
    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert [r["status"] for r in payload["results"]] == ["ok", "missing", "ok"]
    assert payload["cost"]["evals"] == 2
    assert _line_count(cache) == 3


def test_cli_cache_round_trip_marks_second_run_cached_with_zero_evals(
    synthetic_candidates: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = _write_request(tmp_path, SYNTHETIC_EXAMPLE_REQUEST)
    cache = tmp_path / "cache.jsonl"
    args = [
        "--request",
        str(request_path),
        "--root",
        str(synthetic_candidates),
        "--cache",
        str(cache),
    ]

    code, out, err = _run(args, capsys)
    assert (code, err) == (0, "")
    first = json.loads(out)
    assert first["cost"]["evals"] == 3
    assert all(r["cached"] is False for r in first["results"])
    lines_after_first = _line_count(cache)
    assert lines_after_first == 8

    code, out, err = _run(args, capsys)
    assert (code, err) == (0, "")
    second = json.loads(out)
    assert all(r["cached"] is True for r in second["results"] if r["status"] != "unsupported")
    assert [r["cached"] for r in second["results"]].count(False) == 1
    assert all(r["cost"]["evals"] == 0 for r in second["results"])
    assert second["cost"]["evals"] == 0
    assert [r["status"] for r in second["results"]] == EXPECTED_STATUSES
    assert _line_count(cache) == lines_after_first
    schema = json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(second)
