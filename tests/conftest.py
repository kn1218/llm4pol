"""Shared pytest fixtures and path setup.

Inserts the repository's ``scripts/`` directory at the front of ``sys.path``
so tests can ``from history_secret_scan import ...`` -- the same module
``scripts/check.py`` runs as its ``history-secret-scan`` step. This is what
makes "the test exercises the scanner the gate runs" literally true rather
than a coincidence of two copied files.

``tests/`` has no ``__init__.py``, so this is a plain ``sys.path`` insertion,
not a dotted-package import.

Data fixtures (CONTEXT D-09): the pinned PolyOmics CSV is never committed, so
every logic test runs on ``SYNTHETIC_ROWS`` -- 14 invented rows of textbook
repeat units, none copied from the file (``data/README.md``) -- written to a
fake repository root by ``synthetic_root``. The real-file fixtures ``real_csv``
and ``real_load`` skip with a stated reason when the pinned file is absent.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
import pytest

from llm4pol.data import snapshot

if TYPE_CHECKING:
    from llm4pol.data.load import LoadResult

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def repo_root() -> Path:
    """The repository root directory."""
    return REPO_ROOT


# --------------------------------------------------------------------------
# Synthetic PolyOmics fixture (D-09). Facts of this fixture, cited by tests:
#   14 source rows, 23 columns, 10 unique smiles_list;
#   row 13 excluded as second-monomer (before parsing), row 12 excluded as a
#   parse failure -> 12 in-scope rows; 7 unique canonical strings (rows 7 and
#   8 merge; `*OC*` canonicalises to `*CO*`); 9 candidates (`*CC*`/none n=3,
#   `*CC*`/unknown n=1, `*CC(*)C`/isotactic, `*CC(*)C`/atactic,
#   `*CC(*)c1ccccc1`/atactic n=2, and four singletons); 2 multi-row
#   candidates holding 5 rows, max group size 3.
# --------------------------------------------------------------------------

_MISSING = None

# (smiles_list, smiles_2, tacticity, thermal_conductivity, dielectric_const_dc,
#  refractive_index, tg, tg_rmse, check_tc)
_CORE: list[tuple[Any, ...]] = [
    ("*CC*", _MISSING, "none", 0.30, 2.30, 1.50, 250.0, 0.05, True),
    ("*CC*", _MISSING, "none", 0.34, 2.36, 1.50, 270.0, 0.08, True),
    ("*CC*", _MISSING, "none", 0.32, 2.33, 1.50, 260.0, 0.15, True),
    ("*CC(*)C", _MISSING, "isotactic", 0.20, 2.20, 1.45, 450.0, 0.02, True),
    ("*CC(*)C", _MISSING, "atactic", 0.18, 2.25, 1.45, 400.0, 0.03, True),
    ("*CC*", _MISSING, _MISSING, 0.31, 2.34, 1.50, 265.0, 0.06, True),
    ("*CC(*)c1ccccc1", _MISSING, "atactic", 0.15, 2.60, 1.59, 380.0, 0.01, True),
    ("C(C*)(*)c1ccccc1", _MISSING, "atactic", 0.16, 2.62, 1.59, 375.0, 0.02, True),
    ("*CC(*)C(=O)OC", _MISSING, "atactic", 0.19, 25.0, 1.49, 390.0, 0.05, True),
    ("*CC(*)(C)C(=O)OC", _MISSING, "none", 15.0, 3.00, 1.49, 1.0e6, 5.0, False),
    ("*OC*", _MISSING, "none", _MISSING, 3.10, 1.48, 200.0, 0.05, _MISSING),
    ("*C(", _MISSING, "none", 0.20, 2.50, 1.50, 300.0, 0.05, True),
    ("*CC*,*OC*", "*OC*", "none", 0.25, 2.40, 1.50, 320.0, 0.05, True),
    ("*CC(*)F", _MISSING, "none", 0.22, 2.10, 1.40, _MISSING, _MISSING, True),
]


def _synthetic_row(index: int, core: tuple[Any, ...]) -> dict[str, object]:
    smiles_list, smiles_2, tacticity, tc, eps_dc, ri, tg, tg_rmse, check_tc = core
    smiles_1 = "*CC*" if smiles_2 is not None else smiles_list
    # F-14 identity: dielectric_const_dc = static_dielectric_const - 1 + refractive_index**2,
    # so the Maxwell tests of plan 02-05 hold on this fixture by construction.
    static = eps_dc + 1.0 - ri**2
    return {
        "UUID": f"u{index:02d}",
        "smiles_list": smiles_list,
        "smiles_1": smiles_1,
        "smiles_2": smiles_2,
        "tacticity": tacticity,
        "thermal_conductivity": tc,
        "dielectric_const_dc": eps_dc,
        "refractive_index": ri,
        "tg": tg,
        "tg_rmse": tg_rmse,
        "check_tc": check_tc,
        "static_dielectric_const": static,
        "Rg": 20.0,
        "r2": 4.0,
        "fractional_free_volume": 0.18,
        "sp_ced": 300.0,
        "density": 1.0,
        "temp": 300.0,
        "press": 1.0,
        "forcefield": "GAFF2_mod",
        "RadonPy_ver": "0.2.10",
        "do_TC": True,
        "extra_note": "synthetic",
    }


SYNTHETIC_ROWS: list[dict[str, object]] = [
    _synthetic_row(i, core) for i, core in enumerate(_CORE, start=1)
]

SYNTHETIC_README = (
    "# Synthetic PolyOmics card\n"
    "Three invented lines standing in for the dataset card.\n"
    "Nothing here is copied from the pinned file.\n"
)

MANIFEST_HEADER = (
    "# data/MANIFEST-open.sha256 -- PolyOmics general_polymers at one pinned Hugging Face "
    "revision (CC BY 4.0, never committed for size)\n"
    f"# revision: {snapshot.POLYOMICS_REVISION}\n"
    "# source: https://huggingface.co/datasets/yhayashi1986/PolyOmics  (repo_type=dataset)\n"
    "# Format: <sha256>  <size_bytes>  <filename>   "
    "(files live under data/raw/polyomics/<revision>/)\n"
)


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(root: Path, files: list[Path]) -> Path:
    """Write ``root/data/MANIFEST-open.sha256`` for ``files`` (sha256, size, name)."""
    lines = [MANIFEST_HEADER]
    for path in files:
        lines.append(f"{sha256_of_file(path)}  {path.stat().st_size}  {path.name}\n")
    manifest = snapshot.manifest_path(root)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("".join(lines), encoding="utf-8")
    return manifest


@pytest.fixture
def synthetic_root(tmp_path: Path) -> Path:
    """A fake repository root holding the 14-row synthetic CSV, README and manifest."""
    raw = snapshot.raw_dir(tmp_path)
    raw.mkdir(parents=True)
    csv = snapshot.csv_path(tmp_path)
    pd.DataFrame(SYNTHETIC_ROWS).to_csv(csv, index=False)
    readme = snapshot.readme_path(tmp_path)
    readme.write_text(SYNTHETIC_README, encoding="utf-8")
    write_manifest(tmp_path, [csv, readme])
    snapshot.processed_dir(tmp_path).mkdir(parents=True)
    (tmp_path / "docs" / "audit").mkdir(parents=True)
    return tmp_path


# --------------------------------------------------------------------------
# Real-file fixtures (charter section 13 M1 reproductions; CI skips them).
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_csv() -> Path:
    path = snapshot.csv_path(REPO_ROOT)
    if not path.is_file():
        pytest.skip(
            f"pinned PolyOmics file absent at {path} "
            "(never committed; run python -m llm4pol.data fetch)"
        )
    return path


@pytest.fixture(scope="session")
def real_load(real_csv: Path, tmp_path_factory: pytest.TempPathFactory) -> LoadResult:
    """Run ``load.load`` on the real repository once per session, writing to a temp dir.

    Never writes into the real ``data/processed/`` from a test (T-02-07).
    """
    from llm4pol.data import load

    return load.load(REPO_ROOT, processed_dir=tmp_path_factory.mktemp("processed"))
