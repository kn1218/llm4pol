"""Status taxonomy, provenance, no-population-filter and 100-batch order on the synthetic table.

CONTEXT D-02 (each status), D-03 (value semantics; no filter), D-04 / R-2
(per-candidate charging), D-05 (``Backend`` protocol); EVAL-02, EVAL-03,
EVAL-05; charter section 13 M2 (1), (3), (4). Every number is the synthetic
fixture's own arithmetic (RESEARCH F-40) and is cross-checked against the
fixture parquet read back with pandas -- the same writer, no re-derived value.
The barred column's name is assembled from fragments in test bodies (Phase 2
W-1 rule, A-7); it never appears as a literal outside a ``def test_`` line.
"""

from __future__ import annotations

import dataclasses
import itertools
import json
import math
from pathlib import Path
from typing import Any

import jsonschema
import pandas as pd

from conftest import UNKNOWN_CANDIDATE_ID
from llm4pol.data import snapshot
from llm4pol.data.registry import load_registry
from llm4pol.evaluate import (
    RESPONSE_SCHEMA_PATH,
    Backend,
    Cost,
    EvalRequest,
    EvalResponse,
    Evaluator,
    Lookup,
    PropertyTable,
    parse_request,
)
from llm4pol.evaluate.backends.table import TableBackend

THREE_KEYS = ["thermal_conductivity", "dielectric_const_dc", "tg"]
BARRED_KEY = "static_" + "dielectric_const"
UNREGISTERED_KEY = "melting_point"


def _parquet(root: Path) -> Path:
    return snapshot.candidates_parquet(snapshot.processed_dir(root))


def _frame(root: Path) -> Any:
    return pd.read_parquet(_parquet(root)).set_index("candidate_id")


def _evaluator(root: Path) -> Evaluator:
    properties = PropertyTable.load()
    return Evaluator(TableBackend(_parquet(root), properties=properties), properties)


def _request(pairs: list[tuple[str, list[str]]], *, run_id: str = "t") -> EvalRequest:
    return parse_request(
        {
            "run_id": run_id,
            "iteration": 0,
            "batch": [{"candidate_id": cid, "properties": keys} for cid, keys in pairs],
        }
    )


def _one(root: Path, candidate_id: str, key: str) -> Any:
    response = _evaluator(root).evaluate(_request([(candidate_id, [key])]))
    assert len(response.results) == 1
    return response.results[0]


def _assert_non_ok(result: Any, status: str, reason: str | None) -> None:
    assert result.status == status
    assert result.reason == reason
    assert (result.value, result.unit, result.n_replicates, result.spread) == (
        None,
        None,
        None,
        None,
    )
    assert result.cost == Cost(0, 0.0)


def test_ok_with_spread_when_n_ge_2(synthetic_candidates: Path) -> None:
    frame = _frame(synthetic_candidates)
    first = _one(synthetic_candidates, "7ec8cb49ff317efc", "thermal_conductivity")
    assert first.status == "ok"
    assert math.isclose(first.value, 0.32, abs_tol=1e-9)
    assert first.n_replicates == 3
    assert math.isclose(first.spread, 0.02, abs_tol=1e-6)
    assert first.unit == "W/(m*K)"
    assert first.value == frame.loc["7ec8cb49ff317efc", "thermal_conductivity_median"]
    assert first.spread == frame.loc["7ec8cb49ff317efc", "thermal_conductivity_std"]

    second = _one(synthetic_candidates, "b3a635a55e1a6645", "thermal_conductivity")
    assert second.status == "ok"
    assert second.n_replicates == 2
    assert math.isclose(second.spread, 0.007071, abs_tol=1e-6)
    assert second.value == frame.loc["b3a635a55e1a6645", "thermal_conductivity_median"]
    assert second.spread == frame.loc["b3a635a55e1a6645", "thermal_conductivity_std"]


def test_ok_with_null_spread_when_n_is_1(synthetic_candidates: Path) -> None:
    result = _one(synthetic_candidates, "d24805b4ce4c381c", "thermal_conductivity")
    assert result.status == "ok"
    assert result.n_replicates == 1
    assert result.spread is None
    assert math.isclose(result.value, 0.22, abs_tol=1e-9)
    assert result.cost == Cost(1, 0.0)


def test_missing_value_absent_when_median_is_null(synthetic_candidates: Path) -> None:
    _assert_non_ok(
        _one(synthetic_candidates, "81b997b85ccd2069", "thermal_conductivity"),
        "missing",
        "value_absent",
    )
    _assert_non_ok(_one(synthetic_candidates, "d24805b4ce4c381c", "tg"), "missing", "value_absent")


def test_missing_candidate_unknown_for_a_well_formed_absent_id(synthetic_candidates: Path) -> None:
    assert UNKNOWN_CANDIDATE_ID not in _frame(synthetic_candidates).index
    _assert_non_ok(
        _one(synthetic_candidates, UNKNOWN_CANDIDATE_ID, "tg"), "missing", "candidate_unknown"
    )


class _RaisingBackend:
    """A ``Backend`` whose lookup must never be reached."""

    name = "raising"
    source = "nowhere"
    provenance_tier = "md_simulated"
    calls = 0

    def lookup(self, candidate_id: str, property_key: str) -> Lookup:
        self.calls += 1
        raise AssertionError(f"backend consulted for {candidate_id!r}/{property_key!r}")


def test_unsupported_for_an_unregistered_key_and_the_barred_key_even_on_an_unknown_candidate(
    synthetic_candidates: Path,
) -> None:
    properties = PropertyTable.load()
    assert not properties.supported(UNREGISTERED_KEY)
    assert not properties.supported(BARRED_KEY)

    raising = _RaisingBackend()
    assert isinstance(raising, Backend)
    response = Evaluator(raising, properties).evaluate(
        _request([("7ec8cb49ff317efc", [UNREGISTERED_KEY]), (UNKNOWN_CANDIDATE_ID, [BARRED_KEY])])
    )
    assert raising.calls == 0
    for result in response.results:
        _assert_non_ok(result, "unsupported", None)
        assert "reason" not in result.to_json()

    # The same two lookups through the real table: the decision is made before
    # the parquet is touched, so the unknown candidate is `unsupported`, not
    # `missing` (RESEARCH Pattern 1, Pitfall 6).
    counted = TableBackend(_parquet(synthetic_candidates), properties=properties)
    calls: list[tuple[str, str]] = []
    original = counted.lookup

    def counting_lookup(candidate_id: str, property_key: str) -> Lookup:
        calls.append((candidate_id, property_key))
        return original(candidate_id, property_key)

    counted.lookup = counting_lookup  # type: ignore[method-assign]
    response = Evaluator(counted, properties).evaluate(
        _request([(UNKNOWN_CANDIDATE_ID, [BARRED_KEY, "tg"]), ("7ec8cb49ff317efc", ["foo"])])
    )
    assert [r.status for r in response.results] == ["unsupported", "missing", "unsupported"]
    assert response.results[1].reason == "candidate_unknown"
    assert calls == [(UNKNOWN_CANDIDATE_ID, "tg")]


def test_unsupported_and_missing_consume_no_evals(synthetic_candidates: Path) -> None:
    response = _evaluator(synthetic_candidates).evaluate(
        _request(
            [
                ("7ec8cb49ff317efc", [UNREGISTERED_KEY]),
                ("81b997b85ccd2069", ["thermal_conductivity"]),
                (UNKNOWN_CANDIDATE_ID, ["tg", BARRED_KEY]),
            ]
        )
    )
    assert [r.status for r in response.results] == [
        "unsupported",
        "missing",
        "missing",
        "unsupported",
    ]
    assert response.cost == Cost(0, 0.0)
    assert all(r.cost == Cost(0, 0.0) for r in response.results)


def test_every_result_carries_backend_source_and_provenance_tier(
    synthetic_candidates: Path,
) -> None:
    properties = PropertyTable.load()
    backend = TableBackend(_parquet(synthetic_candidates), properties=properties)
    assert isinstance(backend, Backend)
    assert backend.source == properties.snapshot == snapshot.SNAPSHOT_ID

    response = Evaluator(backend, properties).evaluate(
        _request(
            [
                ("7ec8cb49ff317efc", ["thermal_conductivity", UNREGISTERED_KEY]),
                ("81b997b85ccd2069", ["thermal_conductivity"]),
                (UNKNOWN_CANDIDATE_ID, ["tg"]),
            ]
        )
    )
    assert {r.status for r in response.results} == {"ok", "unsupported", "missing"}
    assert [f.name for f in dataclasses.fields(Cost)] == ["evals", "cpu_hours"]
    for result in response.results:
        assert result.backend == "table"
        assert result.source == properties.snapshot
        assert result.provenance_tier == "md_simulated"
        assert result.cached is False
        assert set(result.to_json()["cost"]) == {"evals", "cpu_hours"}  # type: ignore[arg-type]


def test_unit_n_replicates_and_spread_come_from_the_registry_and_the_candidate_table(
    synthetic_candidates: Path,
) -> None:
    registry = load_registry()
    frame = _frame(synthetic_candidates)
    keys = list(registry.properties)
    batch = [(cid, keys) for cid in frame.index]
    response = _evaluator(synthetic_candidates).evaluate(_request(batch))
    assert len(response.results) == len(frame.index) * len(keys)

    for result in response.results:
        spec = registry.properties[result.property]
        n = int(frame.loc[result.candidate_id, spec.column + "_n"])
        std = frame.loc[result.candidate_id, spec.column + "_std"]
        if result.status == "ok":
            assert result.unit == spec.unit
            assert result.n_replicates == n
            if n >= 2:
                assert result.spread == std
            else:
                assert result.spread is None
            assert result.value == frame.loc[result.candidate_id, spec.column + "_median"]
        else:
            assert (result.status, result.reason) == ("missing", "value_absent")
            assert n == 0
    absent = [(r.candidate_id, r.property) for r in response.results if r.status == "missing"]
    assert absent == [("81b997b85ccd2069", "thermal_conductivity"), ("d24805b4ce4c381c", "tg")]


def test_no_population_filter_is_applied(synthetic_candidates: Path) -> None:
    tc = _one(synthetic_candidates, "182075ab56be81bf", "thermal_conductivity")
    tg = _one(synthetic_candidates, "182075ab56be81bf", "tg")
    assert (tc.status, tg.status) == ("ok", "ok")
    assert tc.value == 15.0
    assert tg.value == 1.0e6


def _hundred_batch(root: Path) -> list[tuple[str, list[str]]]:
    ids = [*sorted(_frame(root).index), UNKNOWN_CANDIDATE_ID]
    assert len(ids) == 10
    return [(cid, list(THREE_KEYS)) for cid in itertools.islice(itertools.cycle(ids), 100)]


def test_batch_of_100_synthetic_entries_returns_300_results_in_request_order(
    synthetic_candidates: Path,
) -> None:
    batch = _hundred_batch(synthetic_candidates)
    request = _request(batch, run_id="batch-100")
    assert len(request.batch) == 100
    response = _evaluator(synthetic_candidates).evaluate(request)

    assert len(response.results) == 300
    assert [(r.candidate_id, r.property) for r in response.results] == [
        (entry.candidate_id, key) for entry in request.batch for key in entry.properties
    ]
    assert {r.status for r in response.results} <= {"ok", "missing"}
    assert response.cost.evals == 9
    charged = [r.candidate_id for r in response.results if r.cost.evals == 1]
    assert len(charged) == len(set(charged)) == 9
    assert UNKNOWN_CANDIDATE_ID not in charged

    schema = json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(response.to_json())
    assert EvalResponse.from_json(response.to_json()) == response


def test_response_cost_is_the_sum_of_result_costs(synthetic_candidates: Path) -> None:
    response = _evaluator(synthetic_candidates).evaluate(
        _request(_hundred_batch(synthetic_candidates))
    )
    assert response.cost.evals == sum(r.cost.evals for r in response.results)
    assert response.cost.cpu_hours == sum(r.cost.cpu_hours for r in response.results) == 0.0
    assert response.cost == Cost(9, 0.0)
