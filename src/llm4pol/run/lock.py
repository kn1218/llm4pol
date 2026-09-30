"""An exclusive OS-level lock on a run's ledger for a whole run or resume session (CR-01).

Two drivers over one ledger each derive the same next events from their own snapshot and
interleave duplicate ``seq`` values, which no reader can repair. ``held`` takes the lock on the
ledger file before the driver reads it and keeps it until the session ends. The operating system
drops the lock when the holding process dies, so a killed run leaves no stale-lock state and no
file to clean up.

POSIX uses ``fcntl.flock`` (advisory, whole file). Windows uses ``msvcrt.locking``, whose ranges are
mandatory: the locked range is one byte at an offset far beyond any ledger, so no line of the
ledger is ever inside it and reading and appending in the holding process stay unaffected.

The module imports the standard library only.
"""

from __future__ import annotations

import errno
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

_WINDOWS_LOCK_OFFSET = 1 << 40  # bytes past the end of any ledger; msvcrt locks are mandatory


_HELD = frozenset({errno.EACCES, errno.EAGAIN, errno.EDEADLK})  # what a refused lock reports


class RunLocked(RuntimeError):
    """Another process holds the ledger of this run."""


def _acquire(handle: BinaryIO) -> None:
    """Take the lock without waiting; ``OSError`` when another handle holds it."""
    if sys.platform == "win32":
        import msvcrt

        os.lseek(handle.fileno(), _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


@contextmanager
def held(path: Path) -> Iterator[None]:
    """Hold the exclusive lock on ``path`` inside the block; ``RunLocked`` when it is taken.

    ``FileNotFoundError`` when ``path`` does not exist: the lock never creates a file.
    """
    with path.open("rb") as handle:
        try:
            _acquire(handle)
        except OSError as exc:
            if exc.errno not in _HELD:
                raise
            raise RunLocked(f"{path.name} is locked by another process") from exc
        yield  # the OS releases the lock when the handle closes or the process dies
