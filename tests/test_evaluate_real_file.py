"""Charter section 13 M2 (2), (3) reproduced on the pinned candidate table -- CI cannot run these.

The processed candidate parquet (78,375 rows, ~23.8 MB; RESEARCH F-02, ADR-0006)
is never committed, so every test here depends on the ``real_candidates``
session fixture, which skips with its stated reason when the file is absent
(D-08, F-41). Locally every test must PASS: the batch of 100 pinned candidates
x 3 properties returns 300 results in request order with no ``error``, the
same request answered again is fully cached with ``evals`` 0, and the CLI run
exits 0 with a schema-valid response. No expected number here is ever edited
to make a test pass; a mismatch is an evaluator defect. The tests never print
or persist a candidate id or a property value outside ``tmp_path``: the ids
are read from the parquet at run time and the request file lives in the
per-test temporary directory (data policy; charter section 10).
"""

# Measured wall time on the Windows development machine (2026-09-22, plan 03-03):
# the warm-up lookup (pq.read_table + to_pandas + set_index on the full table)
# 0.03 s; the 300-lookup evaluate 0.012 s (F-09, F-10: 100 x 9 <= 10 ms);
# pytest --durations: batch test 0.13 s, cached-batch test 0.10 s, CLI test
# (two in-process runs, 300-line JSONL) 0.17 s; the module runs in ~0.6 s.
# A later plan sizing a larger real batch can budget from these numbers.

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import jsonschema
import pyarrow.parquet as pq

from conftest import REPO_ROOT
from llm4pol.evaluate import (
    RESPONSE_SCHEMA_PATH,
    Cost,
    EvalRequest,
    EvalResponse,
    Evaluator,
    PropertyTable,
    parse_request,
)
from llm4pol.evaluate import __main__ as cli
from llm4pol.evaluate.backends.table import TableBackend

SNAPSHOT_ID = "polyomics:general_polymers@041e5834"
THREE_KEYS = ["thermal_conductivity", "dielectric_const_dc", "tg"]
BATCH_SIZE = 100
EVALUATE_BUDGET_SECONDS = 1.0


def _first_ids(path: Path) -> list[str]:
    column = pq.read_table(path, columns=["candidate_id"]).column("candidate_id")
    ids: list[str] = [str(value) for value in column[:BATCH_SIZE].to_pylist()]
    assert len(ids) == BATCH_SIZE
    return ids


def _request_payload(ids: list[str]) -> dict[str, Any]:
    return {
        "run_id": "real-batch-100",
        "iteration": 0,
        "batch": [{"candidate_id": cid, "properties": list(THREE_KEYS)} for cid in ids],
    }


def _request(ids: list[str]) -> EvalRequest:
    return parse_request(_request_payload(ids))


def _evaluator(path: Path) -> Evaluator:
    properties = PropertyTable.load()
    return Evaluator(TableBackend(path, properties=properties), properties)


def _schema() -> dict[str, Any]:
    schema: dict[str, Any] = json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return schema


def _flattened(request: EvalRequest) -> list[tuple[str, str]]:
    return [(entry.candidate_id, key) for entry in request.batch for key in entry.properties]


def _assert_real_batch_shape(response: EvalResponse, request: EvalRequest) -> None:
    results = response.results
    assert len(results) == BATCH_SIZE * len(THREE_KEYS)
    assert [(r.candidate_id, r.property) for r in results] == _flattened(request)
    for result in results:
        assert result.status in {"ok", "missing"}
        if result.status == "missing":
            assert result.reason == "value_absent"
        else:
            assert result.n_replicates is not None and result.n_replicates >= 1
            assert (result.spread is None) == (result.n_replicates < 2)
        assert result.backend == "table"
        assert result.source == SNAPSHOT_ID
        assert result.provenance_tier == "md_simulated"


def test_real_table_backend_source_matches_the_parquet_snapshot_metadata(
    real_candidates: Path,
) -> None:
    metadata = pq.ParquetFile(real_candidates).schema_arrow.metadata
    assert metadata[b"llm4pol.snapshot"].decode("utf-8") == SNAPSHOT_ID
    backend = TableBackend(real_candidates, properties=PropertyTable.load())
    assert backend.source == SNAPSHOT_ID


def test_real_batch_of_100_returns_300_results_in_request_order(real_candidates: Path) -> None:
    ids = _first_ids(real_candidates)
    request = _request(ids)
    evaluator = _evaluator(real_candidates)
    warm_up = evaluator.backend.lookup(ids[0], "tg")
    assert warm_up.status in {"ok", "missing"}

    started = time.perf_counter()
    response = evaluator.evaluate(request)
    elapsed = time.perf_counter() - started
    assert elapsed < EVALUATE_BUDGET_SECONDS, elapsed

    _assert_real_batch_shape(response, request)
    assert all(r.cached is False for r in response.results)
    ok_candidates = {r.candidate_id for r in response.results if r.status == "ok"}
    assert response.cost.evals == len(ok_candidates)
    assert response.cost.evals <= BATCH_SIZE
    assert response.cost.cpu_hours == 0.0
    assert evaluator.meter.evals == response.cost.evals
    jsonschema.Draft202012Validator(_schema()).validate(response.to_json())


def test_real_second_identical_batch_is_fully_cached_with_zero_evals(
    real_candidates: Path,
) -> None:
    ids = _first_ids(real_candidates)
    request = _request(ids)
    evaluator = _evaluator(real_candidates)
    first = evaluator.evaluate(request)
    charged = evaluator.meter.evals
    assert charged == first.cost.evals

    second = evaluator.evaluate(request)
    _assert_real_batch_shape(second, request)
    assert all(r.cached is True for r in second.results)
    assert all(r.cost.evals == 0 for r in second.results)
    assert second.cost == Cost(0, 0.0)
    assert evaluator.meter.evals == charged
    jsonschema.Draft202012Validator(_schema()).validate(second.to_json())


def _line_count(path: Path) -> int:
    with path.open("rb") as fh:
        return sum(1 for _ in fh)


def test_real_cli_batch_of_100_exits_0_with_a_schema_valid_response(
    real_candidates: Path, tmp_path: Path, capsys: Any
) -> None:
    ids = _first_ids(real_candidates)
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(_request_payload(ids), sort_keys=True), encoding="utf-8")
    cache_path = tmp_path / "cache.jsonl"
    argv = [
        "--request",
        str(request_path),
        "--root",
        str(REPO_ROOT),
        "--cache",
        str(cache_path),
    ]

    capsys.readouterr()
    assert cli.main(argv) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    jsonschema.Draft202012Validator(_schema()).validate(payload)
    response = EvalResponse.from_json(payload)
    _assert_real_batch_shape(response, _request(ids))
    assert _line_count(cache_path) == BATCH_SIZE * len(THREE_KEYS)

    assert cli.main(argv) == 0
    second = EvalResponse.from_json(json.loads(capsys.readouterr().out))
    assert all(r.cached is True for r in second.results)
    assert second.cost == Cost(0, 0.0)
    assert _line_count(cache_path) == BATCH_SIZE * len(THREE_KEYS)
