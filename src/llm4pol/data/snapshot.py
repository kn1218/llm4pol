"""The pinned PolyOmics snapshot: one place for the revision and every path.

The revision is a full 40-hex Hugging Face commit sha (CONTEXT D-01, RESEARCH
F-01). The snapshot identifier ``polyomics:general_polymers@041e5834`` is the
charter section 7 form and is written into both parquets and the report.
"""

from __future__ import annotations

from pathlib import Path

POLYOMICS_REPO = "yhayashi1986/PolyOmics"
POLYOMICS_REVISION = "041e5834ea1a48682fae12dc39ccd723bcd4f771"
POLYOMICS_REVISION_SHORT = POLYOMICS_REVISION[:8]
POLYOMICS_CONFIG = "general_polymers"
CSV_NAME = "general_polymers_with_sp_abbe_dynamic-dielectric.csv"
README_NAME = "README.md"
SNAPSHOT_ID = f"polyomics:{POLYOMICS_CONFIG}@{POLYOMICS_REVISION_SHORT}"

# src/llm4pol/data/snapshot.py -> repository root. The project runs from
# source with PYTHONPATH=src (env/pixi.toml), never from an installed wheel.
DEFAULT_ROOT = Path(__file__).resolve().parents[3]


def raw_dir(root: Path) -> Path:
    """``root/data/raw/polyomics/<revision>`` -- where the pinned files live."""
    return root / "data" / "raw" / "polyomics" / POLYOMICS_REVISION


def csv_path(root: Path) -> Path:
    """The pinned config CSV."""
    return raw_dir(root) / CSV_NAME


def readme_path(root: Path) -> Path:
    """The pinned dataset card."""
    return raw_dir(root) / README_NAME


def manifest_path(root: Path) -> Path:
    """``root/data/MANIFEST-open.sha256`` -- the committed sha256 + size list."""
    return root / "data" / "MANIFEST-open.sha256"


def processed_dir(root: Path) -> Path:
    """``root/data/processed`` -- git-ignored parquet output directory."""
    return root / "data" / "processed"


def rows_parquet(directory: Path) -> Path:
    """The row-level parquet inside ``directory``."""
    return directory / f"polyomics-{POLYOMICS_REVISION_SHORT}.parquet"


def candidates_parquet(directory: Path) -> Path:
    """The candidate parquet inside ``directory``."""
    return directory / f"candidates-{POLYOMICS_REVISION_SHORT}.parquet"


def report_path(root: Path) -> Path:
    """``root/docs/audit/polyomics-<short>-validation.md`` -- the number authority."""
    return root / "docs" / "audit" / f"polyomics-{POLYOMICS_REVISION_SHORT}-validation.md"
