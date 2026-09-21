"""Replicate structure and the per-property noise floor on the candidate table.

CONTEXT D-04: rows sharing ``candidate_id`` are replicates; the noise floor
of a property is the median, over candidates with n >= 2, of the
within-candidate spread (``std`` with ddof=1 from ``load.build_candidates``),
both absolute and relative to the candidate median. D-7: everything here
reads the candidate table, never raw rows grouped ad hoc; the only path from
rows is ``noise_floor_on_rows``, which filters the rows first and then calls
``build_candidates`` (filter-then-group, RESEARCH F-56 / F-61). The aggregate
is the median because replicate groups hold ``check_tc == False`` outliers a
hundred times the median (F-57). Facts: F-50, F-52, F-55, F-56.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from llm4pol.data.filters import readme_triple_mask
from llm4pol.data.load import build_candidates
from llm4pol.data.registry import Registry
from llm4pol.data.report import CountTable, Section, format_float, format_int

# A candidate contributes to the floor when at least two rows carry the property (D-04).
MIN_REPLICATES = 2
# The upper tail reported beside the median because the Tg tail is heavy (Q3).
P90 = 0.9

# The workflow-version columns of the source file (F-52). Only those present
# in a frame are used, so the synthetic fixture (RadonPy_ver only) works.
VERSION_COLUMNS: tuple[str, ...] = (
    "RadonPy_ver",
    "preset_eq_ver",
    "preset_tc_ver",
    "preset_tg_ver",
    "preset_sp_ver",
    "RDKit_ver",
    "Psi4_ver",
    "Python_ver",
)

CANDIDATES = "candidates"
MULTI_ROW_CANDIDATES = "multi-row candidates"
NOISE_POPULATION_ALL = "candidates with n >= 2 (in-scope rows)"
NOISE_POPULATION_TRIPLE = "candidates with n >= 2 (README-triple rows)"
TRIPLE_COLUMNS: tuple[str, ...] = ("thermal_conductivity", "dielectric_const_dc", "tg")

NOISE_HEADER = (
    "property",
    "population",
    "n_groups",
    "median_abs_std",
    "median_rel_std",
    "p90_rel_std",
)


@dataclass(frozen=True)
class ReplicateStructure:
    """Rows per candidate, read off ``n_rows`` of the candidate table (F-50)."""

    n_candidates: int
    n_multi_row: int
    rows_in_multi_row: int
    max_rows: int
    size_histogram: dict[int, int]


@dataclass(frozen=True)
class NoiseFloor:
    """The within-candidate spread of one property over candidates with n >= 2 (F-55)."""

    property: str
    n_groups: int
    median_abs_std: float
    median_rel_std: float
    p90_rel_std: float


def _require_candidate_columns(candidates: Any, column: str) -> None:
    needed = [f"{column}_median", f"{column}_n", f"{column}_std"]
    missing = [name for name in needed if name not in candidates.columns]
    if missing:
        raise ValueError(
            f"noise_floor takes the candidate table (build_candidates output); "
            f"missing {', '.join(missing)}"
        )


def replicate_structure(candidates: Any) -> ReplicateStructure:
    """Rows per candidate from ``n_rows``; the histogram is printed, not pinned."""
    if "n_rows" not in candidates.columns:
        raise ValueError("replicate_structure takes the candidate table; missing n_rows")
    sizes = candidates["n_rows"].astype(int)
    multi = sizes[sizes >= MIN_REPLICATES]
    histogram = {int(size): int(count) for size, count in sizes.value_counts().sort_index().items()}
    return ReplicateStructure(
        n_candidates=int(len(sizes)),
        n_multi_row=int(len(multi)),
        rows_in_multi_row=int(multi.sum()),
        max_rows=int(sizes.max()) if len(sizes) else 0,
        size_histogram=histogram,
    )


def noise_floor(candidates: Any, columns: Iterable[str]) -> dict[str, NoiseFloor]:
    """Per column: median absolute and relative std, and its p90, over candidates with n >= 2.

    ``rel = std / |median|``; candidates whose median is zero are dropped from
    the relative series only. Values are builtin floats, NaN when no candidate
    qualifies.
    """
    floors: dict[str, NoiseFloor] = {}
    for column in columns:
        _require_candidate_columns(candidates, column)
        group = candidates[candidates[f"{column}_n"] >= MIN_REPLICATES]
        abs_std = group[f"{column}_std"].astype(float)
        scale = group[f"{column}_median"].astype(float).abs()
        rel_std = (abs_std / scale)[scale > 0]
        floors[column] = NoiseFloor(
            property=column,
            n_groups=int(len(group)),
            median_abs_std=float(abs_std.median()),
            median_rel_std=float(rel_std.median()),
            p90_rel_std=float(rel_std.quantile(P90)),
        )
    return floors


def noise_floor_on_rows(rows: Any, mask: Any, columns: Iterable[str]) -> dict[str, NoiseFloor]:
    """Filter ``rows`` by ``mask``, build the candidate table, then take the floor (F-61)."""
    return noise_floor(build_candidates(rows[mask]), columns)


def same_version_split(rows: Any, candidates: Any) -> tuple[int, int]:
    """``(same_version, cross_version)`` counts over multi-row candidates (F-52).

    A candidate is same-version when every present ``VERSION_COLUMNS`` value is
    identical across its rows (NaN counts as a value); otherwise cross-version.
    """
    present = [column for column in VERSION_COLUMNS if column in rows.columns]
    multi_ids = candidates.loc[candidates["n_rows"] >= MIN_REPLICATES, "candidate_id"]
    subset = rows.loc[rows["candidate_id"].isin(multi_ids), ["candidate_id", *present]]
    if subset.empty:
        return 0, 0
    distinct = subset.groupby("candidate_id", sort=False)[present].nunique(dropna=False)
    same = (distinct <= 1).all(axis=1)
    return int(same.sum()), int((~same).sum())


def _format_abs(value: float) -> str:
    return "—" if value != value else f"{value:.4g}"


def _format_rel(value: float) -> str:
    return "—" if value != value else format_float(value, 4)


def _noise_table(
    title: str, floors: dict[str, NoiseFloor], registry: Registry, population: str
) -> CountTable:
    rows: list[tuple[str, ...]] = [
        (
            registry.spec_for_column(column).key,
            population,
            format_int(floor.n_groups),
            _format_abs(floor.median_abs_std),
            _format_rel(floor.median_rel_std),
            _format_rel(floor.p90_rel_std),
        )
        for column, floor in floors.items()
    ]
    return CountTable(title=title, header=NOISE_HEADER, rows=rows)


def replicate_section(
    rows: Any, candidates: Any, registry: Registry, *, rows_population: str = "in-scope rows"
) -> tuple[Section, dict[str, float | int]]:
    """The report section and its findings: structure, floor on all rows, floor on the triple."""
    structure = replicate_structure(candidates)
    same, cross = same_version_split(rows, candidates)
    all_floors = noise_floor(candidates, registry.columns())
    triple_floors = noise_floor_on_rows(rows, readme_triple_mask(rows, registry), TRIPLE_COLUMNS)

    structure_rows: list[tuple[str, ...]] = [
        ("candidates", rows_population, format_int(structure.n_candidates)),
        ("multi-row candidates", rows_population, format_int(structure.n_multi_row)),
        ("rows in multi-row candidates", rows_population, format_int(structure.rows_in_multi_row)),
        ("max rows per candidate", rows_population, format_int(structure.max_rows)),
    ]
    structure_rows.extend(
        (f"rows per candidate = {size}", CANDIDATES, format_int(count))
        for size, count in structure.size_histogram.items()
    )
    structure_rows.append(("same-version replicate candidates", MULTI_ROW_CANDIDATES, format_int(same)))
    structure_rows.append(("cross-version re-run candidates", MULTI_ROW_CANDIDATES, format_int(cross)))

    section = Section(
        title="Replicate structure and noise floor",
        intro=(
            "Rows sharing `candidate_id` are replicates (D-7). Same-version candidates have "
            "identical workflow-version columns across their rows; cross-version candidates are "
            "re-runs under different RadonPy / preset versions (F-52). The noise floor of a "
            "property is the median over candidates with n >= 2 of the within-candidate std "
            "(ddof=1), absolute and relative to the candidate median, with the relative p90 "
            "(D-04, F-55); the median, not the mean, because replicate groups hold outlier runs "
            "(F-57). The README-triple population filters rows first, then groups (F-56, F-61). "
            "An effect smaller than this floor is not an effect (D-9)."
        ),
        tables=[
            CountTable(
                title="Replicate structure",
                header=("quantity", "population", "value"),
                rows=structure_rows,
            ),
            _noise_table("Noise floor, all in-scope rows", all_floors, registry, NOISE_POPULATION_ALL),
            _noise_table(
                "Noise floor, README-triple rows", triple_floors, registry, NOISE_POPULATION_TRIPLE
            ),
        ],
    )
    findings: dict[str, float | int] = {
        "replicate_multi_row_candidates": structure.n_multi_row,
        "replicate_max_rows": structure.max_rows,
        "same_version_replicate_candidates": same,
        "cross_version_rerun_candidates": cross,
        "noise_floor_abs_tg": all_floors[registry.properties["tg"].column].median_abs_std,
    }
    for column in registry.columns():
        key = registry.spec_for_column(column).key
        findings[f"noise_floor_rel_{key}"] = all_floors[column].median_rel_std
    for column in TRIPLE_COLUMNS:
        key = registry.spec_for_column(column).key
        findings[f"noise_floor_triple_rel_{key}"] = triple_floors[column].median_rel_std
    return section, findings
