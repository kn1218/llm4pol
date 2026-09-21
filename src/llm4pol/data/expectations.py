"""The pinned expectations of the PolyOmics validator and the population of every finding.

``EXPECTED_POLYOMICS`` maps a finding id to its class, value, tolerance, note
and print digits (R-5): ``reproduce`` must equal the value exactly,
``documented`` pins the value this research observed within a tolerance, so a
further drift fails. ``POPULATIONS`` names the population each finding is
drawn from (D-10). Facts: plan 02-01 F-06, F-07, F-32, F-37; plan 02-04 F-50,
F-52, F-55, F-56; plan 02-05 F-08, F-11..F-19, F-35, F-38, F-39, F-59, F-61,
F-67 -- all measured on the pinned bytes, none re-derived here.
"""

from __future__ import annotations

from collections.abc import Mapping

from llm4pol.data.replicates import (
    MULTI_ROW_CANDIDATES,
    NOISE_POPULATION_ALL,
    NOISE_POPULATION_TRIPLE,
)
from llm4pol.data.report import DOCUMENTED, REPRODUCE, Expected

Expectations = Mapping[str, Expected]

ALL_SOURCE_ROWS = "all source rows"
IN_SCOPE_ROWS = "in-scope rows"
PINNED_FILES = "pinned revision files"
TRIPLE_ALL_ROWS = "README-triple rows (all source rows)"
TRIPLE_IN_SCOPE = "in-scope README-triple rows"
DIELECTRIC_ROWS = "rows with dielectric_const_dc and refractive_index"
CANDIDATE_TRIPLE = "candidate-level README triple (filter then median)"
CANDIDATE_TRIPLE_ALT = "candidate-level README triple (median then filter)"
TC_TG_ROWS = "rows with thermal_conductivity and tg in range (all source rows)"
TG_RMSE_ROWS = "rows with tg_rmse (all source rows)"

_F52_NOTE = "F-52 counted on (smiles_list, tacticity) groups; here by candidate_id (F-35 merges)"
_NOISE_NOTE = "F-55: median over candidates with n >= 2 of std / |median|"
_TRIPLE_NOTE = "F-56: rows filtered to the README triple first, then grouped (F-61)"
_MAXWELL_NOTE = (
    "F-13: README states 88.9 %; 38,693 / 43,561 = 88.8249 %, which rounds to 88.82 (F-13 "
    "prints 88.83, a rounding slip of the same fraction); the observed share is pinned"
)
_IDENTITY_NOTE = (
    "F-14: eps_dc = static - 1 + n^2 is an identity (arXiv:2511.11626 Table S3), so the 0 "
    "violations of dielectric_const_dc are algebra, not a check"
)
_STATIC_N2_NOTE = "F-17: README states -0.05; not reproduced on any population"
_CANONICAL_TWINS_NOTE = (
    "F-39 counted by smiles_list; by canonical_psmiles the F-35 merges may move a group"
)
_CARD_NOTE = "F-19: the dataset card's description text; the Table S2 origin is an assumption (A1)"
CARD_NOT_REPRODUCIBLE = "not reproducible from any column"
_TG_RMSE_NOTE = "F-23: tg_rmse is a sum of squared density residuals in (g/cm^3)^2, not kelvin"
_Q25_NOTE = "F-60: Q25 of dielectric_const_dc, pandas linear interpolation"
_FEASIBLE_NOTE = (
    "F-62: development defaults (charter section 13, D-16 row); an input to the D-16 gate, "
    "not a decision (ADR-0005)"
)
_FEASIBLE_ROWS_NOTE = (
    "F-62: row-level count under the row-level Q25 (2.6427); the count under the candidate "
    "Q25 is printed beside it"
)
_ORDER_NOTE = "F-61: median then filter is the alternative order, printed and not used"

# Finding ids -> (class, value, tolerance, note, digits). Plan 02-01: F-06, F-07,
# F-32, F-37; plan 02-04: F-50, F-52, F-55, F-56; plan 02-05: F-08, F-11..F-19,
# F-35, F-38, F-39, F-59, F-61, F-67 -- all measured on the pinned bytes.
EXPECTED_POLYOMICS: dict[str, Expected] = {
    "source_rows": Expected(REPRODUCE, 95335),
    "source_columns": Expected(REPRODUCE, 259),
    "unique_smiles_list": Expected(REPRODUCE, 78379),
    "second_monomer_rows": Expected(REPRODUCE, 3),
    "parse_failures": Expected(REPRODUCE, 0),
    "in_scope_rows": Expected(REPRODUCE, 95332),
    "unique_canonical": Expected(REPRODUCE, 78373),
    "unique_candidate_ids": Expected(REPRODUCE, 78676),
    "raw_string_merges": Expected(REPRODUCE, 5),
    "multi_tacticity_smiles_with_unknown": Expected(REPRODUCE, 303),
    "multi_tacticity_smiles_without_unknown": Expected(REPRODUCE, 2),
    "multi_tacticity_canonical_with_unknown": Expected(DOCUMENTED, 303, 5, _CANONICAL_TWINS_NOTE),
    "card_count_73045": Expected(DOCUMENTED, CARD_NOT_REPRODUCIBLE, None, _CARD_NOTE),
    "coverage_thermal_conductivity": Expected(REPRODUCE, 81405),
    "coverage_dielectric_const_dc": Expected(REPRODUCE, 93488),
    "coverage_tg": Expected(REPRODUCE, 56064),
    "coverage_Rg": Expected(REPRODUCE, 95335),
    "coverage_fractional_free_volume": Expected(REPRODUCE, 87849),
    "coverage_sp_ced": Expected(REPRODUCE, 71848),
    "coverage_density": Expected(REPRODUCE, 95335),
    "coverage_refractive_index": Expected(REPRODUCE, 93488),
    "tacticity_none": Expected(REPRODUCE, 48790),
    "tacticity_atactic": Expected(REPRODUCE, 45032),
    "tacticity_isotactic": Expected(REPRODUCE, 951),
    "tacticity_syndiotactic": Expected(REPRODUCE, 8),
    "tacticity_unknown": Expected(REPRODUCE, 554),
    "check_tc_true": Expected(REPRODUCE, 79927),
    "check_tc_false": Expected(REPRODUCE, 15376),
    "eps_outside_physical_range": Expected(REPRODUCE, 5123),
    "dc_identity_max_residual": Expected(DOCUMENTED, 5.7e-7, 1e-5, _IDENTITY_NOTE),
    "static_minimum": Expected(DOCUMENTED, 1.00016, 1e-4, "F-15", 5),
    "static_maxwell_violations_triple": Expected(REPRODUCE, 38693),
    "static_maxwell_violations_all": Expected(REPRODUCE, 78807),
    "static_maxwell_violation_pct_triple": Expected(DOCUMENTED, 88.82, 0.05, _MAXWELL_NOTE, 2),
    "static_maxwell_violation_pct_all": Expected(DOCUMENTED, 84.30, 0.05, "F-13", 2),
    "dc_maxwell_violations": Expected(REPRODUCE, 0),
    "spearman_static_vs_n2_triple": Expected(DOCUMENTED, -0.144, 0.01, _STATIC_N2_NOTE, 3),
    "spearman_eps_vs_n2_triple": Expected(DOCUMENTED, 0.476, 0.01, "F-18", 3),
    "readme_triple_all_rows": Expected(REPRODUCE, 43561),
    "readme_triple_in_scope": Expected(REPRODUCE, 43560),
    "triple_check_tc_all_rows": Expected(REPRODUCE, 42733),
    "candidate_triple_filter_then_median": Expected(REPRODUCE, 40212),
    "eps_alternative_non_null_only": Expected(REPRODUCE, 45821),
    "eps_alternative_le_10": Expected(REPRODUCE, 42186),
    "eps_alternative_le_50": Expected(REPRODUCE, 45134),
    "eps_alternative_le_100": Expected(REPRODUCE, 45704),
    "spearman_tc_eps": Expected(DOCUMENTED, 0.170, 0.001, "F-11", 3),
    "spearman_tc_tg": Expected(DOCUMENTED, 0.010, 0.001, "F-11", 3),
    "spearman_eps_tg": Expected(DOCUMENTED, 0.199, 0.001, "F-11", 3),
    "spearman_sp_ced_tc": Expected(DOCUMENTED, 0.355, 0.001, "F-11", 3),
    "spearman_ffv_tc": Expected(DOCUMENTED, -0.069, 0.001, "F-11", 3),
    "spearman_rg_tc": Expected(DOCUMENTED, 0.304, 0.001, "F-11", 3),
    "spearman_density_tc": Expected(DOCUMENTED, -0.270, 0.001, "F-11", 3),
    "readme_window_rows": Expected(DOCUMENTED, 1140, 2, "F-12"),
    "readme_window_pct": Expected(DOCUMENTED, 2.62, 0.01, "F-12", 2),
    "replicate_multi_row_candidates": Expected(REPRODUCE, 12983),
    "replicate_max_rows": Expected(REPRODUCE, 17),
    "same_version_replicate_candidates": Expected(DOCUMENTED, 1888, 10, _F52_NOTE),
    "cross_version_rerun_candidates": Expected(DOCUMENTED, 11096, 10, _F52_NOTE),
    "noise_floor_rel_thermal_conductivity": Expected(DOCUMENTED, 0.0369, 0.001, _NOISE_NOTE),
    "noise_floor_rel_dielectric_const_dc": Expected(DOCUMENTED, 0.0084, 0.001, _NOISE_NOTE),
    "noise_floor_rel_tg": Expected(DOCUMENTED, 0.0577, 0.001, _NOISE_NOTE),
    "noise_floor_rel_density": Expected(DOCUMENTED, 0.0034, 0.001, _NOISE_NOTE),
    "noise_floor_abs_tg": Expected(DOCUMENTED, 30.2, 0.5, _NOISE_NOTE + " (absolute, K)"),
    "noise_floor_triple_rel_thermal_conductivity": Expected(
        DOCUMENTED, 0.0431, 0.001, _TRIPLE_NOTE
    ),
    "noise_floor_triple_rel_dielectric_const_dc": Expected(DOCUMENTED, 0.0112, 0.001, _TRIPLE_NOTE),
    "noise_floor_triple_rel_tg": Expected(DOCUMENTED, 0.0540, 0.001, _TRIPLE_NOTE),
    "tg_non_null": Expected(REPRODUCE, 56064),
    "tg_inside_window": Expected(REPRODUCE, 52753),
    "tg_outside_window": Expected(REPRODUCE, 3311),
    "tg_rmse_le_0.05": Expected(REPRODUCE, 36592),
    "tg_rmse_le_0.1": Expected(REPRODUCE, 42232),
    "tg_rmse_le_0.2": Expected(REPRODUCE, 43316),
    "tg_rmse_le_0.5": Expected(REPRODUCE, 43521),
    "tg_rmse_le_1.0": Expected(REPRODUCE, 43545),
    "tg_median_all_rows": Expected(DOCUMENTED, 488.5, 0.1, "F-63", 1),
    "tg_median_triple_rows": Expected(DOCUMENTED, 472.2, 0.1, "F-63", 1),
    "tg_rmse_median": Expected(DOCUMENTED, 0.029, 0.001, _TG_RMSE_NOTE, 3),
    "tg_rmse_p95": Expected(DOCUMENTED, 0.099, 0.001, _TG_RMSE_NOTE, 3),
    "tg_rmse_p99": Expected(DOCUMENTED, 0.236, 0.002, _TG_RMSE_NOTE, 3),
    "tg_rmse_max": Expected(DOCUMENTED, 36.3, 0.1, _TG_RMSE_NOTE, 1),
    "eps_q25_candidates": Expected(DOCUMENTED, 2.6524, 0.0005, _Q25_NOTE),
    "eps_q25_triple_rows": Expected(DOCUMENTED, 2.6427, 0.0005, _Q25_NOTE),
    "feasible_candidates_dev_defaults": Expected(REPRODUCE, 6793),
    "feasible_pct_dev_defaults": Expected(DOCUMENTED, 16.89, 0.02, _FEASIBLE_NOTE, 2),
    "feasible_rows_dev_defaults": Expected(DOCUMENTED, 7317, 0, _FEASIBLE_ROWS_NOTE),
    "candidate_triple_median_then_filter": Expected(DOCUMENTED, 40426, 0, _ORDER_NOTE),
}

# The population each observed quantity is drawn from (D-10). Ids built per
# registry column or label (coverage_*, tacticity_*, spearman_*) are registered
# by ``_population_of``.
POPULATIONS: dict[str, str] = {
    "source_rows": ALL_SOURCE_ROWS,
    "source_columns": ALL_SOURCE_ROWS,
    "unique_smiles_list": ALL_SOURCE_ROWS,
    "second_monomer_rows": ALL_SOURCE_ROWS,
    "parse_failures": ALL_SOURCE_ROWS,
    "in_scope_rows": IN_SCOPE_ROWS,
    "unique_canonical": IN_SCOPE_ROWS,
    "unique_candidate_ids": IN_SCOPE_ROWS,
    "raw_string_merges": IN_SCOPE_ROWS,
    "multi_tacticity_smiles_with_unknown": ALL_SOURCE_ROWS,
    "multi_tacticity_smiles_without_unknown": ALL_SOURCE_ROWS,
    "multi_tacticity_smiles_unknown_twins": ALL_SOURCE_ROWS,
    "multi_tacticity_canonical_with_unknown": IN_SCOPE_ROWS,
    "multi_tacticity_canonical_without_unknown": IN_SCOPE_ROWS,
    "card_count_73045": ALL_SOURCE_ROWS,
    "check_tc_true": ALL_SOURCE_ROWS,
    "check_tc_false": ALL_SOURCE_ROWS,
    "check_tc_none": ALL_SOURCE_ROWS,
    "eps_outside_physical_range": ALL_SOURCE_ROWS,
    "dc_identity_max_residual": DIELECTRIC_ROWS,
    "dc_identity_median_residual": DIELECTRIC_ROWS,
    "static_minimum": DIELECTRIC_ROWS,
    "static_maxwell_violations_all": DIELECTRIC_ROWS,
    "static_maxwell_violations_triple": TRIPLE_ALL_ROWS,
    "static_maxwell_violation_pct_all": DIELECTRIC_ROWS,
    "static_maxwell_violation_pct_triple": TRIPLE_ALL_ROWS,
    "dc_maxwell_violations": DIELECTRIC_ROWS,
    "spearman_static_vs_n2_all": DIELECTRIC_ROWS,
    "spearman_eps_vs_n2_all": DIELECTRIC_ROWS,
    "spearman_static_vs_n2_triple": TRIPLE_ALL_ROWS,
    "spearman_eps_vs_n2_triple": TRIPLE_ALL_ROWS,
    "readme_ladder_all_rows": ALL_SOURCE_ROWS,
    "readme_ladder_tc_non_null": ALL_SOURCE_ROWS,
    "readme_ladder_eps_non_null": ALL_SOURCE_ROWS,
    "readme_ladder_eps_in_range": ALL_SOURCE_ROWS,
    "readme_triple_all_rows": ALL_SOURCE_ROWS,
    "readme_triple_in_scope": IN_SCOPE_ROWS,
    "triple_check_tc_all_rows": ALL_SOURCE_ROWS,
    "triple_check_tc_in_scope": IN_SCOPE_ROWS,
    "candidate_triple_filter_then_median": CANDIDATE_TRIPLE,
    "candidate_triple_median_then_filter": CANDIDATE_TRIPLE_ALT,
    "eps_alternative_non_null_only": TC_TG_ROWS,
    "eps_alternative_le_10": TC_TG_ROWS,
    "eps_alternative_le_50": TC_TG_ROWS,
    "eps_alternative_le_100": TC_TG_ROWS,
    "readme_window_rows": TRIPLE_ALL_ROWS,
    "readme_window_pct": TRIPLE_ALL_ROWS,
    "replicate_multi_row_candidates": IN_SCOPE_ROWS,
    "replicate_max_rows": IN_SCOPE_ROWS,
    "same_version_replicate_candidates": MULTI_ROW_CANDIDATES,
    "cross_version_rerun_candidates": MULTI_ROW_CANDIDATES,
    "noise_floor_rel_thermal_conductivity": NOISE_POPULATION_ALL,
    "noise_floor_rel_dielectric_const_dc": NOISE_POPULATION_ALL,
    "noise_floor_rel_tg": NOISE_POPULATION_ALL,
    "noise_floor_rel_density": NOISE_POPULATION_ALL,
    "noise_floor_abs_tg": NOISE_POPULATION_ALL,
    "noise_floor_triple_rel_thermal_conductivity": NOISE_POPULATION_TRIPLE,
    "noise_floor_triple_rel_dielectric_const_dc": NOISE_POPULATION_TRIPLE,
    "noise_floor_triple_rel_tg": NOISE_POPULATION_TRIPLE,
    "tg_non_null": ALL_SOURCE_ROWS,
    "tg_inside_window": ALL_SOURCE_ROWS,
    "tg_outside_window": ALL_SOURCE_ROWS,
    "tg_median_all_rows": ALL_SOURCE_ROWS,
    "tg_median_triple_rows": TRIPLE_ALL_ROWS,
    "tg_rmse_median": TG_RMSE_ROWS,
    "tg_rmse_p95": TG_RMSE_ROWS,
    "tg_rmse_p99": TG_RMSE_ROWS,
    "tg_rmse_max": TG_RMSE_ROWS,
    "eps_q25_candidates": CANDIDATE_TRIPLE,
    "eps_q25_triple_rows": TRIPLE_IN_SCOPE,
    "feasible_candidates_dev_defaults": CANDIDATE_TRIPLE,
    "feasible_pct_dev_defaults": CANDIDATE_TRIPLE,
    "feasible_rows_dev_defaults": TRIPLE_IN_SCOPE,
    "feasible_rows_under_candidate_q25": TRIPLE_IN_SCOPE,
    "triple_in_scope_rows_for_feasible": TRIPLE_IN_SCOPE,
}

# Spearman pairs of the README's correlation table, by registry key (F-11).
SPEARMAN_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("spearman_tc_eps", "thermal_conductivity", "dielectric_const_dc"),
    ("spearman_tc_tg", "thermal_conductivity", "tg"),
    ("spearman_eps_tg", "dielectric_const_dc", "tg"),
    ("spearman_sp_ced_tc", "sp_ced", "thermal_conductivity"),
    ("spearman_ffv_tc", "ffv", "thermal_conductivity"),
    ("spearman_rg_tc", "rg", "thermal_conductivity"),
    ("spearman_density_tc", "density", "thermal_conductivity"),
)


def population_of(finding_id: str) -> str:
    if finding_id in POPULATIONS:
        return POPULATIONS[finding_id]
    if finding_id.startswith(("coverage_", "tacticity_", "range_")):
        return ALL_SOURCE_ROWS
    if finding_id.startswith("spearman_"):
        return TRIPLE_ALL_ROWS
    if finding_id.startswith("tg_rmse_le_"):
        return TRIPLE_IN_SCOPE
    raise KeyError(f"finding {finding_id!r} names no population (D-10)")
