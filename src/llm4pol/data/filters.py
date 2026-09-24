"""Row masks, ladders and shares defined by the loaded registry (CONTEXT D-05, D-07).

Every bound comes from a ``Registry`` object: this module carries no range
literal for any property (a number is published in one place, threat
T-02-20). The only numbers here are the alternative eps_dc ceilings the README
could have meant (F-08), the quantiles of the README window (F-12), the
algebra of the dielectric identity (F-14) and the dataset card's 73,045
(F-19), each cited where it is written. Every function is pure: it takes
frames and the registry and returns counts, masks or small frames; naming a
population and rendering it is ``validate.py``'s job (D-10).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from llm4pol.data.identity import UNKNOWN_TACTICITY, normalise_tacticity, observed_labels
from llm4pol.data.load import build_candidates
from llm4pol.data.registry import PropertySpec, Registry

# The README's triple: thermal conductivity present, dielectric constant and
# Tg inside their registry physical ranges (F-08 reproduces 43,561 on all rows).
TRIPLE_KEYS: tuple[str, str, str] = ("thermal_conductivity", "dielectric_const_dc", "tg")

# Source columns read beside the registry properties. The uncorrected static
# permittivity column is data the F-14 identity needs; it is never a registry
# property and never served as one (A-7, ADR-0004).
STATIC_COLUMN = "static_dielectric_const"
CHECK_TC_COLUMN = "check_tc"
SMILES_COLUMN = "smiles_list"
CANONICAL_COLUMN = "canonical_psmiles"
TACTICITY_COLUMN = "tacticity"
ROW_INDEX_COLUMN = "row_index"
UUID_COLUMN = "UUID"
MONOMER_ID_COLUMN = "monomer_ID"
N_SQUARED = "refractive_index_squared"

# F-08: the naive eps_dc ceilings the README could have meant; printed, never used.
ALTERNATIVE_EPS_CEILINGS: tuple[float, ...] = (10.0, 50.0, 100.0)
# F-12: the README window is top-decile TC and bottom-quartile eps_dc on the triple.
WINDOW_TC_QUANTILE = 0.9
WINDOW_EPS_QUANTILE = 0.25
# F-19: the dataset card's description text, reproduced by no column of the file.
CARD_COUNT = 73045

FILTER_THEN_MEDIAN = "filter_then_median"
MEDIAN_THEN_FILTER = "median_then_filter"
MEDIAN_SUFFIX = "_median"


def _triple_specs(registry: Registry) -> tuple[PropertySpec, PropertySpec, PropertySpec]:
    tc_key, eps_key, tg_key = TRIPLE_KEYS
    return registry.properties[tc_key], registry.properties[eps_key], registry.properties[tg_key]


def _refractive_index_column(registry: Registry) -> str:
    return registry.properties["refractive_index"].column


def within_physical_range(df: Any, spec: PropertySpec, *, suffix: str = "") -> Any:
    """Boolean mask: ``spec.column + suffix`` inside ``spec.physical_range`` (inclusive)."""
    low, high = spec.physical_range
    return df[spec.column + suffix].between(low, high, inclusive="both")


def readme_triple_mask(df: Any, registry: Registry, *, suffix: str = "") -> Any:
    """Boolean mask of the README-triple rows of ``df`` under ``registry``'s ranges.

    TC non-null AND dielectric_const_dc within its physical range AND tg within
    its physical range, both inclusive. ``suffix`` selects derived columns
    (``_median`` on a candidate table).
    """
    tc, eps, tg = _triple_specs(registry)
    return (
        df[tc.column + suffix].notna()
        & within_physical_range(df, eps, suffix=suffix)
        & within_physical_range(df, tg, suffix=suffix)
    )


def _range_label(spec: PropertySpec) -> str:
    low, high = spec.physical_range
    return f"[{low}, {high}]"


def readme_triple_ladder(source_rows: Any, registry: Registry) -> list[tuple[str, int]]:
    """The five cumulative steps from all rows to the README triple (F-08), labelled."""
    tc, eps, tg = _triple_specs(registry)
    all_rows = pd.Series(True, index=source_rows.index)
    step_tc = source_rows[tc.column].notna()
    step_eps_present = step_tc & source_rows[eps.column].notna()
    step_eps_range = step_tc & within_physical_range(source_rows, eps)
    step_tg_range = step_eps_range & within_physical_range(source_rows, tg)
    steps = [
        ("all rows", all_rows),
        (f"{tc.column} non-null", step_tc),
        (f"∧ {eps.column} non-null", step_eps_present),
        (f"∧ {eps.column} in {_range_label(eps)}", step_eps_range),
        (f"∧ {tg.column} in {_range_label(tg)} {tg.unit}", step_tg_range),
    ]
    return [(label, int(mask.sum())) for label, mask in steps]


def alternative_eps_filters(source_rows: Any, registry: Registry) -> list[tuple[str, int]]:
    """F-08's naive eps_dc filters, each with TC non-null and tg in range; printed, not used."""
    tc, eps, tg = _triple_specs(registry)
    base = source_rows[tc.column].notna() & within_physical_range(source_rows, tg)
    values = source_rows[eps.column]
    counts = [(f"{eps.column} non-null only", int((base & values.notna()).sum()))]
    counts.extend(
        (f"{eps.column} <= {ceiling:g}", int((base & (values <= ceiling)).sum()))
        for ceiling in ALTERNATIVE_EPS_CEILINGS
    )
    return counts


def check_tc_mask(df: Any, registry: Registry) -> Any:
    """Boolean mask of the rows the objective's ``check_tc`` filter keeps (F-59).

    ``PropertySpec.check_tc`` is the value to keep; a missing ``check_tc`` in
    the row never passes. When the objective carries no filter every row passes.
    """
    objectives = registry.by_role("objective")
    if len(objectives) != 1:
        raise ValueError(f"expected exactly one objective in the registry, got {len(objectives)}")
    keep = objectives[0].check_tc
    if keep is None:
        return pd.Series(True, index=df.index)
    return (df[CHECK_TC_COLUMN] == keep).fillna(False).astype(bool)


def check_tc_counts(source_rows: Any) -> dict[str, int]:
    """Rows with ``check_tc`` True, False and missing (F-59)."""
    flags = source_rows[CHECK_TC_COLUMN]
    return {
        "True": int((flags == True).fillna(False).sum()),
        "False": int((flags == False).fillna(False).sum()),
        "None": int(flags.isna().sum()),
    }


def candidate_level_triple(
    rows: Any, registry: Registry, *, order: str = FILTER_THEN_MEDIAN
) -> Any:
    """The candidate table of the README triple, in one of two orders (F-61).

    ``filter_then_median``: keep the triple rows, then one row per candidate --
    a candidate is in the table when it has at least one physical row per
    property (the order the report uses). ``median_then_filter``: build every
    candidate, then apply the triple to the ``_median`` columns.
    """
    if order == FILTER_THEN_MEDIAN:
        return build_candidates(rows[readme_triple_mask(rows, registry)])
    if order == MEDIAN_THEN_FILTER:
        candidates = build_candidates(rows)
        return candidates[readme_triple_mask(candidates, registry, suffix=MEDIAN_SUFFIX)]
    raise ValueError(
        f"order must be {FILTER_THEN_MEDIAN!r} or {MEDIAN_THEN_FILTER!r}, got {order!r}"
    )


@dataclass(frozen=True)
class MultiTacticity:
    """Repeat units that occur under more than one tacticity (F-39, R-1)."""

    with_unknown: int
    without_unknown: int
    unknown_twins: int


def _multi_tacticity(frame: Any, key_column: str) -> MultiTacticity:
    """Distinct-tacticity counts per ``key_column`` with NaN mapped to ``unknown`` (F-48)."""
    pairs = pd.DataFrame(
        {
            "key": frame[key_column].astype(object),
            "tac": [normalise_tacticity(value) for value in frame[TACTICITY_COLUMN].tolist()],
        }
    ).drop_duplicates()
    known = pairs[pairs["tac"] != UNKNOWN_TACTICITY]
    with_unknown = int((pairs.groupby("key")["tac"].nunique() > 1).sum())
    without_unknown = int((known.groupby("key")["tac"].nunique() > 1).sum())
    keys_with_unknown = set(pairs.loc[pairs["tac"] == UNKNOWN_TACTICITY, "key"])
    unknown_twins = len(keys_with_unknown & set(known["key"]))
    return MultiTacticity(with_unknown, without_unknown, unknown_twins)


def multi_tacticity_counts(source_rows: Any) -> MultiTacticity:
    """By raw ``smiles_list`` on the source rows (F-39: 303 with unknown, 2 without)."""
    return _multi_tacticity(source_rows, SMILES_COLUMN)


def multi_tacticity_counts_canonical(rows: Any) -> MultiTacticity:
    """By ``canonical_psmiles`` on the in-scope rows (R-1: printed beside the raw count)."""
    return _multi_tacticity(rows, CANONICAL_COLUMN)


@dataclass(frozen=True)
class TacticityResolution:
    """How the ADR-0006 rule disposed of the in-scope rows whose source tacticity was empty."""

    empty_rows: int
    resolved: dict[str, int]
    unresolved: int
    multi_label_canonical: int


def tacticity_resolution_counts(source_rows: Any, rows: Any) -> TacticityResolution:
    """Count the ADR-0006 outcome of every in-scope row whose SOURCE tacticity was empty.

    ``rows`` is the in-scope frame; its ``row_index`` positionally indexes
    ``source_rows`` (``load.add_identity`` assigns it before any filtering), so
    this join is the only thing that recovers which rows were originally empty
    once the column has been resolved. ``resolved`` counts the label each such
    row now carries and ``unresolved`` the ones still spelled ``unknown``, so
    the two partition ``empty_rows`` both before and after the call site is
    flipped. ``multi_label_canonical`` counts the distinct ``canonical_psmiles``
    that carry at least one originally-empty row and two or more distinct
    non-empty labels -- the rows the rule's own guard leaves ``unknown``.
    """
    raw = source_rows.iloc[rows[ROW_INDEX_COLUMN].tolist()]
    source_labels = [
        normalise_tacticity(None if pd.isna(value) else value)
        for value in raw[TACTICITY_COLUMN].tolist()
    ]
    canonical = rows[CANONICAL_COLUMN].tolist()
    current = rows[TACTICITY_COLUMN].tolist()
    seen = observed_labels(canonical, source_labels)

    empty_rows = 0
    unresolved = 0
    resolved: dict[str, int] = {}
    multi_label: set[str] = set()
    for source_label, key, label in zip(source_labels, canonical, current, strict=True):
        if source_label != UNKNOWN_TACTICITY:
            continue
        empty_rows += 1
        if label == UNKNOWN_TACTICITY:
            unresolved += 1
        else:
            resolved[label] = resolved.get(label, 0) + 1
        if len(seen[key]) > 1:
            multi_label.add(key)
    return TacticityResolution(empty_rows, resolved, unresolved, len(multi_label))


def raw_string_merges(rows: Any) -> int:
    """Unique in-scope ``smiles_list`` minus unique ``canonical_psmiles`` (F-35: 5)."""
    return int(rows[SMILES_COLUMN].nunique() - rows[CANONICAL_COLUMN].nunique())


def card_count_candidates(source_rows: Any, rows: Any) -> dict[str, int]:
    """Every count the dataset card's 73,045 could have meant (F-19); none equals it."""
    counts = {
        f"unique {SMILES_COLUMN}": int(source_rows[SMILES_COLUMN].nunique()),
        f"unique {CANONICAL_COLUMN} (in scope)": int(rows[CANONICAL_COLUMN].nunique()),
        f"unique {UUID_COLUMN}": int(source_rows[UUID_COLUMN].nunique()),
        "source rows": len(source_rows),
    }
    if MONOMER_ID_COLUMN in source_rows.columns:
        counts[f"unique {MONOMER_ID_COLUMN}"] = int(source_rows[MONOMER_ID_COLUMN].nunique())
    return counts


def tacticity_counts(source_rows: Any) -> dict[str, int]:
    """Rows per tacticity with NaN as ``unknown`` (F-38), largest first, ties by label."""
    labels = [normalise_tacticity(value) for value in source_rows[TACTICITY_COLUMN].tolist()]
    counts = pd.Series(labels).value_counts()
    ordered = sorted(counts.items(), key=lambda item: (-int(item[1]), str(item[0])))
    return {str(label): int(count) for label, count in ordered}


def coverage(source_rows: Any, registry: Registry) -> dict[str, int]:
    """Non-null rows per registry column, in registry order."""
    return {column: int(source_rows[column].notna().sum()) for column in registry.columns()}


def physical_range_counts(source_rows: Any, registry: Registry) -> dict[str, tuple[int, int, int]]:
    """Per registry column: ``(inside, outside, missing)`` against its physical range."""
    counts: dict[str, tuple[int, int, int]] = {}
    for spec in registry.properties.values():
        present = source_rows[spec.column].notna()
        inside = within_physical_range(source_rows, spec)
        counts[spec.column] = (
            int(inside.sum()),
            int((present & ~inside).sum()),
            int((~present).sum()),
        )
    return counts


def with_n_squared(df: Any, registry: Registry) -> Any:
    """The registry columns and the static column of ``df`` plus ``refractive_index_squared``.

    A narrow copy: the derived column is added to a fresh frame, never to the
    259-column source (F-14, F-17, F-18).
    """
    narrow = df[[*registry.columns(), STATIC_COLUMN]].copy()
    narrow[N_SQUARED] = narrow[_refractive_index_column(registry)] ** 2
    return narrow


def _dielectric_rows(df: Any, registry: Registry) -> Any:
    eps = registry.properties["dielectric_const_dc"].column
    present = df[eps].notna() & df[_refractive_index_column(registry)].notna()
    return df.loc[present & df[STATIC_COLUMN].notna()]


def dielectric_identity_residual(df: Any, registry: Registry) -> Any:
    """``|eps_dc - (static - 1 + n^2)|`` over rows carrying all three columns (F-14)."""
    rows = _dielectric_rows(df, registry)
    eps = rows[registry.properties["dielectric_const_dc"].column]
    n_squared = rows[_refractive_index_column(registry)] ** 2
    # arXiv:2511.11626 Table S3: corrected static = (static) - 1 + (refractive index)^2.
    return (eps - (rows[STATIC_COLUMN] - 1.0 + n_squared)).abs()


def static_minimum(df: Any) -> float:
    """The smallest uncorrected static permittivity in ``df`` (F-15: 1.00016)."""
    return float(df[STATIC_COLUMN].min())


def static_maxwell_violation_share(
    df: Any, mask: Any, registry: Registry
) -> tuple[int, int, float]:
    """``(violations, population, percentage)`` of ``static < n^2`` within ``mask`` (F-13)."""
    rows = df.loc[mask]
    n_squared = rows[_refractive_index_column(registry)] ** 2
    both = rows[STATIC_COLUMN].notna() & n_squared.notna()
    violations = int((rows[STATIC_COLUMN] < n_squared)[both].sum())
    size = int(both.sum())
    return violations, size, round(100.0 * violations / size, 2) if size else 0.0


def dc_maxwell_violations(df: Any, mask: Any, registry: Registry) -> int:
    """Rows within ``mask`` with ``eps_dc < n^2``; 0 by the F-14 identity and F-15."""
    rows = df.loc[mask]
    eps = rows[registry.properties["dielectric_const_dc"].column]
    n_squared = rows[_refractive_index_column(registry)] ** 2
    return int((eps < n_squared)[eps.notna() & n_squared.notna()].sum())


def spearman_table(
    df: Any, mask: Any, pairs: Iterable[tuple[str, str]]
) -> list[tuple[str, str, float]]:
    """Spearman rank correlation per column pair on the masked rows (pandas only, F-11)."""
    rows = df.loc[mask]
    return [
        (left, right, float(rows[[left, right]].corr(method="spearman").iloc[0, 1]))
        for left, right in pairs
    ]


def readme_window(df: Any, mask: Any, registry: Registry) -> tuple[int, float]:
    """Rows within ``mask`` in the top TC decile and bottom eps_dc quartile (F-12)."""
    tc, eps, _ = _triple_specs(registry)
    rows = df.loc[mask]
    window = (rows[tc.column] >= rows[tc.column].quantile(WINDOW_TC_QUANTILE)) & (
        rows[eps.column] <= rows[eps.column].quantile(WINDOW_EPS_QUANTILE)
    )
    count = int(window.sum())
    return count, round(100.0 * count / len(rows), 2) if len(rows) else 0.0


# Development defaults from the charter section 13 gate-parameter table (D-16
# row): constrained single objective, eps_dc <= Q25 of the candidate medians,
# Tg >= 400 K. They are inputs to the D-16 gate, which is fixed at the Phase 7
# pre-registration (ADR-0005); they are cited here and decided nowhere in this
# package.
DEV_DEFAULT_TG_MIN_K = 400.0
DEV_DEFAULT_EPS_QUANTILE = 0.25

TG_RMSE_COLUMN = "tg_rmse"
# The tail quantiles printed beside the median of tg_rmse (F-23).
TG_RMSE_P95 = 0.95
TG_RMSE_P99 = 0.99


def tg_window_counts(source_rows: Any, registry: Registry) -> tuple[int, int, int]:
    """``(non-null, inside, outside)`` of ``tg`` against its physical range (F-64)."""
    inside, outside, missing = physical_range_counts(source_rows, registry)[
        registry.properties["tg"].column
    ]
    return inside + outside, inside, outside


def tg_rmse_ladder_counts(rows: Any, mask: Any, registry: Registry) -> list[tuple[float, int]]:
    """Rows within ``mask`` with ``tg_rmse <= rung`` for every registry rung (F-65).

    The rungs are ``PropertySpec.tg_rmse_ladder`` of ``tg``; no rung is applied
    as a cut (R-2). A registry without a ladder yields an empty list.
    """
    ladder = registry.properties["tg"].tg_rmse_ladder or ()
    values = rows.loc[mask, TG_RMSE_COLUMN]
    return [(rung, int((values <= rung).sum())) for rung in ladder]


def tg_rmse_descriptives(source_rows: Any) -> dict[str, float]:
    """Median, p95, p99 and max of ``tg_rmse`` over the rows that carry it (F-23)."""
    values = source_rows[TG_RMSE_COLUMN].dropna()
    return {
        "median": float(values.median()),
        "p95": float(values.quantile(TG_RMSE_P95)),
        "p99": float(values.quantile(TG_RMSE_P99)),
        "max": float(values.max()),
    }


@dataclass(frozen=True)
class FeasibleSet:
    """The feasible-set size under one (Q25, Tg minimum) pair -- an input, not a decision."""

    q25_eps: float
    tg_min_k: float
    n_feasible: int
    n_population: int
    pct: float


def feasible_set(
    candidates: Any,
    registry: Registry,
    *,
    quantile: float = DEV_DEFAULT_EPS_QUANTILE,
    tg_min_k: float = DEV_DEFAULT_TG_MIN_K,
) -> FeasibleSet:
    """Candidates with ``eps_dc_median <= Q(quantile)`` and ``tg_median >= tg_min_k`` (F-62).

    Q is taken over the candidate medians of the frame given; both comparisons
    are inclusive.
    """
    eps = candidates[registry.properties["dielectric_const_dc"].column + MEDIAN_SUFFIX]
    tg = candidates[registry.properties["tg"].column + MEDIAN_SUFFIX]
    q25 = float(eps.quantile(quantile))
    feasible = (eps <= q25) & (tg >= tg_min_k)
    n_feasible = int(feasible.sum())
    n_population = int(len(candidates))
    pct = round(100.0 * n_feasible / n_population, 2) if n_population else 0.0
    return FeasibleSet(q25, tg_min_k, n_feasible, n_population, pct)


def feasible_rows(rows: Any, mask: Any, registry: Registry, *, q25_eps: float, tg_min_k: float) -> int:
    """Rows within ``mask`` with ``eps_dc <= q25_eps`` and ``tg >= tg_min_k`` (row level, F-62)."""
    subset = rows.loc[mask]
    eps = subset[registry.properties["dielectric_const_dc"].column]
    tg = subset[registry.properties["tg"].column]
    return int(((eps <= q25_eps) & (tg >= tg_min_k)).sum())
