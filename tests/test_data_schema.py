"""The declared schema and the loader rules (CONTEXT D-02, D-03, D-04; DATA-02) on the fixture.

Fixture facts cited (``conftest.py``): 14 source rows, 23 columns; row u13 is
the second-monomer row (``smiles_2`` set) excluded before parsing, row u12
(``*C(``) is the parse failure; 12 in-scope rows; u06 has a missing
tacticity; u07 / u08 are the same molecule; u11 is ``*OC*``; 9 candidates.
The barred column name is built from fragments so a grep for the literal
never matches a test (plan 02-02).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from conftest import SYNTHETIC_ROWS
from llm4pol.data import load, snapshot
from llm4pol.data.fetch import sha256_of
from llm4pol.data.schema import (
    DECLARED_FIELDS,
    DTYPES,
    IDENTITY_COLUMNS,
    PROPERTY_COLUMNS,
)

BARRED_COLUMN = "static_" + "dielectric_const"
ID_PATTERN = r"^[0-9a-f]{16}$"


def _declared_types() -> dict[str, Any]:
    return {field.name: field.type for field in DECLARED_FIELDS}


def _rows_frame(result: load.LoadResult) -> Any:
    return pd.read_parquet(result.rows_parquet)


# --------------------------------------------------------------------------
# schema.py
# --------------------------------------------------------------------------


def test_property_columns_are_the_nine_registry_columns_in_charter_order() -> None:
    assert PROPERTY_COLUMNS == (
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
    assert BARRED_COLUMN not in PROPERTY_COLUMNS


def test_dtypes_never_declare_the_per_chain_string_columns_numeric() -> None:
    assert DTYPES.get("n_atom") in (None, "str")
    assert DTYPES.get("mol_weight") in (None, "str")
    assert DTYPES["check_tc"] == "boolean"
    assert DTYPES["do_TC"] == "boolean"
    assert DTYPES["smiles_list"] == "str"
    for column in PROPERTY_COLUMNS:
        assert DTYPES[column] == "float64", column
    assert "smiles_search" not in IDENTITY_COLUMNS
    assert IDENTITY_COLUMNS == ("candidate_id", "canonical_psmiles", "row_index")


def test_declared_fields_cover_registry_identity_and_flag_columns() -> None:
    types = _declared_types()
    required = {
        *PROPERTY_COLUMNS,
        *IDENTITY_COLUMNS,
        "UUID",
        "smiles_list",
        "smiles_2",
        "tacticity",
        "check_tc",
        "tg_rmse",
        BARRED_COLUMN,
    }
    assert required <= set(types)
    for name in (
        "UUID",
        "smiles_list",
        "smiles_2",
        "tacticity",
        "candidate_id",
        "canonical_psmiles",
    ):
        assert types[name] == pa.string(), name
    for name in (*PROPERTY_COLUMNS, "tg_rmse", BARRED_COLUMN):
        assert types[name] == pa.float64(), name
    assert types["check_tc"] == pa.bool_()
    assert types["row_index"] == pa.int64()


# --------------------------------------------------------------------------
# load.py on the synthetic root
# --------------------------------------------------------------------------


def test_loaded_parquet_schema_has_declared_types_after_cast(synthetic_root: Path) -> None:
    result = load.load(synthetic_root)
    schema = pq.read_schema(result.rows_parquet)
    for field in DECLARED_FIELDS:
        assert schema.field(field.name).type == field.type, field.name
    assert schema.field("smiles_list").type == pa.string()
    assert schema.field("smiles_list").type != pa.large_string()
    assert schema.get_field_index("extra_note") >= 0


def test_parquet_metadata_carries_snapshot_revision_and_source_counts(
    synthetic_root: Path,
) -> None:
    result = load.load(synthetic_root)
    metadata = pq.read_schema(result.rows_parquet).metadata
    assert metadata[b"llm4pol.snapshot"] == b"polyomics:general_polymers@041e5834"
    assert metadata[b"llm4pol.revision"] == snapshot.POLYOMICS_REVISION.encode()
    assert metadata[b"llm4pol.source_rows"] == b"14"
    assert metadata[b"llm4pol.source_columns"] == b"23"
    assert metadata[b"llm4pol.excluded_second_monomer"] == b"1"
    assert metadata[b"llm4pol.excluded_parse_failure"] == b"1"
    assert (
        metadata[b"llm4pol.source_sha256"] == sha256_of(snapshot.csv_path(synthetic_root)).encode()
    )
    candidates_metadata = pq.read_schema(result.candidates_parquet).metadata
    assert candidates_metadata[b"llm4pol.snapshot"] == b"polyomics:general_polymers@041e5834"


def test_loader_excludes_second_monomer_rows_before_parsing_and_counts_parse_failures(
    synthetic_root: Path,
) -> None:
    result = load.load(synthetic_root)
    assert result.excluded_second_monomer == 1
    assert result.excluded_parse_failure == 1
    assert result.rows_written == 12
    rows = _rows_frame(result)
    assert set(rows["row_index"].tolist()) == set(range(14)) - {11, 12}
    uuids = set(rows["UUID"].tolist())
    assert "u12" not in uuids
    assert "u13" not in uuids
    assert len(uuids) == 12


def test_loader_maps_missing_tacticity_to_unknown_and_ids_are_total(synthetic_root: Path) -> None:
    rows = _rows_frame(load.load(synthetic_root))
    assert rows["candidate_id"].notna().all()
    assert rows.loc[rows["UUID"] == "u06", "tacticity"].tolist() == ["unknown"]
    assert rows["candidate_id"].str.fullmatch(ID_PATTERN).all()


def test_loader_merges_equivalent_raw_smiles_into_one_candidate(synthetic_root: Path) -> None:
    rows = _rows_frame(load.load(synthetic_root))
    pair = rows.loc[rows["UUID"].isin(["u07", "u08"])]
    assert pair["candidate_id"].nunique() == 1
    assert pair["canonical_psmiles"].tolist() == ["*CC(*)c1ccccc1", "*CC(*)c1ccccc1"]
    assert rows.loc[rows["UUID"] == "u11", "canonical_psmiles"].tolist() == ["*CO*"]
    assert rows["candidate_id"].nunique() == 9


def test_candidate_table_has_median_n_min_max_std_per_property(synthetic_root: Path) -> None:
    result = load.load(synthetic_root)
    candidates = pd.read_parquet(result.candidates_parquet)
    for column in PROPERTY_COLUMNS:
        for statistic in ("median", "n", "min", "max", "std"):
            assert f"{column}_{statistic}" in candidates.columns, f"{column}_{statistic}"
    for column in ("n_rows", "canonical_psmiles", "tacticity", "candidate_id"):
        assert column in candidates.columns, column

    ethylene = candidates.loc[
        (candidates["canonical_psmiles"] == "*CC*") & (candidates["tacticity"] == "none")
    ]
    assert len(ethylene) == 1
    row = ethylene.iloc[0]
    assert int(row["n_rows"]) == 3
    assert float(row["thermal_conductivity_median"]) == pytest.approx(0.32)
    assert float(row["thermal_conductivity_min"]) == pytest.approx(0.30)
    assert float(row["thermal_conductivity_max"]) == pytest.approx(0.34)
    assert float(row["thermal_conductivity_std"]) == pytest.approx(0.02)
    assert float(row["tg_median"]) == pytest.approx(260.0)

    oxymethylene = candidates.loc[
        (candidates["canonical_psmiles"] == "*CO*") & (candidates["tacticity"] == "none")
    ]
    assert len(oxymethylene) == 1
    single = oxymethylene.iloc[0]
    assert int(single["n_rows"]) == 1
    assert int(single["thermal_conductivity_n"]) == 0
    assert math.isnan(float(single["thermal_conductivity_std"]))


def test_loader_raises_loader_error_naming_missing_required_columns(tmp_path: Path) -> None:
    frame = pd.DataFrame(SYNTHETIC_ROWS).drop(columns=["tg_rmse", "check_tc"])
    csv = tmp_path / "short.csv"
    frame.to_csv(csv, index=False)
    with pytest.raises(load.LoaderError) as excinfo:
        load.read_source(csv)
    message = str(excinfo.value)
    assert "missing required columns: check_tc, tg_rmse" in message


def test_loader_raises_loader_error_when_csv_is_missing(tmp_path: Path) -> None:
    absent = tmp_path / "absent.csv"
    with pytest.raises(load.LoaderError) as excinfo:
        load.read_source(absent)
    assert str(absent) in str(excinfo.value)


def test_read_source_keeps_every_source_column(synthetic_root: Path) -> None:
    frame = load.read_source(snapshot.csv_path(synthetic_root))
    assert frame.shape == (14, 23)
    assert "extra_note" in frame.columns
    assert set(SYNTHETIC_ROWS[0]) == set(frame.columns)
