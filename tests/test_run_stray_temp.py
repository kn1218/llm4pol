"""RR-4: a resume clears the stray ``.<name>.<pid>.tmp`` files a crashed ``write_new`` left.

``atomic.write_new`` puts the bytes in ``.<name>.<pid>.tmp`` before it publishes them. A process
killed between the two leaves that file behind, with no target. The next ``resume`` (which holds
the run lock, so no other driver is writing) removes files of exactly that shape from the run
directory, and nothing else: not a file another tool put there, not a directory, not the record.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import make_synthetic_root
from llm4pol.data import load
from llm4pol.run import atomic, config, ledger, resume, selector
from run_support import (
    FIXED_CODE_SHA,
    REFERENCE_PLAN,
    charter_problem,
    constant_clock,
    cut_run,
    reference_run,
)

STRAY = (
    ".results.csv.4242.tmp",
    ".usage.json.7.tmp",
    ".run_summary.json.99999.tmp",
    ".meta.json.1.tmp",
)
KEPT = (
    ".results.csv.tmp",  # no pid
    ".results.csv.12.tmp.bak",  # another suffix
    "results.csv.12.tmp",  # no leading dot
    ".notes.txt",  # not a temporary
    ".x.abc.tmp",  # the pid is not a number
    "..12.tmp",  # no name
)


@pytest.fixture(scope="module")
def table_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = make_synthetic_root(tmp_path_factory.mktemp("stray-table"))
    load.load(root)
    return root


@pytest.fixture(scope="module")
def reference(table_root: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    return reference_run(table_root, tmp_path_factory.mktemp("stray-reference") / "experiments")


def _names(directory: Path) -> set[str]:
    return {p.name for p in directory.iterdir()}


def _litter(directory: Path) -> None:
    for name in (*STRAY, *KEPT):
        (directory / name).write_bytes(b"x")
    (directory / ".dir.5.tmp").mkdir()  # a directory of the shape is not a file write_new made


def test_remove_stray_temporaries_removes_exactly_the_write_new_shape(tmp_path: Path) -> None:
    _litter(tmp_path)
    removed = atomic.remove_stray_temporaries(tmp_path)
    assert sorted(removed) == sorted(STRAY)
    assert _names(tmp_path) == {*KEPT, ".dir.5.tmp"}


def test_remove_stray_temporaries_on_a_clean_directory_is_a_no_op(tmp_path: Path) -> None:
    (tmp_path / "ledger.jsonl").write_bytes(b"{}\n")
    assert atomic.remove_stray_temporaries(tmp_path) == []
    assert _names(tmp_path) == {"ledger.jsonl"}


def _selector() -> selector.PlanSelector:
    problem = config.parse_problem_spec(charter_problem(2, 3, 2))
    return selector.PlanSelector.from_payload(REFERENCE_PLAN, problem)


@pytest.mark.parametrize("k", [5, 17])  # an open run, a run whose ledger is complete
def test_resume_clears_the_stray_temporaries_of_its_run_directory(
    table_root: Path, reference: Path, tmp_path: Path, k: int
) -> None:
    run_dir = cut_run(reference, tmp_path / "experiments", k)
    _litter(run_dir)
    before = (run_dir / ledger.LEDGER_NAME).read_bytes()

    resume.resume(
        run_dir,
        root=table_root,
        selector=_selector(),
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
        clock=constant_clock(),
    )

    assert not any(name in _names(run_dir) for name in STRAY)
    assert {*KEPT, ".dir.5.tmp"} <= _names(run_dir)
    assert (run_dir / ledger.LEDGER_NAME).read_bytes().startswith(before)  # only ever appended to
