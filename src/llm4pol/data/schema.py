"""The declared subset of the PolyOmics schema (CONTEXT D-02, RESEARCH Pattern 3).

Only the registry, identity and flag columns are declared; every other source
column passes through with whatever type pandas infers. ``n_atom`` and
``mol_weight`` look numeric but are ``/``-joined per-chain strings (F-41) and
are never declared (threat T-02-03).
"""

from __future__ import annotations

from typing import Any

import pyarrow as pa

# The nine registry columns in charter section 6 order.
PROPERTY_COLUMNS: tuple[str, ...] = (
    "thermal_conductivity",
    "dielectric_const_dc",
    "tg",
    "Rg",
    "r2",
    "fractional_free_volume",
    "sp_ced",
    "density",
    "refractive_index",
)

IDENTITY_COLUMNS: tuple[str, ...] = ("candidate_id", "canonical_psmiles", "row_index")

_STRING_COLUMNS: tuple[str, ...] = (
    "UUID",
    "smiles_list",
    "smiles_1",
    "smiles_2",
    "tacticity",
    "RadonPy_ver",
    "forcefield",
)
_FLOAT_COLUMNS: tuple[str, ...] = (
    *PROPERTY_COLUMNS,
    "tg_rmse",
    "static_dielectric_const",  # kept as a column, never a registry property (A-7)
    "temp",
    "press",
)
_BOOLEAN_COLUMNS: tuple[str, ...] = ("check_tc", "do_TC")

# pandas read_csv dtype map. Keys absent from a CSV are ignored by pandas.
DTYPES: dict[str, str] = {
    **{name: "str" for name in _STRING_COLUMNS},
    **{name: "float64" for name in _FLOAT_COLUMNS},
    **{name: "boolean" for name in _BOOLEAN_COLUMNS},
}

REQUIRED_SOURCE_COLUMNS: tuple[str, ...] = (
    *PROPERTY_COLUMNS,
    "UUID",
    "smiles_list",
    "smiles_2",
    "tacticity",
    "static_dielectric_const",
    "check_tc",
    "tg_rmse",
)

# pyarrow fields asserted on the row-level parquet. pandas 3 `str` arrives as
# large_string and `boolean` as bool-with-nulls (F-42); the cast normalises
# both. Values are `Any` because pyarrow ships no stubs (pyproject override).
DECLARED_FIELDS: tuple[Any, ...] = (
    pa.field("UUID", pa.string()),
    pa.field("smiles_list", pa.string()),
    pa.field("smiles_2", pa.string()),
    pa.field("tacticity", pa.string()),
    *(pa.field(name, pa.float64()) for name in PROPERTY_COLUMNS),
    pa.field("tg_rmse", pa.float64()),
    pa.field("static_dielectric_const", pa.float64()),
    pa.field("check_tc", pa.bool_()),
    pa.field("candidate_id", pa.string()),
    pa.field("canonical_psmiles", pa.string()),
    pa.field("row_index", pa.int64()),
)


def cast_declared(table: Any) -> Any:
    """Set every declared field on ``table``'s schema by index, then cast the table.

    A declared column that is absent raises ``ValueError``; a value that does
    not fit its declared type raises pyarrow's ``ArrowInvalid``.
    """
    schema = table.schema
    for field in DECLARED_FIELDS:
        index = schema.get_field_index(field.name)
        if index < 0:
            raise ValueError(f"declared column {field.name!r} is absent from the table")
        schema = schema.set(index, field)
    return table.cast(schema)
