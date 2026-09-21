"""Charter section 13 M1 reproductions on the pinned PolyOmics bytes -- CI cannot run these.

The pinned CSV (196,910,783 bytes) is never committed, so every test here
depends on the ``real_csv`` session fixture, which skips with a stated reason
when the file is absent (D-09). Locally every test must PASS: the first three
are the real-file proof of the tracer (F-02, F-03, F-06, F-07, F-32, F-37);
plan 02-03 adds the identity counts, the declared-schema round-trip and the
candidate sizes (F-07, F-37, F-44, F-50). No expected number here is ever
edited to make a test pass; a mismatch is a loader defect.
"""

# Measured wall time on the Windows development machine (2026-09-22, plan 02-01):
# the session fixture `real_load` (read_csv + 78,379 RDKit canonicalisations +
# two parquet writes) takes 16.2-16.5 s of setup; `test_real_validate_...` 2.3 s;
# `test_real_fetch_...` 0.14 s (sha256 of 197 MB); the module runs in ~19 s.
# A later plan sizing its own real-file tests can budget from these numbers.

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
import pytest

from conftest import REPO_ROOT
from llm4pol.data import fetch, load, snapshot, validate
from llm4pol.data.schema import DECLARED_FIELDS


def _refusing_downloader(**_kwargs: Any) -> str:
    raise AssertionError("downloader must not be called")


def test_real_fetch_verifies_pinned_files_without_downloading(
    real_csv: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert real_csv == snapshot.csv_path(REPO_ROOT)
    assert fetch.fetch(REPO_ROOT, downloader=_refusing_downloader) == 0
    out = capsys.readouterr().out
    assert f"verified {snapshot.CSV_NAME}" in out
    assert f"verified {snapshot.README_NAME}" in out


def test_real_load_writes_95332_rows_and_78676_candidates(real_load: load.LoadResult) -> None:
    assert real_load.source_rows == 95335
    assert real_load.source_columns == 259
    assert real_load.excluded_second_monomer == 3
    assert real_load.excluded_parse_failure == 0
    assert real_load.rows_written == 95332
    assert real_load.candidates == 78676


def test_real_validate_reproduces_source_shape(real_load: load.LoadResult, tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    assert (
        validate.run(REPO_ROOT, processed_dir=real_load.processed_dir, report_path=report_path) == 0
    )
    text = report_path.read_text(encoding="utf-8")
    assert "| source_rows | all source rows | 95,335 | 95,335 | reproduce | reproduced |" in text
    assert "| source_columns | all source rows | 259 | 259 | reproduce | reproduced |" in text
    assert (
        "| unique_smiles_list | all source rows | 78,379 | 78,379 | reproduce | reproduced |"
        in text
    )
    assert (
        "| unique_candidate_ids | in-scope rows | 78,676 | 78,676 | reproduce | reproduced |"
        in text
    )


# --------------------------------------------------------------------------
# Plan 02-03: identity counts, declared schema, candidate sizes (F-07, F-37, F-44, F-50)
# --------------------------------------------------------------------------


def test_real_identity_counts_match_research(real_load: load.LoadResult) -> None:
    assert real_load.excluded_second_monomer == 3
    assert real_load.excluded_parse_failure == 0
    rows = pd.read_parquet(real_load.rows_parquet, columns=["canonical_psmiles", "candidate_id"])
    assert rows["canonical_psmiles"].notna().all()
    assert rows["candidate_id"].notna().all()
    assert rows["canonical_psmiles"].nunique() == 78373
    assert rows["candidate_id"].nunique() == 78676


def test_real_parquet_schema_round_trips_with_declared_types(real_load: load.LoadResult) -> None:
    metadata = pq.read_metadata(real_load.rows_parquet)
    assert metadata.num_rows == 95332
    assert metadata.num_columns == 262
    schema = pq.read_schema(real_load.rows_parquet)
    for field in DECLARED_FIELDS:
        assert schema.field(field.name).type == field.type, field.name


def test_real_candidates_have_unique_ids_and_sizes_sum_to_in_scope_rows(
    real_load: load.LoadResult,
) -> None:
    candidates = pd.read_parquet(real_load.candidates_parquet, columns=["candidate_id", "n_rows"])
    assert candidates["candidate_id"].nunique() == 78676
    assert len(candidates) == 78676
    assert int(candidates["n_rows"].sum()) == 95332
    assert int(candidates["n_rows"].max()) == 17
    assert int((candidates["n_rows"] >= 2).sum()) == 12983
