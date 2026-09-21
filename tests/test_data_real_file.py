"""Charter section 13 M1 reproductions on the pinned PolyOmics bytes -- CI cannot run these.

The pinned CSV (196,910,783 bytes) is never committed, so every test here
depends on the ``real_csv`` session fixture, which skips with a stated reason
when the file is absent (D-09). Locally the three tests must PASS: they are
the real-file proof of the tracer (F-02, F-03, F-06, F-07, F-32, F-37).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT
from llm4pol.data import fetch, load, snapshot, validate


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
