"""The populations a run is measured against, captured once (ADR-0008 items 2 and 3; CONTEXT R-1, R-4).

This is the only module of ``llm4pol.run`` that reads a parquet and the only one that imports the
dataframe stack; ``replay`` never loads it (RESEARCH F-28, Pattern 4).

Membership follows the filters of ``llm4pol.data``: ``check_tc`` is the README triple and the
objective's ``check_tc`` mask together, ``readme_triple`` the triple alone, each taken over the
rows parquet and turned into candidates by ``build_candidates``. No mask is re-implemented. The
values are the medians the evaluator serves from the candidate parquet, so a candidate is ranked
among values the loop can observe (RESEARCH Pitfall 7). ``capture`` returns them as parallel
arrays sorted ascending by objective and then by each constraint in spec order, missing values
last, with the candidate ids dropped: the arrays enter a record that Phase 6 reads (A-4).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from llm4pol.data import filters, snapshot
from llm4pol.data.load import build_candidates
from llm4pol.data.registry import Registry
from llm4pol.run.config import ProblemSpec

POPULATION_NAMES: tuple[str, ...] = ("check_tc", "readme_triple")
PRIMARY_POPULATION = POPULATION_NAMES[0]

SNAPSHOT_KEY = b"llm4pol.snapshot"
SOURCE_SHA256_KEY = b"llm4pol.source_sha256"
_ROW_EXTRA_COLUMNS = ("candidate_id", "canonical_psmiles", "tacticity", filters.CHECK_TC_COLUMN)


class PopulationError(ValueError):
    """A table that is absent, unreadable or not the snapshot the problem names."""


@dataclass(frozen=True, slots=True)
class Population:
    """One named population: parallel value arrays sorted by objective, no identifiers."""

    name: str
    objective: tuple[float | None, ...]
    constraints: Mapping[str, tuple[float | None, ...]]

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "objective": list(self.objective),
            "constraints": {key: list(values) for key, values in self.constraints.items()},
        }


def candidate_metadata(root: Path) -> tuple[str, str]:
    """``(snapshot, source sha256)`` from the metadata of the candidate parquet under ``root``."""
    path = snapshot.candidates_parquet(snapshot.processed_dir(root))
    try:
        metadata = pq.read_schema(path).metadata or {}
    except (OSError, ValueError) as exc:  # a missing file is FileNotFoundError, an OSError
        raise PopulationError(f"candidate table unreadable: {path.name}: {exc}") from exc
    try:
        return (
            metadata[SNAPSHOT_KEY].decode("utf-8"),
            metadata[SOURCE_SHA256_KEY].decode("utf-8"),
        )
    except KeyError as exc:
        raise PopulationError(f"{path.name}: metadata key {exc.args[0]!r} is missing") from exc


def _read(path: Path, columns: list[str] | None = None) -> Any:
    try:
        return pq.read_table(path, columns=columns).to_pandas()
    except (OSError, ValueError, KeyError) as exc:
        raise PopulationError(f"table unreadable: {path.name}: {exc}") from exc


def members(root: Path, registry: Registry) -> dict[str, tuple[str, ...]]:
    """The candidate ids of each population, in candidate-id order, by the filters of the data layer."""
    path = snapshot.rows_parquet(snapshot.processed_dir(root))
    rows = _read(path, [*registry.columns(), *_ROW_EXTRA_COLUMNS])
    triple = filters.readme_triple_mask(rows, registry)
    check = filters.check_tc_mask(rows, registry)
    masks = {"check_tc": triple & check, "readme_triple": triple}
    return {
        name: tuple(str(cid) for cid in build_candidates(rows[masks[name]])["candidate_id"])
        for name in POPULATION_NAMES
    }


def _served(frame: Any, ids: tuple[str, ...], column: str) -> list[float | None]:
    """The served ``<column>_median`` of every id; a missing value or a missing id is ``None``."""
    values = frame.reindex(list(ids))[column + filters.MEDIAN_SUFFIX].tolist()
    return [None if math.isnan(float(v)) else float(v) for v in values]


def _sort_key(record: tuple[float | None, ...]) -> tuple[tuple[bool, float], ...]:
    return tuple((v is None, 0.0 if v is None else v) for v in record)


def capture(root: Path, problem: ProblemSpec, registry: Registry) -> tuple[Population, ...]:
    """Both populations with the values the evaluator serves, in the order of ``POPULATION_NAMES``.

    ``PopulationError`` when the candidate parquet's ``llm4pol.snapshot`` metadata is not the
    snapshot the problem names.
    """
    found, _ = candidate_metadata(root)
    if found != problem.table:
        raise PopulationError(f"candidate table is {found!r}, the problem names {problem.table!r}")
    served = _read(snapshot.candidates_parquet(snapshot.processed_dir(root))).set_index(
        "candidate_id"
    )
    keys = problem.property_keys()
    columns = [registry.properties[key].column for key in keys]
    captured: list[Population] = []
    for name, ids in members(root, registry).items():
        cells = [_served(served, ids, column) for column in columns]
        records = sorted(zip(*cells, strict=True), key=_sort_key)
        arrays = [tuple(record[i] for record in records) for i in range(len(keys))]
        captured.append(
            Population(
                name=name,
                objective=arrays[0],
                constraints=dict(zip(keys[1:], arrays[1:], strict=True)),
            )
        )
    return tuple(captured)
