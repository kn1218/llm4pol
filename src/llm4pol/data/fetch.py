"""Fetch the pinned PolyOmics files and verify them against ``data/MANIFEST-open.sha256``.

CONTEXT D-01: a file is downloaded with ``hf_hub_download`` at the pinned
revision only when absent; whatever is on disk is then verified by byte size
and streamed sha256 against the committed manifest, and a present file that
mismatches is reported, never re-downloaded (the library's local fast path
would return it unchanged, RESEARCH Q5). The download-metadata sidecar the
library writes under ``local_dir`` (F-05) is never read: the payload hash is
the only verification (threat T-02-01). No child process, no shell.
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import hf_hub_download

from llm4pol.data import snapshot

Downloader = Callable[..., str]

_HEX = frozenset("0123456789abcdef")
_REVISION_PREFIX = "# revision:"


@dataclass(frozen=True)
class Manifest:
    """The parsed manifest: the ``# revision:`` header and ``{name: (sha256, size)}``."""

    revision: str | None
    entries: dict[str, tuple[str, int]]


@dataclass(frozen=True)
class FileCheck:
    """One file compared against its manifest entry."""

    name: str
    ok: bool
    observed_sha: str | None
    observed_size: int | None


def parse_manifest(path: Path) -> Manifest:
    """Parse ``<sha256>  <size_bytes>  <filename>`` lines and the ``# revision:`` header.

    The one parser for ``data/MANIFEST-open.sha256`` and ``data/MANIFEST.sha256``
    (``tests/test_manifest.py`` imports it). A malformed line raises
    ``ValueError`` naming the file and the 1-based line number; a manifest
    without a ``# revision:`` header parses with ``revision`` ``None``.
    """
    revision: str | None = None
    entries: dict[str, tuple[str, int]] = {}
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.startswith(_REVISION_PREFIX):
                revision = line[len(_REVISION_PREFIX) :].strip()
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            raise ValueError(
                f"{path}:{lineno}: expected '<sha256>  <size_bytes>  <filename>', got {raw_line!r}"
            )
        sha, size_text, name = parts
        if len(sha) != 64 or not set(sha) <= _HEX:
            raise ValueError(f"{path}:{lineno}: sha256 must be 64 lowercase hex characters")
        try:
            size = int(size_text)
        except ValueError as exc:
            raise ValueError(
                f"{path}:{lineno}: size must be an integer, got {size_text!r}"
            ) from exc
        if size <= 0:
            raise ValueError(f"{path}:{lineno}: size must be positive")
        entries[name] = (sha, size)
    return Manifest(revision=revision, entries=entries)


def sha256_of(path: Path) -> str:
    """Streamed sha256 (1 MiB chunks) of ``path``."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, sha: str, size: int) -> FileCheck:
    """Compare ``path`` with the manifest entry by byte size and sha256."""
    if not path.is_file():
        return FileCheck(name=path.name, ok=False, observed_sha=None, observed_size=None)
    observed_size = path.stat().st_size
    observed_sha = sha256_of(path)
    return FileCheck(
        name=path.name,
        ok=observed_size == size and observed_sha == sha,
        observed_sha=observed_sha,
        observed_size=observed_size,
    )


def _short(sha: str | None) -> str:
    """The first 12 hex characters of ``sha`` followed by an ellipsis (or ``none``)."""
    return f"{sha[:12]}…" if sha else "none"


def _report(name: str, check: FileCheck, sha: str, size: int, origin: str) -> None:
    """Print the ``verified`` / ``downloaded`` / ``MISMATCH`` line for one file."""
    if check.ok:
        print(f"{origin} {name} size={check.observed_size} sha256={_short(check.observed_sha)}")
        return
    print(
        f"MISMATCH {name} expected sha256={_short(sha)} size={size} "
        f"observed sha256={_short(check.observed_sha)} size={check.observed_size}"
    )


def _download(download: Downloader, name: str, target_dir: Path) -> bool:
    """Call the downloader for one absent file; any failure is reported and returns False.

    Only ``Exception`` is caught, and only here: every huggingface_hub error
    (``HfHubHTTPError``, ``LocalEntryNotFoundError``, ...) is an ``Exception``
    subclass (threat T-02-17); ``KeyboardInterrupt`` propagates.
    """
    try:
        download(
            repo_id=snapshot.POLYOMICS_REPO,
            repo_type="dataset",
            filename=name,
            revision=snapshot.POLYOMICS_REVISION,
            local_dir=target_dir,
        )
    except Exception as exc:  # noqa: BLE001 -- the library's error tree is open-ended (T-02-17)
        print(f"ERROR: download failed for {name}: {exc}", file=sys.stderr)
        return False
    return True


def fetch(root: Path, *, downloader: Downloader | None = None) -> int:
    """Verify the pinned files under ``root``; download only what is absent.

    ``downloader`` defaults to this module's ``hf_hub_download`` (looked up at
    call time so tests can monkeypatch it). The manifest revision is checked
    before any file; every entry is then hashed and sized, and every mismatch
    is printed before the return value is decided (threat T-02-14). Returns 0
    when every entry verifies, 1 on any ``MISMATCH`` (file or revision), 2
    when the manifest is missing or malformed or the downloader raises.
    """
    manifest_file = snapshot.manifest_path(root)
    if not manifest_file.is_file():
        print(f"ERROR: manifest not found: {manifest_file}", file=sys.stderr)
        return 2
    try:
        manifest = parse_manifest(manifest_file)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if manifest.revision != snapshot.POLYOMICS_REVISION:
        print(
            f"MISMATCH revision expected={snapshot.POLYOMICS_REVISION} manifest={manifest.revision}"
        )
        return 1
    missing = [
        name for name in (snapshot.CSV_NAME, snapshot.README_NAME) if name not in manifest.entries
    ]
    if missing:
        print(f"ERROR: {manifest_file} has no entry for {', '.join(missing)}", file=sys.stderr)
        return 2

    download = downloader if downloader is not None else hf_hub_download
    target_dir = snapshot.raw_dir(root)
    checks: list[FileCheck] = []
    for name, (sha, size) in manifest.entries.items():
        path = target_dir / name
        origin = "verified"
        if not path.is_file():
            if not _download(download, name, target_dir):
                return 2
            origin = "downloaded"
        check = verify_file(path, sha, size)
        _report(name, check, sha, size, origin)
        checks.append(check)
    if not all(check.ok for check in checks):
        return 1
    print(f"snapshot: {snapshot.SNAPSHOT_ID}")
    return 0
