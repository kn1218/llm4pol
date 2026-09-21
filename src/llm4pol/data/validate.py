"""The validator: reproduce the pinned snapshot's numbers and write the report (D-07).

Sections: ``Fetch identity``, ``Source shape``, ``Scope exclusions and
identity`` (plan 02-01), ``Replicate structure and noise floor`` (plan 02-04:
D-04, D-9, charter section 13 M1 (4)), ``Findings``. Later plans append
sections and expectations. Exit 0 when every expectation is reproduced or
documented, 1 on any ``FAILED`` or ``MISSING`` finding, 2 when an input is
missing or does not match the manifest (D-10).
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from llm4pol.data import snapshot
from llm4pol.data.fetch import parse_manifest, verify_file
from llm4pol.data.load import LoaderError, read_source
from llm4pol.data.registry import Registry, load_registry
from llm4pol.data.replicates import (
    MULTI_ROW_CANDIDATES,
    NOISE_POPULATION_ALL,
    NOISE_POPULATION_TRIPLE,
    VERSION_COLUMNS,
    replicate_section,
)
from llm4pol.data.report import (
    DOCUMENTED,
    REPRODUCE,
    CountTable,
    Expected,
    Finding,
    Report,
    Section,
    Value,
    evaluate_finding,
    exit_code,
    format_value,
    render_markdown,
)

Expectations = Mapping[str, Expected]

ALL_SOURCE_ROWS = "all source rows"
IN_SCOPE_ROWS = "in-scope rows"
PINNED_FILES = "pinned revision files"

_F52_NOTE = "F-52 counted on (smiles_list, tacticity) groups; here by candidate_id (F-35 merges)"
_NOISE_NOTE = "F-55: median over candidates with n >= 2 of std / |median|"
_TRIPLE_NOTE = "F-56: rows filtered to the README triple first, then grouped (F-61)"

# F-06, F-07, F-32, F-37 measured on the pinned bytes (plan 02-01); F-50, F-52,
# F-55, F-56 (plan 02-04); later plans append.
EXPECTED_POLYOMICS: dict[str, Expected] = {
    "source_rows": Expected(REPRODUCE, 95335),
    "source_columns": Expected(REPRODUCE, 259),
    "unique_smiles_list": Expected(REPRODUCE, 78379),
    "second_monomer_rows": Expected(REPRODUCE, 3),
    "parse_failures": Expected(REPRODUCE, 0),
    "in_scope_rows": Expected(REPRODUCE, 95332),
    "unique_canonical": Expected(REPRODUCE, 78373),
    "unique_candidate_ids": Expected(REPRODUCE, 78676),
    "replicate_multi_row_candidates": Expected(REPRODUCE, 12983),
    "replicate_max_rows": Expected(REPRODUCE, 17),
    "same_version_replicate_candidates": Expected(DOCUMENTED, 1888, 10, _F52_NOTE),
    "cross_version_rerun_candidates": Expected(DOCUMENTED, 11096, 10, _F52_NOTE),
    "noise_floor_rel_thermal_conductivity": Expected(DOCUMENTED, 0.0369, 0.001, _NOISE_NOTE),
    "noise_floor_rel_dielectric_const_dc": Expected(DOCUMENTED, 0.0084, 0.001, _NOISE_NOTE),
    "noise_floor_rel_tg": Expected(DOCUMENTED, 0.0577, 0.001, _NOISE_NOTE),
    "noise_floor_rel_density": Expected(DOCUMENTED, 0.0034, 0.001, _NOISE_NOTE),
    "noise_floor_abs_tg": Expected(DOCUMENTED, 30.2, 0.5, _NOISE_NOTE + " (absolute, K)"),
    "noise_floor_triple_rel_thermal_conductivity": Expected(DOCUMENTED, 0.0431, 0.001, _TRIPLE_NOTE),
    "noise_floor_triple_rel_dielectric_const_dc": Expected(DOCUMENTED, 0.0112, 0.001, _TRIPLE_NOTE),
    "noise_floor_triple_rel_tg": Expected(DOCUMENTED, 0.0540, 0.001, _TRIPLE_NOTE),
}

# The population each observed quantity is drawn from (D-10).
POPULATIONS: dict[str, str] = {
    "source_rows": ALL_SOURCE_ROWS,
    "source_columns": ALL_SOURCE_ROWS,
    "unique_smiles_list": ALL_SOURCE_ROWS,
    "second_monomer_rows": ALL_SOURCE_ROWS,
    "parse_failures": ALL_SOURCE_ROWS,
    "in_scope_rows": IN_SCOPE_ROWS,
    "unique_canonical": IN_SCOPE_ROWS,
    "unique_candidate_ids": IN_SCOPE_ROWS,
    "replicate_multi_row_candidates": IN_SCOPE_ROWS,
    "replicate_max_rows": IN_SCOPE_ROWS,
    "same_version_replicate_candidates": MULTI_ROW_CANDIDATES,
    "cross_version_rerun_candidates": MULTI_ROW_CANDIDATES,
    "noise_floor_rel_thermal_conductivity": NOISE_POPULATION_ALL,
    "noise_floor_rel_dielectric_const_dc": NOISE_POPULATION_ALL,
    "noise_floor_rel_tg": NOISE_POPULATION_ALL,
    "noise_floor_rel_density": NOISE_POPULATION_ALL,
    "noise_floor_abs_tg": NOISE_POPULATION_ALL,
    "noise_floor_triple_rel_thermal_conductivity": NOISE_POPULATION_TRIPLE,
    "noise_floor_triple_rel_dielectric_const_dc": NOISE_POPULATION_TRIPLE,
    "noise_floor_triple_rel_tg": NOISE_POPULATION_TRIPLE,
}

_SEVENTY_THREE_THOUSAND = (
    "The dataset card describes \"73,045 general polymers in the isotropic amorphous state\"; "
    "no column of the file reproduces that number (unique `smiles_list` 78,379, `monomer_ID` "
    "78,336, `UUID` 95,335). It is the card's description text, not a row count: the file "
    "has 95,335 rows (RESEARCH F-19, charter section 13 M1 exit criterion (3))."
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
        header=("quantity", "population", "value"),
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
    return [(name, POPULATIONS[name], format_value(observed[name])) for name in ids]


def _source_shape(root: Path) -> tuple[Section, dict[str, Value]]:
    frame = read_source(snapshot.csv_path(root))
    observed: dict[str, Value] = {
        "source_rows": int(frame.shape[0]),
        "source_columns": int(frame.shape[1]),
        "unique_smiles_list": int(frame["smiles_list"].nunique()),
    }
    table = CountTable(
        title="Source shape",
        header=("quantity", "population", "value"),
        rows=_count_rows(observed, ("source_rows", "source_columns", "unique_smiles_list")),
    )
    return Section(title="Source shape", intro=_SEVENTY_THREE_THOUSAND, tables=[table]), observed


def _metadata_int(metadata: Mapping[bytes, bytes], key: str, path: Path) -> int:
    raw = metadata.get(key.encode("utf-8"))
    if raw is None:
        raise ValueError(f"{path}: parquet metadata lacks {key}")
    return int(raw.decode("utf-8"))


def _scope_and_identity(
    processed: Path, csv_sha: str, source_rows: int
) -> tuple[Section, dict[str, Value]]:
    rows_path = snapshot.rows_parquet(processed)
    candidates_path = snapshot.candidates_parquet(processed)
    for path in (rows_path, candidates_path):
        if not path.is_file():
            raise LoaderError(f"parquet not found: {path} (run `python -m llm4pol.data load`)")
    rows: Any = pq.read_table(rows_path, columns=["canonical_psmiles", "candidate_id"])
    metadata: Mapping[bytes, bytes] = rows.schema.metadata or {}
    parquet_sha = (metadata.get(b"llm4pol.source_sha256") or b"").decode("utf-8")
    if parquet_sha != csv_sha:
        raise ValueError(
            f"{rows_path}: llm4pol.source_sha256 {parquet_sha[:12]}… differs from the manifest "
            f"{csv_sha[:12]}… (re-run `python -m llm4pol.data load`)"
        )
    candidates: Any = pq.read_table(candidates_path, columns=["candidate_id"])
    second = _metadata_int(metadata, "llm4pol.excluded_second_monomer", rows_path)
    parse = _metadata_int(metadata, "llm4pol.excluded_parse_failure", rows_path)
    in_scope = int(rows.num_rows)
    if source_rows - second - parse != in_scope:
        raise ValueError(
            f"{rows_path}: {in_scope} in-scope rows but the source has {source_rows} rows "
            f"minus {second} second-monomer and {parse} parse failures"
        )
    observed: dict[str, Value] = {
        "second_monomer_rows": second,
        "parse_failures": parse,
        "in_scope_rows": in_scope,
        "unique_canonical": int(len(pc.unique(rows.column("canonical_psmiles")))),
        "unique_candidate_ids": int(len(pc.unique(candidates.column("candidate_id")))),
    }
    exclusions = CountTable(
        title="Scope exclusions",
        header=("quantity", "population", "value"),
        rows=_count_rows(observed, ("second_monomer_rows", "parse_failures")),
    )
    identity = CountTable(
        title="Identity",
        header=("quantity", "population", "value"),
        rows=_count_rows(observed, ("in_scope_rows", "unique_canonical", "unique_candidate_ids")),
    )
    section = Section(
        title="Scope exclusions and identity",
        intro=(
            "Rows with a second monomer are excluded before parsing (homopolymer scope, "
            "ADR-0004); rows whose SMILES RDKit cannot parse are excluded and counted (D-03). "
            "`unique_candidate_ids` is read from the candidate parquet, one row per "
            "`candidate_id` (D-7)."
        ),
        tables=[exclusions, identity],
    )
    return section, observed


def _replicates(processed: Path, registry: Registry) -> tuple[Section, dict[str, Value]]:
    """Read the candidate table and the row columns the replicate section needs (D-7)."""
    rows_path = snapshot.rows_parquet(processed)
    names = set(pq.read_schema(rows_path).names)
    wanted = ("candidate_id", "canonical_psmiles", "tacticity", *registry.columns(), *VERSION_COLUMNS)
    rows = pd.read_parquet(rows_path, columns=[name for name in wanted if name in names])
    candidates = pd.read_parquet(snapshot.candidates_parquet(processed))
    section, observed = replicate_section(rows, candidates, registry, rows_population=IN_SCOPE_ROWS)
    return section, dict(observed)


def _build_report(
    root: Path, expected: Expectations, processed_dir: Path | None, registry: Registry
) -> Report:
    fetch_section, csv_sha = _fetch_identity(root)
    shape_section, observed = _source_shape(root)
    processed = processed_dir if processed_dir is not None else snapshot.processed_dir(root)
    scope_section, scope_observed = _scope_and_identity(
        processed, csv_sha, int(observed["source_rows"])
    )
    replicate_sec, replicate_observed = _replicates(processed, registry)
    observed = {**observed, **scope_observed, **replicate_observed}
    findings: list[Finding] = [
        evaluate_finding(finding_id, expectation, observed.get(finding_id), POPULATIONS[finding_id])
        for finding_id, expectation in expected.items()
    ]
    return Report(
        snapshot=snapshot.SNAPSHOT_ID,
        revision=snapshot.POLYOMICS_REVISION,
        sections=[fetch_section, shape_section, scope_section, replicate_sec],
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
        print(
            f"finding {finding.finding_id}: {finding.cls} "
            f"expected={format_value(finding.expected)} "
            f"observed={format_value(finding.observed)} {finding.status}"
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
