"""The single local check command.

One command, identical on Windows and Linux: ``ruff check``, ``ruff format
--check``, ``mypy`` (strict, on ``src/``), the import boundary
(import-linter, via ``lint_imports_argv()``), and ``pytest``. Every external
tool is invoked through ``sys.executable -m`` or through the resolved
import-linter argv -- never a bare tool name, never ``shell=True`` -- so the
same invocation behaves identically on both platforms.

Does not read ``.env`` and does not print any environment-variable value.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import sysconfig
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def lint_imports_argv(extra: list[str] | None = None) -> list[str]:
    """Resolve the argv list that actually RUNS the import-linter checker.

    import-linter ships console scripts (``lint-imports``) but no
    ``__main__``, so ``python -m importlinter`` fails and
    ``python -m importlinter.cli`` exits 0 without evaluating any contract.
    This resolves the declared console script instead.

    Resolution order:
    1. ``shutil.which("lint-imports")``.
    2. The same script name inside ``sysconfig.get_path("scripts")``
       (``lint-imports.exe`` on Windows) -- covers an environment whose
       ``Scripts``/``bin`` directory is not on ``PATH``.
    3. Last resort: call ``importlinter.cli.lint_imports_command`` directly
       through ``sys.executable -c``; it still parses ``sys.argv`` and
       evaluates the configured contracts.
    """
    extra = list(extra) if extra else []

    found = shutil.which("lint-imports")
    if found:
        return [found, *extra]

    script_name = "lint-imports.exe" if os.name == "nt" else "lint-imports"
    scripts_dir = sysconfig.get_path("scripts")
    candidate = os.path.join(scripts_dir, script_name)
    if os.path.isfile(candidate):
        return [candidate, *extra]

    return [
        sys.executable,
        "-c",
        "from importlinter.cli import lint_imports_command; lint_imports_command()",
        *extra,
    ]


def _run(argv: list[str], cwd: Path) -> tuple[bool, str]:
    # encoding="utf-8" + errors="replace": tool output can contain non-ASCII
    # characters that are not valid in the platform's default locale encoding
    # (e.g. cp949 on a Korean-locale Windows machine), which would otherwise
    # crash the subprocess reader instead of reporting a clean FAIL.
    result = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode == 0, (result.stdout or "") + (result.stderr or "")


def _print_output(output: str) -> None:
    if output.strip():
        print(output, end="" if output.endswith("\n") else "\n")


def step_ruff_check() -> bool:
    ok, output = _run([sys.executable, "-m", "ruff", "check", "."], ROOT)
    _print_output(output)
    return ok


def step_ruff_format() -> bool:
    ok, output = _run([sys.executable, "-m", "ruff", "format", "--check", "."], ROOT)
    _print_output(output)
    return ok


def step_mypy() -> bool:
    ok, output = _run([sys.executable, "-m", "mypy"], ROOT)
    _print_output(output)
    return ok


def step_import_linter() -> bool:
    # The [tool.importlinter] section currently declares zero contracts;
    # contracts are added when the architecture is frozen. Running the tool
    # anyway keeps the step wired and proves the resolver works.
    ok, output = _run(lint_imports_argv(), ROOT)
    _print_output(output)
    return ok


def step_pytest() -> bool:
    ok, output = _run([sys.executable, "-m", "pytest"], ROOT)
    _print_output(output)
    return ok


# Ordered, appendable list of (name, callable) pairs -- later plans append
# steps here without editing the runner below.
STEPS: list[tuple[str, Callable[[], bool]]] = [
    ("ruff check", step_ruff_check),
    ("ruff format --check", step_ruff_format),
    ("mypy", step_mypy),
    ("import-linter", step_import_linter),
    ("pytest", step_pytest),
]


def main(argv: list[str] | None = None) -> int:
    # Tool output can contain characters that are not representable in the
    # platform's default console encoding; reconfigure so print() reports a
    # clean FAIL instead of raising UnicodeEncodeError.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    argv = list(argv) if argv is not None else sys.argv[1:]
    fast = "--fast" in argv

    steps = [s for s in STEPS if not (fast and s[0] == "mypy")]
    print("Steps: " + ", ".join(name for name, _ in steps))

    failed = 0
    for name, fn in steps:
        print(f"--- {name} ---")
        passed = fn()
        print(f"{'PASS' if passed else 'FAIL'} {name}")
        if not passed:
            failed += 1

    print(f"SUMMARY: {len(steps) - failed}/{len(steps)} steps passed")
    return failed


if __name__ == "__main__":
    sys.exit(main())
