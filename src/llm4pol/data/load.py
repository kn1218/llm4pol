"""Read the pinned CSV, add the identity, write the row-level and candidate parquets.

CONTEXT D-02 (one parquet, declared schema), D-03 (identity, scope
exclusions counted never raised), D-04 (replicates grouped by ``candidate_id``
with median / n / min / max / std per registry property). Every source column
is kept; ``candidate_id``, ``canonical_psmiles`` and ``row_index`` are added.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from llm4pol.data import snapshot
from llm4pol.data.fetch import sha256_of
from llm4pol.data.identity import candidate_id, canonical_psmiles, normalise_tacticity
from llm4pol.data.schema import DTYPES, PROPERTY_COLUMNS, REQUIRED_SOURCE_COLUMNS, cast_declared


class LoaderError(RuntimeError):
    """A missing input or a source that does not carry the required columns."""


@dataclass(frozen=True)
class LoadResult:
    """What ``load`` wrote and the counts the validator reproduces."""

    rows_parquet: Path
    candidates_parquet: Path
    processed_dir: Path
    source_rows: int
    source_columns: int
    excluded_second_monomer: int
    excluded_parse_failure: int
    rows_written: int
    candidates: int


def read_source(csv_path: Path) -> Any:
    """``pd.read_csv`` with the declared dtype map; fails fast on a missing file or column."""
    if not csv_path.is_file():
        raise LoaderError(f"source CSV not found: {csv_path}")
    frame = pd.read_csv(csv_path, low_memory=False, dtype=DTYPES)
    missing = [name for name in REQUIRED_SOURCE_COLUMNS if name not in frame.columns]
    if missing:
        raise LoaderError(f"{csv_path}: missing required columns: {missing}")
    return frame


def add_identity(frame: Any) -> tuple[Any, int, int]:
    """Add ``row_index``, drop second-monomer and unparseable rows, add the identity columns.

    Returns ``(rows, excluded_second_monomer, excluded_parse_failure)``. Each
    unique ``smiles_list`` is canonicalised once through a dict cache.
    """
    rows = frame.copy()
    rows["row_index"] = range(len(rows))

    second_monomer = rows["smiles_2"].notna()
    excluded_second_monomer = int(second_monomer.sum())
    rows = rows.loc[~second_monomer]

    cache: dict[str, str | None] = {}

    def canonical(value: object) -> str | None:
        key = str(value)
        if key not in cache:
            cache[key] = canonical_psmiles(key)
        return cache[key]

    canonical_values = [canonical(value) for value in rows["smiles_list"].tolist()]
    parsed = [value is not None for value in canonical_values]
    excluded_parse_failure = len(parsed) - sum(parsed)
    rows = rows.loc[parsed]

    tacticity = [
        normalise_tacticity(None if pd.isna(value) else value)
        for value in rows["tacticity"].tolist()
    ]
    kept_canonical = [value for value in canonical_values if value is not None]
    rows["tacticity"] = tacticity
    rows["canonical_psmiles"] = kept_canonical
    rows["candidate_id"] = [
        candidate_id(canon, tac) for canon, tac in zip(kept_canonical, tacticity, strict=True)
    ]
    return rows, excluded_second_monomer, excluded_parse_failure


def build_candidates(rows: Any) -> Any:
    """One row per ``candidate_id`` (D-7): median / n / min / max / std per registry property.

    Grouping happens here, before any metric is computed anywhere else.
    ``std`` is pandas' default ddof=1 (NaN for a singleton).
    """
    grouped = rows.groupby("candidate_id", sort=True)
    table = grouped[list(PROPERTY_COLUMNS)].agg(["median", "count", "min", "max", "std"])
    table.columns = [
        f"{column}_{'n' if statistic == 'count' else statistic}"
        for column, statistic in table.columns
    ]
    table["n_rows"] = grouped.size()
    table["canonical_psmiles"] = grouped["canonical_psmiles"].first()
    table["tacticity"] = grouped["tacticity"].first()
    return table.reset_index()


def _display(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _with_metadata(table: Any, metadata: dict[bytes, bytes]) -> Any:
    existing = dict(table.schema.metadata or {})
    return table.replace_schema_metadata({**existing, **metadata})


def load(root: Path, *, processed_dir: Path | None = None) -> LoadResult:
    """Read ``root``'s pinned CSV and write both parquets into ``processed_dir``."""
    csv_path = snapshot.csv_path(root)
    frame = read_source(csv_path)
    source_rows = int(frame.shape[0])
    source_columns = int(frame.shape[1])
    rows, excluded_second_monomer, excluded_parse_failure = add_identity(frame)
    candidates = build_candidates(rows)

    out_dir = processed_dir if processed_dir is not None else snapshot.processed_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_path = snapshot.rows_parquet(out_dir)
    candidates_path = snapshot.candidates_parquet(out_dir)

    metadata = {
        b"llm4pol.snapshot": snapshot.SNAPSHOT_ID.encode("utf-8"),
        b"llm4pol.revision": snapshot.POLYOMICS_REVISION.encode("utf-8"),
        b"llm4pol.source_rows": str(source_rows).encode("utf-8"),
        b"llm4pol.source_columns": str(source_columns).encode("utf-8"),
        b"llm4pol.excluded_second_monomer": str(excluded_second_monomer).encode("utf-8"),
        b"llm4pol.excluded_parse_failure": str(excluded_parse_failure).encode("utf-8"),
        b"llm4pol.source_sha256": sha256_of(csv_path).encode("utf-8"),
    }
    rows_table = cast_declared(pa.Table.from_pandas(rows, preserve_index=False))
    pq.write_table(_with_metadata(rows_table, metadata), rows_path)
    candidates_table = pa.Table.from_pandas(candidates, preserve_index=False)
    pq.write_table(_with_metadata(candidates_table, metadata), candidates_path)

    rows_written = int(len(rows))
    n_candidates = int(len(candidates))
    print(
        f"load: read {source_rows:,} rows x {source_columns:,} columns; "
        f"excluded {excluded_second_monomer:,} second-monomer rows, "
        f"{excluded_parse_failure:,} parse failures; "
        f"wrote {rows_written:,} rows -> {_display(rows_path, root)}; "
        f"{n_candidates:,} candidates -> {_display(candidates_path, root)}"
    )
    return LoadResult(
        rows_parquet=rows_path,
        candidates_parquet=candidates_path,
        processed_dir=out_dir,
        source_rows=source_rows,
        source_columns=source_columns,
        excluded_second_monomer=excluded_second_monomer,
        excluded_parse_failure=excluded_parse_failure,
        rows_written=rows_written,
        candidates=n_candidates,
    )
