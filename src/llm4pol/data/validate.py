"""The validator: reproduce the pinned snapshot's numbers and write the report (D-07).

Sections, in report order: ``Fetch identity``, ``Source shape``, ``Scope
exclusions and identity`` (plan 02-01), ``Coverage per registry property``,
``Physical-range filter counts``, ``Dielectric columns: identity and Maxwell
check``, ``README triple ladder``, ``Tg window and tg_rmse ladder`` (plan
02-05, charter section 13 M1 (2)-(3), DATA-09), ``Replicate structure and
noise floor`` (plan 02-04: D-04, D-9, M1 (4)), ``Feasible set under the
development defaults (input to the D-16 gate)`` (plan 02-05, M1 (5), DATA-08),
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
    TG_RMSE_ROWS,
    TRIPLE_ALL_ROWS,
    TRIPLE_IN_SCOPE,
    Expectations,
    population_of,
)
from llm4pol.data.fetch import parse_manifest, verify_file
from llm4pol.data.load import LoaderError, read_source
from llm4pol.data.registry import Registry, load_registry
from llm4pol.data.replicates import VERSION_COLUMNS, replicate_section
from llm4pol.data.sections import (
    QUANTITY_HEADER,
    coverage_section,
    dielectric_section,
    ladder_observed,
    ladder_section,
    pct,
    physical_range_section,
    unit_label,
)
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
    "(D-7). An empty `tacticity` takes the label of its twin when the same "
    "`canonical_psmiles` carries exactly one non-empty label elsewhere in the snapshot; a "
    "row with no labelled twin, or with more than one distinct labelled twin, keeps the "
    "literal `unknown`. The rule is a lookup inside this snapshot, never an inference from "
    "chemistry, and it runs over the whole in-scope frame before the identity is taken. It "
    "answers the owner question R-1 raised at M1, decided as D-25 and recorded as ADR-0006; "
    "the resolution table below states each outcome with the population it is drawn from. "
    "The `multi_tacticity_smiles_*` counts are taken on the source column before the "
    "resolution, the `multi_tacticity_canonical_*` counts on the in-scope rows after it "
    "(F-39, F-48). `raw_string_merges` is the number of "
    "distinct `smiles_list` strings that canonicalise to the same repeat unit (F-35)."
)

_TG_INTRO = (
    "`tg` is the glass-transition temperature of RadonPy's two-line density fit; `tg_rmse` is "
    "the sum of squared density residuals of that fit, in the registry's `tg_rmse_unit` "
    "(g/cm^3)^2, not kelvin (F-23). The window counts rows inside and outside the registry "
    "physical range on all source rows (F-64). The ladder counts the in-scope README-triple "
    "rows at every registry rung (F-65); no `tg_rmse` cut is applied in M1 (R-2), so the "
    "numbers satisfy either reading of DATA-09 and the evaluator's population stays a Phase 3 "
    "decision."
)
_DATA_09_FLAG = (
    "Wording discrepancy raised for the owner: REQUIREMENTS.md DATA-09 reads \"filtered by "
    "tg_rmse\"; CONTEXT R-2 (a development default recorded with the owner unavailable) applies "
    "no tg_rmse cut in M1 and records the ladder instead. This report records the count at "
    "every rung so the numbers satisfy either reading; which reading holds is an owner "
    "decision (precedence: charter > REQUIREMENTS.md > phase context, ADR-0002). Nothing is "
    "resolved here."
)
_FEASIBLE_INTRO = (
    "The feasible set is the candidates of the README triple (filter then median) whose "
    "`dielectric_const_dc` median is at or below the Q25 of those medians and whose `tg` "
    "median is at or above the Tg minimum, both inclusive (F-60, F-62). The row-level count "
    "on the in-scope README-triple rows is printed under the row-level Q25 and under the "
    "candidate Q25 so nothing is lost either way. These thresholds are the charter's "
    "development defaults (section 13, D-16 row). This section is an input to the D-16 gate, "
    "which is fixed at the Phase 7 pre-registration (ADR-0005); nothing here is a decision."
)


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
        "row_index",
        filters.CANONICAL_COLUMN,
        filters.SMILES_COLUMN,
        filters.TACTICITY_COLUMN,
        filters.CHECK_TC_COLUMN,
        filters.STATIC_COLUMN,
        filters.TG_RMSE_COLUMN,
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
    resolution = filters.tacticity_resolution_counts(source, rows)
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
        "tacticity_empty_in_scope": resolution.empty_rows,
        "tacticity_unresolved": resolution.unresolved,
        "tacticity_multi_label_canonical": resolution.multi_label_canonical,
    }
    for label in filters.RESOLVED_LABELS:
        observed[f"tacticity_resolved_{label}"] = resolution.resolved.get(label, 0)
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
    resolution_table = CountTable(
        title="Tacticity resolution (ADR-0006)",
        header=QUANTITY_HEADER,
        rows=_count_rows(
            observed,
            (
                "tacticity_empty_in_scope",
                *(f"tacticity_resolved_{label}" for label in filters.RESOLVED_LABELS),
                "tacticity_unresolved",
                "tacticity_multi_label_canonical",
            ),
        ),
    )
    section = Section(
        title="Scope exclusions and identity",
        intro=_IDENTITY_INTRO,
        tables=[exclusions, identity, resolution_table],
    )
    return section, observed


def _tg_section(source: Any, rows: Any, registry: Registry) -> tuple[Section, dict[str, Value]]:
    tg = registry.properties["tg"]
    low, high = tg.physical_range
    window_label = f"[{low}, {high}] {unit_label(tg.unit)}"
    non_null, inside, outside = filters.tg_window_counts(source, registry)
    triple_all = filters.readme_triple_mask(source, registry)
    triple_scope = filters.readme_triple_mask(rows, registry)
    ladder = filters.tg_rmse_ladder_counts(rows, triple_scope, registry)
    descriptives = filters.tg_rmse_descriptives(source)
    observed: dict[str, Value] = {
        "tg_non_null": non_null,
        "tg_inside_window": inside,
        "tg_outside_window": outside,
        "tg_median_all_rows": float(source[tg.column].median()),
        "tg_median_triple_rows": float(source.loc[triple_all, tg.column].median()),
        "tg_rmse_median": descriptives["median"],
        "tg_rmse_p95": descriptives["p95"],
        "tg_rmse_p99": descriptives["p99"],
        "tg_rmse_max": descriptives["max"],
    }
    for rung, count in ladder:
        observed[f"tg_rmse_le_{rung}"] = count
    window = CountTable(
        title="Tg window",
        header=("quantity", "population", "rows"),
        rows=[
            (f"{tg.column} non-null", ALL_SOURCE_ROWS, format_int(non_null)),
            (f"{tg.column} inside {window_label}", ALL_SOURCE_ROWS, format_int(inside)),
            (f"{tg.column} outside {window_label}", ALL_SOURCE_ROWS, format_int(outside)),
        ],
    )
    medians = CountTable(
        title="Tg medians",
        header=QUANTITY_HEADER,
        rows=[
            (f"{tg.column} median", ALL_SOURCE_ROWS, f"{observed['tg_median_all_rows']:.1f} {tg.unit}"),
            (
                f"{tg.column} median",
                TRIPLE_ALL_ROWS,
                f"{observed['tg_median_triple_rows']:.1f} {tg.unit}",
            ),
        ],
    )
    ladder_table = CountTable(
        title="tg_rmse ladder (no cut applied)",
        header=("tg_rmse <= rung", "population", "rows"),
        rows=[(f"tg_rmse <= {rung}", TRIPLE_IN_SCOPE, format_int(count)) for rung, count in ladder],
    )
    unit = tg.tg_rmse_unit or ""
    spread = CountTable(
        title="tg_rmse descriptives",
        header=QUANTITY_HEADER,
        rows=[
            ("tg_rmse median", TG_RMSE_ROWS, f"{descriptives['median']:.3f} {unit}"),
            ("tg_rmse p95", TG_RMSE_ROWS, f"{descriptives['p95']:.3f} {unit}"),
            ("tg_rmse p99", TG_RMSE_ROWS, f"{descriptives['p99']:.3f} {unit}"),
            ("tg_rmse max", TG_RMSE_ROWS, f"{descriptives['max']:.1f} {unit}"),
        ],
    )
    section = Section(
        title="Tg window and tg_rmse ladder",
        intro=_TG_INTRO + "\n\n" + _DATA_09_FLAG,
        tables=[window, medians, ladder_table, spread],
    )
    return section, observed


def _feasible_section(rows: Any, registry: Registry) -> tuple[Section, dict[str, Value]]:
    eps = registry.properties["dielectric_const_dc"]
    tg = registry.properties["tg"]
    triple = filters.readme_triple_mask(rows, registry)
    candidates = filters.candidate_level_triple(rows, registry)
    feasible = filters.feasible_set(candidates, registry)
    row_q25 = float(rows.loc[triple, eps.column].quantile(filters.DEV_DEFAULT_EPS_QUANTILE))
    tg_min = feasible.tg_min_k
    observed: dict[str, Value] = {
        "eps_q25_candidates": feasible.q25_eps,
        "eps_q25_triple_rows": row_q25,
        "feasible_candidates_dev_defaults": feasible.n_feasible,
        "feasible_pct_dev_defaults": feasible.pct,
        "feasible_rows_dev_defaults": filters.feasible_rows(
            rows, triple, registry, q25_eps=row_q25, tg_min_k=tg_min
        ),
        "feasible_rows_under_candidate_q25": filters.feasible_rows(
            rows, triple, registry, q25_eps=feasible.q25_eps, tg_min_k=tg_min
        ),
        "triple_in_scope_rows_for_feasible": int(triple.sum()),
    }
    tg_label = f"{tg_min} {tg.unit}"
    candidate_table = CountTable(
        title="Feasible candidates",
        header=QUANTITY_HEADER,
        rows=[
            (
                f"Q25 of {eps.column} candidate medians",
                CANDIDATE_TRIPLE,
                format_float(feasible.q25_eps, 4),
            ),
            (f"{tg.column} minimum (development default)", CANDIDATE_TRIPLE, tg_label),
            (
                f"feasible candidates (eps_dc_median <= Q25 and tg_median >= {tg_label})",
                CANDIDATE_TRIPLE,
                format_int(feasible.n_feasible),
            ),
            ("candidates", CANDIDATE_TRIPLE, format_int(feasible.n_population)),
            ("feasible share", CANDIDATE_TRIPLE, pct(feasible.pct)),
        ],
    )
    row_table = CountTable(
        title="Feasible rows",
        header=QUANTITY_HEADER,
        rows=[
            (f"Q25 of {eps.column} rows", TRIPLE_IN_SCOPE, format_float(row_q25, 4)),
            (
                "feasible rows under the row Q25",
                TRIPLE_IN_SCOPE,
                format_value(observed["feasible_rows_dev_defaults"]),
            ),
            (
                "feasible rows under the candidate Q25",
                TRIPLE_IN_SCOPE,
                format_value(observed["feasible_rows_under_candidate_q25"]),
            ),
            ("rows", TRIPLE_IN_SCOPE, format_value(observed["triple_in_scope_rows_for_feasible"])),
        ],
    )
    section = Section(
        title="Feasible set under the development defaults (input to the D-16 gate)",
        intro=_FEASIBLE_INTRO,
        tables=[candidate_table, row_table],
    )
    return section, observed


def _build_report(
    root: Path, expected: Expectations, processed_dir: Path | None, registry: Registry
) -> Report:
    fetch_section, csv_sha = _fetch_identity(root)
    source = read_source(snapshot.csv_path(root))
    processed = processed_dir if processed_dir is not None else snapshot.processed_dir(root)
    rows, candidates, second, parse = _read_processed(processed, csv_sha, registry)

    shape_section, observed = _source_shape(source, rows)
    scope_section, scope_observed = _scope_and_identity(source, rows, candidates, second, parse)
    coverage_sec, coverage_observed = coverage_section(source, registry)
    range_sec, range_observed = physical_range_section(source, registry)
    dielectric_sec, dielectric_observed = dielectric_section(source, registry)
    ladder_counts, steps = ladder_observed(source, rows, registry)
    tg_section, tg_observed = _tg_section(source, rows, registry)
    feasible_section, feasible_observed = _feasible_section(rows, registry)
    replicate_sec, replicate_observed = replicate_section(
        rows, candidates, registry, rows_population=IN_SCOPE_ROWS
    )
    observed = {
        **observed,
        **scope_observed,
        **coverage_observed,
        **range_observed,
        **dielectric_observed,
        **ladder_counts,
        **tg_observed,
        **feasible_observed,
        **replicate_observed,
    }
    findings: list[Finding] = [
        evaluate_finding(
            finding_id, expectation, observed.get(finding_id), population_of(finding_id)
        )
        for finding_id, expectation in expected.items()
    ]
    by_id = {finding.finding_id: finding for finding in findings}
    ladder_sec = ladder_section(observed, steps, by_id, registry)
    return Report(
        snapshot=snapshot.SNAPSHOT_ID,
        revision=snapshot.POLYOMICS_REVISION,
        sections=[
            fetch_section,
            shape_section,
            scope_section,
            coverage_sec,
            range_sec,
            dielectric_sec,
            ladder_sec,
            tg_section,
            replicate_sec,
            feasible_section,
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
