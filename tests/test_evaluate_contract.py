"""The evaluator contract as protocol (CONTEXT D-01, R-3; EVAL-01; charter section 13 M2 (5)).

Both schemas are valid Draft 2020-12 documents; the committed examples under
``protocol/examples/`` validate, carry invented ids only, and the response
example is exactly what the evaluator prints on the synthetic table; the
negative cases of RESEARCH F-24..F-30 are each rejected with the validator's
message; the dataclasses round-trip through JSON and are frozen.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import math
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from conftest import REPO_ROOT, SYNTHETIC_EXAMPLE_REQUEST, SYNTHETIC_ROWS, UNKNOWN_CANDIDATE_ID
from llm4pol.data import identity, snapshot
from llm4pol.evaluate import (
    REQUEST_SCHEMA_PATH,
    RESPONSE_SCHEMA_PATH,
    Cost,
    EvalResponse,
    EvalResult,
    Evaluator,
    PropertyTable,
    RequestError,
    parse_request,
)
from llm4pol.evaluate.backends.table import TableBackend

EXAMPLES = REPO_ROOT / "protocol" / "examples"
REQUEST_EXAMPLE = EXAMPLES / "eval-request.example.json"
RESPONSE_EXAMPLE = EXAMPLES / "eval-response.example.json"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _synthetic_ids() -> set[str]:
    """Every candidate id the synthetic rows can produce (single-monomer, parseable)."""
    ids: set[str] = set()
    for row in SYNTHETIC_ROWS:
        if row["smiles_2"] is not None:
            continue
        canonical = identity.canonical_psmiles(str(row["smiles_list"]))
        if canonical is not None:
            ids.add(identity.candidate_id(canonical, row["tacticity"]))
    return ids


def _evaluate_example(root: Path) -> EvalResponse:
    properties = PropertyTable.load()
    backend = TableBackend(
        snapshot.candidates_parquet(snapshot.processed_dir(root)), properties=properties
    )
    return Evaluator(backend, properties).evaluate(parse_request(SYNTHETIC_EXAMPLE_REQUEST))


def _assert_json_close(actual: Any, expected: Any, path: str = "$") -> None:
    if isinstance(expected, float) and not isinstance(expected, bool):
        assert isinstance(actual, (int, float)) and not isinstance(actual, bool), path
        assert math.isclose(actual, expected, rel_tol=1e-9, abs_tol=0.0), (path, actual, expected)
    elif isinstance(expected, dict):
        assert isinstance(actual, dict), path
        assert sorted(actual) == sorted(expected), (path, sorted(actual), sorted(expected))
        for key in expected:
            _assert_json_close(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), path
        for index, (a, e) in enumerate(zip(actual, expected, strict=True)):
            _assert_json_close(a, e, f"{path}[{index}]")
    else:
        assert actual == expected, (path, actual, expected)


def test_both_schemas_are_valid_draft_2020_12() -> None:
    request_schema = _load(REQUEST_SCHEMA_PATH)
    response_schema = _load(RESPONSE_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(request_schema)
    jsonschema.Draft202012Validator.check_schema(response_schema)
    assert request_schema["$schema"] == DRAFT_2020_12
    assert response_schema["$schema"] == DRAFT_2020_12
    cost = response_schema["$defs"]["cost"]
    assert cost["required"] == ["evals", "cpu_hours"]
    assert cost["additionalProperties"] is False
    tier = response_schema["$defs"]["result"]["properties"]["provenance_tier"]
    assert tier["enum"] == ["md_simulated"]


def test_committed_examples_validate_against_their_schemas() -> None:
    request = _load(REQUEST_EXAMPLE)
    response = _load(RESPONSE_EXAMPLE)
    jsonschema.Draft202012Validator(_load(REQUEST_SCHEMA_PATH)).validate(request)
    jsonschema.Draft202012Validator(_load(RESPONSE_SCHEMA_PATH)).validate(response)

    allowed = _synthetic_ids() | {UNKNOWN_CANDIDATE_ID}
    request_ids = {entry["candidate_id"] for entry in request["batch"]}
    response_ids = {result["candidate_id"] for result in response["results"]}
    assert request_ids <= allowed, request_ids - allowed
    assert response_ids <= allowed, response_ids - allowed
    assert UNKNOWN_CANDIDATE_ID in response_ids


def test_committed_response_example_equals_evaluator_output_on_the_synthetic_root(
    synthetic_candidates: Path,
) -> None:
    text = RESPONSE_EXAMPLE.read_text(encoding="utf-8", newline="")
    parsed = json.loads(text)
    _assert_json_close(_evaluate_example(synthetic_candidates).to_json(), parsed)
    assert "\r" not in text
    assert json.dumps(parsed, indent=2, sort_keys=True) + "\n" == text
    assert _load(REQUEST_EXAMPLE) == SYNTHETIC_EXAMPLE_REQUEST


_OK_RESULT: dict[str, Any] = {
    "candidate_id": "7ec8cb49ff317efc",
    "property": "thermal_conductivity",
    "status": "ok",
    "value": 0.315,
    "unit": "W/(m*K)",
    "n_replicates": 4,
    "spread": 0.017078,
    "backend": "table",
    "source": "polyomics:general_polymers@041e5834",
    "provenance_tier": "md_simulated",
    "cached": False,
    "cost": {"evals": 1, "cpu_hours": 0.0},
}
_NULLS: dict[str, Any] = {"value": None, "unit": None, "n_replicates": None, "spread": None}


def _result(**overrides: Any) -> dict[str, Any]:
    return {**copy.deepcopy(_OK_RESULT), **overrides}


def _non_ok(status: str, **overrides: Any) -> dict[str, Any]:
    fields = {**_NULLS, "cost": {"evals": 0, "cpu_hours": 0.0}, **overrides}
    return _result(status=status, **fields)


def _response(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": "r",
        "iteration": 0,
        "results": [result],
        "cost": copy.deepcopy(result["cost"]),
    }


@pytest.mark.parametrize(
    ("result", "fragment"),
    [
        pytest.param(_result(value=None), "None is not of type 'number'", id="ok-value-null"),
        pytest.param(
            _non_ok("missing", reason="value_absent", value=0.3),
            "0.3 is not of type 'null'",
            id="missing-with-value",
        ),
        pytest.param(_result(reason="x"), "should not be valid", id="ok-with-reason"),
        pytest.param(
            _non_ok("missing"), "'reason' is a required property", id="missing-without-reason"
        ),
        pytest.param(_non_ok("missing", reason="nope"), "is not one of", id="missing-bad-reason"),
        pytest.param(
            _non_ok("error"), "'reason' is a required property", id="error-without-reason"
        ),
        pytest.param(
            _non_ok("missing", reason="value_absent", cost={"evals": 1, "cpu_hours": 0.0}),
            "0 was expected",
            id="missing-charged",
        ),
        pytest.param(_result(cached=True), "0 was expected", id="cached-charged"),
        pytest.param(_result(provenance_tier="experimental"), "is not one of", id="bad-tier"),
        pytest.param(
            _result(note="extra"), "Additional properties are not allowed", id="extra-key"
        ),
    ],
)
def test_response_schema_rejects_each_status_shape_violation(
    result: dict[str, Any], fragment: str
) -> None:
    validator = jsonschema.Draft202012Validator(_load(RESPONSE_SCHEMA_PATH))
    valid_ok = _response(_result())
    validator.validate(valid_ok)
    validator.validate(_response(_result(n_replicates=1, spread=None)))
    with pytest.raises(jsonschema.ValidationError) as excinfo:
        validator.validate(_response(result))
    messages = [excinfo.value.message, *(e.message for e in excinfo.value.context)]
    assert any(fragment in message for message in messages), messages


def _request(**overrides: Any) -> dict[str, Any]:
    return {**copy.deepcopy(SYNTHETIC_EXAMPLE_REQUEST), **overrides}


@pytest.mark.parametrize(
    ("payload", "fragment", "pointer"),
    [
        pytest.param(
            _request(
                batch=[
                    {
                        "candidate_id": "7ec8cb49ff317efc",
                        "properties": ["thermal_conductivity", "thermal_conductivity"],
                    }
                ]
            ),
            "has non-unique elements",
            "batch/0/properties",
            id="duplicate-properties",
        ),
        pytest.param(_request(batch=[]), "should be non-empty", "batch", id="empty-batch"),
        pytest.param(
            _request(batch=[{"candidate_id": "7ec8cb49ff317efc", "properties": ["tg"]}] * 1001),
            "is too long",
            "batch",
            id="1001-batch",
        ),
        pytest.param(_request(iteration=True), "is not of type 'integer'", "iteration", id="bool"),
        pytest.param(
            _request(batch=[{"candidate_id": "ZZZZ", "properties": ["tg"]}]),
            "does not match",
            "batch/0/candidate_id",
            id="malformed-id",
        ),
        pytest.param(_request(run_id=""), "should be non-empty", "run_id", id="empty-run-id"),
    ],
)
def test_request_schema_rejects_dup_props_empty_batch_1001_batch_bool_iteration_and_malformed_id(
    payload: dict[str, Any], fragment: str, pointer: str
) -> None:
    validator = jsonschema.Draft202012Validator(_load(REQUEST_SCHEMA_PATH))
    validator.validate(SYNTHETIC_EXAMPLE_REQUEST)
    errors = list(validator.iter_errors(payload))
    assert errors
    assert any(fragment in error.message for error in errors), [e.message for e in errors]
    with pytest.raises(RequestError) as excinfo:
        parse_request(payload)
    assert pointer in str(excinfo.value)


def test_dataclasses_round_trip_through_json(synthetic_candidates: Path) -> None:
    response = _evaluate_example(synthetic_candidates)
    assert EvalResponse.from_json(response.to_json()) == response
    assert EvalResponse.from_json(json.loads(json.dumps(response.to_json()))) == response

    ok = response.results[0]
    assert ok.status == "ok"
    assert "reason" not in ok.to_json()
    assert Cost(1, 0.0).to_json() == {"evals": 1, "cpu_hours": 0.0}

    with pytest.raises(ValueError, match="cached"):
        EvalResult.from_json({**ok.to_json(), "cached": "yes"})
    with pytest.raises(ValueError, match="unknown status"):
        EvalResult.from_json({**ok.to_json(), "status": "pending"})
    with pytest.raises(ValueError, match="n_replicates"):
        EvalResult.from_json({**ok.to_json(), "n_replicates": True})

    for frozen in (ok, ok.cost, response):
        with pytest.raises(dataclasses.FrozenInstanceError):
            frozen.run_id = "x"
