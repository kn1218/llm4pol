"""The data package (charter section 6): fetch, load, identity, validate.

``fetch`` verifies the pinned PolyOmics files against ``data/MANIFEST-open.sha256``
and downloads only what is absent; ``load`` writes the row-level and candidate
parquets with a declared schema; ``identity`` freezes the candidate definition;
``validate`` writes the report that is the authority for every number cited later.

This package imports nothing from any sibling ``llm4pol`` subpackage
(``pyproject.toml`` ``[tool.importlinter]`` enforces the boundary).
"""

from __future__ import annotations

from llm4pol.data.snapshot import POLYOMICS_REVISION, SNAPSHOT_ID

__all__ = ["POLYOMICS_REVISION", "SNAPSHOT_ID"]
