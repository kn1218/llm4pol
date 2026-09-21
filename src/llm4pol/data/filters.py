"""Row masks defined by the loaded registry (CONTEXT D-05; RESEARCH F-08).

Every bound comes from a ``Registry`` object: this module carries no numeric
literal (a number is published in one place, threat T-02-20). Plan 02-05
extends it with the ladder and feasible-set functions.
"""

from __future__ import annotations

from typing import Any

from llm4pol.data.registry import PropertySpec, Registry

# The README's triple: thermal conductivity present, dielectric constant and
# Tg inside their registry physical ranges (F-08 reproduces 43,561 on all rows).
TRIPLE_KEYS: tuple[str, str, str] = ("thermal_conductivity", "dielectric_const_dc", "tg")


def within_physical_range(df: Any, spec: PropertySpec) -> Any:
    """Boolean mask: ``spec.column`` inside ``spec.physical_range`` (inclusive)."""
    low, high = spec.physical_range
    return df[spec.column].between(low, high, inclusive="both")


def readme_triple_mask(df: Any, registry: Registry) -> Any:
    """Boolean mask of the README-triple rows of ``df`` under ``registry``'s ranges.

    TC non-null AND dielectric_const_dc within its physical range AND tg within
    its physical range, both inclusive.
    """
    tc_key, eps_key, tg_key = TRIPLE_KEYS
    tc = registry.properties[tc_key]
    eps = registry.properties[eps_key]
    tg = registry.properties[tg_key]
    return (
        df[tc.column].notna()
        & within_physical_range(df, eps)
        & within_physical_range(df, tg)
    )
