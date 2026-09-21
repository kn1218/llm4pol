"""The import boundary is frozen and its guards are live (D-06, R-1, EVAL-06, A-1, A-2).

``pyproject.toml`` ``[tool.importlinter]`` declares four contracts: the Phase 2
``llm4pol.data`` contract (D-06 clause 3), A-1 as a ``forbidden`` contract on
``llm4pol.evaluate``, A-2 in the optional-layers form (RESEARCH F-22: a
``forbidden`` contract errors on an absent *source*, F-19, and a wildcard source
misses ``loop/__init__.py``, F-21) and the "only ``llm4pol.loop.agents`` may
import ``llm4pol.llm``" rule with a wildcard source and four ``ignore_imports``
(F-23). The positive test runs the exact argv the gate runs
(``check.lint_imports_argv()``). A contract that is KEPT because its modules
are absent is indistinguishable from a vacuous one, so two negative probes
(RESEARCH Pattern 7) copy ``src/llm4pol`` into ``tmp_path``, add the violating
module there and prove the contract reports BROKEN with the exact chain --
never touching the repository tree, which must hold no ``radonpy.py``,
``loop``, ``llm`` or ``run`` (D-05; CLAUDE.md: a stub is a blocker).
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import check
from conftest import REPO_ROOT

PYPROJECT = REPO_ROOT / "pyproject.toml"
PACKAGE = REPO_ROOT / "src" / "llm4pol"

A1_EVALUATE_PREFIX = "A-1: llm4pol.evaluate never imports"
A2_PREFIX = "A-2:"
LLM_RULE_PREFIX = "A-1: only llm4pol.loop.agents"
DATA_PREFIX = "llm4pol.data is independent"

LLM_IGNORE_IMPORTS = [
    "llm4pol.loop.agents -> llm4pol.llm",
    "llm4pol.loop.agents -> llm4pol.llm.*",
    "llm4pol.loop.agents.* -> llm4pol.llm",
    "llm4pol.loop.agents.* -> llm4pol.llm.*",
]


def _importlinter() -> dict[str, Any]:
    with PYPROJECT.open("rb") as fh:
        data: dict[str, Any] = tomllib.load(fh)
    section: dict[str, Any] = data["tool"]["importlinter"]
    return section


def _contract(section: dict[str, Any], prefix: str) -> dict[str, Any]:
    matches = [c for c in section["contracts"] if str(c["name"]).startswith(prefix)]
    assert len(matches) == 1, (prefix, [c["name"] for c in section["contracts"]])
    contract: dict[str, Any] = matches[0]
    return contract


def _run_linter(extra: list[str] | None, *, cwd: Path, pythonpath: str) -> tuple[int, str]:
    result = subprocess.run(
        check.lint_imports_argv(extra),
        cwd=cwd,
        env={**os.environ, "PYTHONPATH": pythonpath},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def _scratch_copy(tmp_path: Path) -> Path:
    """A copy of ``src/llm4pol`` under ``tmp_path/src`` without bytecode caches (Pattern 7)."""
    target = tmp_path / "src" / "llm4pol"
    shutil.copytree(PACKAGE, target, ignore=shutil.ignore_patterns("__pycache__"))
    return target


def _toml_list(values: list[str]) -> str:
    return "[" + ", ".join(f'"{v}"' for v in values) + "]"


def _probe_toml(tmp_path: Path, contract: dict[str, Any]) -> Path:
    """Write ``tmp_path/probe.toml`` holding one contract read back from ``pyproject.toml``."""
    lines = [
        "[tool.importlinter]",
        'root_package = "llm4pol"',
        "",
        "[[tool.importlinter.contracts]]",
        f'name = "{contract["name"]}"',
        f'type = "{contract["type"]}"',
    ]
    for key in ("source_modules", "forbidden_modules", "layers", "ignore_imports"):
        if key in contract:
            lines.append(f"{key} = {_toml_list(list(contract[key]))}")
    if "unmatched_ignore_imports_alerting" in contract:
        lines.append(
            f'unmatched_ignore_imports_alerting = "{contract["unmatched_ignore_imports_alerting"]}"'
        )
    probe = tmp_path / "probe.toml"
    probe.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return probe


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------
# Test 1: the four contracts are declared with the exact modules
# --------------------------------------------------------------------------


def test_a1_a2_contracts_are_declared_with_exact_modules() -> None:
    section = _importlinter()
    assert section["root_package"] == "llm4pol"
    assert section["include_external_packages"] is True
    assert len(section["contracts"]) == 4

    a1 = _contract(section, A1_EVALUATE_PREFIX)
    assert a1["type"] == "forbidden"
    assert a1["source_modules"] == ["llm4pol.evaluate"]
    assert a1["forbidden_modules"] == ["llm4pol.loop", "llm4pol.llm", "llm4pol.run"]

    a2 = _contract(section, A2_PREFIX)
    assert a2["type"] == "layers"
    assert a2["layers"] == ["(llm4pol.evaluate.backends.radonpy)", "(llm4pol.loop)"]

    llm_rule = _contract(section, LLM_RULE_PREFIX)
    assert llm_rule["type"] == "forbidden"
    assert llm_rule["source_modules"] == ["llm4pol.*"]
    assert llm_rule["forbidden_modules"] == ["llm4pol.llm"]
    assert llm_rule["ignore_imports"] == LLM_IGNORE_IMPORTS
    assert llm_rule["unmatched_ignore_imports_alerting"] == "none"

    data = _contract(section, DATA_PREFIX)
    assert data["source_modules"] == ["llm4pol.data"]
    assert "sklearn" in data["forbidden_modules"]
    assert "llm4pol.evaluate" in data["forbidden_modules"]


# --------------------------------------------------------------------------
# Test 2: the gate's own argv reports every contract KEPT
# --------------------------------------------------------------------------


def test_a1_contracts_are_declared_and_kept_by_the_gate_argv() -> None:
    code, output = _run_linter(None, cwd=REPO_ROOT, pythonpath="src")
    assert code == 0, output
    assert "Contracts: 4 kept, 0 broken." in output, output
    assert output.count(" KEPT") == 4, output
    assert "BROKEN" not in output, output


# --------------------------------------------------------------------------
# Test 3: the A-2 optional-layers guard breaks on a violating import (F-22)
# --------------------------------------------------------------------------


def test_a2_layers_guard_breaks_on_a_violating_import(tmp_path: Path) -> None:
    radonpy_stub = PACKAGE / "evaluate" / "backends" / "radonpy.py"
    assert not radonpy_stub.exists()

    copy = _scratch_copy(tmp_path)
    _write(copy / "loop" / "__init__.py", "from llm4pol.evaluate.backends import radonpy\n")
    _write(copy / "evaluate" / "backends" / "radonpy.py", "")
    probe = _probe_toml(tmp_path, _contract(_importlinter(), A2_PREFIX))

    code, output = _run_linter(
        ["--config", str(probe)], cwd=tmp_path, pythonpath=str(tmp_path / "src")
    )
    assert code == 1, output
    assert "BROKEN" in output, output
    assert "llm4pol.loop -> llm4pol.evaluate.backends.radonpy" in output, output

    assert not radonpy_stub.exists()
    assert not (PACKAGE / "loop").exists()


# --------------------------------------------------------------------------
# Test 4: the llm rule breaks outside loop.agents and holds inside it (F-23)
# --------------------------------------------------------------------------


def test_llm_rule_breaks_when_a_non_agents_module_imports_llm(tmp_path: Path) -> None:
    llm_rule = _contract(_importlinter(), LLM_RULE_PREFIX)

    violating = tmp_path / "violating"
    copy = _scratch_copy(violating)
    _write(copy / "llm" / "__init__.py", "")
    _write(copy / "loop" / "__init__.py", "")
    _write(copy / "loop" / "agents" / "__init__.py", "import llm4pol.llm\n")
    _write(copy / "loop" / "problem.py", "import llm4pol.llm\n")
    probe = _probe_toml(violating, llm_rule)
    code, output = _run_linter(
        ["--config", str(probe)], cwd=violating, pythonpath=str(violating / "src")
    )
    assert code == 1, output
    assert "BROKEN" in output, output
    assert "llm4pol.loop.problem -> llm4pol.llm" in output, output

    exempt = tmp_path / "exempt"
    copy = _scratch_copy(exempt)
    _write(copy / "llm" / "__init__.py", "")
    _write(copy / "loop" / "__init__.py", "")
    _write(copy / "loop" / "agents" / "__init__.py", "import llm4pol.llm\n")
    probe = _probe_toml(exempt, llm_rule)
    code, output = _run_linter(["--config", str(probe)], cwd=exempt, pythonpath=str(exempt / "src"))
    assert code == 0, output
    assert "KEPT" in output, output
    assert "BROKEN" not in output, output

    assert not (PACKAGE / "llm").exists()
    assert not (PACKAGE / "loop").exists()


# --------------------------------------------------------------------------
# Test 5: the package root imports no backend; no stub or future package exists (F-49, D-05)
# --------------------------------------------------------------------------


def test_evaluate_package_init_imports_no_backend_and_no_radonpy_stub_exists() -> None:
    tree = ast.parse((PACKAGE / "evaluate" / "__init__.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert "backends" not in (node.module or ""), ast.dump(node)
            assert all("backends" not in alias.name for alias in node.names), ast.dump(node)
        elif isinstance(node, ast.Import):
            assert all("backends" not in alias.name for alias in node.names), ast.dump(node)

    assert not (PACKAGE / "evaluate" / "backends" / "radonpy.py").exists()
    for name in ("loop", "llm", "run"):
        assert not (PACKAGE / name).exists(), name
