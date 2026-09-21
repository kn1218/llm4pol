"""Fetch the pinned PolyOmics files and verify them against ``data/MANIFEST-open.sha256``.

CONTEXT D-01: the two files are downloaded with ``hf_hub_download`` at the
pinned revision only when absent; whatever is on disk is then verified by
byte size and streamed sha256 against the committed manifest. The library's
own etag fast path is never trusted (RESEARCH Q5, threat T-02-01): the hash on
disk is the only verification. No child process, no shell.
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import hf_hub_download
from huggingface_hub.errors import EntryNotFoundError

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

    Same three-field split as ``tests/test_manifest.py::_parse_manifest``; a
    malformed line raises ``ValueError`` naming the line.
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
            raise ValueError(f"{path}:{lineno}: size must be an integer, got {size_text!r}") from exc
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


def _verified_line(name: str, check: FileCheck, origin: str) -> str:
    sha = check.observed_sha or ""
    return f"verified {name} size={check.observed_size} sha256={sha[:12]}… ({origin})"


def fetch(root: Path, *, downloader: Downloader | None = None) -> int:
    """Verify the pinned files under ``root``; download only what is absent or wrong.

    ``downloader`` defaults to this module's ``hf_hub_download`` (looked up at
    call time so tests can monkeypatch it). Returns 0 when every manifest
    entry verifies, 1 on a hash / size / revision mismatch, 2 on an I/O error.
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
            f"MISMATCH revision expected={snapshot.POLYOMICS_REVISION} "
            f"manifest={manifest.revision}"
        )
        return 1

    download = downloader if downloader is not None else hf_hub_download
    target_dir = snapshot.raw_dir(root)
    mismatched = False
    for name in (snapshot.CSV_NAME, snapshot.README_NAME):
        if name not in manifest.entries:
            print(f"ERROR: {manifest_file} has no entry for {name}", file=sys.stderr)
            return 2
        sha, size = manifest.entries[name]
        path = target_dir / name
        if path.is_file():
            check = verify_file(path, sha, size)
            if check.ok:
                print(_verified_line(name, check, "existing"))
                continue
        try:
            download(
                repo_id=snapshot.POLYOMICS_REPO,
                repo_type="dataset",
                filename=name,
                revision=snapshot.POLYOMICS_REVISION,
                local_dir=target_dir,
            )
        except (OSError, EntryNotFoundError) as exc:
            print(f"ERROR: download of {name} failed: {exc}", file=sys.stderr)
            return 2
        check = verify_file(path, sha, size)
        if check.ok:
            print(_verified_line(name, check, "downloaded"))
        else:
            print(
                f"MISMATCH {name} expected sha256={sha} size={size} "
                f"observed sha256={check.observed_sha} size={check.observed_size}"
            )
            mismatched = True
    if mismatched:
        return 1
    print(f"snapshot: {snapshot.SNAPSHOT_ID}")
    return 0
