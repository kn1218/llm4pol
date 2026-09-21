"""The cache and the budget meter around the evaluator (CONTEXT D-04, R-2, R-4; charter A-3).

Charter section 13 M2 (2): a cache hit on ``(candidate_id, property, backend,
source)`` leaves ``evals`` unchanged -- in memory and after a JSONL replay
(EVAL-04). ``evals`` is charged once per distinct candidate per request on its
first non-cached ``ok`` result (R-2, RESEARCH Pitfall 5). ``BudgetMeter``
keeps ``evals`` and ``cpu_hours`` as two currencies that are never combined
(A-3; the test named in ``docs/governance/INVARIANTS.md``). ``BudgetExceeded``
commits nothing (RESEARCH Pattern 4). The JSONL lines are LF-only, canonical
and NaN-free (F-33, F-34, F-35); a malformed line is a loud ``CacheError``.
Every id below is a synthetic fixture fact (F-40).
"""

from __future__ import annotations

import dataclasses
import inspect
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from llm4pol.data import snapshot
from llm4pol.evaluate import (
    RESPONSE_SCHEMA_PATH,
    BudgetExceeded,
    BudgetMeter,
    CacheError,
    Cost,
    EvalRequest,
    EvalResult,
    Evaluator,
    JsonlCache,
    PropertyTable,
    parse_request,
)
from llm4pol.evaluate import budget as budget_module
from llm4pol.evaluate.backends.table import TableBackend
from llm4pol.evaluate.cache import canonical_line

THREE_KEYS = ["thermal_conductivity", "dielectric_const_dc", "tg"]
THREE_OK = ("7ec8cb49ff317efc", THREE_KEYS)
ALL_MISSING = ("81b997b85ccd2069", ["thermal_conductivity"])
N_ONE = ("d24805b4ce4c381c", ["thermal_conductivity"])
SECOND_OK = ("b3a635a55e1a6645", ["thermal_conductivity"])


def _parquet(root: Path) -> Path:
    return snapshot.candidates_parquet(snapshot.processed_dir(root))


def _evaluator(
    root: Path,
    *,
    cache: JsonlCache | None = None,
    meter: BudgetMeter | None = None,
    evals_limit: int | None = None,
) -> Evaluator:
    properties = PropertyTable.load()
    return Evaluator(
        TableBackend(_parquet(root), properties=properties),
        properties,
        cache=cache,
        meter=meter,
        evals_limit=evals_limit,
    )


def _request(pairs: list[tuple[str, list[str]]], *, run_id: str = "t") -> EvalRequest:
    return parse_request(
        {
            "run_id": run_id,
            "iteration": 0,
            "batch": [{"candidate_id": cid, "properties": keys} for cid, keys in pairs],
        }
    )


def _validate(response: Any) -> None:
    schema = json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(response.to_json())


def _assert_all_cached(response: Any) -> None:
    assert response.results, "a cached response still carries every result"
    for result in response.results:
        assert result.cached is True
        assert result.cost.evals == 0
        assert result.cost == Cost(0, 0.0)
    assert response.cost.evals == 0


# --------------------------------------------------------------------------
# Cache hits (charter section 13 M2 (2); EVAL-04)
# --------------------------------------------------------------------------


def test_cache_hit_leaves_evals_unchanged_in_memory(synthetic_candidates: Path) -> None:
    evaluator = _evaluator(synthetic_candidates)
    request = _request([THREE_OK])

    first = evaluator.evaluate(request)
    assert first.cost.evals == 1
    assert all(r.cached is False for r in first.results)
    assert evaluator.meter.evals == 1

    second = evaluator.evaluate(request)
    _assert_all_cached(second)
    assert evaluator.meter.evals == 1
    _validate(second)


def test_cache_hit_leaves_evals_unchanged_after_jsonl_replay(
    synthetic_candidates: Path, tmp_path: Path
) -> None:
    path = tmp_path / "cache.jsonl"
    request = _request([THREE_OK])

    writer = _evaluator(synthetic_candidates, cache=JsonlCache(path))
    first = writer.evaluate(request)
    assert first.cost.evals == 1
    assert writer.meter.evals == 1
    assert len(writer.cache) == 3
    assert path.is_file()

    replayed = JsonlCache(path)
    assert len(replayed) == 3
    reader = _evaluator(synthetic_candidates, cache=replayed)
    assert reader.meter == BudgetMeter()
    second = reader.evaluate(request)
    _assert_all_cached(second)
    assert reader.meter == BudgetMeter()
    assert len(replayed) == 3
    _validate(second)


def test_cache_key_includes_backend_and_source(synthetic_candidates: Path) -> None:
    cache = JsonlCache()
    evaluator = _evaluator(synthetic_candidates, cache=cache)
    evaluator.evaluate(_request([THREE_OK]))
    source = PropertyTable.load().snapshot

    hit = cache.get(("7ec8cb49ff317efc", "tg", "table", source))
    assert isinstance(hit, EvalResult)
    assert hit.cached is False
    assert hit.status == "ok"
    assert cache.get(("7ec8cb49ff317efc", "tg", "table", "other")) is None
    assert cache.get(("7ec8cb49ff317efc", "tg", "radonpy", source)) is None


# --------------------------------------------------------------------------
# Per-candidate charging (D-04, R-2, RESEARCH Pitfall 5)
# --------------------------------------------------------------------------


def test_evals_charged_once_per_distinct_candidate_per_request(
    synthetic_candidates: Path,
) -> None:
    response = _evaluator(synthetic_candidates).evaluate(_request([THREE_OK]))
    assert [r.cost.evals for r in response.results] == [1, 0, 0]
    assert response.cost.evals == 1

    twice = _evaluator(synthetic_candidates).evaluate(
        _request([("7ec8cb49ff317efc", ["tg"]), ("7ec8cb49ff317efc", ["thermal_conductivity"])])
    )
    assert [r.cost.evals for r in twice.results] == [1, 0]
    assert twice.cost.evals == 1

    two = _evaluator(synthetic_candidates).evaluate(_request([THREE_OK, SECOND_OK]))
    assert [r.cost.evals for r in two.results] == [1, 0, 0, 1]
    assert two.cost.evals == 2


def test_all_missing_candidate_charges_zero(synthetic_candidates: Path) -> None:
    cache = JsonlCache()
    response = _evaluator(synthetic_candidates, cache=cache).evaluate(_request([ALL_MISSING]))
    assert [r.status for r in response.results] == ["missing"]
    assert response.cost.evals == 0
    assert len(cache) == 1


def test_new_property_of_a_cached_candidate_charges_one_eval(
    synthetic_candidates: Path,
) -> None:
    evaluator = _evaluator(synthetic_candidates)
    first = evaluator.evaluate(_request([("7ec8cb49ff317efc", ["thermal_conductivity"])]))
    assert first.cost.evals == 1
    assert evaluator.meter.evals == 1

    second = evaluator.evaluate(_request([("7ec8cb49ff317efc", ["thermal_conductivity", "tg"])]))
    cached, fresh = second.results
    assert cached.cached is True
    assert cached.cost.evals == 0
    assert fresh.cached is False
    assert fresh.cost.evals == 1
    assert second.cost.evals == 1
    assert evaluator.meter.evals == 2


# --------------------------------------------------------------------------
# A-3: two currencies, never combined (docs/governance/INVARIANTS.md names this test)
# --------------------------------------------------------------------------


def test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies() -> None:
    meter = BudgetMeter().charge(Cost(3, 0.0)).charge(Cost(0, 2.5))
    assert meter == BudgetMeter(evals=3, cpu_hours=2.5)
    assert meter.remaining(10) == 7
    assert meter.remaining(2) == 0
    assert meter.exhausted(3) is True
    assert meter.exhausted(4) is False

    assert [f.name for f in dataclasses.fields(BudgetMeter)] == ["evals", "cpu_hours"]
    assert [f.name for f in dataclasses.fields(Cost)] == ["evals", "cpu_hours"]
    assert not hasattr(BudgetMeter, "total")
    source = inspect.getsource(budget_module)
    for combining_name in ("__float__", "__add__", "total"):
        assert combining_name not in source, combining_name

    schema = json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))
    cost_definition = schema["$defs"]["cost"]
    assert cost_definition["required"] == ["evals", "cpu_hours"]
    assert cost_definition["additionalProperties"] is False

    with pytest.raises(dataclasses.FrozenInstanceError):
        meter.evals = 1  # type: ignore[misc]


# --------------------------------------------------------------------------
# BudgetExceeded commits nothing (RESEARCH Pattern 4)
# --------------------------------------------------------------------------


def test_budget_exceeded_leaves_cache_and_meter_untouched(
    synthetic_candidates: Path, tmp_path: Path
) -> None:
    path = tmp_path / "cache.jsonl"
    cache = JsonlCache(path)
    evaluator = _evaluator(synthetic_candidates, cache=cache, evals_limit=1)
    request = _request([THREE_OK, SECOND_OK])

    with pytest.raises(BudgetExceeded) as excinfo:
        evaluator.evaluate(request)
    exc = excinfo.value
    assert (exc.requested, exc.remaining, exc.limit) == (2, 1, 1)
    message = str(exc)
    assert "2" in message and "1" in message
    assert "requested" in message and "remaining" in message and "limit" in message
    assert len(cache) == 0
    assert not path.exists()
    assert evaluator.meter == BudgetMeter()

    allowed = _evaluator(synthetic_candidates, cache=cache, evals_limit=2)
    response = allowed.evaluate(request)
    assert response.cost.evals == 2
    assert allowed.meter.evals == 2
    assert allowed.meter.exhausted(2) is True

    with pytest.raises(BudgetExceeded) as again:
        allowed.evaluate(_request([N_ONE]))
    assert (again.value.requested, again.value.remaining, again.value.limit) == (1, 0, 2)
    assert allowed.meter.evals == 2


# --------------------------------------------------------------------------
# JSONL lines (R-4; F-33, F-34, F-35) and replay validation (T-03-07)
# --------------------------------------------------------------------------


def test_jsonl_lines_are_lf_only_canonical_and_nan_free(
    synthetic_candidates: Path, tmp_path: Path
) -> None:
    path = tmp_path / "nested" / "cache.jsonl"
    cache = JsonlCache(path)
    evaluator = _evaluator(synthetic_candidates, cache=cache)
    evaluator.evaluate(_request([THREE_OK, N_ONE, ALL_MISSING]))
    assert len(cache) == 5

    raw = path.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    assert b"NaN" not in raw
    lines = raw.decode("utf-8").split("\n")
    assert lines[-1] == ""
    body = lines[:-1]
    assert len(body) == len(cache)

    stored: dict[tuple[str, str, str, str], EvalResult] = {}
    for line in body:
        record = json.loads(line)
        assert set(record) == {"key", "result"}
        assert isinstance(record["key"], list) and len(record["key"]) == 4
        assert all(isinstance(part, str) for part in record["key"])
        key = tuple(record["key"])
        result = cache.get(key)  # type: ignore[arg-type]
        assert result is not None
        assert line + "\n" == canonical_line(key, result)  # type: ignore[arg-type]
        stored[key] = result  # type: ignore[index]
    assert len(stored) == 5

    source = PropertyTable.load().snapshot
    n_one_line = next(
        json.loads(line)
        for line in body
        if json.loads(line)["key"][:2] == ["d24805b4ce4c381c", "thermal_conductivity"]
    )
    assert n_one_line["key"] == ["d24805b4ce4c381c", "thermal_conductivity", "table", source]
    assert n_one_line["result"]["n_replicates"] == 1
    assert n_one_line["result"]["spread"] is None


def test_malformed_cache_line_raises_cache_error_with_line_number(
    synthetic_candidates: Path, tmp_path: Path
) -> None:
    path = tmp_path / "cache.jsonl"
    _evaluator(synthetic_candidates, cache=JsonlCache(path)).evaluate(
        _request([("7ec8cb49ff317efc", ["thermal_conductivity", "tg"])])
    )
    assert path.read_text(encoding="utf-8").count("\n") == 2

    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write("{not json\n")
    with pytest.raises(CacheError) as excinfo:
        JsonlCache(path)
    assert ":3:" in str(excinfo.value)
    assert str(path) in str(excinfo.value)

    tampered = tmp_path / "tampered.jsonl"
    record = json.loads(path.read_text(encoding="utf-8").split("\n")[0])
    record["result"]["cached"] = "yes"
    tampered.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(CacheError) as tampered_info:
        JsonlCache(tampered)
    assert ":1:" in str(tampered_info.value)
    assert "cached" in str(tampered_info.value)


def test_stored_records_keep_cached_false(synthetic_candidates: Path, tmp_path: Path) -> None:
    path = tmp_path / "cache.jsonl"
    cache = JsonlCache(path)
    evaluator = _evaluator(synthetic_candidates, cache=cache)
    request = _request([THREE_OK])
    evaluator.evaluate(request)
    hit_response = evaluator.evaluate(request)

    for result in hit_response.results:
        assert result.cached is True
        assert result.cost == Cost(0, 0.0)
    for line in path.read_text(encoding="utf-8").splitlines():
        assert json.loads(line)["result"]["cached"] is False
    source = PropertyTable.load().snapshot
    for key in THREE_KEYS:
        stored = cache.get(("7ec8cb49ff317efc", key, "table", source))
        assert stored is not None and stored.cached is False
