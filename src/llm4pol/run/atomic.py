"""Files of the run record that appear whole or not at all (WR-03).

``write_new`` writes the bytes to a temporary file in the target's directory, fsyncs it, and only
then publishes it under the target name without overwriting: ``os.link`` then an unlink of the
temporary on POSIX (``os.rename`` there would replace a target), ``os.rename`` on Windows (it
fails when the target exists). A process that dies mid-write leaves a stray ``.<name>.<pid>.tmp``
and no target, so a rerun writes the file, where an in-place ``xb`` write would leave a truncated
target that every later run reads as tampering. The temporary is removed whenever the write
fails.

``fsync_dir`` makes a new directory entry durable: an fsynced file can still vanish after a power
loss on POSIX when its entry was never synced. Windows cannot open a directory for fsync, so
there it does nothing (``DIRECTORY_FSYNC``).

An operating-system failure while writing the run record is a ``RecordWriteError`` (an
``OSError``): the CLI reports it as an I/O failure, not as a defect of the operator's input, and
for an append it names the byte offset after which a torn line may now sit (IN-02).

A present target is never replaced: ``FileExistsError`` names it and its bytes are untouched,
also when a concurrent writer creates the target between the pre-check and the publish, because
the publish itself refuses an existing target (RR-3). A caller that writes bytes a ledger
determines uses ``write_new_or_keep``, which compares the bytes (``reduce.write_outputs``).

The module imports the standard library only.
"""

from __future__ import annotations

import os
from pathlib import Path

DIRECTORY_FSYNC = os.name == "posix"
PUBLISH_WITH_LINK = os.name == "posix"  # rename replaces a target there; a hard link does not


class RecordWriteError(OSError):
    """The operating system failed while a file of the run record was being written.

    ``last_lf_offset`` is the offset of the last LF the ledger held before the failed append (the
    byte after which a torn line may follow), or ``None`` when the failure was not an append.
    """

    def __init__(self, message: str, *, last_lf_offset: int | None = None) -> None:
        super().__init__(message)
        self.last_lf_offset = last_lf_offset


def _sync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def fsync_dir(directory: Path) -> None:
    """Make the entries of ``directory`` durable on POSIX; nothing where that is unsupported."""
    if DIRECTORY_FSYNC:
        _sync_directory(directory)


def _publish(temporary: Path, path: Path) -> None:
    """Give ``temporary`` the name ``path``, which must be absent (``FileExistsError`` if not)."""
    if PUBLISH_WITH_LINK:
        try:
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    else:
        os.rename(temporary, path)


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
        _publish(temporary, path)
        fsync_dir(path.parent)
    except FileExistsError:
        raise FileExistsError(f"{path} exists; it is never overwritten") from None
    except OSError as exc:
        raise RecordWriteError(f"writing {path.name} failed: {exc}") from exc
    finally:
        # Nothing to remove after a publish; after any failure the temporary must not stay.
        # A failed removal is left for the next resume of the run to clear (RR-4).
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def write_new_or_keep(path: Path, data: bytes) -> bool:
    """``write_new``, but a target that exists is judged by its bytes: True when it holds ``data``.

    The target may have been there already or created a moment ago by a concurrent writer (RR-3);
    either way nothing is overwritten. False means the file holds other bytes.
    """
    try:
        write_new(path, data)
    except FileExistsError:
        return path.read_bytes() == data
    return True
