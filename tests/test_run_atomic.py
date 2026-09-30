"""WR-03: the reduced files and ``meta.json`` are written atomically (review 04-REVIEW.md).

A file opened ``xb`` and written in place leaves a truncated ``results.csv`` when the process
dies mid-write, and the next ``resume``, ``replay`` or ``usage`` then reads it as tampering
(``differs from what the ledger reduces to``) with no way back. The bytes now go to a temporary
file in the same directory, are fsynced, and only then replace the absent target, so a reader
sees the whole file or none, and a rerun completes what a crash left. The rule that a present
file is never overwritten is unchanged.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from llm4pol.run import atomic, config, ledger, reduce
from run_support import (
    FIXED_CODE_SHA,
    FIXED_RUN_ID,
    REFERENCE_RESULTS_CSV,
    charter_problem,
    valid_header,
)

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "run" / "reference-ledger.jsonl"
OUTPUTS = (reduce.RESULTS_NAME, reduce.USAGE_NAME, reduce.SUMMARY_NAME)


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    target = tmp_path / FIXED_RUN_ID
    target.mkdir()
    shutil.copyfile(FIXTURE, target / ledger.LEDGER_NAME)
    return target


def _names(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.iterdir())


def _fail_nth_replace(monkeypatch: pytest.MonkeyPatch, nth: int) -> list[tuple[Path, Path]]:
    """Make the ``nth`` (1-based) ``os.replace`` of ``atomic`` raise; record every call."""
    real: Callable[..., None] = atomic.os.replace
    calls: list[tuple[Path, Path]] = []

    def replace(src: str | Path, dst: str | Path) -> None:
        calls.append((Path(src), Path(dst)))
        if len(calls) == nth:
            raise OSError("disk full")
        real(src, dst)

    monkeypatch.setattr(atomic.os, "replace", replace)
    return calls


def test_write_new_writes_through_a_temp_in_the_same_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    real_fsync = atomic.os.fsync
    real_replace = atomic.os.replace

    def fsync(fd: int) -> None:
        events.append("fsync")
        real_fsync(fd)

    def replace(src: str | Path, dst: str | Path) -> None:
        events.append(f"replace:{Path(src).parent == Path(dst).parent}")
        real_replace(src, dst)

    monkeypatch.setattr(atomic.os, "fsync", fsync)
    monkeypatch.setattr(atomic.os, "replace", replace)

    atomic.write_new(tmp_path / "out.csv", b"a,b\n")

    assert (tmp_path / "out.csv").read_bytes() == b"a,b\n"
    assert events[:2] == ["fsync", "replace:True"]  # the data is durable before it is published
    assert _names(tmp_path) == ["out.csv"]


def test_write_new_never_overwrites_a_present_file(tmp_path: Path) -> None:
    target = tmp_path / "out.csv"
    target.write_bytes(b"old")
    with pytest.raises(FileExistsError):
        atomic.write_new(target, b"new")
    assert target.read_bytes() == b"old"
    assert _names(tmp_path) == ["out.csv"]


def test_a_failure_before_the_replace_leaves_no_target_and_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fail_nth_replace(monkeypatch, 1)
    with pytest.raises(OSError, match="disk full"):
        atomic.write_new(tmp_path / "out.csv", b"data")
    assert _names(tmp_path) == []


def test_a_crash_between_the_files_is_completed_by_the_rerun(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _fail_nth_replace(monkeypatch, 2)
    with pytest.raises(OSError, match="disk full"):
        reduce.write_outputs(run_dir)
    assert _names(run_dir) == sorted([ledger.LEDGER_NAME, OUTPUTS[0]])
    assert (run_dir / OUTPUTS[0]).read_bytes() == REFERENCE_RESULTS_CSV  # whole, never a prefix
    assert all(src.parent == run_dir for src, _ in calls)

    monkeypatch.undo()
    sums = reduce.write_outputs(run_dir)  # nothing is blocked; the missing two are written
    assert _names(run_dir) == sorted([ledger.LEDGER_NAME, *OUTPUTS])
    assert set(sums) == set(OUTPUTS)


def test_write_outputs_still_refuses_a_differing_file_and_keeps_an_equal_one(
    run_dir: Path,
) -> None:
    reduce.write_outputs(run_dir)
    before = {name: (run_dir / name).read_bytes() for name in OUTPUTS}
    reduce.write_outputs(run_dir)  # equal bytes: nothing to do
    assert {name: (run_dir / name).read_bytes() for name in OUTPUTS} == before
    (run_dir / reduce.USAGE_NAME).write_bytes(b"{}\n")
    with pytest.raises(ledger.LedgerIntegrityError, match="differs"):
        reduce.write_outputs(run_dir)
    assert (run_dir / reduce.USAGE_NAME).read_bytes() == b"{}\n"


def test_write_meta_is_atomic_and_exclusive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = config.parse_problem_spec(charter_problem(1, 3, 2))
    meta = config.build_meta(
        run_id=FIXED_RUN_ID,
        created_at="2026-01-01T00:00:00Z",
        problem=problem,
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
        snapshot="polyomics:general_polymers@041e5834",
        snapshot_sha256="0" * 64,
        registry_version="v1",
        selector="plan:sha256:" + "0" * 64,
        environ={},
    )
    _fail_nth_replace(monkeypatch, 1)
    with pytest.raises(OSError, match="disk full"):
        config.write_meta(tmp_path, meta)
    assert _names(tmp_path) == []
    monkeypatch.undo()
    config.write_meta(tmp_path, meta)
    assert _names(tmp_path) == [config.META_NAME]
    with pytest.raises(FileExistsError):
        config.write_meta(tmp_path, meta)


# --------------------------------------------------------------------------
# WR-06: the directory entry of a new file is made durable (POSIX; a no-op where a directory
# cannot be fsynced)
# --------------------------------------------------------------------------


@pytest.fixture
def synced(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Path, tuple[str, ...]]]:
    """Force directory fsync on and record each call with the names present in that directory."""
    calls: list[tuple[Path, tuple[str, ...]]] = []

    def spy(directory: Path) -> None:
        calls.append((directory, tuple(_names(directory))))

    monkeypatch.setattr(atomic, "DIRECTORY_FSYNC", True)
    monkeypatch.setattr(atomic, "_sync_directory", spy)
    return calls


def test_fsync_dir_is_a_no_op_when_the_platform_cannot_do_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(directory: Path) -> None:
        raise AssertionError("a directory fsync was attempted")

    monkeypatch.setattr(atomic, "DIRECTORY_FSYNC", False)
    monkeypatch.setattr(atomic, "_sync_directory", refuse)
    atomic.fsync_dir(tmp_path)
    atomic.write_new(tmp_path / "out.csv", b"x")
    ledger.create(tmp_path / "ledger.jsonl", valid_header())


def test_fsync_dir_syncs_a_real_directory_on_posix_and_is_off_elsewhere(tmp_path: Path) -> None:
    assert atomic.DIRECTORY_FSYNC is (os.name == "posix")
    atomic.fsync_dir(tmp_path)  # a real directory fsync on POSIX, nothing on Windows


def test_the_ledger_is_synced_into_its_directory_after_create(
    tmp_path: Path, synced: list[tuple[Path, tuple[str, ...]]]
) -> None:
    ledger.create(tmp_path / "ledger.jsonl", valid_header())
    assert synced == [(tmp_path, ("ledger.jsonl",))]  # the entry existed when it was synced


def test_write_new_syncs_the_directory_after_the_replace(
    tmp_path: Path, synced: list[tuple[Path, tuple[str, ...]]]
) -> None:
    atomic.write_new(tmp_path / "out.csv", b"x")
    assert synced == [(tmp_path, ("out.csv",))]  # no temporary name is left to sync


def test_meta_and_every_output_are_synced(
    run_dir: Path, synced: list[tuple[Path, tuple[str, ...]]]
) -> None:
    reduce.write_outputs(run_dir)
    assert [directory for directory, _ in synced] == [run_dir] * 3
    assert [names for _, names in synced][-1] == tuple(sorted([ledger.LEDGER_NAME, *OUTPUTS]))
    synced.clear()
    problem = config.parse_problem_spec(charter_problem(1, 3, 2))
    meta = config.build_meta(
        run_id=FIXED_RUN_ID,
        created_at="2026-01-01T00:00:00Z",
        problem=problem,
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
        snapshot="polyomics:general_polymers@041e5834",
        snapshot_sha256="0" * 64,
        registry_version="v1",
        selector="plan:sha256:" + "0" * 64,
        environ={},
    )
    config.write_meta(run_dir, meta)
    assert [directory for directory, _ in synced] == [run_dir]


def test_a_new_run_directory_is_synced_into_the_experiments_directory(
    tmp_path: Path, synced: list[tuple[Path, tuple[str, ...]]]
) -> None:
    experiments = tmp_path / "experiments"
    config.create_run_dir(experiments, FIXED_RUN_ID)
    assert synced == [(experiments, (FIXED_RUN_ID,))]
