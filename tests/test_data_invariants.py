"""Promotes ``docs/governance/INVARIANTS.md`` rows from prose to tests inside the gate.

D-7 and D-10 are promoted here because plan 02-01 adds the code they constrain
(``load.build_candidates`` and ``report.CountTable``); D-9 is added by plan
02-04, D-8 and A-7 by plan 02-05 (INVARIANTS.md promotion policy, DATA-10).
Every test names the invariant it guards. All run on the synthetic root (D-09).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from llm4pol.data import load, report, validate
from test_data_cli import SYNTHETIC_EXPECTED


def test_d7_candidate_table_dedups_replicates_before_any_metric(
    synthetic_root: Path, tmp_path: Path
) -> None:
    """D-7: rows sharing a candidate_id are replicates, grouped before any metric."""
    result = load.load(synthetic_root)
    candidates = pd.read_parquet(result.candidates_parquet)
    assert len(candidates) == 9
    assert candidates["candidate_id"].is_unique
    assert int(candidates["n_rows"].sum()) == 12
    polyethylene_none = candidates[
        (candidates["canonical_psmiles"] == "*CC*") & (candidates["tacticity"] == "none")
    ]
    assert len(polyethylene_none) == 1
    assert int(polyethylene_none["n_rows"].iloc[0]) == 3

    # The validator takes unique_candidate_ids from the candidate parquet, not
    # by recounting rows: the row exists in the report ...
    report_path = tmp_path / "report.md"
    assert validate.run(synthetic_root, expected={}, report_path=report_path) == 0
    text = report_path.read_text(encoding="utf-8")
    assert "| unique_candidate_ids | in-scope rows | 9 |" in text
    # ... and without the candidate parquet the validator cannot run at all.
    result.candidates_parquet.unlink()
    assert validate.run(synthetic_root, expected={}, report_path=tmp_path / "again.md") == 2


_SEPARATOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")


def _markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return ``(header_cells, data_rows)`` for every pipe table in ``text``."""
    lines = text.splitlines()
    tables: list[tuple[list[str], list[list[str]]]] = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("|") and _SEPARATOR.match(lines[i + 1]):
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            tables.append((header, rows))
            i = j
        else:
            i += 1
    return tables


def test_d10_every_count_table_in_report_names_its_population(
    synthetic_root: Path, tmp_path: Path
) -> None:
    """D-10: every reported count states the population it is drawn from."""
    load.load(synthetic_root)
    report_path = tmp_path / "report.md"
    validate.run(synthetic_root, expected=SYNTHETIC_EXPECTED, report_path=report_path)
    tables = _markdown_tables(report_path.read_text(encoding="utf-8"))
    assert tables, "the report has no tables"
    for header, rows in tables:
        assert "population" in header, header
        column = header.index("population")
        for row in rows:
            assert row[column], f"empty population cell in row {row}"

    with pytest.raises(ValueError, match="population"):
        report.CountTable(title="x", header=("quantity", "value"), rows=[])
