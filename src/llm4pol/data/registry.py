"""The typed loader of the property registry protocol (CONTEXT D-05, DATA-03, A-7).

``protocol/property-registry_v1.yaml`` is the instance, ``protocol/schemas/
property-registry.json`` its JSON Schema. ``load_registry`` reads both,
validates the instance before any field is read (``yaml.safe_load`` only,
threat T-02-19) and returns a frozen ``Registry``: every range, unit and
filter the code applies comes from here, never from a literal (a number is
published in one place). An instance carrying a key outside the nine charter
keys -- the barred static permittivity column included -- fails validation
and is refused with ``RegistryError`` (A-7).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from llm4pol.data.snapshot import DEFAULT_ROOT

REGISTRY_PATH = DEFAULT_ROOT / "protocol" / "property-registry_v1.yaml"
SCHEMA_PATH = DEFAULT_ROOT / "protocol" / "schemas" / "property-registry.json"


class RegistryError(ValueError):
    """A registry file that is missing, unreadable or invalid against its schema."""


@dataclass(frozen=True)
class PropertySpec:
    """One registry entry: the column it serves and the protocol facts about it."""

    key: str
    column: str
    unit: str
    unit_status: str
    role: str
    physical_range: tuple[float, float]
    check_tc: bool | None
    tg_rmse_ladder: tuple[float, ...] | None
    tg_rmse_unit: str | None
    unit_note: str | None


@dataclass(frozen=True)
class Registry:
    """The validated registry instance, keyed in registry (charter section 6) order."""

    schema_version: int
    registry_version: str
    snapshot: str
    revision: str
    properties: dict[str, PropertySpec]

    def columns(self) -> tuple[str, ...]:
        """The served columns in registry order (equals ``schema.PROPERTY_COLUMNS``)."""
        return tuple(spec.column for spec in self.properties.values())

    def spec_for_column(self, column: str) -> PropertySpec:
        """The entry serving ``column``; ``RegistryError`` when no entry does."""
        for spec in self.properties.values():
            if spec.column == column:
                return spec
        raise RegistryError(f"no registry entry serves column {column!r}")

    def by_role(self, role: str) -> tuple[PropertySpec, ...]:
        """Every entry whose ``role`` is ``role``, in registry order."""
        return tuple(spec for spec in self.properties.values() if spec.role == role)


def _read(path: Path, kind: str) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RegistryError(f"{kind} file not found: {path}") from exc
    return yaml.safe_load(text) if path.suffix in (".yaml", ".yml") else json.loads(text)


def _spec(key: str, entry: Mapping[str, Any]) -> PropertySpec:
    low, high = entry["physical_range"]
    filters: Mapping[str, Any] = entry.get("filters", {})
    ladder = filters.get("tg_rmse_ladder")
    return PropertySpec(
        key=key,
        column=str(entry["column"]),
        unit=str(entry["unit"]),
        unit_status=str(entry["unit_status"]),
        role=str(entry["role"]),
        physical_range=(float(low), float(high)),
        check_tc=None if "check_tc" not in filters else bool(filters["check_tc"]),
        tg_rmse_ladder=None if ladder is None else tuple(float(x) for x in ladder),
        tg_rmse_unit=None if "tg_rmse_unit" not in filters else str(filters["tg_rmse_unit"]),
        unit_note=None if "unit_note" not in entry else str(entry["unit_note"]),
    )


def load_registry(path: Path = REGISTRY_PATH, *, schema_path: Path = SCHEMA_PATH) -> Registry:
    """Read, validate and type the registry instance at ``path``.

    Raises ``RegistryError`` naming the path when a file is missing, and with
    the validator's message when the instance violates the schema.
    """
    instance = _read(path, "registry")
    schema = _read(schema_path, "schema")
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as exc:
        raise RegistryError(f"{path}: {exc.message}") from exc
    properties = {key: _spec(key, entry) for key, entry in instance["properties"].items()}
    return Registry(
        schema_version=int(instance["schema_version"]),
        registry_version=str(instance["registry_version"]),
        snapshot=str(instance["snapshot"]),
        revision=str(instance["revision"]),
        properties=properties,
    )
