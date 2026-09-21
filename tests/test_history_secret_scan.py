"""Positive and negative controls for ``scripts/history_secret_scan.py`` (D-01, R-3).

These tests promote invariant R-3 ("no secret value is printed, logged or
committed") from prose to a guard: every pattern class fires on its own
synthetic control, ordinary text never fires, a seeded secret in a temporary
repository turns the scan red without the value being printed, a committed
dotenv path turns it red, a clean repository scans green, and a shallow clone
is refused rather than scanned vacuously.

Every secret-shaped sample reuses the scanner's own runtime-built
``positive_control`` or is joined from fragments at runtime, and every dotenv
name is spelled ``"." + "env"`` -- this file is committed into the very
history the scanner walks, so a contiguous literal here would be a
self-inflicted hit on the next run.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from history_secret_scan import (
    PATTERNS,
    PatternClass,
    _join,
    _matches,
    is_dotenv_path,
    scan_history,
    self_test,
)

DOTENV = "." + "env"

EXPECTED_PATTERN_NAMES = {
    "openai_secret_key",
    "anthropic_secret_key",
    "google_ai_api_key",
    "huggingface_token",
    "github_token",
    "github_fine_grained_token",
    "aws_access_key_id",
    "slack_token",
    "private_key_header",
    "generic_credential_assignment",
}

ORDINARY_PROSE = (
    "Thermal conductivity in a polymer rises with chain alignment of the repeat units, and "
    "tacticity sets how densely they pack. The dielectric constant and the glass transition "
    "shift with side-group polarity."
)

SHORT_IDENTIFIERS = [
    "id",
    "SECRET",
    "TOKEN",
    "key",
    "x",
    "config",
    "settings_hash",
    "PYTHONPATH=src",
]

# Benign lines observed in vendored framework source and workstation config.
# The scanner must not flag them (the opposite risk from a pattern that
# matches nothing): an "sk-" substring inside an ordinary word, dotted config
# values, digit-free identifier mirrors, and their unquoted dotenv-style forms.
FALSE_POSITIVE_REGRESSIONS = [
    "task-content-resolution-seam.md",
    "GIT_CONFIG_KEY_0: 'diff.ignoreSubmodules'",
    "ADD_AI_INTEGRATION_PHASE_KEY: 'addAiIntegrationPhaseKey'",
    "CONFIG_KEY_NOT_FOUND: 'config_key_not_found'",
    "GSD_TOKEN_BUDGET=smart_zone_default_profile",
    "CACHE_KEY=diff.ignoreSubmodules.v2",
]

_GIT_IDENTITY = [
    "-c",
    "user.name=llm4pol-test",
    "-c",
    "user.email=test@example.invalid",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "init.defaultBranch=main",
]


def _git(root: Path, *args: str) -> str:
    """Run git inside ``root`` only; never against the real repository."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"}
    }
    result = subprocess.run(
        ["git", *_GIT_IDENTITY, *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout


def _seed_repo(root: Path, files: dict[str, str]) -> str:
    """Create a repository under ``root`` with one commit of ``files``; return its sha."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    _git(root, "add", "--force", "--", *files)
    _git(root, "commit", "-q", "-m", "seed")
    return _git(root, "rev-parse", "HEAD").strip()


def _pattern(name: str) -> PatternClass:
    return next(p for p in PATTERNS if p.name == name)


# --- positive controls ------------------------------------------------------


def test_every_pattern_matches_its_positive_control() -> None:
    for pattern in PATTERNS:
        matches = list(_matches(pattern, pattern.positive_control))
        assert matches, f"{pattern.name} did not match its own positive control"


def test_pattern_names_are_exactly_the_declared_set() -> None:
    names = [pattern.name for pattern in PATTERNS]
    assert len(names) == 10, f"expected 10 pattern classes, found {len(names)}: {names}"
    assert set(names) == EXPECTED_PATTERN_NAMES, f"pattern set drifted: {sorted(names)}"


def test_self_test_exits_zero_and_reports_every_class(capsys: pytest.CaptureFixture[str]) -> None:
    assert self_test() == 0
    out = capsys.readouterr().out
    assert "SELF-TEST OK: 10 pattern classes each matched their positive control" in out
    for pattern in PATTERNS:
        assert f"self-test {pattern.name}:" in out, f"no self-test line for {pattern.name}"


# --- negative controls ------------------------------------------------------


def test_ordinary_prose_does_not_match_any_pattern() -> None:
    for pattern in PATTERNS:
        assert not list(_matches(pattern, ORDINARY_PROSE)), f"{pattern.name} matched prose"


def test_short_identifiers_do_not_match_any_pattern() -> None:
    for identifier in SHORT_IDENTIFIERS:
        for pattern in PATTERNS:
            assert not list(_matches(pattern, identifier)), (
                f"{pattern.name} matched short identifier {identifier!r}"
            )


def test_generic_pattern_requires_an_actual_assignment() -> None:
    generic = _pattern("generic_credential_assignment")
    assert not list(_matches(generic, "API_KEY"))
    assert not list(_matches(generic, 'API_KEY = "short"'))
    value = _join("abcdEFGH", "12345678", "wxyz9012")
    unquoted = _join("MY_API_", "KEY", "=", value)
    quoted = _join("MY_API_", "KEY", '="', value, '"')
    assert list(_matches(generic, unquoted)), "unquoted dotenv-style assignment must match"
    assert list(_matches(generic, quoted)), "double-quoted assignment must match"


def test_known_false_positive_lines_do_not_match_any_pattern() -> None:
    for line in FALSE_POSITIVE_REGRESSIONS:
        for pattern in PATTERNS:
            assert not list(_matches(pattern, line)), (
                f"{pattern.name} matched known-benign line {line!r}"
            )


# --- dotenv path detection --------------------------------------------------


def test_dotenv_paths_are_flagged_and_example_is_not() -> None:
    assert is_dotenv_path(DOTENV)
    assert is_dotenv_path(DOTENV + ".local")
    assert is_dotenv_path("nested/dir/" + DOTENV)
    assert not is_dotenv_path(DOTENV + ".example")
    assert not is_dotenv_path("nested/" + DOTENV + ".example")
    assert not is_dotenv_path("scripts/check.py")
    assert not is_dotenv_path("environment.py")
    assert not is_dotenv_path("env/pixi.toml")


# --- temp-repo end-to-end ---------------------------------------------------


def test_seeded_secrets_in_temp_repo_are_detected_without_printing_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "seeded"
    files = {f"{p.name}.txt": "note: " + p.positive_control + "\n" for p in PATTERNS}
    sha = _seed_repo(root, files)

    assert scan_history(root) == 1
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert "scanned 1 commit(s)" in output
    for pattern in PATTERNS:
        expected = f"HIT pattern={pattern.name} commit={sha} path={pattern.name}.txt"
        assert expected in output, f"missing hit line for {pattern.name}"
        assert pattern.positive_control not in output, f"{pattern.name} value was printed"


def test_seeded_dotenv_file_in_temp_repo_is_detected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "dotenv"
    flagged = [DOTENV, "sub/" + DOTENV + ".local"]
    allowed = DOTENV + ".example"
    files = {name: "PLACEHOLDER=1\n" for name in [*flagged, allowed]}
    _seed_repo(root, files)

    assert scan_history(root) == 1
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert "dotenv-path-in-history: 2 hit(s)" in output
    for path in flagged:
        assert f"HIT dotenv-path-in-history path={path}" in output
    assert f"HIT dotenv-path-in-history path={allowed}" not in output


def test_clean_temp_repo_scans_green(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "clean"
    _seed_repo(root, {"notes.md": ORDINARY_PROSE + "\n"})

    assert scan_history(root) == 0
    out = capsys.readouterr().out
    assert "no secrets found in any reachable commit; dotenv path never committed" in out


def test_shallow_repository_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "src"
    _seed_repo(src, {"notes.md": ORDINARY_PROSE + "\n"})
    dst = tmp_path / "shallow"
    # A file:// URI is required: git silently ignores --depth on a plain local path.
    _git(tmp_path, "clone", "-q", "--depth", "1", src.as_uri(), str(dst))

    assert scan_history(dst) == 2
    err = capsys.readouterr().err
    assert "refusing to scan a shallow repository" in err
