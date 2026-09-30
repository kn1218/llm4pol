"""IN-04: the ``git`` calls behind ``code_identity`` time out and keep git's own reason.

``subprocess.run(..., check=False)`` had no timeout, so a stuck ``git`` (an index lock, a network
file system) hung ``run`` and ``resume`` for good, and on failure the message was only ``git <verb>
failed in <repo>``, with git's stderr (``detected dubious ownership``) captured and discarded.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from llm4pol.run import config


def _fake_run(monkeypatch: pytest.MonkeyPatch, behaviour: Any) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"argv": argv, **kwargs})
        return behaviour(argv, **kwargs)

    monkeypatch.setattr(config.subprocess, "run", run)
    return calls


def test_every_git_call_has_a_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = _fake_run(
        monkeypatch, lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout="abc\n")
    )
    config.code_identity(tmp_path)
    assert len(calls) == 2
    assert all(call["timeout"] == config.GIT_TIMEOUT_SECONDS > 0 for call in calls)


def test_a_stuck_git_is_a_code_identity_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def hang(argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(argv, kw["timeout"])

    _fake_run(monkeypatch, hang)
    with pytest.raises(config.CodeIdentityError, match=r"git rev-parse timed out after \d+"):
        config.code_identity(tmp_path)


def test_the_first_line_of_gits_stderr_is_kept(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    stderr = "\nfatal: detected dubious ownership in repository at 'X'\nhint: to add an exception\n"
    _fake_run(
        monkeypatch, lambda argv, **kw: subprocess.CompletedProcess(argv, 128, "", stderr=stderr)
    )
    with pytest.raises(config.CodeIdentityError) as refused:
        config.code_identity(tmp_path)
    message = str(refused.value)
    assert "dubious ownership" in message and "hint" not in message
    assert message.startswith("git rev-parse failed in")


def test_a_very_long_stderr_line_is_cut(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _fake_run(
        monkeypatch,
        lambda argv, **kw: subprocess.CompletedProcess(argv, 1, "", stderr="fatal: " + "x" * 5000),
    )
    with pytest.raises(config.CodeIdentityError) as refused:
        config.code_identity(tmp_path)
    assert len(str(refused.value)) < 400


def test_a_directory_that_is_not_a_repository_says_so(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    with pytest.raises(config.CodeIdentityError, match="not a git repository"):
        config.code_identity(tmp_path)
