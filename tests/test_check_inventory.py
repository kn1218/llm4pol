"""The explicit ``[tool.llm4polcheck]`` schema-validation inventory fails loudly (D-06).

A sibling-schema discovery rule (find a schema next to its instance by naming
convention) would let a deleted or renamed schema silently remove its own
validation. The inventory in ``pyproject.toml`` is explicit by construction:
an absent table, a missing schema path and a ``required = true`` glob that
matches nothing are each a failure, and a YAML instance is validated, never
skipped. ``validate_inventory`` and ``STEPS`` are imported from ``check`` --
the same module ``scripts/check.py`` runs -- through ``tests/conftest.py``'s
``sys.path`` insertion, so these tests exercise the step the gate runs
(CLAUDE.md: a payload with no schema has no guard).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from check import STEPS, validate_inventory
from conftest import REPO_ROOT

_PYPROJECT_HEADER = '[project]\nname = "throwaway"\nversion = "0.0.0"\n\n'

EXPECTED_STEPS = [
    "ruff check",
    "ruff format --check",
    "mypy",
    "import-linter",
    "schema-inventory",
    "history-secret-scan",
    "pytest",
]


def _write_pyproject(root: Path, llm4polcheck_toml: str) -> None:
    (root / "pyproject.toml").write_text(_PYPROJECT_HEADER + llm4polcheck_toml, encoding="utf-8")


def test_missing_schema_path_fails(tmp_path: Path) -> None:
    """A declared `schema` path that does not exist is a failure naming the entry."""
    _write_pyproject(
        tmp_path,
        """
[tool.llm4polcheck]
[[tool.llm4polcheck.validated]]
name = "missing-schema"
schema = "schemas/does_not_exist.schema.json"
instances = "instances/*.json"
required = false
""",
    )
    failures = validate_inventory(tmp_path)
    assert failures, "expected at least one failure for a missing schema path"
    assert any("missing-schema" in f for f in failures), failures


def test_required_entry_matching_zero_instances_fails(tmp_path: Path) -> None:
    """A `required = true` entry whose instances glob matches zero files is a failure."""
    (tmp_path / "schema.json").write_text(json.dumps({"type": "object"}), encoding="utf-8")
    _write_pyproject(
        tmp_path,
        """
[tool.llm4polcheck]
[[tool.llm4polcheck.validated]]
name = "required-empty"
schema = "schema.json"
instances = "instances/*.json"
required = true
""",
    )
    failures = validate_inventory(tmp_path)
    assert failures, "expected at least one failure for a required entry matching zero files"
    assert any("required-empty" in f for f in failures), failures


def test_absent_llm4polcheck_table_fails(tmp_path: Path) -> None:
    """A pyproject.toml with no [tool.llm4polcheck] table at all is a failure."""
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_HEADER, encoding="utf-8")
    failures = validate_inventory(tmp_path)
    assert failures, "expected a failure when [tool.llm4polcheck] is absent"
    assert any("llm4polcheck" in f for f in failures), failures


def test_well_formed_entry_with_matching_instance_passes(tmp_path: Path) -> None:
    """A well-formed entry with a real schema and a matching, valid instance passes."""
    (tmp_path / "schema.json").write_text(
        json.dumps({"type": "object", "required": ["ok"]}), encoding="utf-8"
    )
    instances_dir = tmp_path / "instances"
    instances_dir.mkdir()
    (instances_dir / "one.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    _write_pyproject(
        tmp_path,
        """
[tool.llm4polcheck]
[[tool.llm4polcheck.validated]]
name = "well-formed"
schema = "schema.json"
instances = "instances/*.json"
required = true
""",
    )
    assert validate_inventory(tmp_path) == []


def test_yaml_instance_is_validated_not_skipped(tmp_path: Path) -> None:
    """A `.yaml` instance is parsed and validated; a violation is exactly one failure."""
    (tmp_path / "schema.json").write_text(
        json.dumps({"type": "object", "required": ["ok"]}), encoding="utf-8"
    )
    instances_dir = tmp_path / "instances"
    instances_dir.mkdir()
    (instances_dir / "bad.yaml").write_text("not_ok: true\n", encoding="utf-8")
    _write_pyproject(
        tmp_path,
        """
[tool.llm4polcheck]
[[tool.llm4polcheck.validated]]
name = "yaml-entry"
schema = "schema.json"
instances = "instances/*.yaml"
required = true
""",
    )
    failures = validate_inventory(tmp_path)
    assert len(failures) == 1, failures
    assert "yaml-entry" in failures[0], failures


def test_repository_inventory_validates(capsys: pytest.CaptureFixture[str]) -> None:
    """The committed inventory validates and reports one entry, one instance."""
    assert validate_inventory(REPO_ROOT) == []
    assert "llm4polcheck inventory: 1 entries, 1 instances processed" in capsys.readouterr().out


def test_check_steps_include_schema_inventory_after_import_linter() -> None:
    """The gate is seven steps with `schema-inventory` right after `import-linter`."""
    assert [name for name, _ in STEPS] == EXPECTED_STEPS
