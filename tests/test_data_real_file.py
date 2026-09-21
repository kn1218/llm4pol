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


# --------------------------------------------------------------------------
# Plan 02-05: the README numbers on the pinned file (F-08..F-19, F-38, F-39, F-59, F-61)
# --------------------------------------------------------------------------

_FINDING_HEADER = ["finding", "population", "expected", "observed", "class", "status"]


def _findings_table(text: str) -> dict[str, tuple[str, str, str, str, str]]:
    """The `## Findings` table: id -> (population, expected, observed, class, status)."""
    lines = text.splitlines()
    start = lines.index("## Findings")
    header = [cell.strip() for cell in lines[start + 2].strip().strip("|").split("|")]
    assert header == _FINDING_HEADER, header
    found: dict[str, tuple[str, str, str, str, str]] = {}
    for line in lines[start + 4 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        found[cells[0]] = (cells[1], cells[2], cells[3], cells[4], cells[5])
    return found


def _run_validator(real_load: load.LoadResult, tmp_path: Path) -> tuple[int, str]:
    report_path = tmp_path / "report.md"
    code = validate.run(REPO_ROOT, processed_dir=real_load.processed_dir, report_path=report_path)
    return code, report_path.read_text(encoding="utf-8")


REPRODUCED_README_NUMBERS: dict[str, str] = {
    "readme_triple_all_rows": "43,561",
    "readme_triple_in_scope": "43,560",
    "triple_check_tc_all_rows": "42,733",
    "candidate_triple_filter_then_median": "40,212",
    "eps_alternative_non_null_only": "45,821",
    "eps_alternative_le_10": "42,186",
    "eps_alternative_le_50": "45,134",
    "eps_alternative_le_100": "45,704",
    "coverage_thermal_conductivity": "81,405",
    "coverage_dielectric_const_dc": "93,488",
    "coverage_tg": "56,064",
    "coverage_fractional_free_volume": "87,849",
    "coverage_sp_ced": "71,848",
    "coverage_refractive_index": "93,488",
    "coverage_density": "95,335",
    "coverage_Rg": "95,335",
    "tacticity_none": "48,790",
    "tacticity_atactic": "45,032",
    "tacticity_isotactic": "951",
    "tacticity_syndiotactic": "8",
    "tacticity_unknown": "554",
    "multi_tacticity_smiles_with_unknown": "303",
    "multi_tacticity_smiles_without_unknown": "2",
    "raw_string_merges": "5",
    "eps_outside_physical_range": "5,123",
    "dc_maxwell_violations": "0",
    "static_maxwell_violations_triple": "38,693",
    "static_maxwell_violations_all": "78,807",
    "check_tc_true": "79,927",
    "check_tc_false": "15,376",
}

# documented findings pin the observed research value (R-5); the README's figure is a note.
DOCUMENTED_README_NUMBERS: dict[str, str] = {
    # F-13 prints 88.83 %, but its own fraction 38,693 / 43,561 = 88.8249 % rounds to 88.82.
    "static_maxwell_violation_pct_triple": "88.82",
    "static_maxwell_violation_pct_all": "84.30",
    "dc_identity_max_residual": "5.7e-07",
    "static_minimum": "1.00016",
    "spearman_tc_eps": "0.170",
    "spearman_tc_tg": "0.010",
    "spearman_eps_tg": "0.199",
    "spearman_sp_ced_tc": "0.355",
    "spearman_ffv_tc": "-0.069",
    "spearman_rg_tc": "0.304",
    "spearman_density_tc": "-0.270",
    "spearman_static_vs_n2_triple": "-0.144",
    "spearman_eps_vs_n2_triple": "0.476",
    "readme_window_rows": "1,140",
    "readme_window_pct": "2.62",
    "multi_tacticity_canonical_with_unknown": "303",
    "card_count_73045": "not reproducible from any column",
}

TRIPLE_ROWS_POPULATION = "README-triple rows (all source rows)"


def test_real_readme_numbers_reproduce_or_are_documented(
    real_load: load.LoadResult, tmp_path: Path
) -> None:
    code, text = _run_validator(real_load, tmp_path)
    findings = _findings_table(text)
    assert code == 0, [k for k, v in findings.items() if v[4] in ("FAILED", "MISSING")]
    for finding_id, expected in REPRODUCED_README_NUMBERS.items():
        assert finding_id in findings, finding_id
        _, expected_cell, observed_cell, cls, status = findings[finding_id]
        assert (expected_cell, observed_cell, cls, status) == (
            expected,
            expected,
            "reproduce",
            "reproduced",
        ), (finding_id, findings[finding_id])
    for finding_id, expected in DOCUMENTED_README_NUMBERS.items():
        assert finding_id in findings, finding_id
        _, expected_cell, _, cls, status = findings[finding_id]
        assert (expected_cell, cls, status) == (expected, "documented", "documented"), (
            finding_id,
            findings[finding_id],
        )
    for finding_id in (
        "spearman_tc_eps",
        "spearman_tc_tg",
        "spearman_eps_tg",
        "spearman_sp_ced_tc",
        "spearman_ffv_tc",
        "spearman_rg_tc",
        "spearman_density_tc",
    ):
        assert findings[finding_id][0] == TRIPLE_ROWS_POPULATION, finding_id
    assert "The dataset card's 73,045" in text
    assert "the corrected static dielectric constant" in text
    assert "| ∧ check_tc == True (protocol filter, not in the README) |" in text


# --------------------------------------------------------------------------
# Plan 02-05: Tg window, tg_rmse ladder and the feasible set (F-23, F-60..F-65)
# --------------------------------------------------------------------------

REPRODUCED_TG_AND_FEASIBLE: dict[str, str] = {
    "tg_non_null": "56,064",
    "tg_inside_window": "52,753",
    "tg_outside_window": "3,311",
    "tg_rmse_le_0.05": "36,592",
    "tg_rmse_le_0.1": "42,232",
    "tg_rmse_le_0.2": "43,316",
    "tg_rmse_le_0.5": "43,521",
    "tg_rmse_le_1.0": "43,545",
    "feasible_candidates_dev_defaults": "6,793",
    "candidate_triple_filter_then_median": "40,212",
}

DOCUMENTED_TG_AND_FEASIBLE: dict[str, str] = {
    "feasible_pct_dev_defaults": "16.89",
    "eps_q25_candidates": "2.6524",
    "eps_q25_triple_rows": "2.6427",
    "tg_median_all_rows": "488.5",
    "tg_median_triple_rows": "472.2",
    "tg_rmse_median": "0.029",
    "tg_rmse_p95": "0.099",
    "tg_rmse_p99": "0.236",
    "tg_rmse_max": "36.3",
    "candidate_triple_median_then_filter": "40,426",
    "feasible_rows_dev_defaults": "7,317",
}


def test_real_tg_window_ladder_and_feasible_set(real_load: load.LoadResult, tmp_path: Path) -> None:
    code, text = _run_validator(real_load, tmp_path)
    findings = _findings_table(text)
    assert code == 0, [k for k, v in findings.items() if v[4] in ("FAILED", "MISSING")]
    for finding_id, expected in REPRODUCED_TG_AND_FEASIBLE.items():
        assert finding_id in findings, finding_id
        _, expected_cell, observed_cell, cls, status = findings[finding_id]
        assert (expected_cell, observed_cell, cls, status) == (
            expected,
            expected,
            "reproduce",
            "reproduced",
        ), (finding_id, findings[finding_id])
    for finding_id, expected in DOCUMENTED_TG_AND_FEASIBLE.items():
        assert finding_id in findings, finding_id
        _, expected_cell, _, cls, status = findings[finding_id]
        assert (expected_cell, cls, status) == (expected, "documented", "documented"), (
            finding_id,
            findings[finding_id],
        )
    assert "input to the D-16 gate" in text
    assert "Wording discrepancy raised for the owner: REQUIREMENTS.md DATA-09" in text
