"""Files of the run record that appear whole or not at all (WR-03).

``write_new`` writes the bytes to a temporary file in the target's directory, fsyncs it, and only
then ``os.replace``s it onto the target, which must be absent. A process that dies mid-write
leaves a stray ``.<name>.<pid>.tmp`` and no target, so a rerun writes the file, where an
in-place ``xb`` write would leave a truncated target that every later run reads as tampering.

A present target is never replaced: ``FileExistsError`` names it and its bytes are untouched. The
check and the replace are two steps, which is safe here because the callers write bytes a ledger
determines and hold the run lock (or write identical bytes), so a racing writer writes the same
file.

The module imports the standard library only.
"""

from __future__ import annotations

import os
from pathlib import Path


def write_new(path: Path, data: bytes) -> None:
    """Write ``data`` to the absent ``path`` atomically; ``FileExistsError`` when it exists."""
    if path.exists():
        raise FileExistsError(f"{path} exists; it is never overwritten")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
