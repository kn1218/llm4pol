"""The fetch contract (CONTEXT D-01, D-10; DATA-01): every failure path and its exit code.

Runs on the synthetic root of ``conftest.py`` (D-09) with a fake downloader
that records the keyword arguments ``hf_hub_download`` receives and writes
bytes into ``local_dir / filename`` the way the library does. Nothing here
touches the network; the on-disk hash is the only verification (RESEARCH Q5,
threat T-02-14). The last test pins the committed manifest's content to the
research hashes (F-02, F-03).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from conftest import MANIFEST_HEADER, REPO_ROOT
from llm4pol.data import snapshot
from llm4pol.data.fetch import fetch as run_fetch
from llm4pol.data.fetch import parse_manifest, sha256_of

CSV_SHA = "71e955ac1e90574ad009ccbf1238e595cf42905f3e600523ba2a6ea65c350213"
README_SHA = "c2340252a720f7b9f56fcc368105d9e1e351c2bd75f31a364f7c2afcb5a6cc13"


def _recording_downloader(
    bytes_by_name: dict[str, bytes],
) -> tuple[Callable[..., str], list[dict[str, Any]]]:
    """A fake ``hf_hub_download``: records each call's kwargs, writes the bytes it knows."""
    calls: list[dict[str, Any]] = []

    def download(
        *, repo_id: str, repo_type: str, filename: str, revision: str, local_dir: Path
    ) -> str:
        calls.append(
            {
                "repo_id": repo_id,
                "repo_type": repo_type,
                "filename": filename,
                "revision": revision,
                "local_dir": local_dir,
            }
        )
        target = Path(local_dir) / filename
        if filename in bytes_by_name:
            target.write_bytes(bytes_by_name[filename])
        return str(target)

    return download, calls


def _raise(*_args: Any, **_kwargs: Any) -> str:
    raise AssertionError("downloader must not be called")


def _rewrite_manifest(root: Path, entries: dict[str, tuple[str, int]], revision: str) -> None:
    header = MANIFEST_HEADER.replace(snapshot.POLYOMICS_REVISION, revision)
    lines = [header] + [f"{sha}  {size}  {name}\n" for name, (sha, size) in entries.items()]
    snapshot.manifest_path(root).write_text("".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------
# parse_manifest
# --------------------------------------------------------------------------


def test_parse_manifest_reads_revision_header_and_entries(tmp_path: Path) -> None:
    manifest = tmp_path / "MANIFEST-open.sha256"
    manifest.write_text(
        "# first comment\n"
        "# second comment\n"
        f"# revision: {snapshot.POLYOMICS_REVISION}\n"
        "\n"
        f"{CSV_SHA}  10  a.csv\n"
        f"{README_SHA}  3  README.md\n",
        encoding="utf-8",
    )
    parsed = parse_manifest(manifest)
    assert parsed.revision == snapshot.POLYOMICS_REVISION
    assert parsed.entries == {"a.csv": (CSV_SHA, 10), "README.md": (README_SHA, 3)}


def test_parse_manifest_rejects_malformed_lines(tmp_path: Path) -> None:
    short_sha = tmp_path / "short.sha256"
    short_sha.write_text(f"# revision: {snapshot.POLYOMICS_REVISION}\n{CSV_SHA[:63]}  10  a.csv\n")
    with pytest.raises(ValueError, match=r":2:"):
        parse_manifest(short_sha)

    bad_size = tmp_path / "size.sha256"
    bad_size.write_text(f"{CSV_SHA}  ten  a.csv\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r":1:"):
        parse_manifest(bad_size)

    no_header = tmp_path / "noheader.sha256"
    no_header.write_text(f"{CSV_SHA}  10  a.csv\n", encoding="utf-8")
    assert parse_manifest(no_header).revision is None
    assert parse_manifest(no_header).entries == {"a.csv": (CSV_SHA, 10)}


# --------------------------------------------------------------------------
# fetch on the synthetic root
# --------------------------------------------------------------------------


def test_fetch_verifies_existing_files_and_never_calls_the_downloader(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_fetch(synthetic_root, downloader=_raise) == 0
    out = capsys.readouterr().out
    assert f"verified {snapshot.CSV_NAME}" in out
    assert f"verified {snapshot.README_NAME}" in out
    assert "snapshot: polyomics:general_polymers@041e5834" in out


def test_fetch_downloads_a_missing_file_then_verifies_it(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    readme = snapshot.readme_path(synthetic_root)
    original = readme.read_bytes()
    readme.unlink()
    download, calls = _recording_downloader({"README.md": original})

    assert run_fetch(synthetic_root, downloader=download) == 0

    assert len(calls) == 1
    assert calls[0] == {
        "repo_id": snapshot.POLYOMICS_REPO,
        "repo_type": "dataset",
        "filename": "README.md",
        "revision": snapshot.POLYOMICS_REVISION,
        "local_dir": snapshot.raw_dir(synthetic_root),
    }
    assert readme.read_bytes() == original
    assert (
        sha256_of(readme)
        == parse_manifest(snapshot.manifest_path(synthetic_root)).entries["README.md"][0]
    )
    out = capsys.readouterr().out
    assert "downloaded README.md" in out
    assert f"verified {snapshot.CSV_NAME}" in out


def test_fetch_returns_1_on_sha256_mismatch_and_names_the_file(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    readme = snapshot.readme_path(synthetic_root)
    readme.write_bytes(readme.read_bytes() + b"\n")
    expected_sha = parse_manifest(snapshot.manifest_path(synthetic_root)).entries["README.md"][0]
    download, calls = _recording_downloader({})

    assert run_fetch(synthetic_root, downloader=download) == 1

    out = capsys.readouterr().out
    assert f"MISMATCH README.md expected sha256={expected_sha[:12]}…" in out
    assert "observed sha256=" in out
    assert f"verified {snapshot.CSV_NAME}" in out
    assert calls == [], "a present file is never re-downloaded; it is reported (D-01)"


def test_fetch_returns_1_on_size_mismatch_in_the_manifest(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entries = dict(parse_manifest(snapshot.manifest_path(synthetic_root)).entries)
    csv_sha, csv_size = entries[snapshot.CSV_NAME]
    entries[snapshot.CSV_NAME] = (csv_sha, csv_size + 1)
    _rewrite_manifest(synthetic_root, entries, snapshot.POLYOMICS_REVISION)
    download, _calls = _recording_downloader({})

    assert run_fetch(synthetic_root, downloader=download) == 1

    out = capsys.readouterr().out
    assert f"MISMATCH {snapshot.CSV_NAME}" in out
    assert "size=" in out


def test_fetch_returns_1_when_manifest_revision_differs_from_the_constant(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entries = dict(parse_manifest(snapshot.manifest_path(synthetic_root)).entries)
    _rewrite_manifest(synthetic_root, entries, "f" * 40)

    assert run_fetch(synthetic_root, downloader=_raise) == 1

    out = capsys.readouterr().out
    assert "MISMATCH revision" in out
    assert "verified" not in out


def test_fetch_returns_2_when_manifest_is_missing(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    snapshot.manifest_path(synthetic_root).unlink()

    assert run_fetch(synthetic_root, downloader=_raise) == 2

    err = capsys.readouterr().err
    assert err.startswith("ERROR:")
    assert "MANIFEST-open.sha256" in err


def test_fetch_returns_2_when_downloader_raises(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    snapshot.readme_path(synthetic_root).unlink()

    def offline(**_kwargs: Any) -> str:
        raise OSError("offline")

    assert run_fetch(synthetic_root, downloader=offline) == 2

    err = capsys.readouterr().err
    assert "ERROR:" in err
    assert "README.md" in err


def test_fetch_checks_every_file_before_returning(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for path in (snapshot.csv_path(synthetic_root), snapshot.readme_path(synthetic_root)):
        path.write_bytes(path.read_bytes() + b"x")
    download, _calls = _recording_downloader({})

    assert run_fetch(synthetic_root, downloader=download) == 1

    out = capsys.readouterr().out
    mismatch_lines = [line for line in out.splitlines() if line.startswith("MISMATCH ")]
    assert len(mismatch_lines) == 2
    assert any(snapshot.CSV_NAME in line for line in mismatch_lines)
    assert any("README.md" in line for line in mismatch_lines)


# --------------------------------------------------------------------------
# the committed manifest (F-02, F-03)
# --------------------------------------------------------------------------


def test_committed_manifest_open_lists_the_two_pinned_files_with_research_hashes() -> None:
    parsed = parse_manifest(REPO_ROOT / "data" / "MANIFEST-open.sha256")
    assert parsed.revision == snapshot.POLYOMICS_REVISION
    assert parsed.entries == {
        snapshot.CSV_NAME: (CSV_SHA, 196910783),
        "README.md": (README_SHA, 15532),
    }
