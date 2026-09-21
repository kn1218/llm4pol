"""The evaluator's view of the property registry (CONTEXT Specific Ideas; CLAUDE.md one-place rule).

``PropertyTable`` adapts ``llm4pol.data.registry.load_registry()`` -- the only
call site of the registry loader under ``llm4pol.evaluate``. Every key, unit
and the snapshot identifier the evaluator writes into a result comes from
here; no list of keys and no unit or snapshot literal is duplicated in this
package. A key outside the registry -- the barred static permittivity column
included, which the registry schema refuses (A-7) -- is simply ``unsupported``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from llm4pol.data.registry import (
    REGISTRY_PATH,
    SCHEMA_PATH,
    PropertySpec,
    Registry,
    load_registry,
)


@dataclass(frozen=True, slots=True)
class PropertyTable:
    """Read-only lookups over one validated ``Registry``."""

    registry: Registry

    @classmethod
    def load(cls, path: Path = REGISTRY_PATH, *, schema_path: Path = SCHEMA_PATH) -> PropertyTable:
        """Load and validate the registry instance (``RegistryError`` on a bad file)."""
        return cls(load_registry(path, schema_path=schema_path))

    @property
    def snapshot(self) -> str:
        """The snapshot identifier every result cites as ``source``."""
        return self.registry.snapshot

    def supported(self, key: str) -> bool:
        """Whether ``key`` is a registry key (the ``unsupported`` decision, D-02)."""
        return key in self.registry.properties

    def spec(self, key: str) -> PropertySpec:
        """The registry entry for a supported ``key`` (``KeyError`` otherwise)."""
        return self.registry.properties[key]

    def columns(self) -> tuple[str, ...]:
        """The served candidate-table columns in registry order."""
        return self.registry.columns()
