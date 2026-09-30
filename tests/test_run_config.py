"""The run id, strict JSON, the problem spec and the run directory (plan 04-01, task 1).

Guards RUN-01 and RUN-06 and the A-6 preconditions (CONTEXT D-01, D-05): a rerun gets a new run
id, a run directory cannot be taken twice, and a problem spec is validated against
``protocol/schemas/problem-spec.json`` before any typed object exists (RESEARCH Pattern 6).
Test names starting ``test_a6_`` are cited by ``docs/governance/INVARIANTS.md``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT
from llm4pol.run import config, ids, jsonio
from run_support import FIXED_NOW, FIXED_RUN_ID, charter_problem

SCHEMAS = REPO_ROOT / "protocol" / "schemas"


def _load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    return data


# --------------------------------------------------------------------------
# jsonio: two byte forms fixed by their separators (CONTEXT D-02; F-29, F-39)
# --------------------------------------------------------------------------


def test_canonical_and_pretty_bytes() -> None:
    record = {"b": 1, "a": [0.5, None]}

    canonical = jsonio.canonical_bytes(record)
    assert canonical == b'{"a":[0.5,null],"b":1}\n'
    assert len(canonical) == 23

    pretty = jsonio.pretty_bytes(record)
    assert len(pretty) == 45
    assert pretty.endswith(b"}\n") and not pretty.endswith(b"\n\n")
    lines = pretty.decode("utf-8").split("\n")
    assert len(lines) == 8 and lines[-1] == ""
    assert lines[1] == '  "a": ['
    assert b"\r" not in pretty

    for form in (jsonio.canonical_bytes, jsonio.pretty_bytes):
        with pytest.raises(jsonio.StrictJsonError):
            form({"x": float("nan")})
        with pytest.raises(jsonio.StrictJsonError):
            form({"x": float("inf")})


def test_strict_json_refuses_repeated_keys_and_non_finite_constants() -> None:
    assert jsonio.loads_strict('{"a": [1, 2.5, null]}') == {"a": [1, 2.5, None]}

    with pytest.raises(jsonio.StrictJsonError):
        jsonio.loads_strict('{"seq": 1, "seq": 2}')
    for constant in ("NaN", "Infinity", "-Infinity"):
        with pytest.raises(jsonio.StrictJsonError):
            jsonio.loads_strict(f'{{"x": {constant}}}')
    with pytest.raises(jsonio.StrictJsonError):
        jsonio.loads_strict("{not json")
    assert issubclass(jsonio.StrictJsonError, ValueError)


# --------------------------------------------------------------------------
# problem spec (RUN-06; CONTEXT D-05, RESEARCH Pattern 6, F-54, F-58)
# --------------------------------------------------------------------------


def test_problem_spec_is_validated_before_it_is_typed(tmp_path: Path) -> None:
    payload = charter_problem(1, 3, 2)
    spec = config.parse_problem_spec(payload)
    assert isinstance(spec, config.ProblemSpec)
    assert spec.evals_limit == 6
    assert spec.property_keys() == ("thermal_conductivity", "dielectric_const_dc", "tg")
    assert spec.to_json() == payload

    without_version = {k: v for k, v in payload.items() if k != "schema_version"}
    pareto = {**payload, "form": "pareto"}
    extra = {**payload, "note": "x"}
    for bad in (without_version, pareto, extra):
        with pytest.raises(config.ProblemSpecError):
            config.parse_problem_spec(bad)

    nan_threshold = {
        **payload,
        "constraints": [{"property": "tg", "op": ">=", "value": float("nan")}],
    }
    with pytest.raises(config.ProblemSpecError):
        config.parse_problem_spec(nan_threshold)

    path = tmp_path / "problem.json"
    path.write_bytes(jsonio.pretty_bytes(payload))
    assert config.load_problem_spec(path) == spec
    text = path.read_text(encoding="utf-8").replace("2.6", "NaN")
    path.write_text(text, encoding="utf-8")
    with pytest.raises(config.ProblemSpecError):
        config.load_problem_spec(path)


def test_problem_spec_refuses_a_repeated_or_shared_property() -> None:
    payload = charter_problem(1, 3, 2)
    repeated = {
        **payload,
        "constraints": [
            {"property": "tg", "op": ">=", "value": 400.0},
            {"property": "tg", "op": "<=", "value": 500.0},
        ],
    }
    objective_as_constraint = {
        **payload,
        "constraints": [{"property": "thermal_conductivity", "op": ">=", "value": 0.2}],
    }
    for bad in (repeated, objective_as_constraint):
        with pytest.raises(config.ProblemSpecError):
            config.parse_problem_spec(bad)


def test_problem_spec_property_enum_equals_the_registry_schema_enum() -> None:
    registry = _load("property-registry.json")["properties"]["properties"]["propertyNames"]["enum"]
    spec = _load("problem-spec.json")["properties"]
    assert spec["objective"]["properties"]["property"]["enum"] == registry
    assert spec["constraints"]["items"]["properties"]["property"]["enum"] == registry
    assert spec["form"]["enum"] == ["constrained_single"]


# --------------------------------------------------------------------------
# run id and run directory (RUN-01; CONTEXT D-01; A-6)
# --------------------------------------------------------------------------


def test_a6_a_rerun_gets_a_new_run_id() -> None:
    run_id = ids.new_run_id(FIXED_NOW, "00000000")
    assert run_id == "20260101T000000Z-00000000"
    assert len(run_id) == 25
    assert ids.RUN_ID_PATTERN.fullmatch(run_id)
    assert ids.new_run_id(FIXED_NOW, "0000000a") != run_id

    for token in ("0000000", "000000000", "0000000G", "0000000A", ""):
        with pytest.raises(ids.RunIdError):
            ids.new_run_id(FIXED_NOW, token)

    assert ids.require_run_id(run_id) == run_id
    for text in ("../20260101T000000Z-00000000", "a/b", "a\\b", "..", "x..y", "", run_id + "\n"):
        with pytest.raises(ids.RunIdError):
            ids.require_run_id(text)

    assert ids.format_ts(FIXED_NOW) == "2026-01-01T00:00:00Z"
    assert ids.RUN_ID_PATTERN.fullmatch(ids.new_run_id(ids.utc_now(), ids.random_token()))


def test_a6_run_directory_refuses_to_be_created_twice(tmp_path: Path) -> None:
    experiments = tmp_path / "experiments"
    run_dir = config.create_run_dir(experiments, FIXED_RUN_ID)
    assert run_dir == experiments / FIXED_RUN_ID
    assert run_dir.is_dir()

    marker = run_dir / "marker.txt"
    marker.write_text("kept", encoding="utf-8")
    with pytest.raises(config.RunExists) as excinfo:
        config.create_run_dir(experiments, FIXED_RUN_ID)
    assert str(excinfo.value) == "run exists; use replay"
    assert marker.read_text(encoding="utf-8") == "kept"
    assert sorted(p.name for p in run_dir.iterdir()) == ["marker.txt"]

    with pytest.raises(ids.RunIdError):
        config.create_run_dir(experiments, "../escape")
    assert not (tmp_path / "escape").exists()
