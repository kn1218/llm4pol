"""The Phase 2 tracer on the synthetic root, plus the CLI exit-code contract (D-10).

One path through every layer -- manifest -> fetch -> dtype map -> identity ->
parquet cast -> candidate table -> report -> exit code -- exercised on the
14-row synthetic fixture of ``conftest.py`` (D-09). Fixture facts cited here:
14 source rows, 23 columns, 10 unique ``smiles_list``, 1 second-monomer row,
1 parse failure, 12 in-scope rows, 7 unique canonical strings, 8 candidates
(9 before ADR-0006 resolved u06's empty tacticity from its `*CC*` twin).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import pytest

from conftest import SYNTHETIC_ROWS
from llm4pol.data import __main__ as cli
from llm4pol.data import fetch, load, report, snapshot, validate

Expected = report.Expected

SYNTHETIC_EXPECTED: dict[str, report.Expected] = {
    "source_rows": Expected("reproduce", 14),
    "source_columns": Expected("reproduce", 23),
    "unique_smiles_list": Expected("reproduce", 10),
    "second_monomer_rows": Expected("reproduce", 1),
    "parse_failures": Expected("reproduce", 1),
    "in_scope_rows": Expected("reproduce", 12),
    "unique_canonical": Expected("reproduce", 7),
    "unique_candidate_ids": Expected("reproduce", 8),
}


def _refusing_downloader(**_kwargs: Any) -> str:
    raise AssertionError("downloader must not be called")


def test_tracer_fetch_load_validate_round_trip_on_synthetic_root(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert len(SYNTHETIC_ROWS) == 14

    assert fetch.fetch(synthetic_root, downloader=_refusing_downloader) == 0
    out = capsys.readouterr().out
    assert f"verified {snapshot.CSV_NAME}" in out
    assert f"verified {snapshot.README_NAME}" in out

    result = load.load(synthetic_root)
    assert result.source_rows == 14
    assert result.source_columns == 23
    assert result.excluded_second_monomer == 1
    assert result.excluded_parse_failure == 1
    assert result.rows_written == 12
    assert result.candidates == 8

    rows = pq.read_table(result.rows_parquet)
    assert rows.num_rows == 12
    for column in ("candidate_id", "canonical_psmiles", "row_index", "extra_note"):
        assert column in rows.column_names, column
    assert rows.schema.metadata[b"llm4pol.snapshot"] == b"polyomics:general_polymers@041e5834"

    candidates = pq.read_table(result.candidates_parquet)
    assert candidates.num_rows == 8
    ids = candidates.column("candidate_id").to_pylist()
    assert len(set(ids)) == 8

    assert validate.run(synthetic_root, expected=SYNTHETIC_EXPECTED) == 0
    report = (synthetic_root / "docs" / "audit" / "polyomics-041e5834-validation.md").read_text(
        encoding="utf-8"
    )
    for heading in (
        "## Fetch identity",
        "## Source shape",
        "## Scope exclusions and identity",
        "## Findings",
    ):
        assert heading in report, heading
    assert "polyomics:general_polymers@041e5834" in report
    assert "041e5834ea1a48682fae12dc39ccd723bcd4f771" in report
    assert "| source_rows | all source rows | 14 | 14 | reproduce | reproduced |" in report


def test_cli_validate_exits_1_on_synthetic_root_because_expected_values_are_polyomics(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    load.load(synthetic_root)
    capsys.readouterr()
    assert cli.main(["validate", "--root", str(synthetic_root)]) == 1
    out = capsys.readouterr().out
    assert "finding source_rows: reproduce expected=95,335 observed=14 FAILED" in out
    assert out.rstrip("\n").splitlines()[-1].startswith("VALIDATION:")


def test_cli_load_exits_2_when_the_pinned_csv_is_absent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["load", "--root", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("ERROR:")
    assert str(snapshot.csv_path(tmp_path)) in err


def test_cli_fetch_exits_1_on_a_sha256_mismatch(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    readme = snapshot.readme_path(synthetic_root)
    data = bytearray(readme.read_bytes())
    data[0] ^= 0x01
    readme.write_bytes(bytes(data))

    def fake_download(**kwargs: Any) -> str:
        # The "download" copies the corrupted file back onto itself, so the
        # bytes on disk do not change and the verification must still fail.
        target = Path(kwargs["local_dir"]) / kwargs["filename"]
        target.write_bytes(target.read_bytes())
        return str(target)

    monkeypatch.setattr(fetch, "hf_hub_download", fake_download)
    assert cli.main(["fetch", "--root", str(synthetic_root)]) == 1
    out = capsys.readouterr().out
    assert "MISMATCH README.md" in out
