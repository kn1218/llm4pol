"""The two run populations shown apart on a fixture where they differ (plan 04-06, task 2).

Guards RUN-04 and ADR-0008 items 2 and 3 (CONTEXT R-1, R-4; RESEARCH Pitfall 7): membership follows
the filters of the data layer, values are the medians the evaluator serves, and the arrays are
parallel, sorted by objective and free of candidate ids. On the shared synthetic table both
populations are the same four candidates (F-79), so the fixture ``run_extended_candidates`` adds two
rows to a copy of the shared rows (``conftest.RUN_EXTRA_CORE``); every id and value is invented.
"""

from __future__ import annotations

import hashlib
import itertools
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
import pytest

from llm4pol.data import filters, identity, snapshot
from llm4pol.data.registry import Registry, load_registry
from llm4pol.run import config, jsonio, population
from run_support import PE, PP_ATA, PP_ISO, PS, charter_problem, fixed_run

NEW = "e46d685d3399e6b4"  # `*CC(*)Cl` / atactic, inside the README triple, check_tc False

# One iteration, one beam of three candidates, budget limit 3 (plan 04-06 objective).
EXTENDED_PLAN: dict[str, Any] = {
    "schema_version": 1,
    "iterations": [{"iteration": 1, "beams": [{"beam": "full", "candidates": [PE, PP_ISO, NEW]}]}],
}
EXTENDED_RESULTS_CSV = (
    b"iteration,beam,population,n_selected,n_ok,median_objective,feasible_frac,"
    b"n_population,pct_of_population,hits_top10,hits_top1\n"
    b"1,full,check_tc,3,3,0.315,0.6666666666666666,4,75.0,2,2\n"
    b"1,full,readme_triple,3,3,0.315,0.6666666666666666,5,60.0,1,1\n"
)
EXTENDED_RESULTS_SHA256 = "93f225f9540e5c2f162fd4bebb10279090e37c6382c7892d1e92f832863850cf"


@pytest.fixture
def registry() -> Registry:
    return load_registry()


def _problem() -> config.ProblemSpec:
    return config.parse_problem_spec(charter_problem(1, 3, 1))


def _candidate_table(root: Path) -> Any:
    path = snapshot.candidates_parquet(snapshot.processed_dir(root))
    return pq.read_table(path).to_pandas().set_index("candidate_id")


def _rewrite_snapshot(path: Path, name: str) -> None:
    """Rewrite ``path`` with another ``llm4pol.snapshot`` metadata value, data unchanged."""
    table = pq.read_table(path)
    metadata = dict(table.schema.metadata or {})
    metadata[population.SNAPSHOT_KEY] = name.encode("utf-8")
    pq.write_table(table.replace_schema_metadata(metadata), path)


def test_the_extended_fixture_is_what_the_plan_derives(
    run_extended_candidates: Path, synthetic_candidates: Path, registry: Registry
) -> None:
    source = pd.read_csv(snapshot.csv_path(run_extended_candidates))
    assert len(source) == 16

    served = _candidate_table(run_extended_candidates)
    assert len(served) == 9
    new_id = identity.candidate_id(identity.canonical_psmiles("*CC(*)Cl") or "", "atactic")
    assert new_id == NEW
    assert NEW in served.index

    def median(key: str) -> float:
        column = registry.properties[key].column + filters.MEDIAN_SUFFIX
        return float(served.loc[PP_ISO, column])

    assert median("thermal_conductivity") == pytest.approx(0.23)
    assert median("dielectric_const_dc") == pytest.approx(2.22)
    assert median("tg") == pytest.approx(445.0)

    assert len(pd.read_csv(snapshot.csv_path(synthetic_candidates))) == 14
    assert len(_candidate_table(synthetic_candidates)) == 8


def test_members_follow_the_filter(run_extended_candidates: Path, registry: Registry) -> None:
    found = population.members(run_extended_candidates, registry, _problem().table)
    assert list(found) == ["check_tc", "readme_triple"]
    assert set(found["check_tc"]) == {PE, PP_ISO, PP_ATA, PS}
    assert set(found["readme_triple"]) == {PE, PP_ISO, PP_ATA, PS, NEW}
    assert set(found["check_tc"]) < set(found["readme_triple"])
    assert len(found["check_tc"]) == 4 and len(found["readme_triple"]) == 5


def test_values_are_the_served_medians_not_the_filtered_ones(
    run_extended_candidates: Path, registry: Registry
) -> None:
    first = population.capture(run_extended_candidates, _problem(), registry)[0]
    assert first.name == "check_tc"
    assert 0.23 in first.objective
    assert 0.2 not in first.objective

    # The median of the member over its check_tc-passing row alone would rank it at 0.2.
    rows = pq.read_table(snapshot.rows_parquet(snapshot.processed_dir(run_extended_candidates)))
    frame = rows.to_pandas()
    own = frame[frame["candidate_id"] == PP_ISO]
    passing = own[own[filters.CHECK_TC_COLUMN].astype(bool)]
    tc = registry.properties["thermal_conductivity"].column
    assert float(passing[tc].median()) == pytest.approx(0.2)
    assert float(own[tc].median()) == pytest.approx(0.23)


def test_populations_are_sorted_parallel_and_carry_no_id(
    run_extended_candidates: Path, registry: Registry
) -> None:
    first, second = population.capture(run_extended_candidates, _problem(), registry)
    assert (first.name, second.name) == ("check_tc", "readme_triple")

    assert list(first.objective) == [0.155, 0.18, 0.23, 0.315]
    assert list(second.objective) == [0.155, 0.18, 0.23, 0.315, 0.4]
    assert list(first.constraints) == ["dielectric_const_dc", "tg"]
    assert list(first.constraints["dielectric_const_dc"]) == [2.6100000000000003, 2.25, 2.22, 2.335]
    assert list(second.constraints["dielectric_const_dc"]) == [
        2.6100000000000003,
        2.25,
        2.22,
        2.335,
        2.4,
    ]
    assert list(first.constraints["tg"]) == [377.5, 400.0, 445.0, 262.5]
    assert list(second.constraints["tg"]) == [377.5, 400.0, 445.0, 262.5, 420.0]

    for pop in (first, second):
        payload = pop.to_json()
        assert sorted(payload) == ["constraints", "name", "objective"]
        assert (
            len({len(v) for v in payload["constraints"].values()} | {len(payload["objective"])})
            == 1
        )
        data = jsonio.canonical_bytes(payload).decode("utf-8")
        assert re.search(r'"[0-9a-f]{16}"', data) is None
        for candidate_id in _candidate_table(run_extended_candidates).index:
            assert candidate_id not in data


def test_the_two_populations_are_reported_side_by_side(
    run_extended_candidates: Path, tmp_path: Path
) -> None:
    run_dir = fixed_run(
        run_extended_candidates, tmp_path / "experiments", EXTENDED_PLAN, charter_problem(1, 3, 1)
    )
    data = (run_dir / "results.csv").read_bytes()
    assert data == EXTENDED_RESULTS_CSV
    assert len(data) == 242
    assert hashlib.sha256(data).hexdigest() == EXTENDED_RESULTS_SHA256


def test_capture_refuses_a_table_of_another_snapshot(
    run_extended_candidates: Path, registry: Registry
) -> None:
    processed = snapshot.processed_dir(run_extended_candidates)
    other = "polyomics:general_polymers@ffffffff"

    # the problem names a snapshot that neither parquet carries
    unlike = config.parse_problem_spec({**charter_problem(1, 3, 1), "table": other})
    with pytest.raises(population.PopulationError):
        population.capture(run_extended_candidates, unlike, registry)
    with pytest.raises(population.PopulationError):
        population.members(run_extended_candidates, registry, other)

    rows_path = snapshot.rows_parquet(processed)
    candidates_path = snapshot.candidates_parquet(processed)
    assert population.capture(run_extended_candidates, _problem(), registry)  # sound as built

    _rewrite_snapshot(rows_path, other)
    with pytest.raises(population.PopulationError):
        population.capture(run_extended_candidates, _problem(), registry)

    _rewrite_snapshot(rows_path, _problem().table)
    _rewrite_snapshot(candidates_path, other)
    with pytest.raises(population.PopulationError):
        population.capture(run_extended_candidates, _problem(), registry)

    _rewrite_snapshot(candidates_path, _problem().table)
    rows_path.unlink()
    with pytest.raises(population.PopulationError):
        population.capture(run_extended_candidates, _problem(), registry)


RECORDS: list[tuple[float | None, ...]] = [
    (0.2, 2.0, 400.0),
    (0.2, None, 300.0),
    (0.2, 1.0, None),
    (None, 1.0, 1.0),
    (0.1, 5.0, 5.0),
    (0.2, 1.0, 100.0),
    (0.2, 1.0, 100.0),
]
SORTED_RECORDS: list[tuple[float | None, ...]] = [
    (0.1, 5.0, 5.0),
    (0.2, 1.0, 100.0),
    (0.2, 1.0, 100.0),
    (0.2, 1.0, None),
    (0.2, 2.0, 400.0),
    (0.2, None, 300.0),
    (None, 1.0, 1.0),
]


def test_sort_records_puts_nulls_last_and_is_stable_under_ties() -> None:
    assert population.sort_records(RECORDS) == SORTED_RECORDS
    assert population.sort_records([]) == []
    assert population.sort_records([(None,), (0.5,), (0.1,)]) == [(0.1,), (0.5,), (None,)]

    distinct = RECORDS[:6]
    for permutation in itertools.permutations(distinct):
        assert population.sort_records(permutation) == population.sort_records(distinct)
    assert population.sort_records(reversed(RECORDS)) == SORTED_RECORDS
