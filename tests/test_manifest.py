"""Repository-layout and data-manifest checks.

These are the only tests that exist before the charter is approved: they
prove the package imports, that any raw data file present locally matches
``data/MANIFEST.sha256``, and that the audit report the project is founded
on is in the tree.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import llm4pol

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "MANIFEST.sha256"
RAW_DIR = ROOT / "data" / "raw"
AUDIT_REPORT = ROOT / "docs" / "audit" / "DATA-FOUNDATION-REPORT.md"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_manifest(path: Path) -> dict[str, tuple[str, int]]:
    """Return ``{filename: (sha256, size_bytes)}`` from the manifest.

    Format, one entry per non-comment line: ``<sha256>  <size_bytes>  <filename>``.
    """
    entries: dict[str, tuple[str, int]] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        sha, size, name = line.split(None, 2)
        entries[name] = (sha, int(size))
    return entries


def test_package_imports() -> None:
    assert llm4pol.__version__ == "0.0.1"


def test_manifest_exists_and_is_well_formed() -> None:
    assert MANIFEST.is_file(), f"missing {MANIFEST}"
    entries = _parse_manifest(MANIFEST)
    assert entries, "manifest lists no files"
    for name, (sha, size) in entries.items():
        assert len(sha) == 64, f"{name}: sha256 must be 64 hex characters"
        int(sha, 16)
        assert size > 0, f"{name}: size must be positive"


def test_raw_files_match_manifest() -> None:
    entries = _parse_manifest(MANIFEST)
    present = {name: RAW_DIR / name for name in entries if (RAW_DIR / name).is_file()}
    if not present:
        pytest.skip(
            "no PoLyInfo-derived raw files under data/raw/ (they are never committed; "
            "see data/README.md)"
        )
    for name, path in present.items():
        expected_sha, expected_size = entries[name]
        assert path.stat().st_size == expected_size, f"{name}: size mismatch"
        assert _sha256(path) == expected_sha, f"{name}: sha256 mismatch"


def test_audit_report_present() -> None:
    assert AUDIT_REPORT.is_file(), f"missing {AUDIT_REPORT}"
