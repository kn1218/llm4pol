"""IN-02: an OS error while writing the run record is an I/O failure, not "input refused".

``OSError`` sat in the CLI's input errors, so ``ENOSPC`` or ``EIO`` raised while an event was
appended (which is how a torn tail is made) was reported as a defect of the operator's input, with
exit 2, although the run is then unresumable until the torn line is dealt with. It now has its own
error, exit code and message, and the detail names the byte offset the torn tail follows.
"""

from __future__ import annotations

import errno
import json
from pathlib import Path
from typing import Any

import pytest

from llm4pol.run import __main__ as cli
from llm4pol.run import atomic, ledger
from run_support import (
    TRACER_PLAN,
    charter_problem,
    valid_event,
    valid_header,
)


def _partial_then_fail(monkeypatch: pytest.MonkeyPatch, fail_at: int) -> None:
    """Make the ``fail_at``-th append (1-based) write half its line and raise ``ENOSPC``."""
    real = ledger._write
    appends = 0

    def write(path: Path, mode: str, data: bytes) -> None:
        nonlocal appends
        if mode == "ab":
            appends += 1
            if appends == fail_at:
                with path.open("ab") as fh:
                    fh.write(data[: len(data) // 2])
                raise OSError(errno.ENOSPC, "No space left on device")
        real(path, mode, data)

    monkeypatch.setattr(ledger, "_write", write)


def test_a_failed_append_is_a_record_write_error_naming_the_torn_tail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / ledger.LEDGER_NAME
    ledger.create(path, valid_header())
    ledger.append(path, valid_event("run_opened", 1))
    size = path.stat().st_size
    _partial_then_fail(monkeypatch, 1)

    with pytest.raises(atomic.RecordWriteError) as failed:
        ledger.append(path, valid_event("iteration_opened", 2))

    assert isinstance(failed.value, OSError)  # library callers that catch OSError still do
    assert failed.value.last_lf_offset == size - 1
    message = str(failed.value)
    assert "No space left on device" in message
    assert f"byte offset {size - 1}" in message and "torn" in message
    monkeypatch.undo()
    with pytest.raises(ledger.TornTail):  # the partial line is there and is refused, not repaired
        ledger.read(path)


def test_a_failed_create_and_a_failed_output_are_record_write_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(path: Path, mode: str, data: bytes) -> None:
        raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(ledger, "_write", refuse)
    with pytest.raises(atomic.RecordWriteError, match="Input/output error"):
        ledger.create(tmp_path / ledger.LEDGER_NAME, valid_header())
    monkeypatch.undo()

    def replace(src: Any, dst: Any) -> None:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(atomic.os, "replace", replace)
    with pytest.raises(atomic.RecordWriteError, match="No space left on device"):
        atomic.write_new(tmp_path / "results.csv", b"x")
    assert not any(tmp_path.glob("*.tmp"))


def test_a_deliberate_refusal_to_overwrite_stays_a_file_exists_error(tmp_path: Path) -> None:
    (tmp_path / "out").write_bytes(b"x")
    with pytest.raises(FileExistsError) as refused:
        atomic.write_new(tmp_path / "out", b"y")
    assert not isinstance(refused.value, atomic.RecordWriteError)


def _cli_run(tmp_path: Path, root: Path) -> list[str]:
    problem = tmp_path / "problem.json"
    problem.write_text(json.dumps(charter_problem(1, 3, 2)), encoding="utf-8")
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(TRACER_PLAN), encoding="utf-8")
    return [
        "run",
        "--problem",
        str(problem),
        "--selector",
        "plan",
        "--plan",
        str(plan),
        "--root",
        str(root),
        "--experiments",
        str(tmp_path / "experiments"),
    ]


def test_the_cli_reports_an_io_failure_with_its_own_exit_code_and_line(
    synthetic_candidates: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _partial_then_fail(monkeypatch, 3)
    capsys.readouterr()

    code = cli.main(_cli_run(tmp_path, synthetic_candidates))

    captured = capsys.readouterr()
    assert code == cli.EXIT_IO
    assert captured.out.splitlines()[-1] == "ERROR: I/O failure while writing the run record"
    assert "input refused" not in captured.out
    assert "torn" in captured.err and "byte offset" in captured.err
    (run_dir,) = (tmp_path / "experiments").iterdir()
    with pytest.raises(ledger.TornTail):
        ledger.read(run_dir / ledger.LEDGER_NAME)


def test_an_unreadable_input_is_still_an_input_refusal(
    synthetic_candidates: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _cli_run(tmp_path, synthetic_candidates)
    args[args.index("--problem") + 1] = str(tmp_path / "missing.json")
    capsys.readouterr()
    assert cli.main(args) == cli.EXIT_INPUT
    assert capsys.readouterr().out == "ERROR: input refused\n"
