"""CR-01: one writer per run, and an append that checks where it lands (review 04-REVIEW.md).

Two ``resume`` calls over one ledger both read N events, both derive the same next events and
interleave duplicate ``seq`` values, and the record is unreadable for good. The guard is an OS
lock held for the whole session (released by the operating system when the process dies, so there
is no stale-lock state) plus an ``append`` that refuses any event that does not follow the tail.
Every id and value is an invented fixture fact.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from conftest import REPO_ROOT, make_synthetic_root
from llm4pol.data import load
from llm4pol.run import __main__ as cli
from llm4pol.run import config, ledger, lock, resume, selector
from run_support import (
    FIXED_CODE_SHA,
    REFERENCE_PLAN,
    charter_problem,
    constant_clock,
    cut_run,
    reference_run,
    valid_event,
    valid_header,
)

FIXED_CODE = config.CodeIdentity(FIXED_CODE_SHA, False)
HOLDER = (
    "import sys\n"
    "from pathlib import Path\n"
    "from llm4pol.run import lock\n"
    "with lock.held(Path(sys.argv[1])):\n"
    "    print('locked', flush=True)\n"
    "    sys.stdin.read()\n"
)


@pytest.fixture(scope="module")
def table_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = make_synthetic_root(tmp_path_factory.mktemp("lock-table"))
    load.load(root)
    return root


@pytest.fixture(scope="module")
def reference(table_root: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    return reference_run(table_root, tmp_path_factory.mktemp("lock-reference") / "experiments")


def _holder(path: Path) -> subprocess.Popen[str]:
    """A second process that holds the lock on ``path`` until its stdin closes."""
    child = subprocess.Popen(
        [sys.executable, "-c", HOLDER, str(path)],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert child.stdout is not None
    assert child.stdout.readline().strip() == "locked"
    return child


@pytest.fixture
def held_elsewhere(reference: Path, tmp_path: Path) -> Iterator[tuple[Path, subprocess.Popen[str]]]:
    run_dir = cut_run(reference, tmp_path / "experiments", 5)
    child = _holder(run_dir / ledger.LEDGER_NAME)
    yield run_dir, child
    child.kill()
    child.wait()


def _selector() -> selector.PlanSelector:
    problem = config.parse_problem_spec(charter_problem(2, 3, 2))
    return selector.PlanSelector.from_payload(REFERENCE_PLAN, problem)


def test_a_second_holder_is_refused_and_the_release_frees_it(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    path.write_bytes(b"{}\n")
    with lock.held(path), pytest.raises(lock.RunLocked), lock.held(path):
        raise AssertionError("the second holder must not get in")
    with lock.held(path):
        pass


def test_the_lock_does_not_stand_in_the_way_of_reading_or_appending(
    reference: Path, tmp_path: Path
) -> None:
    run_dir = cut_run(reference, tmp_path / "experiments", 3)
    path = run_dir / ledger.LEDGER_NAME
    with lock.held(path):
        assert len(ledger.read(path).events) == 3
        ledger.append(path, valid_event("iteration_closed", 4))
        assert len(ledger.read(path).events) == 4


def test_a_lock_held_by_another_process_refuses_and_dying_releases_it(
    held_elsewhere: tuple[Path, subprocess.Popen[str]],
) -> None:
    run_dir, child = held_elsewhere
    path = run_dir / ledger.LEDGER_NAME
    with pytest.raises(lock.RunLocked), lock.held(path):
        raise AssertionError("the lock is held by another process")
    child.kill()
    child.wait()
    # The operating system releases the lock of a dead holder, on Windows a moment after the
    # process has gone: a short bounded retry keeps this from being flaky while it still asserts
    # that the lock IS eventually acquirable (RR-2).
    _acquirable_within(path, seconds=2.0)


def _acquirable_within(path: Path, *, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while True:
        try:
            with lock.held(path):
                return
        except lock.RunLocked:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.05)


def _spy_unlock(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]:
    """Record each explicit unlock the platform's locking call receives, with its file offset."""
    calls: list[tuple[str, int]] = []
    if sys.platform == "win32":
        import msvcrt

        real_locking: Callable[[int, int, int], None] = msvcrt.locking

        def locking(fd: int, mode: int, nbytes: int) -> None:
            if mode == msvcrt.LK_UNLCK:
                calls.append(("unlock", os.lseek(fd, 0, os.SEEK_CUR)))
            real_locking(fd, mode, nbytes)

        monkeypatch.setattr(msvcrt, "locking", locking)
    else:
        import fcntl

        real_flock: Callable[[int, int], None] = fcntl.flock

        def flock(fd: int, operation: int) -> None:
            if operation == fcntl.LOCK_UN:
                calls.append(("unlock", 0))
            real_flock(fd, operation)

        monkeypatch.setattr(fcntl, "flock", flock)
    return calls


def test_the_lock_is_explicitly_released_at_the_lock_offset_before_the_handle_closes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "ledger.jsonl"
    path.write_bytes(b"{}\n")
    calls = _spy_unlock(monkeypatch)
    with lock.held(path):
        assert calls == []
    expected = lock._WINDOWS_LOCK_OFFSET if sys.platform == "win32" else 0
    assert calls == [("unlock", expected)]  # exactly once, at the byte that was locked


def test_the_lock_is_released_when_the_block_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "ledger.jsonl"
    path.write_bytes(b"{}\n")
    calls = _spy_unlock(monkeypatch)
    with pytest.raises(RuntimeError, match="boom"), lock.held(path):
        raise RuntimeError("boom")
    assert len(calls) == 1
    _acquirable_within(path, seconds=2.0)


def test_a_refused_holder_does_not_unlock_the_lock_it_never_took(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "ledger.jsonl"
    path.write_bytes(b"{}\n")
    with lock.held(path):
        calls = _spy_unlock(monkeypatch)
        with pytest.raises(lock.RunLocked), lock.held(path):
            raise AssertionError("the second holder must not get in")
        assert calls == []  # the refused handle released nothing: the first holder still holds it
        with pytest.raises(lock.RunLocked), lock.held(path):
            raise AssertionError("the first holder must still hold the lock")


def test_drive_refuses_a_locked_run_and_appends_nothing(
    table_root: Path, held_elsewhere: tuple[Path, subprocess.Popen[str]]
) -> None:
    run_dir, _ = held_elsewhere
    before = (run_dir / ledger.LEDGER_NAME).read_bytes()
    with pytest.raises(lock.RunLocked):
        resume.resume(
            run_dir,
            root=table_root,
            selector=_selector(),
            code=FIXED_CODE,
            clock=constant_clock(),
        )
    assert (run_dir / ledger.LEDGER_NAME).read_bytes() == before
    assert not (run_dir / "results.csv").exists()


def test_the_cli_refuses_a_locked_run_with_its_own_exit_code(
    table_root: Path,
    held_elsewhere: tuple[Path, subprocess.Popen[str]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    run_dir, _ = held_elsewhere
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(REFERENCE_PLAN), encoding="utf-8")
    monkeypatch.setattr(cli, "code_identity", lambda: FIXED_CODE)
    before = (run_dir / ledger.LEDGER_NAME).read_bytes()
    capsys.readouterr()

    code = cli.main(
        [
            "resume",
            "--run",
            run_dir.name,
            "--selector",
            "plan",
            "--plan",
            str(plan),
            "--root",
            str(table_root),
            "--experiments",
            str(run_dir.parent),
        ]
    )

    captured = capsys.readouterr()
    assert code == cli.EXIT_LOCKED != 0
    assert captured.out == "ERROR: run is in use by another process\n"
    assert "detail:" in captured.err
    assert (run_dir / ledger.LEDGER_NAME).read_bytes() == before


def _seeded(tmp_path: Path, kinds: list[str]) -> Path:
    """A ledger holding the header and one valid event per kind, seq 1..n."""
    path = tmp_path / "ledger.jsonl"
    ledger.create(path, valid_header())
    for seq, kind in enumerate(kinds, start=1):
        ledger.append(path, valid_event(kind, seq))
    return path


@pytest.mark.parametrize("seq", [3, 1])  # a gap, a repeated seq
def test_append_requires_the_next_seq(tmp_path: Path, seq: int) -> None:
    path = _seeded(tmp_path, ["run_opened"])
    before = path.read_bytes()
    with pytest.raises(ledger.LedgerIntegrityError, match="follow"):
        ledger.append(path, valid_event("iteration_opened", seq))
    assert path.read_bytes() == before


def test_append_accepts_seq_one_after_the_header_only(tmp_path: Path) -> None:
    path = _seeded(tmp_path, [])
    ledger.append(path, valid_event("run_opened", 1))
    assert [e.seq for e in ledger.read(path).events] == [1]


def test_append_refuses_an_event_after_run_closed(tmp_path: Path) -> None:
    path = _seeded(tmp_path, ["run_opened", "run_closed"])
    before = path.read_bytes()
    with pytest.raises(ledger.LedgerIntegrityError, match="follow"):
        ledger.append(path, valid_event("iteration_opened", 3))
    assert path.read_bytes() == before


def test_append_refuses_an_event_of_another_run(tmp_path: Path) -> None:
    path = _seeded(tmp_path, ["run_opened"])
    foreign = valid_event("iteration_opened", 2)
    foreign["run_id"] = "20260202T000000Z-ffffffff"
    before = path.read_bytes()
    with pytest.raises(ledger.LedgerIntegrityError, match="follow"):
        ledger.append(path, foreign)
    assert path.read_bytes() == before
