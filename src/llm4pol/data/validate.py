"""The validator: reproduce the pinned snapshot's numbers and write the report (D-07).

Sections, in report order: ``Fetch identity``, ``Source shape``, ``Scope
exclusions and identity`` (plan 02-01), ``Coverage per registry property``,
``Physical-range filter counts``, ``Dielectric columns: identity and Maxwell
check``, ``README triple ladder`` (plan 02-05, charter section 13 M1 (2)-(3)),
``Replicate structure and noise floor`` (plan 02-04: D-04, D-9, M1 (4)),
``Findings``. Every count is a pure function of the frames and the registry in
``filters.py`` / ``replicates.py``; this module names populations (D-10) and
renders. Exit 0 when every expectation is reproduced or documented, 1 on any
``FAILED`` or ``MISSING`` finding, 2 when an input is missing or does not match
the manifest (D-10 CLI).
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

from llm4pol.data import filters, snapshot
from llm4pol.data.expectations import (
    ALL_SOURCE_ROWS,
    CANDIDATE_TRIPLE,
    CANDIDATE_TRIPLE_ALT,
    CARD_NOT_REPRODUCIBLE,
    DIELECTRIC_ROWS,
    EXPECTED_POLYOMICS,
    IN_SCOPE_ROWS,
    PINNED_FILES,
    SPEARMAN_PAIRS,
    TC_TG_ROWS,
    TRIPLE_ALL_ROWS,
    Expectations,
    population_of,
)
from llm4pol.data.fetch import parse_manifest, verify_file
from llm4pol.data.load import LoaderError, read_source
from llm4pol.data.registry import Registry, load_registry
from llm4pol.data.replicates import VERSION_COLUMNS, replicate_section
from llm4pol.data.report import (
    CountTable,
    Finding,
    Report,
    Section,
    Value,
    evaluate_finding,
    exit_code,
    format_finding_values,
    format_float,
    format_int,
    format_value,
    render_markdown,
)

QUANTITY_HEADER = ("quantity", "population", "value")

_SEVENTY_THREE_THOUSAND = (
    'The dataset card\'s 73,045 ("73,045 general polymers in the isotropic amorphous state") '
    "is reproduced by no column of the file: the table below lists the unique count of every "
    "identifier the card could have meant, and none equals 73,045. It is the card's "
    "description text, not a row count. The closest explanation, the paper's Table S2 "
    "per-class sum of unique structures, is an assumption (A1; RESEARCH F-19; charter "
    "section 13 M1 exit criterion (3))."
)

_IDENTITY_INTRO = (
    "Rows with a second monomer are excluded before parsing (homopolymer scope, ADR-0004); "
    "rows whose SMILES RDKit cannot parse are excluded and counted (D-03). "
    "`unique_candidate_ids` is read from the candidate parquet, one row per `candidate_id` "
    "(D-7). A missing tacticity is the literal `unknown` and stays a separate candidate in "
    "M1, so a repeat unit that also occurs with a known tacticity gets an `unknown` twin; "
    "the count with and without those twins is printed (F-39, F-48) and the twins are "
    "raised for the owner before Phase 3 (R-1). `raw_string_merges` is the number of "
    "distinct `smiles_list` strings that canonicalise to the same repeat unit (F-35)."
)

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


def _pct(value: float) -> str:
    return f"{value:.2f} %"


def _unit_label(unit: str) -> str:
    """A registry unit for display: `*` becomes `·` so the aggregates-only grep for
    SMILES-like tokens (`*` followed by a letter, charter section 10) stays at zero."""
    return unit.replace("*", "·")


def _fetch_identity(root: Path) -> tuple[Section, str]:
    """Verify both pinned files against the manifest; return the section and the CSV sha."""
    manifest = parse_manifest(snapshot.manifest_path(root))
    if manifest.revision != snapshot.POLYOMICS_REVISION:
        raise ValueError(
            f"manifest revision {manifest.revision!r} differs from the pinned "
            f"{snapshot.POLYOMICS_REVISION!r}"
        )
    rows: list[tuple[str, ...]] = []
    for name in (snapshot.CSV_NAME, snapshot.README_NAME):
        if name not in manifest.entries:
            raise ValueError(f"manifest has no entry for {name}")
        sha, size = manifest.entries[name]
        check = verify_file(snapshot.raw_dir(root) / name, sha, size)
        if not check.ok:
            raise ValueError(
                f"{name} does not match data/MANIFEST-open.sha256 "
                "(run `python -m llm4pol.data fetch`)"
            )
        rows.append((name, PINNED_FILES, format_value(size), sha, "yes"))
    files = CountTable(
        title="Pinned files",
        header=("file", "population", "size", "sha256", "manifest match"),
        rows=rows,
    )
    identity = CountTable(
        title="Snapshot identity",
        header=QUANTITY_HEADER,
        rows=[
            ("snapshot", PINNED_FILES, snapshot.SNAPSHOT_ID),
            ("revision", PINNED_FILES, snapshot.POLYOMICS_REVISION),
            ("repository", PINNED_FILES, snapshot.POLYOMICS_REPO),
        ],
    )
    section = Section(
        title="Fetch identity",
        intro="Both pinned files verify by byte size and streamed sha256 against the manifest.",
        tables=[files, identity],
    )
    csv_sha = manifest.entries[snapshot.CSV_NAME][0]
    return section, csv_sha


def _count_rows(observed: Mapping[str, Value], ids: tuple[str, ...]) -> list[tuple[str, ...]]:
    return [(name, population_of(name), format_value(observed[name])) for name in ids]


def _source_shape(source: Any, rows: Any) -> tuple[Section, dict[str, Value]]:
    observed: dict[str, Value] = {
        "source_rows": int(source.shape[0]),
        "source_columns": int(source.shape[1]),
        "unique_smiles_list": int(source["smiles_list"].nunique()),
    }
    card = filters.card_count_candidates(source, rows)
    observed["card_count_73045"] = (
        CARD_NOT_REPRODUCIBLE
        if filters.CARD_COUNT not in card.values()
        else f"reproduced by {', '.join(k for k, v in card.items() if v == filters.CARD_COUNT)}"
    )
    shape = CountTable(
        title="Source shape",
        header=QUANTITY_HEADER,
        rows=_count_rows(observed, ("source_rows", "source_columns", "unique_smiles_list")),
    )
    candidates = CountTable(
        title="Counts the dataset card's 73,045 could have meant",
        header=("column", "population", "unique values"),
        rows=[(label, ALL_SOURCE_ROWS, format_int(count)) for label, count in card.items()],
    )
    section = Section(
        title="Source shape", intro=_SEVENTY_THREE_THOUSAND, tables=[shape, candidates]
    )
    return section, observed


def _metadata_int(metadata: Mapping[bytes, bytes], key: str, path: Path) -> int:
    raw = metadata.get(key.encode("utf-8"))
    if raw is None:
        raise ValueError(f"{path}: parquet metadata lacks {key}")
    return int(raw.decode("utf-8"))


def _read_processed(processed: Path, csv_sha: str, registry: Registry) -> tuple[Any, Any, int, int]:
    """The row frame (needed columns only), the candidate frame and the two exclusion counts."""
    rows_path = snapshot.rows_parquet(processed)
    candidates_path = snapshot.candidates_parquet(processed)
    for path in (rows_path, candidates_path):
        if not path.is_file():
            raise LoaderError(f"parquet not found: {path} (run `python -m llm4pol.data load`)")
    schema = pq.read_schema(rows_path)
    metadata: Mapping[bytes, bytes] = schema.metadata or {}
    parquet_sha = (metadata.get(b"llm4pol.source_sha256") or b"").decode("utf-8")
    if parquet_sha != csv_sha:
        raise ValueError(
            f"{rows_path}: llm4pol.source_sha256 {parquet_sha[:12]}… differs from the manifest "
            f"{csv_sha[:12]}… (re-run `python -m llm4pol.data load`)"
        )
    wanted = (
        "candidate_id",
        filters.CANONICAL_COLUMN,
        filters.SMILES_COLUMN,
        filters.TACTICITY_COLUMN,
        filters.CHECK_TC_COLUMN,
        filters.STATIC_COLUMN,
        *registry.columns(),
        *VERSION_COLUMNS,
    )
    names = set(schema.names)
    rows = pd.read_parquet(rows_path, columns=[name for name in wanted if name in names])
    candidates = pd.read_parquet(candidates_path)
    second = _metadata_int(metadata, "llm4pol.excluded_second_monomer", rows_path)
    parse = _metadata_int(metadata, "llm4pol.excluded_parse_failure", rows_path)
    return rows, candidates, second, parse


def _scope_and_identity(
    source: Any, rows: Any, candidates: Any, second: int, parse: int
) -> tuple[Section, dict[str, Value]]:
    in_scope = len(rows)
    if len(source) - second - parse != in_scope:
        raise ValueError(
            f"{in_scope} in-scope rows but the source has {len(source)} rows "
            f"minus {second} second-monomer and {parse} parse failures"
        )
    by_smiles = filters.multi_tacticity_counts(source)
    by_canonical = filters.multi_tacticity_counts_canonical(rows)
    observed: dict[str, Value] = {
        "second_monomer_rows": second,
        "parse_failures": parse,
        "in_scope_rows": in_scope,
        "unique_canonical": int(rows[filters.CANONICAL_COLUMN].nunique()),
        "unique_candidate_ids": int(candidates["candidate_id"].nunique()),
        "raw_string_merges": filters.raw_string_merges(rows),
        "multi_tacticity_smiles_with_unknown": by_smiles.with_unknown,
        "multi_tacticity_smiles_without_unknown": by_smiles.without_unknown,
        "multi_tacticity_smiles_unknown_twins": by_smiles.unknown_twins,
        "multi_tacticity_canonical_with_unknown": by_canonical.with_unknown,
        "multi_tacticity_canonical_without_unknown": by_canonical.without_unknown,
    }
    exclusions = CountTable(
        title="Scope exclusions",
        header=QUANTITY_HEADER,
        rows=_count_rows(observed, ("second_monomer_rows", "parse_failures")),
    )
    identity = CountTable(
        title="Identity",
        header=QUANTITY_HEADER,
        rows=_count_rows(
            observed,
            (
                "in_scope_rows",
                "unique_canonical",
                "unique_candidate_ids",
                "raw_string_merges",
                "multi_tacticity_smiles_with_unknown",
                "multi_tacticity_smiles_without_unknown",
                "multi_tacticity_smiles_unknown_twins",
                "multi_tacticity_canonical_with_unknown",
                "multi_tacticity_canonical_without_unknown",
            ),
        ),
    )
    section = Section(
        title="Scope exclusions and identity", intro=_IDENTITY_INTRO, tables=[exclusions, identity]
    )
    return section, observed


def _coverage(source: Any, registry: Registry) -> tuple[Section, dict[str, Value]]:
    observed: dict[str, Value] = {}
    coverage_rows: list[tuple[str, ...]] = []
    total = len(source)
    for column, count in filters.coverage(source, registry).items():
        key = registry.spec_for_column(column).key
        observed[f"coverage_{column}"] = count
        share = _pct(100.0 * count / total) if total else _pct(0.0)
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


def _physical_ranges(source: Any, registry: Registry) -> tuple[Section, dict[str, Value]]:
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
                f"[{low}, {high}] {_unit_label(spec.unit)}",
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


def _dielectric(source: Any, registry: Registry) -> tuple[Section, dict[str, Value]]:
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
                _pct(pct_triple),
            ),
            (
                f"{filters.STATIC_COLUMN} < n^2",
                DIELECTRIC_ROWS,
                format_int(violations_all),
                format_int(size_all),
                _pct(pct_all),
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


def _ladder_observed(
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


def _ladder_section(
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
            ("window share", TRIPLE_ALL_ROWS, _pct(float(observed["readme_window_pct"]))),
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


def _build_report(
    root: Path, expected: Expectations, processed_dir: Path | None, registry: Registry
) -> Report:
    fetch_section, csv_sha = _fetch_identity(root)
    source = read_source(snapshot.csv_path(root))
    processed = processed_dir if processed_dir is not None else snapshot.processed_dir(root)
    rows, candidates, second, parse = _read_processed(processed, csv_sha, registry)

    shape_section, observed = _source_shape(source, rows)
    scope_section, scope_observed = _scope_and_identity(source, rows, candidates, second, parse)
    coverage_section, coverage_observed = _coverage(source, registry)
    range_section, range_observed = _physical_ranges(source, registry)
    dielectric_section, dielectric_observed = _dielectric(source, registry)
    ladder_observed, steps = _ladder_observed(source, rows, registry)
    replicate_sec, replicate_observed = replicate_section(
        rows, candidates, registry, rows_population=IN_SCOPE_ROWS
    )
    observed = {
        **observed,
        **scope_observed,
        **coverage_observed,
        **range_observed,
        **dielectric_observed,
        **ladder_observed,
        **replicate_observed,
    }
    findings: list[Finding] = [
        evaluate_finding(
            finding_id, expectation, observed.get(finding_id), population_of(finding_id)
        )
        for finding_id, expectation in expected.items()
    ]
    by_id = {finding.finding_id: finding for finding in findings}
    ladder_section = _ladder_section(observed, steps, by_id, registry)
    return Report(
        snapshot=snapshot.SNAPSHOT_ID,
        revision=snapshot.POLYOMICS_REVISION,
        sections=[
            fetch_section,
            shape_section,
            scope_section,
            coverage_section,
            range_section,
            dielectric_section,
            ladder_section,
            replicate_sec,
        ],
        findings=findings,
    )


def run(
    root: Path,
    *,
    expected: Expectations = EXPECTED_POLYOMICS,
    processed_dir: Path | None = None,
    report_path: Path | None = None,
    registry: Registry | None = None,
) -> int:
    """Validate ``root`` against ``expected``; write the report; return the exit code.

    ``registry`` defaults to the protocol instance (``load_registry()``); a
    ``RegistryError`` is a ``ValueError`` and exits 2 like any other bad input.
    """
    try:
        report = _build_report(
            root, expected, processed_dir, registry if registry is not None else load_registry()
        )
    except (LoaderError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    counts = {"reproduced": 0, "documented": 0, "failed": 0}
    for finding in report.findings:
        expected_text, observed_text = format_finding_values(finding)
        print(
            f"finding {finding.finding_id}: {finding.cls} "
            f"expected={expected_text} observed={observed_text} {finding.status}"
        )
        key = finding.status if finding.status in counts else "failed"
        counts[key] += 1
    code = exit_code(report.findings)
    target = report_path if report_path is not None else snapshot.report_path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(report), encoding="utf-8", newline="\n")
    print(
        f"VALIDATION: {counts['reproduced']} reproduced, {counts['documented']} documented, "
        f"{counts['failed']} failed -> exit {code}"
    )
    return code
