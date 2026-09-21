"""Guards on the property-registry protocol triad (charter §6, §7; D-05, R-2, R-4).

The registry is protocol, not code: ``protocol/property-registry_v1.yaml`` is the
instance, ``protocol/schemas/property-registry.json`` the draft 2020-12 schema
that constrains it, and ``protocol/property-registry_v1.provenance.yaml`` names
the origin of every leaf. These tests pin the committed files against the Phase 2
research facts (F-20..F-31, F-45, F-47, F-59, F-65..F-67) and make A-7 a
structural rule: the schema's ``propertyNames`` enum admits exactly nine keys, so
the uncorrected static permittivity column cannot be registered.

Only ``json``, ``yaml``, ``jsonschema`` and ``pathlib`` are imported: this module
does not depend on the source package (plan 02-04 adds the loader tests that do).
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "protocol" / "property-registry_v1.yaml"
SCHEMA = ROOT / "protocol" / "schemas" / "property-registry.json"
PROVENANCE = ROOT / "protocol" / "property-registry_v1.provenance.yaml"

NINE_KEYS = [
    "thermal_conductivity",
    "dielectric_const_dc",
    "tg",
    "rg",
    "r2",
    "ffv",
    "sp_ced",
    "density",
    "refractive_index",
]

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

PINNED_CONDITION = {
    "temperature_K": 300,
    "pressure_atm": 1,
    "forcefield": "GAFF2_mod",
    "charges": "RESP",
    "state": "isotropic_amorphous",
}

EXPONENT_STRING = re.compile(r"^-?[0-9.]+e-?[0-9]+$")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    assert isinstance(loaded, dict), f"{path} did not load as a mapping"
    return loaded


def _load_schema() -> dict[str, Any]:
    with SCHEMA.open(encoding="utf-8") as handle:
        loaded = json.load(handle)
    assert isinstance(loaded, dict), f"{SCHEMA} did not load as a mapping"
    return loaded


def _walk_scalars(node: Any, path: str = "") -> list[tuple[str, Any]]:
    if isinstance(node, dict):
        out: list[tuple[str, Any]] = []
        for key, value in node.items():
            out.extend(_walk_scalars(value, f"{path}.{key}" if path else str(key)))
        return out
    if isinstance(node, list):
        out = []
        for index, value in enumerate(node):
            out.extend(_walk_scalars(value, f"{path}[{index}]"))
        return out
    return [(path, node)]


# --- Task 1: schema and instance ------------------------------------------------------


def test_registry_schema_is_a_valid_draft_2020_12_schema() -> None:
    schema = _load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == DRAFT_2020_12, f"$schema is {schema.get('$schema')!r}"


def test_registry_instance_validates_against_its_schema() -> None:
    jsonschema.validate(_load_yaml(REGISTRY), _load_schema())


def test_registry_declares_exactly_the_nine_keys_in_charter_order() -> None:
    instance = _load_yaml(REGISTRY)
    keys = list(instance["properties"])
    assert keys == NINE_KEYS, f"registry keys {keys} != charter order {NINE_KEYS}"


def test_a7_static_dielectric_const_is_rejected_by_the_registry_schema() -> None:
    barred = "static_" + "dielectric_const"
    instance = _load_yaml(REGISTRY)
    schema = _load_schema()

    injected = copy.deepcopy(instance)
    entry = copy.deepcopy(injected["properties"]["dielectric_const_dc"])
    entry["column"] = barred
    injected["properties"][barred] = entry
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(injected, schema)

    text = REGISTRY.read_text(encoding="utf-8")
    assert barred not in text, f"the barred column name appears in {REGISTRY.name}"
    served = instance["properties"]["dielectric_const_dc"]["column"]
    assert served == "dielectric_const_dc", f"dielectric_const_dc serves column {served!r}"


def test_registry_units_and_status_match_research_r4() -> None:
    instance = _load_yaml(REGISTRY)
    props = instance["properties"]
    observed = {k: (v["column"], v["unit"], v["unit_status"]) for k, v in props.items()}
    expected = {
        "thermal_conductivity": ("thermal_conductivity", "W/(m*K)", "verified"),
        "dielectric_const_dc": ("dielectric_const_dc", "1", "verified"),
        "tg": ("tg", "K", "verified"),
        "rg": ("Rg", "angstrom", "verified"),
        "r2": ("r2", "nm^2", "unverified"),
        "ffv": ("fractional_free_volume", "1", "verified"),
        "sp_ced": ("sp_ced", "MPa", "verified"),
        "density": ("density", "g/cm^3", "verified"),
        "refractive_index": ("refractive_index", "1", "verified"),
    }
    assert observed == expected, f"units/status differ from R-4: {observed}"

    note = props["r2"].get("unit_note", "")
    assert note, "r2 must carry a unit_note stating both candidate units (F-25)"
    assert "nm^2" in note and "angstrom^2" in note, (
        f"r2 unit_note does not name both units: {note!r}"
    )
    with_note = [k for k, v in props.items() if "unit_note" in v]
    assert with_note == ["r2"], f"only r2 may carry unit_note, found {with_note}"

    columns = [v["column"] for v in props.values()]
    assert len(set(columns)) == len(columns), f"duplicate columns: {columns}"


def test_registry_physical_ranges_and_filters_are_pinned() -> None:
    instance = _load_yaml(REGISTRY)
    props = instance["properties"]
    expected_ranges = {
        "dielectric_const_dc": [1.0, 20.0],
        "tg": [100.0, 900.0],
        "thermal_conductivity": [0.0, 2.0],
        "rg": [0.0, 200.0],
        "r2": [0.0, 2000.0],
        "ffv": [0.0, 1.0],
        "sp_ced": [0.0, 2000.0],
        "density": [0.5, 2.5],
        "refractive_index": [1.0, 3.0],
    }
    observed_ranges = {k: v["physical_range"] for k, v in props.items()}
    assert observed_ranges == expected_ranges, f"physical ranges differ: {observed_ranges}"
    for key, (low, high) in observed_ranges.items():
        assert low < high, f"{key}: physical_range min {low} is not below max {high}"

    assert props["thermal_conductivity"]["filters"] == {"check_tc": True}
    assert props["tg"]["filters"] == {
        "tg_rmse_ladder": [0.05, 0.1, 0.2, 0.5, 1.0],
        "tg_rmse_unit": "(g/cm^3)^2",
    }
    with_filters = sorted(k for k, v in props.items() if "filters" in v)
    assert with_filters == ["tg", "thermal_conductivity"], f"unexpected filters on {with_filters}"
    for key, entry in props.items():
        for filter_key in entry.get("filters", {}):
            assert "max" not in filter_key and "cut" not in filter_key, (
                f"{key}: filter {filter_key!r} applies a cut; R-2 records the ladder only"
            )


def test_registry_numbers_are_numbers_not_strings() -> None:
    instance = _load_yaml(REGISTRY)
    exponent_strings = [
        (path, value)
        for path, value in _walk_scalars(instance)
        if isinstance(value, str) and EXPONENT_STRING.match(value)
    ]
    assert not exponent_strings, f"numbers written as strings (F-47): {exponent_strings}"
    for key, entry in instance["properties"].items():
        for element in entry["physical_range"]:
            assert type(element) in (int, float), f"{key}: physical_range element {element!r}"
        for element in entry.get("filters", {}).get("tg_rmse_ladder", []):
            assert type(element) in (int, float), f"{key}: ladder element {element!r}"


def test_registry_condition_matches_the_pinned_run_conditions() -> None:
    instance = _load_yaml(REGISTRY)
    for key, entry in instance["properties"].items():
        assert entry["condition"] == PINNED_CONDITION, f"{key}: condition {entry['condition']}"


def test_registry_roles_follow_charter_table() -> None:
    instance = _load_yaml(REGISTRY)
    observed = {k: v["role"] for k, v in instance["properties"].items()}
    expected = {
        "thermal_conductivity": "objective",
        "dielectric_const_dc": "constraint",
        "tg": "constraint",
        "rg": "intermediate",
        "r2": "validator",
        "ffv": "intermediate",
        "sp_ced": "intermediate",
        "density": "intermediate",
        "refractive_index": "validator",
    }
    assert observed == expected, f"roles differ from charter §6: {observed}"


def test_registry_header_names_snapshot_and_revision() -> None:
    instance = _load_yaml(REGISTRY)
    assert instance["schema_version"] == 1
    assert instance["registry_version"] == "v1"
    assert instance["snapshot"] == "polyomics:general_polymers@041e5834"
    assert instance["revision"] == "041e5834ea1a48682fae12dc39ccd723bcd4f771"


def test_schema_rejects_an_unknown_filter_key_and_a_bad_range() -> None:
    instance = _load_yaml(REGISTRY)
    schema = _load_schema()

    unknown_filter = copy.deepcopy(instance)
    unknown_filter["properties"]["tg"]["filters"] = {"something_else": 1}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(unknown_filter, schema)

    bad_range = copy.deepcopy(instance)
    bad_range["properties"]["tg"]["physical_range"] = [1.0]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_range, schema)

    bad_status = copy.deepcopy(instance)
    bad_status["properties"]["tg"]["unit_status"] = "guessed"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_status, schema)

    extra_top_level = copy.deepcopy(instance)
    extra_top_level["extra"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(extra_top_level, schema)


# --- Task 2: provenance -----------------------------------------------------------------

PROVENANCE_CLASSES = {"paper_or_source", "protocol_decision", "unresolved"}
FACT_ID = re.compile(r"^F-[0-9]{2}$")
FILTER_CHOICE_LEAVES = {
    "properties.thermal_conductivity.filters.check_tc",
    "properties.tg.filters.tg_rmse_ladder",
}


def _leaf_paths(mapping: dict[str, Any], prefix: str = "") -> set[str]:
    """Dotted paths of every scalar or list leaf; a `condition` mapping is one leaf."""
    leaves: set[str] = set()
    for key, value in mapping.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict) and key != "condition":
            leaves |= _leaf_paths(value, path)
        else:
            leaves.add(path)
    return leaves


def test_provenance_leaf_paths_equal_registry_leaf_paths() -> None:
    instance_leaves = _leaf_paths(_load_yaml(REGISTRY))
    provenance_leaves = set(_load_yaml(PROVENANCE)["entries"])
    missing = sorted(instance_leaves - provenance_leaves)
    extra = sorted(provenance_leaves - instance_leaves)
    assert not missing and not extra, f"provenance missing {missing}, extra {extra}"
    assert len(instance_leaves) == 62, f"expected 62 leaves, found {len(instance_leaves)}"


def test_provenance_classes_are_valid_and_complete() -> None:
    entries = _load_yaml(PROVENANCE)["entries"]
    for path, entry in entries.items():
        klass = entry.get("provenance_class")
        assert klass in PROVENANCE_CLASSES, f"{path}: provenance_class {klass!r}"
        if klass == "paper_or_source":
            assert entry.get("source"), f"{path}: paper_or_source needs a source"
            assert FACT_ID.match(str(entry.get("fact", ""))), f"{path}: fact {entry.get('fact')!r}"
        elif klass == "protocol_decision":
            assert entry.get("rationale"), f"{path}: protocol_decision needs a rationale"
        else:
            for field in ("rationale", "target_phase", "pass_condition"):
                assert entry.get(field), f"{path}: unresolved needs {field}"

    unresolved = [p for p, e in entries.items() if e["provenance_class"] == "unresolved"]
    assert unresolved == ["properties.r2.unit"], f"unresolved leaves: {unresolved}"

    for path, entry in entries.items():
        tail = path.rsplit(".", 1)[-1]
        if tail == "unit" and path != "properties.r2.unit":
            assert entry["provenance_class"] == "paper_or_source", f"{path} is not sourced"
        if tail in ("physical_range", "role") or path in FILTER_CHOICE_LEAVES:
            assert entry["provenance_class"] == "protocol_decision", f"{path} is not a decision"
        if tail == "condition":
            assert entry["provenance_class"] == "paper_or_source", f"{path} is not sourced"
            assert entry["fact"] == "F-30", f"{path}: fact {entry['fact']!r} != F-30"

    unit_leaf = entries["properties.tg.filters.tg_rmse_unit"]
    assert unit_leaf["provenance_class"] == "paper_or_source", "tg_rmse_unit is a source fact"
    assert unit_leaf["fact"] == "F-23", f"tg_rmse_unit fact {unit_leaf['fact']!r} != F-23"


def test_provenance_never_calls_a_range_a_decision() -> None:
    entries = _load_yaml(PROVENANCE)["entries"]
    for path, entry in entries.items():
        rationale = str(entry.get("rationale", ""))
        assert not re.search(r"D-16.*fixed", rationale), f"{path}: rationale fixes D-16"
        assert "threshold =" not in rationale, f"{path}: rationale states a threshold"
        if path.endswith(".physical_range"):
            assert "physical-range filter" in rationale, (
                f"{path}: rationale must call the range a physical-range filter (ADR-0005)"
            )
