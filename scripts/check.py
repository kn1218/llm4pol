"""The single local check command.

One command, identical on Windows and Linux: ``ruff check``, ``ruff format
--check``, ``mypy`` (strict, on ``src/``), the import boundary
(import-linter, via ``lint_imports_argv()``), the explicit schema-validation
inventory (``[tool.llm4polcheck]`` in ``pyproject.toml``, via
``validate_inventory()``: every listed protocol instance is validated against
its JSON Schema -- invariant "a payload with no schema has no guard",
CLAUDE.md; CONTEXT D-06), the history secret scan
(``scripts/history_secret_scan.py``, called in-process: self-test, then a
walk of every reachable commit -- invariant R-3), and ``pytest``. Every
external tool is invoked through ``sys.executable -m`` or through the
resolved import-linter argv -- never a bare tool name, never through a
shell -- so the same invocation behaves identically on both platforms.

``validate_inventory`` and ``STEPS`` are imported by
``tests/test_check_inventory.py`` (via ``tests/conftest.py``'s ``sys.path``
insertion) so there is exactly one definition of the inventory step -- the
test suite runs the same function this command runs.

Does not read ``.env`` and does not print any environment-variable value.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import sysconfig
import tomllib
from collections.abc import Callable
from pathlib import Path

import jsonschema
import yaml

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


def validate_inventory(root: str | os.PathLike[str]) -> list[str]:
    """Validate the explicit ``[tool.llm4polcheck]`` schema-validation inventory.

    Reads ``pyproject.toml`` at ``root`` and returns a list of failure
    messages (empty means everything validated). Fails when:

    - the ``[tool.llm4polcheck]`` table is absent entirely (a missing
      inventory cannot silently mean "nothing to validate");
    - a declared ``schema`` path does not exist;
    - a ``required = true`` entry's ``instances`` glob matches zero files;
    - a matched instance fails to validate against its declared schema.

    A sibling-schema discovery rule would let a deleted or renamed schema
    silently remove its own validation; the inventory is explicit instead.
    YAML instances (``.yaml`` / ``.yml``) are loaded with ``yaml.safe_load``
    and validated exactly like JSON ones, never skipped. Prints how many
    inventory entries and how many instances were processed, so a zero-entry
    inventory is visible in the check output rather than silent.
    """
    root = Path(root)
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.is_file():
        return [f"pyproject.toml not found at {pyproject_path}"]

    with open(pyproject_path, "rb") as fh:
        data = tomllib.load(fh)

    llm4polcheck = data.get("tool", {}).get("llm4polcheck")
    if llm4polcheck is None:
        return [
            (
                "[tool.llm4polcheck] table is absent from pyproject.toml -- "
                "schema validation cannot be silenced by deletion"
            )
        ]

    entries = llm4polcheck.get("validated", [])
    failures: list[str] = []
    n_instances = 0

    for entry in entries:
        name = entry.get("name", "<unnamed>")
        schema_rel = entry.get("schema")
        instances_glob = entry.get("instances")
        required = bool(entry.get("required", False))

        if not schema_rel:
            failures.append(f"{name}: entry declares no 'schema' path")
            continue

        schema_path = root / schema_rel
        if not schema_path.is_file():
            failures.append(f"{name}: declared schema path {schema_rel!r} does not exist")
            continue

        with open(schema_path, encoding="utf-8") as sf:
            schema = json.load(sf)

        matches = sorted(root.glob(instances_glob)) if instances_glob else []
        if required and not matches:
            failures.append(
                f"{name}: required=true but instances glob {instances_glob!r} matched zero files"
            )
            continue

        n_instances += len(matches)
        for match in matches:
            with open(match, encoding="utf-8") as mf:
                if match.suffix.lower() in (".yaml", ".yml"):
                    instance = yaml.safe_load(mf)
                else:
                    instance = json.load(mf)
            try:
                jsonschema.validate(instance=instance, schema=schema)
            except jsonschema.ValidationError as exc:
                failures.append(f"{name}: instance {match} failed schema validation: {exc.message}")

    print(f"llm4polcheck inventory: {len(entries)} entries, {n_instances} instances processed")
    return failures


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


def step_schema_inventory() -> bool:
    failures = validate_inventory(ROOT)
    for failure in failures:
        print(f"  - {failure}")
    return not failures


def step_history_secret_scan() -> bool:
    # In-process call of the scanner's main (no child process, no shell).
    # The self-test runs first so a zero-match regex fails the step before a
    # vacuous scan could pass it; the scan itself refuses a shallow clone.
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from history_secret_scan import main as scan_main

    return scan_main(["--self-test"]) == 0 and scan_main([]) == 0


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
    ("schema-inventory", step_schema_inventory),
    ("history-secret-scan", step_history_secret_scan),
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
