"""Promotes ``docs/governance/INVARIANTS.md`` rows from prose to tests inside the gate.

D-7 and D-10 were promoted by plan 02-01, which added the code they constrain
(``load.build_candidates`` and ``report.CountTable``); plan 02-04 promotes D-9
(the report states the per-property noise floor over candidates with n >= 2,
on two named populations) and extends the D-7 test with the replicate
structure of the candidate table; D-8 and A-7 are plan 02-05's (INVARIANTS.md
promotion policy, DATA-10). Every test names the invariant it guards. All run
on the synthetic root (D-09); the one real-file test skips without the pinned
file.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from conftest import REPO_ROOT
from llm4pol.data import filters, load, registry, replicates, report, validate
from llm4pol.data.load import LoadResult
from llm4pol.data.schema import PROPERTY_COLUMNS
from test_data_cli import SYNTHETIC_EXPECTED

NOISE_HEADER = [
    "property",
    "population",
    "n_groups",
    "median_abs_std",
    "median_rel_std",
    "p90_rel_std",
]
NOISE_ALL = "candidates with n >= 2 (in-scope rows)"
NOISE_TRIPLE = "candidates with n >= 2 (README-triple rows)"
TRIPLE = ("thermal_conductivity", "dielectric_const_dc", "tg")


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

    # The replicate structure is read off the candidate table (plan 02-04).
    structure = replicates.replicate_structure(candidates)
    assert structure.n_candidates == 9
    assert structure.n_multi_row == 2
    assert structure.rows_in_multi_row == 5
    assert structure.max_rows == 3
    assert structure.size_histogram == {1: 7, 2: 1, 3: 1}

    # The noise floor accepts only the candidate table, never raw rows.
    rows = pd.read_parquet(result.rows_parquet)
    with pytest.raises(ValueError, match="candidate"):
        replicates.noise_floor(rows, PROPERTY_COLUMNS)
    assert set(replicates.noise_floor(candidates, PROPERTY_COLUMNS)) == set(PROPERTY_COLUMNS)

    # The validator takes unique_candidate_ids from the candidate parquet, not
    # by recounting rows: the row exists in the report ...
    report_path = tmp_path / "report.md"
    assert validate.run(synthetic_root, expected={}, report_path=report_path) == 0
    text = report_path.read_text(encoding="utf-8")
    assert "| unique_candidate_ids | in-scope rows | 9 |" in text
    # ... and every noise-floor population is a candidate population.
    noise_tables = [rows_ for header, rows_ in _markdown_tables(text) if header == NOISE_HEADER]
    assert len(noise_tables) == 2, "expected two noise-floor tables"
    for table_rows in noise_tables:
        for row in table_rows:
            assert row[1].startswith("candidates with n >= 2"), row
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


# --- Plan 02-04: replicate structure and noise floor (D-04, D-07, D-9) ----------------


def _loaded(synthetic_root: Path) -> tuple[Any, Any]:
    result = load.load(synthetic_root)
    return pd.read_parquet(result.rows_parquet), pd.read_parquet(result.candidates_parquet)


def test_noise_floor_values_on_synthetic_are_medians_of_relative_std(
    synthetic_root: Path,
) -> None:
    """D-04: the floor is the median over candidates with n >= 2 of std / |median| (F-55, F-57)."""
    _, candidates = _loaded(synthetic_root)
    tc = replicates.noise_floor(candidates, ("thermal_conductivity",))["thermal_conductivity"]
    assert tc.n_groups == 2
    assert tc.median_rel_std == pytest.approx(0.054060, abs=1e-5)
    assert tc.median_abs_std == pytest.approx(0.0135355, abs=1e-6)
    assert 0.0456 <= tc.p90_rel_std <= 0.0625
    density = replicates.noise_floor(candidates, ("density",))["density"]
    assert density.n_groups == 2
    assert density.median_rel_std == 0.0

    # A single outlier candidate does not move the floor: the aggregate is the median.
    frame = pd.DataFrame(
        {
            "candidate_id": ["a", "b", "c", "d"],
            "x_median": [1.0, 1.0, 1.0, 1.0],
            "x_n": [2, 2, 2, 1],
            "x_std": [0.01, 0.02, 1.0e6, float("nan")],
        }
    )
    outlier = replicates.noise_floor(frame, ("x",))["x"]
    assert outlier.n_groups == 3
    assert outlier.median_rel_std == pytest.approx(0.02)
    assert outlier.median_abs_std == pytest.approx(0.02)


def test_readme_triple_mask_uses_registry_ranges(synthetic_root: Path) -> None:
    """The triple mask reads its bounds from the loaded registry, not from a literal."""
    rows, _ = _loaded(synthetic_root)
    assert len(rows) == 12
    reg = registry.load_registry()
    assert int(filters.readme_triple_mask(rows, reg).sum()) == 8

    widened_eps = dataclasses.replace(
        reg.properties["dielectric_const_dc"], physical_range=(1.0, 30.0)
    )
    widened = dataclasses.replace(
        reg, properties={**reg.properties, "dielectric_const_dc": widened_eps}
    )
    assert int(filters.readme_triple_mask(rows, widened).sum()) == 9


def test_noise_floor_on_readme_triple_rows_filters_then_groups(synthetic_root: Path) -> None:
    """F-56 / F-61: filter rows to the triple population first, then group by candidate."""
    rows, _ = _loaded(synthetic_root)
    reg = registry.load_registry()
    floors = replicates.noise_floor_on_rows(rows, filters.readme_triple_mask(rows, reg), TRIPLE)
    assert set(floors) == set(TRIPLE)
    for column in TRIPLE:
        assert floors[column].n_groups == 2, column


def test_same_version_split_uses_only_present_version_columns(synthetic_root: Path) -> None:
    """F-52: the split uses the version columns present; the fixture has only RadonPy_ver."""
    rows, candidates = _loaded(synthetic_root)
    present = [column for column in replicates.VERSION_COLUMNS if column in rows.columns]
    assert present == ["RadonPy_ver"]
    assert replicates.same_version_split(rows, candidates) == (2, 0)


def test_d9_report_states_noise_floor_per_property_with_population(
    synthetic_root: Path, tmp_path: Path
) -> None:
    """D-9: the report states the noise floor per property, each table naming its population."""
    load.load(synthetic_root)
    report_path = tmp_path / "report.md"
    assert validate.run(synthetic_root, expected={}, report_path=report_path) == 0
    text = report_path.read_text(encoding="utf-8")
    assert "## Replicate structure and noise floor" in text
    for line in (
        "| candidates | in-scope rows | 9 |",
        "| multi-row candidates | in-scope rows | 2 |",
        "| rows in multi-row candidates | in-scope rows | 5 |",
        "| max rows per candidate | in-scope rows | 3 |",
        "| rows per candidate = 1 | candidates | 7 |",
        "| rows per candidate = 3 | candidates | 1 |",
        "| same-version replicate candidates | multi-row candidates | 2 |",
        "| cross-version re-run candidates | multi-row candidates | 0 |",
    ):
        assert line in text, line

    noise_tables = [rows for header, rows in _markdown_tables(text) if header == NOISE_HEADER]
    assert len(noise_tables) == 2
    all_rows, triple_rows = noise_tables
    assert [row[0] for row in all_rows] == list(registry.load_registry().properties)
    assert all(row[1] == NOISE_ALL for row in all_rows), all_rows
    tc = next(row for row in all_rows if row[0] == "thermal_conductivity")
    assert tc[2] == "2"
    assert [row[0] for row in triple_rows] == list(TRIPLE)
    assert all(row[1] == NOISE_TRIPLE for row in triple_rows), triple_rows


def _findings(stdout: str) -> dict[str, tuple[str, str, str, str]]:
    """``finding <id>: <class> expected=<e> observed=<o> <status>`` -> id -> fields."""
    pattern = re.compile(r"^finding (\S+): (\S+) expected=(\S+) observed=(\S+) (\S+)$")
    found: dict[str, tuple[str, str, str, str]] = {}
    for line in stdout.splitlines():
        match = pattern.match(line)
        if match:
            found[match.group(1)] = (match.group(2), match.group(3), match.group(4), match.group(5))
    return found


def test_real_replicate_structure_and_noise_floor_match_research(
    real_load: LoadResult, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """F-50, F-52, F-55, F-56 on the pinned file (skips without it, D-09)."""
    code = validate.run(
        REPO_ROOT, processed_dir=real_load.processed_dir, report_path=tmp_path / "report.md"
    )
    findings = _findings(capsys.readouterr().out)
    assert code == 0, findings
    expected = {
        "replicate_multi_row_candidates": ("reproduce", "12,983", "reproduced"),
        "replicate_max_rows": ("reproduce", "17", "reproduced"),
        "noise_floor_rel_thermal_conductivity": ("documented", "0.0369", "documented"),
        "noise_floor_rel_dielectric_const_dc": ("documented", "0.0084", "documented"),
        "noise_floor_rel_tg": ("documented", "0.0577", "documented"),
        "noise_floor_abs_tg": ("documented", "30.2000", "documented"),
        "noise_floor_rel_density": ("documented", "0.0034", "documented"),
        "noise_floor_triple_rel_thermal_conductivity": ("documented", "0.0431", "documented"),
        "noise_floor_triple_rel_dielectric_const_dc": ("documented", "0.0112", "documented"),
        "noise_floor_triple_rel_tg": ("documented", "0.0540", "documented"),
        "same_version_replicate_candidates": ("documented", "1,888", "documented"),
        "cross_version_rerun_candidates": ("documented", "11,096", "documented"),
    }
    for finding_id, (cls, expected_value, status) in expected.items():
        assert finding_id in findings, finding_id
        observed_cls, observed_expected, _, observed_status = findings[finding_id]
        assert (observed_cls, observed_expected, observed_status) == (
            cls,
            expected_value,
            status,
        ), (finding_id, findings[finding_id])
