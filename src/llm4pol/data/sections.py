"""The README-number sections of the validator report (plan 02-05, charter section 13 M1 (2)-(3)).

Coverage per registry property, physical-range filter counts, the dielectric
identity and Maxwell check, and the README triple ladder. Every count is a pure
function of the frames and the registry in ``filters.py``; this module names
populations (D-10) and renders tables. The ladder table is built after the
findings are evaluated so each step can show its expected value and status.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from llm4pol.data import filters
from llm4pol.data.expectations import (
    ALL_SOURCE_ROWS,
    DIELECTRIC_ROWS,
    SPEARMAN_PAIRS,
    TC_TG_ROWS,
    TRIPLE_ALL_ROWS,
    population_of,
)
from llm4pol.data.registry import Registry
from llm4pol.data.report import (
    CountTable,
    Finding,
    Section,
    Value,
    format_finding_values,
    format_float,
    format_int,
    format_value,
)

QUANTITY_HEADER = ("quantity", "population", "value")

_COVERAGE_INTRO = (
    "Non-null rows per registry property on all source rows (charter section 6 order), and "
    "rows per tacticity label with a missing value as `unknown` (F-38)."
)

_RANGE_INTRO = (
    "Rows inside, outside and missing each registry property's `physical_range` on all source "
    "rows. Only the `dielectric_const_dc` and `tg` ranges enter the README ladder below; the "
    "others are reported, not applied (F-67)."
)

_DIELECTRIC_INTRO = (
    "The uncorrected static permittivity column `static_dielectric_const` is the orientational "
    "permittivity of a non-polarisable force field; `dielectric_const_dc` adds the electronic "
    "part `n^2 - 1` and is what the paper calls the corrected static dielectric constant "
    "(arXiv:2511.11626 Table S3): `dielectric_const_dc = static_dielectric_const - 1 + refractive_index^2` holds "
    "on every row carrying the three columns (F-14). Because `static_dielectric_const >= 1` on "
    "every row (F-15), `dielectric_const_dc >= refractive_index^2` follows algebraically: the "
    "zero Maxwell violations of `dielectric_const_dc` are the identity, not an independent "
    "physics check. The README's Maxwell-violation share of the uncorrected column is pinned "
    "at its observed value with the README's rounded figure in the finding note (F-13); the "
    "README's rank correlation of that column with `n^2` did not reproduce (F-17). A-7 stands: "
    "the registry serves `dielectric_const_dc` only. ADR-0004's consequence stands while its "
    '"broken column" wording is superseded by this section (R-3).'
)

_LADDER_INTRO = (
    "The README's 43,561 is exactly `thermal_conductivity` non-null and `dielectric_const_dc` "
    "and `tg` inside their registry physical ranges, on all source rows, a filter the README "
    "never stated (F-08); `tg_rmse` plays no part in it (F-09). Three triple counts exist and "
    "are all printed: on all source rows, on the in-scope rows (the cellulose second-monomer "
    "row is excluded, D-03) and at candidate level after grouping, filter then median (F-61; "
    "the other order is printed as the alternative, not used). `check_tc == True` is a "
    "protocol quality filter absent from the README (F-59): its count stands beside the "
    "reproduction and which population the evaluator serves is a Phase 3 decision (R-2). "
    "The naive `dielectric_const_dc` filters the README could have meant are printed and "
    "not used. The rank correlations and the README window (top-decile thermal conductivity "
    "and bottom-quartile `dielectric_const_dc`) are confirmations (F-11, F-12)."
)



def pct(value: float) -> str:
    return f"{value:.2f} %"


def unit_label(unit: str) -> str:
    """A registry unit for display: `*` becomes `·` so the aggregates-only grep for
    SMILES-like tokens (`*` followed by a letter, charter section 10) stays at zero."""
    return unit.replace("*", "·")



def coverage_section(source: Any, registry: Registry) -> tuple[Section, dict[str, Value]]:
    observed: dict[str, Value] = {}
    coverage_rows: list[tuple[str, ...]] = []
    total = len(source)
    for column, count in filters.coverage(source, registry).items():
        key = registry.spec_for_column(column).key
        observed[f"coverage_{column}"] = count
        share = pct(100.0 * count / total) if total else pct(0.0)
        coverage_rows.append((key, ALL_SOURCE_ROWS, format_int(count), share))
    tacticity_rows: list[tuple[str, ...]] = []
    for label, count in filters.tacticity_counts(source).items():
        observed[f"tacticity_{label}"] = count
        tacticity_rows.append((label, ALL_SOURCE_ROWS, format_int(count)))
    flag_rows: list[tuple[str, ...]] = []
    for label, count in filters.check_tc_counts(source).items():
        observed[f"check_tc_{label.lower()}"] = count
        flag_rows.append((f"check_tc == {label}", ALL_SOURCE_ROWS, format_int(count)))
    section = Section(
        title="Coverage per registry property",
        intro=_COVERAGE_INTRO,
        tables=[
            CountTable(
                title="Coverage",
                header=("property", "population", "non-null", "share"),
                rows=coverage_rows,
            ),
            CountTable(
                title="Tacticity", header=("tacticity", "population", "rows"), rows=tacticity_rows
            ),
            CountTable(title="check_tc flag", header=QUANTITY_HEADER, rows=flag_rows),
        ],
    )
    return section, observed


def physical_range_section(source: Any, registry: Registry) -> tuple[Section, dict[str, Value]]:
    observed: dict[str, Value] = {}
    table_rows: list[tuple[str, ...]] = []
    for column, (inside, outside, missing) in filters.physical_range_counts(
        source, registry
    ).items():
        spec = registry.spec_for_column(column)
        low, high = spec.physical_range
        observed[f"range_outside_{column}"] = outside
        table_rows.append(
            (
                spec.key,
                ALL_SOURCE_ROWS,
                f"[{low}, {high}] {unit_label(spec.unit)}",
                format_int(inside),
                format_int(outside),
                format_int(missing),
            )
        )
    eps_column = registry.properties["dielectric_const_dc"].column
    observed["eps_outside_physical_range"] = observed[f"range_outside_{eps_column}"]
    section = Section(
        title="Physical-range filter counts",
        intro=_RANGE_INTRO,
        tables=[
            CountTable(
                title="Physical ranges",
                header=("property", "population", "range", "inside", "outside", "missing"),
                rows=table_rows,
            )
        ],
    )
    return section, observed


def dielectric_section(source: Any, registry: Registry) -> tuple[Section, dict[str, Value]]:
    n_squared = filters.N_SQUARED
    frame = filters.with_n_squared(source, registry)
    eps_column = registry.properties["dielectric_const_dc"].column
    dielectric = frame[eps_column].notna() & frame[n_squared].notna()
    triple = filters.readme_triple_mask(frame, registry)
    residual = filters.dielectric_identity_residual(frame, registry)
    violations_all, size_all, pct_all = filters.static_maxwell_violation_share(
        frame, dielectric, registry
    )
    violations_triple, size_triple, pct_triple = filters.static_maxwell_violation_share(
        frame, triple, registry
    )
    correlations = {
        "spearman_static_vs_n2_all": (filters.STATIC_COLUMN, n_squared, dielectric),
        "spearman_eps_vs_n2_all": (eps_column, n_squared, dielectric),
        "spearman_static_vs_n2_triple": (filters.STATIC_COLUMN, n_squared, triple),
        "spearman_eps_vs_n2_triple": (eps_column, n_squared, triple),
    }
    observed: dict[str, Value] = {
        "dc_identity_max_residual": float(residual.max()),
        "dc_identity_median_residual": float(residual.median()),
        "static_minimum": filters.static_minimum(frame),
        "static_maxwell_violations_all": violations_all,
        "static_maxwell_violations_triple": violations_triple,
        "static_maxwell_violation_pct_all": pct_all,
        "static_maxwell_violation_pct_triple": pct_triple,
        "dc_maxwell_violations": filters.dc_maxwell_violations(frame, dielectric, registry),
    }
    for finding_id, (left, right, mask) in correlations.items():
        observed[finding_id] = filters.spearman_table(frame, mask, [(left, right)])[0][2]
    identity = CountTable(
        title="Identity and static minimum",
        header=QUANTITY_HEADER,
        rows=[
            ("rows with the three columns", DIELECTRIC_ROWS, format_int(len(residual))),
            (
                "identity max residual",
                DIELECTRIC_ROWS,
                format_value(observed["dc_identity_max_residual"]),
            ),
            (
                "identity median residual",
                DIELECTRIC_ROWS,
                format_value(observed["dc_identity_median_residual"]),
            ),
            (
                f"{filters.STATIC_COLUMN} minimum",
                DIELECTRIC_ROWS,
                format_float(float(observed["static_minimum"]), 5),
            ),
            (
                "dielectric_const_dc < n^2 (algebraically 0)",
                DIELECTRIC_ROWS,
                format_value(observed["dc_maxwell_violations"]),
            ),
        ],
    )
    maxwell = CountTable(
        title="Maxwell violation of the uncorrected column (static < n^2)",
        header=("quantity", "population", "violations", "rows", "share"),
        rows=[
            (
                f"{filters.STATIC_COLUMN} < n^2",
                TRIPLE_ALL_ROWS,
                format_int(violations_triple),
                format_int(size_triple),
                pct(pct_triple),
            ),
            (
                f"{filters.STATIC_COLUMN} < n^2",
                DIELECTRIC_ROWS,
                format_int(violations_all),
                format_int(size_all),
                pct(pct_all),
            ),
        ],
    )
    spearman = CountTable(
        title="Rank correlation with n^2",
        header=("pair", "population", "spearman"),
        rows=[
            (
                f"{left} vs n^2",
                population_of(finding_id),
                format_float(float(observed[finding_id]), 3),
            )
            for finding_id, (left, _, _) in correlations.items()
        ],
    )
    section = Section(
        title="Dielectric columns: identity and Maxwell check",
        intro=_DIELECTRIC_INTRO,
        tables=[identity, maxwell, spearman],
    )
    return section, observed



LadderStep = tuple[str, str]  # (label, finding id)


def ladder_observed(
    source: Any, rows: Any, registry: Registry
) -> tuple[dict[str, Value], list[LadderStep]]:
    ladder = filters.readme_triple_ladder(source, registry)
    step_ids = (
        "readme_ladder_all_rows",
        "readme_ladder_tc_non_null",
        "readme_ladder_eps_non_null",
        "readme_ladder_eps_in_range",
        "readme_triple_all_rows",
    )
    observed: dict[str, Value] = {}
    steps: list[LadderStep] = []
    for (label, count), finding_id in zip(ladder, step_ids, strict=True):
        observed[finding_id] = count
        steps.append((label, finding_id))
    triple_all = filters.readme_triple_mask(source, registry)
    triple_scope = filters.readme_triple_mask(rows, registry)
    observed["readme_triple_in_scope"] = int(triple_scope.sum())
    observed["triple_check_tc_all_rows"] = int(
        (triple_all & filters.check_tc_mask(source, registry)).sum()
    )
    observed["triple_check_tc_in_scope"] = int(
        (triple_scope & filters.check_tc_mask(rows, registry)).sum()
    )
    observed["candidate_triple_filter_then_median"] = len(filters.candidate_level_triple(rows, registry))
    observed["candidate_triple_median_then_filter"] = len(filters.candidate_level_triple(rows, registry, order=filters.MEDIAN_THEN_FILTER))
    steps.extend(
        [
            ("in-scope subset", "readme_triple_in_scope"),
            ("∧ check_tc == True (protocol filter, not in the README)", "triple_check_tc_all_rows"),
            ("in-scope ∧ check_tc", "triple_check_tc_in_scope"),
            ("candidates (filter then median)", "candidate_triple_filter_then_median"),
            (
                "candidates (median then filter; alternative, not used)",
                "candidate_triple_median_then_filter",
            ),
        ]
    )
    alternative_ids = (
        "eps_alternative_non_null_only",
        "eps_alternative_le_10",
        "eps_alternative_le_50",
        "eps_alternative_le_100",
    )
    for (label, count), finding_id in zip(
        filters.alternative_eps_filters(source, registry), alternative_ids, strict=True
    ):
        observed[finding_id] = count
        observed[f"{finding_id}_label"] = label
    pairs = [
        (registry.properties[left].column, registry.properties[right].column)
        for _, left, right in SPEARMAN_PAIRS
    ]
    for (finding_id, _, _), (_, _, value) in zip(
        SPEARMAN_PAIRS, filters.spearman_table(source, triple_all, pairs), strict=True
    ):
        observed[finding_id] = value
    window_rows, window_pct = filters.readme_window(source, triple_all, registry)
    observed["readme_window_rows"] = window_rows
    observed["readme_window_pct"] = window_pct
    return observed, steps


def ladder_section(
    observed: Mapping[str, Value],
    steps: list[LadderStep],
    findings: Mapping[str, Finding],
    registry: Registry,
) -> Section:
    ladder_rows: list[tuple[str, ...]] = []
    for label, finding_id in steps:
        finding = findings.get(finding_id)
        expected = "—" if finding is None else format_finding_values(finding)[0]
        status = "—" if finding is None else finding.status
        ladder_rows.append(
            (
                label,
                population_of(finding_id),
                format_value(observed[finding_id]),
                expected,
                status,
            )
        )
    alternatives = CountTable(
        title="Alternative dielectric_const_dc filters (printed, not used)",
        header=("filter", "population", "rows"),
        rows=[
            (str(observed[f"{finding_id}_label"]), TC_TG_ROWS, format_value(observed[finding_id]))
            for finding_id in (
                "eps_alternative_non_null_only",
                "eps_alternative_le_10",
                "eps_alternative_le_50",
                "eps_alternative_le_100",
            )
        ],
    )
    spearman_rows: list[tuple[str, ...]] = [
        (
            f"{registry.properties[left].column} vs {registry.properties[right].column}",
            TRIPLE_ALL_ROWS,
            format_float(float(observed[finding_id]), 3),
        )
        for finding_id, left, right in SPEARMAN_PAIRS
    ]
    window = CountTable(
        title="README window (top-decile thermal_conductivity, bottom-quartile dielectric_const_dc)",
        header=QUANTITY_HEADER,
        rows=[
            ("window rows", TRIPLE_ALL_ROWS, format_value(observed["readme_window_rows"])),
            ("window share", TRIPLE_ALL_ROWS, pct(float(observed["readme_window_pct"]))),
        ],
    )
    return Section(
        title="README triple ladder",
        intro=_LADDER_INTRO,
        tables=[
            CountTable(
                title="Ladder",
                header=("step", "population", "rows", "expected", "status"),
                rows=ladder_rows,
            ),
            alternatives,
            CountTable(
                title="Rank correlations",
                header=("pair", "population", "spearman"),
                rows=spearman_rows,
            ),
            window,
        ],
    )
