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
from typing import Any

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
    """The committed inventory validates: the registry, both evaluator examples (EVAL-01), and
    the run record: problem spec, selection plan, meta, eight ledger lines (04-04) and usage (04-07)."""
    assert validate_inventory(REPO_ROOT) == []
    assert "llm4polcheck inventory: 9 entries, 16 instances processed" in capsys.readouterr().out


def test_check_steps_include_schema_inventory_after_import_linter() -> None:
    """The gate is seven steps with `schema-inventory` right after `import-linter`."""
    assert [name for name, _ in STEPS] == EXPECTED_STEPS


# --------------------------------------------------------------------------
# RR-8: every `pattern` of a committed schema is anchored. The run validators compile it as a
# full match (llm4pol.run.strictschema), but the data and evaluator validators and any other JSON
# Schema tool use the stock search semantics, where an unanchored pattern accepts a substring.
# --------------------------------------------------------------------------


def _patterns_of(node: Any) -> list[str]:
    """Every string under a ``pattern`` key, at any depth."""
    found: list[str] = []
    if isinstance(node, dict):
        pattern = node.get("pattern")
        if isinstance(pattern, str):
            found.append(pattern)
        for value in node.values():
            found.extend(_patterns_of(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_patterns_of(value))
    return found


def _top_level_alternation(pattern: str) -> bool:
    """True when an unescaped ``|`` sits outside every group and class, so ``^a|b$`` is two arms."""
    depth, in_class, index = 0, False, 0
    while index < len(pattern):
        char = pattern[index]
        if char == "\\":
            index += 1  # the next character is escaped
        elif in_class:
            in_class = char != "]"
        elif char == "[":
            in_class = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "|" and depth == 0:
            return True
        index += 1
    return False


def _anchored(pattern: str) -> bool:
    return (
        pattern.startswith("^")
        and pattern.endswith("$")
        and not pattern.endswith("\\$")
        and not _top_level_alternation(pattern)
    )


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("^[0-9]{8}$", True),
        ("^(?:a|b)$", True),
        ("^[|]$", True),
        ("[0-9]{8}", False),
        ("^[0-9]{8}", False),
        ("[0-9]{8}$", False),
        ("^a$|^b$", False),
        ("^a|b$", False),
        ("^a" + "\\" + "$", False),
    ],
)
def test_the_anchoring_check_tells_anchored_patterns_from_the_others(
    pattern: str, expected: bool
) -> None:
    assert _anchored(pattern) is expected


def test_every_pattern_in_the_schemas_is_anchored_at_both_ends() -> None:
    schemas = sorted((REPO_ROOT / "protocol" / "schemas").glob("*.json"))
    assert schemas, "no schema found under protocol/schemas"
    unanchored = [
        f"{path.name}: {pattern}"
        for path in schemas
        for pattern in _patterns_of(json.loads(path.read_text(encoding="utf-8")))
        if not _anchored(pattern)
    ]
    assert unanchored == []
