"""The ``table`` backend: the candidate parquet of the pinned snapshot (CONTEXT D-03, D-05, R-5).

The parquet is read once per instance with pyarrow, its ``llm4pol.snapshot``
metadata asserted against the registry's snapshot (a substituted table would
otherwise serve wrong values under the right ``source``; threat T-03-02),
converted to a pandas frame and indexed by ``candidate_id`` for O(1) lookups.
A failed load keeps nothing, so the next lookup retries -- the ``error`` path
of D-02 is retryable by construction.

Value semantics (D-03): ``value`` is ``<column>_median``, ``n_replicates`` is
``<column>_n``, ``spread`` is ``<column>_std`` when ``n >= 2`` and ``None``
otherwise, ``unit`` comes from the registry. NaN never leaves this module
(threat T-03-03). No population filter of any kind is applied: a candidate
outside the README triple or with ``check_tc`` False still gets its values.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from llm4pol.evaluate.contract import Lookup
from llm4pol.evaluate.registry import PropertyTable

SNAPSHOT_METADATA_KEY = b"llm4pol.snapshot"


class SnapshotMismatch(RuntimeError):
    """The parquet's ``llm4pol.snapshot`` metadata is not the registry's snapshot."""


class TableBackend:
    """``Backend`` over the candidate parquet at ``path``."""

    name: str = "table"
    provenance_tier: str = "md_simulated"

    def __init__(self, path: Path, *, properties: PropertyTable) -> None:
        self._path = path
        self._properties = properties
        self.source: str = properties.snapshot
        self._table: Any | None = None

    @property
    def path(self) -> Path:
        return self._path

    def _frame(self) -> Any:
        """The candidate frame indexed by ``candidate_id``, loaded on first use."""
        if self._table is None:
            table = pq.read_table(self._path)
            metadata = table.schema.metadata or {}
            found = metadata.get(SNAPSHOT_METADATA_KEY, b"").decode("utf-8")
            if found != self.source:
                raise SnapshotMismatch(
                    f"{self._path}: parquet snapshot {found!r} != registry snapshot {self.source!r}"
                )
            self._table = table.to_pandas().set_index("candidate_id")
        return self._table

    def lookup(self, candidate_id: str, property_key: str) -> Lookup:
        """The facts for one (candidate, registered property); see the module docstring."""
        frame = self._frame()
        if candidate_id not in frame.index:
            return Lookup("missing", reason="candidate_unknown")
        spec = self._properties.spec(property_key)
        median = float(frame.at[candidate_id, spec.column + "_median"])
        if math.isnan(median):
            return Lookup("missing", reason="value_absent")
        n = int(frame.at[candidate_id, spec.column + "_n"])
        std = float(frame.at[candidate_id, spec.column + "_std"])
        spread = None if n < 2 or math.isnan(std) else std
        return Lookup("ok", value=median, unit=spec.unit, n_replicates=n, spread=spread)
