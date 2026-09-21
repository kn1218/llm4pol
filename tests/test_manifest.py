"""Repository-layout and data-manifest checks.

These tests predate the charter: they prove the package imports, that any raw
data file present locally matches ``data/MANIFEST.sha256``, and that the audit
report the project is founded on is in the tree. Since plan 02-03 they also
prove the shared manifest parser: the PoLyInfo manifest is read by the same
``parse_manifest`` and ``sha256_of`` that ``python -m llm4pol.data fetch``
uses on ``data/MANIFEST-open.sha256`` (RESEARCH "Don't Hand-Roll").
"""

from __future__ import annotations

from pathlib import Path

import pytest

import llm4pol
from llm4pol.data.fetch import parse_manifest, sha256_of

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "MANIFEST.sha256"
RAW_DIR = ROOT / "data" / "raw"
AUDIT_REPORT = ROOT / "docs" / "audit" / "DATA-FOUNDATION-REPORT.md"


def test_package_imports() -> None:
    assert llm4pol.__version__ == "0.0.1"


def test_manifest_exists_and_is_well_formed() -> None:
    assert MANIFEST.is_file(), f"missing {MANIFEST}"
    entries = parse_manifest(MANIFEST).entries
    assert entries, "manifest lists no files"
    for name, (sha, size) in entries.items():
        assert len(sha) == 64, f"{name}: sha256 must be 64 hex characters"
        int(sha, 16)
        assert size > 0, f"{name}: size must be positive"


def test_raw_files_match_manifest() -> None:
    entries = parse_manifest(MANIFEST).entries
    present = {name: RAW_DIR / name for name in entries if (RAW_DIR / name).is_file()}
    if not present:
        pytest.skip(
            "no PoLyInfo-derived raw files under data/raw/ (they are never committed; "
            "see data/README.md)"
        )
    for name, path in present.items():
        expected_sha, expected_size = entries[name]
        assert path.stat().st_size == expected_size, f"{name}: size mismatch"
        assert sha256_of(path) == expected_sha, f"{name}: sha256 mismatch"


def test_audit_report_present() -> None:
    assert AUDIT_REPORT.is_file(), f"missing {AUDIT_REPORT}"
