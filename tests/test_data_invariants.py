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

import ast
import dataclasses
import re
import tomllib
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from conftest import REPO_ROOT
from llm4pol.data import filters, load, registry, replicates, report, snapshot, validate
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
    assert len(tables) >= 12, f"the report has only {len(tables)} tables"
    _assert_every_table_names_its_population(tables)

    # The committed number authority obeys the same rule once it exists (plan 02-05).
    committed = snapshot.report_path(REPO_ROOT)
    if committed.is_file():
        _assert_every_table_names_its_population(
            _markdown_tables(committed.read_text(encoding="utf-8"))
        )

    with pytest.raises(ValueError, match="population"):
        report.CountTable(title="x", header=("quantity", "value"), rows=[])


def _assert_every_table_names_its_population(
    tables: list[tuple[list[str], list[list[str]]]],
) -> None:
    for header, rows in tables:
        assert "population" in header, header
        column = header.index("population")
        for row in rows:
            assert row[column], f"empty population cell in row {row}"


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


# --- Plan 02-05: the README numbers (D-07, R-1, R-3, R-5, DATA-06) -------------------


def _source_rows(synthetic_root: Path) -> Any:
    return load.read_source(snapshot.csv_path(synthetic_root))


def test_readme_ladder_counts_on_synthetic(synthetic_root: Path) -> None:
    """F-08: the README triple is a ladder of named steps on all source rows."""
    source = _source_rows(synthetic_root)
    rows, _ = _loaded(synthetic_root)
    reg = registry.load_registry()

    ladder = filters.readme_triple_ladder(source, reg)
    assert [label for label, _ in ladder] == [
        "all rows",
        "thermal_conductivity non-null",
        "∧ dielectric_const_dc non-null",
        "∧ dielectric_const_dc in [1.0, 20.0]",
        "∧ tg in [100.0, 900.0] K",
    ]
    assert [count for _, count in ladder] == [14, 13, 13, 12, 10]

    triple = filters.readme_triple_mask(rows, reg)
    assert int(triple.sum()) == 8
    assert int((triple & filters.check_tc_mask(rows, reg)).sum()) == 8

    # F-61: filter rows then median per candidate is the order the report uses.
    assert len(filters.candidate_level_triple(rows, reg)) == 5
    assert len(filters.candidate_level_triple(rows, reg, order="median_then_filter")) == 5
    with pytest.raises(ValueError, match="order"):
        filters.candidate_level_triple(rows, reg, order="sideways")


def test_alternative_eps_filters_are_printed_not_used(synthetic_root: Path) -> None:
    """F-08: the naive eps_dc filters are printed beside the ladder, never applied."""
    source = _source_rows(synthetic_root)
    reg = registry.load_registry()
    alternatives = filters.alternative_eps_filters(source, reg)
    assert [label for label, _ in alternatives] == [
        "dielectric_const_dc non-null only",
        "dielectric_const_dc <= 10",
        "dielectric_const_dc <= 50",
        "dielectric_const_dc <= 100",
    ]
    assert [count for _, count in alternatives] == [11, 10, 11, 11]


@pytest.mark.parametrize("population", ["synthetic", "real"])
def test_maxwell_identity_holds_on_dielectric_rows(
    population: str, synthetic_root: Path, request: pytest.FixtureRequest
) -> None:
    """F-14 / F-15: eps_dc = static - 1 + n^2 and static >= 1, so eps_dc >= n^2 is algebra."""
    reg = registry.load_registry()
    if population == "synthetic":
        rows, _ = _loaded(synthetic_root)
        residual_bound, static_floor = 1e-9, 1.05
    else:
        result: LoadResult = request.getfixturevalue("real_load")
        rows = pd.read_parquet(result.rows_parquet)
        residual_bound, static_floor = 1e-5, 1.00016
    residual = filters.dielectric_identity_residual(rows, reg)
    assert float(residual.max()) < residual_bound
    assert filters.static_minimum(rows) >= 1.0
    assert filters.static_minimum(rows) == pytest.approx(static_floor, abs=1e-4)
    everywhere = pd.Series(True, index=rows.index)
    assert filters.dc_maxwell_violations(rows, everywhere, reg) == 0
    if population == "synthetic":
        source = _source_rows(synthetic_root)
        triple = filters.readme_triple_mask(source, reg)
        violations, size, pct = filters.static_maxwell_violation_share(source, triple, reg)
        assert (violations, size, pct) == (10, 10, 100.0)


def test_multi_tacticity_counts_on_synthetic(synthetic_root: Path) -> None:
    """F-39 / F-48: NaN tacticity is `unknown`, never a dropped group key (R-1 prints both)."""
    source = _source_rows(synthetic_root)
    rows, _ = _loaded(synthetic_root)
    by_smiles = filters.multi_tacticity_counts(source)
    assert by_smiles.with_unknown == 2
    assert by_smiles.without_unknown == 1
    assert by_smiles.unknown_twins == 1
    by_canonical = filters.multi_tacticity_counts_canonical(rows)
    assert by_canonical.with_unknown == 2
    assert by_canonical.without_unknown == 1
    assert filters.raw_string_merges(rows) == 1


def test_card_count_73045_matches_no_column_on_synthetic(synthetic_root: Path) -> None:
    """F-19: no column reproduces the dataset card's 73,045; the candidates are printed."""
    source = _source_rows(synthetic_root)
    rows, _ = _loaded(synthetic_root)
    counts = filters.card_count_candidates(source, rows)
    assert counts == {
        "unique smiles_list": 10,
        "unique canonical_psmiles (in scope)": 7,
        "unique UUID": 14,
        "source rows": 14,
    }
    assert filters.CARD_COUNT not in counts.values()
    assert filters.CARD_COUNT == 73045


def test_findings_documented_class_uses_tolerance_and_reproduce_is_exact() -> None:
    """R-5: `reproduce` is exact; `documented` pins the observed value within a tolerance."""
    population = "x"
    reproduce = report.Expected("reproduce", 43561)
    assert report.evaluate_finding("a", reproduce, 43561, population).status == "reproduced"
    assert report.evaluate_finding("a", reproduce, 43560, population).status == "FAILED"

    rounded = report.Expected("documented", 88.9, tolerance=0.05, note="README rounds")
    assert report.evaluate_finding("b", rounded, 88.83, population).status == "FAILED"
    pinned = report.Expected("documented", 88.83, tolerance=0.05, note="README states 88.9 %")
    assert report.evaluate_finding("b", pinned, 88.83, population).status == "documented"
    assert report.evaluate_finding("b", pinned, 88.75, population).status == "FAILED"

    text = report.Expected("documented", "not reproducible from any column")
    assert report.evaluate_finding("c", text, "no column equals 73,045", population).status == (
        "documented"
    )
    missing = report.evaluate_finding("c", text, None, population)
    assert missing.status == "MISSING"
    assert report.exit_code([missing]) == 1
    assert report.exit_code([report.evaluate_finding("a", reproduce, 43561, population)]) == 0


# --- Plan 02-05: Tg ladder, feasible set as a D-16 input, D-8 / A-7 (D-07, D-08, DATA-08..10)


REPORT_HEADINGS: tuple[str, ...] = (
    "## Fetch identity",
    "## Source shape",
    "## Scope exclusions and identity",
    "## Coverage per registry property",
    "## Physical-range filter counts",
    "## Dielectric columns: identity and Maxwell check",
    "## README triple ladder",
    "## Tg window and tg_rmse ladder",
    "## Replicate structure and noise floor",
    "## Feasible set under the development defaults (input to the D-16 gate)",
    "## Findings",
)
DATA_09_FLAG = (
    'Wording discrepancy raised for the owner: REQUIREMENTS.md DATA-09 reads "filtered by tg_rmse"'
)
CANDIDATE_TRIPLE = "candidate-level README triple (filter then median)"
SMILES_LIKE = re.compile(r"\*[A-Za-z]")


def _sections(text: str) -> dict[str, str]:
    """``## heading`` -> body text, in report order."""
    sections: dict[str, str] = {}
    current = "preamble"
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:]
            sections[current] = ""
        else:
            sections[current] = sections.get(current, "") + line + "\n"
    return sections


def _synthetic_report(synthetic_root: Path, tmp_path: Path) -> str:
    load.load(synthetic_root)
    report_path = tmp_path / "report.md"
    assert validate.run(synthetic_root, expected={}, report_path=report_path) == 0
    return report_path.read_text(encoding="utf-8")


def test_tg_window_and_tg_rmse_ladder_on_synthetic(synthetic_root: Path, tmp_path: Path) -> None:
    """DATA-09 / R-2: the window and the ladder are counted at every rung; no cut is applied."""
    source = _source_rows(synthetic_root)
    rows, _ = _loaded(synthetic_root)
    reg = registry.load_registry()
    assert filters.tg_window_counts(source, reg) == (13, 12, 1)

    triple = filters.readme_triple_mask(rows, reg)
    assert filters.tg_rmse_ladder_counts(rows, triple, reg) == [
        (0.05, 5),
        (0.1, 7),
        (0.2, 8),
        (0.5, 8),
        (1.0, 8),
    ]
    replaced_tg = dataclasses.replace(reg.properties["tg"], tg_rmse_ladder=(0.06,))
    replaced = dataclasses.replace(reg, properties={**reg.properties, "tg": replaced_tg})
    assert filters.tg_rmse_ladder_counts(rows, triple, replaced) == [(0.06, 6)]

    descriptives = filters.tg_rmse_descriptives(source)
    assert set(descriptives) == {"median", "p95", "p99", "max"}
    assert descriptives["max"] == 5.0

    text = _synthetic_report(synthetic_root, tmp_path)
    tg_section = _sections(text)["Tg window and tg_rmse ladder"]
    assert DATA_09_FLAG in tg_section
    assert "| tg_rmse <= 0.1 | in-scope README-triple rows | 7 |" in tg_section
    assert "| tg outside [100.0, 900.0] K | all source rows | 1 |" in tg_section


def test_feasible_set_on_synthetic_is_labelled_as_d16_input(
    synthetic_root: Path, tmp_path: Path
) -> None:
    """DATA-08 / ADR-0005: the feasible set is reported as an input to the D-16 gate."""
    rows, _ = _loaded(synthetic_root)
    reg = registry.load_registry()
    assert filters.DEV_DEFAULT_TG_MIN_K == 400.0
    assert filters.DEV_DEFAULT_EPS_QUANTILE == 0.25
    candidates = filters.candidate_level_triple(rows, reg)
    assert filters.feasible_set(candidates, reg) == filters.FeasibleSet(
        q25_eps=2.25, tg_min_k=400.0, n_feasible=2, n_population=5, pct=40.0
    )
    triple = filters.readme_triple_mask(rows, reg)
    assert filters.feasible_rows(rows, triple, reg, q25_eps=2.25, tg_min_k=400.0) == 2

    text = _synthetic_report(synthetic_root, tmp_path)
    section = _sections(text)[
        "Feasible set under the development defaults (input to the D-16 gate)"
    ]
    assert "input to the D-16 gate" in section
    assert "development default" in section
    assert (
        "| feasible candidates (eps_dc_median <= Q25 and tg_median >= 400.0 K) | "
        f"{CANDIDATE_TRIPLE} | 2 |"
    ) in section
    assert f"Q25 of dielectric_const_dc candidate medians | {CANDIDATE_TRIPLE} | 2.2500" in section
    assert "threshold =" not in section


SPLIT_IDENTIFIERS = ("train_test_split", "KFold", "model_selection", "ShuffleSplit")


def _identifiers(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def test_d8_no_row_level_split_code_under_llm4pol_data() -> None:
    """D-8: no splitter is imported or named under llm4pol.data; the import-linter contract stays."""
    package = REPO_ROOT / "src" / "llm4pol" / "data"
    modules = sorted(package.glob("*.py"))
    assert modules
    for module in modules:
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("sklearn"), (module.name, alias.name)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("sklearn"), (module.name, node.module)
        for identifier in _identifiers(tree):
            assert not any(token in identifier for token in SPLIT_IDENTIFIERS), (
                module.name,
                identifier,
            )

    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        contracts = tomllib.load(handle)["tool"]["importlinter"]["contracts"]
    data_contracts = [c for c in contracts if c.get("source_modules") == ["llm4pol.data"]]
    assert len(data_contracts) == 1
    assert "sklearn" in data_contracts[0]["forbidden_modules"]


def test_a7_validator_and_loader_never_serve_static_dielectric_const(
    synthetic_root: Path, tmp_path: Path
) -> None:
    """A-7: the barred column is data for the identity, never a served property."""
    barred = "static_" + "dielectric_const"
    assert barred not in PROPERTY_COLUMNS
    assert barred not in registry.load_registry().columns()
    rows, _ = _loaded(synthetic_root)
    assert barred in rows.columns, "F-14 needs the column as data"

    text = _synthetic_report(synthetic_root, tmp_path)
    for header, table_rows in _markdown_tables(text):
        if header[0] == "property":
            assert barred not in [row[0] for row in table_rows], header
    for title, body in _sections(text).items():
        if title == "Dielectric columns: identity and Maxwell check":
            continue
        for line in body.splitlines():
            if barred in line:
                assert title == "Findings" and line.startswith("| static_"), (title, line)


def test_synthetic_report_has_every_section_in_order(synthetic_root: Path, tmp_path: Path) -> None:
    """D-07: the eleven sections in order; aggregates only even on the synthetic root."""
    text = _synthetic_report(synthetic_root, tmp_path)
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == list(REPORT_HEADINGS)
    offending = [line for line in text.splitlines() if SMILES_LIKE.search(line)]
    assert not offending, offending


# --- Plan 02-05: the committed number authority (D-07, charter section 10, T-02-24) ------

BARE_16_HEX = re.compile(r"(^|[^0-9a-f])[0-9a-f]{16}([^0-9a-f]|$)")
UUID_SHAPE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}")
MAX_CELL_CHARACTERS = 80


def test_committed_validator_report_exists_and_names_revision_and_sections() -> None:
    """The committed report is the number authority: complete, green and aggregates only."""
    committed = snapshot.report_path(REPO_ROOT)
    assert committed.is_file(), committed
    text = committed.read_text(encoding="utf-8")
    assert "041e5834ea1a48682fae12dc39ccd723bcd4f771" in text
    assert "polyomics:general_polymers@041e5834" in text
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == list(REPORT_HEADINGS)

    findings_header = ["finding", "population", "expected", "observed", "class", "status"]
    findings = [rows for header, rows in _markdown_tables(text) if header == findings_header]
    assert len(findings) == 1
    assert findings[0], "the findings table is empty"
    assert {row[5] for row in findings[0]} <= {"reproduced", "documented"}, findings[0]

    lines = text.splitlines()
    assert not [line for line in lines if SMILES_LIKE.search(line)]
    assert not [line for line in lines if BARE_16_HEX.search(line)]
    assert not [line for line in lines if UUID_SHAPE.search(line)]
    long_cells = [
        cell
        for _, rows in _markdown_tables(text)
        for row in rows
        for cell in row
        if len(cell) > MAX_CELL_CHARACTERS
    ]
    assert not long_cells, long_cells
