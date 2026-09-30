"""IN-03: ``replay --out`` follows the rule of ``write_outputs``: it never overwrites a differing file.

``(args.out / name).write_bytes(data)`` replaced whatever was in ``--out``, so a rerun into a
populated directory silently changed earlier replay output, while everything else in the package
"never overwrites". Now a file that is present must hold the bytes the ledger reduces to (else
exit 4 and nothing is written, into ``--out`` or into the run directory), an equal file is left as
it is, and an absent one is written atomically.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from llm4pol.run import __main__ as cli
from llm4pol.run import ledger, reduce
from run_support import FIXED_RUN_ID

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "run" / "reference-ledger.jsonl"
OUTPUTS = (reduce.RESULTS_NAME, reduce.USAGE_NAME, reduce.SUMMARY_NAME)


@pytest.fixture
def experiments(tmp_path: Path) -> Path:
    run_dir = tmp_path / "experiments" / FIXED_RUN_ID
    run_dir.mkdir(parents=True)
    shutil.copyfile(FIXTURE, run_dir / ledger.LEDGER_NAME)
    return tmp_path / "experiments"


def _replay(experiments: Path, out: Path) -> int:
    return cli.main(
        ["replay", "--run", FIXED_RUN_ID, "--experiments", str(experiments), "--out", str(out)]
    )


def _names(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.iterdir())


def test_replay_out_refuses_a_differing_file_and_writes_nothing_anywhere(
    experiments: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / reduce.USAGE_NAME).write_bytes(b"earlier replay output\n")
    capsys.readouterr()

    code = _replay(experiments, out)

    captured = capsys.readouterr()
    assert code == cli.EXIT_INTEGRITY
    assert captured.out == "ERROR: ledger integrity check failed\n"
    assert reduce.USAGE_NAME in captured.err and "differs" in captured.err
    assert (out / reduce.USAGE_NAME).read_bytes() == b"earlier replay output\n"
    assert _names(out) == [reduce.USAGE_NAME]  # the other two were not written either
    assert _names(experiments / FIXED_RUN_ID) == [ledger.LEDGER_NAME]  # nor the run directory


def test_replay_out_keeps_equal_files_and_writes_the_absent_ones(
    experiments: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    assert _replay(experiments, out) == cli.EXIT_OK
    assert _names(out) == sorted(OUTPUTS)
    first = {name: (out / name).read_bytes() for name in OUTPUTS}
    (out / reduce.SUMMARY_NAME).unlink()

    assert _replay(experiments, out) == cli.EXIT_OK  # equal files stay, the missing one returns

    assert {name: (out / name).read_bytes() for name in OUTPUTS} == first
    assert not any(out.glob("*.tmp"))


def test_replay_out_writes_the_same_bytes_as_the_run_directory(
    experiments: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    assert _replay(experiments, out) == cli.EXIT_OK
    run_dir = experiments / FIXED_RUN_ID
    for name in OUTPUTS:
        assert (out / name).read_bytes() == (run_dir / name).read_bytes()
