"""Charter section 13 M3 (1), (2), (3) reproduced on the pinned table -- CI cannot run these.

The two processed parquets of the pinned snapshot are never committed, so every test here depends
on the module fixture ``real_processed``, which skips with its stated reason when either is absent
(CONTEXT D-08, plan 04-09). Locally every test must PASS.

What is asserted are the aggregate counts the research measured (F-21, F-23, F-25 as corrected)
and the size of the two populations ADR-0008 names; no expected number is ever edited to make a
test pass, a difference is a defect of the capture or a snapshot that is not the post-ADR-0006 one.
Ids are read from the parquet at run time, this file holds no id and no value of a candidate, and
every file a test writes lives under ``tmp_path`` (data policy; charter section 10).
"""

from __future__ import annotations

import bisect
import csv
import io
import json
import re
from pathlib import Path
from typing import Any, NamedTuple

import pyarrow.parquet as pq
import pytest

from conftest import REPO_ROOT
from llm4pol.data import filters, snapshot
from llm4pol.data.load import build_candidates
from llm4pol.data.registry import Registry, load_registry
from llm4pol.run import __main__ as cli
from llm4pol.run import config, ledger, population, reduce, resume, selector
from run_support import FIXED_CODE_SHA, charter_problem, constant_clock, cut_run, fixed_run

CHECK_TC_SIZE = 39454
README_TRIPLE_SIZE = 40212
BELOW_THRESHOLD = (24497, 24589)
DISTINCT_SERVED = 39449
DISTINCT_FILTERED = 39446
FEASIBLE = (5533, 5620)
TC_THRESHOLD = 0.25
EPS_MAX = 2.6
TG_MIN = 400.0
SERVED_MAXIMUM = 1.284
FILTERED_MAXIMUM = 0.910
BEAM_SIZE = 10
CUT_AFTER = 8
QUOTED_ID = re.compile(r'"[0-9a-f]{16}"')
REDUCED = (reduce.RESULTS_NAME, reduce.USAGE_NAME, reduce.SUMMARY_NAME)


class Real(NamedTuple):
    """What the module reads once from the pinned table."""

    registry: Registry
    members: dict[str, tuple[str, ...]]
    captured: dict[str, population.Population]


@pytest.fixture(scope="module")
def real_processed() -> Path:
    """The repository root, when both processed parquets of the pinned snapshot are present."""
    processed = snapshot.processed_dir(REPO_ROOT)
    for path in (snapshot.rows_parquet(processed), snapshot.candidates_parquet(processed)):
        if not path.is_file():
            pytest.skip(
                f"processed parquet absent at {path} "
                "(never committed; run python -m llm4pol.data fetch, then load)"
            )
    return REPO_ROOT


@pytest.fixture(scope="module")
def real(real_processed: Path) -> Real:
    registry = load_registry()
    spec = config.parse_problem_spec(charter_problem(1, BEAM_SIZE, 2))
    found = population.members(real_processed, registry, spec.table)
    captured = {p.name: p for p in population.capture(real_processed, spec, registry)}
    return Real(registry=registry, members=found, captured=captured)


def _constraint_arrays(pop: population.Population) -> tuple[Any, Any]:
    return pop.constraints["dielectric_const_dc"], pop.constraints["tg"]


def _filtered_medians(root: Path, registry: Registry) -> list[float]:
    """The TC median of each ``check_tc`` member over its ``check_tc``-passing rows alone."""
    rows = pq.read_table(snapshot.rows_parquet(snapshot.processed_dir(root))).to_pandas()
    triple = filters.readme_triple_mask(rows, registry)
    check = filters.check_tc_mask(rows, registry)
    column = registry.properties["thermal_conductivity"].column + filters.MEDIAN_SUFFIX
    frame = build_candidates(rows[triple & check])
    return [float(value) for value in frame[column].dropna().tolist()]


def test_real_population_sizes(real: Real) -> None:
    check, triple = real.members["check_tc"], real.members["readme_triple"]
    assert len(check) == CHECK_TC_SIZE
    assert len(triple) == README_TRIPLE_SIZE
    assert len(set(check)) == len(check) and len(set(triple)) == len(triple)
    assert set(check) <= set(triple)


def test_real_reference_counts_on_served_values(real_processed: Path, real: Real) -> None:
    check, triple = real.captured["check_tc"], real.captured["readme_triple"]
    assert len(check.objective) == CHECK_TC_SIZE
    assert len(triple.objective) == README_TRIPLE_SIZE
    for pop in (check, triple):
        assert None not in pop.objective
    check_values = [v for v in check.objective if v is not None]
    triple_values = [v for v in triple.objective if v is not None]

    below = (
        bisect.bisect_left(check_values, TC_THRESHOLD),
        bisect.bisect_left(triple_values, TC_THRESHOLD),
    )
    assert below == BELOW_THRESHOLD

    assert len(set(check.objective)) == DISTINCT_SERVED
    filtered = _filtered_medians(real_processed, real.registry)
    assert len(filtered) == CHECK_TC_SIZE
    assert len(set(filtered)) == DISTINCT_FILTERED

    def feasible(pop: population.Population) -> int:
        eps, tg = _constraint_arrays(pop)
        return sum(
            1
            for e, t in zip(eps, tg, strict=True)
            if e is not None and t is not None and e <= EPS_MAX and t >= TG_MIN
        )

    assert (feasible(check), feasible(triple)) == FEASIBLE


def test_real_served_values_above_the_filtered_maximum(real_processed: Path, real: Real) -> None:
    served = real.captured["check_tc"].objective
    filtered = _filtered_medians(real_processed, real.registry)
    assert round(max(v for v in served if v is not None), 3) == SERVED_MAXIMUM
    assert round(max(filtered), 3) == FILTERED_MAXIMUM
    ceiling = max(filtered)
    above = [v for v in served if v is not None and v > ceiling]
    assert len(above) == 2


def _campaign_plan(real: Real) -> dict[str, Any]:
    check = sorted(real.members["check_tc"])[:BEAM_SIZE]
    only = sorted(set(real.members["readme_triple"]) - set(real.members["check_tc"]))[:BEAM_SIZE]
    assert len(check) == len(only) == BEAM_SIZE
    return {
        "schema_version": 1,
        "iterations": [
            {
                "iteration": 1,
                "beams": [
                    {"beam": "full", "candidates": check},
                    {"beam": "random", "candidates": only},
                ],
            }
        ],
    }


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _ledger_evals(run_dir: Path) -> int:
    events = ledger.read(run_dir / ledger.LEDGER_NAME).events
    return sum(e.payload["cost"]["evals"] for e in events if e.event == "evaluation")


def test_real_run_prints_both_populations_side_by_side(
    real: Real, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    problem = _write_json(tmp_path / "problem.json", charter_problem(1, BEAM_SIZE, 2))
    plan = _write_json(tmp_path / "plan.json", _campaign_plan(real))
    experiments = tmp_path / "experiments"

    capsys.readouterr()
    code = cli.main(
        [
            "run",
            "--problem",
            str(problem),
            "--selector",
            "plan",
            "--plan",
            str(plan),
            "--root",
            str(REPO_ROOT),
            "--experiments",
            str(experiments),
        ]
    )
    printed = capsys.readouterr().out.splitlines()
    assert code == 0
    assert printed[0].startswith("run_id: ")
    run_dir = experiments / printed[0].removeprefix("run_id: ")

    assert sorted(p.name for p in run_dir.iterdir()) == [
        "ledger.jsonl",
        "meta.json",
        "results.csv",
        "run_summary.json",
        "usage.json",
    ]
    table = list(csv.DictReader(io.StringIO((run_dir / reduce.RESULTS_NAME).read_text("utf-8"))))
    assert len(table) == 4
    assert [(row["beam"], row["population"]) for row in table] == [
        ("full", "check_tc"),
        ("full", "readme_triple"),
        ("random", "check_tc"),
        ("random", "readme_triple"),
    ]
    sizes = {"check_tc": str(CHECK_TC_SIZE), "readme_triple": str(README_TRIPLE_SIZE)}
    for row in table:
        assert row["n_population"] == sizes[row["population"]]
        assert row["n_selected"] == str(BEAM_SIZE)

    usage = json.loads((run_dir / reduce.USAGE_NAME).read_text("utf-8"))
    assert usage["evals"] == _ledger_evals(run_dir)
    assert usage["evals"] <= 2 * BEAM_SIZE

    lines = (run_dir / ledger.LEDGER_NAME).read_bytes().split(b"\n")
    assert json.loads(lines[1])["event"] == "run_opened"
    assert not QUOTED_ID.search(lines[1].decode("utf-8"))

    out = tmp_path / "replayed"
    assert cli.main(["replay", "--run", run_dir.name, "--experiments", str(experiments)]) == 0
    assert (
        cli.main(
            ["replay", "--run", run_dir.name, "--experiments", str(experiments), "--out", str(out)]
        )
        == 0
    )
    for name in REDUCED:
        assert (out / name).read_bytes() == (run_dir / name).read_bytes()
    assert cli.main(["usage", "--run", run_dir.name, "--experiments", str(experiments)]) == 0


def test_real_run_resumes_to_the_same_bytes(real: Real, tmp_path: Path) -> None:
    problem = charter_problem(1, BEAM_SIZE, 2)
    plan = _campaign_plan(real)
    whole = fixed_run(REPO_ROOT, tmp_path / "whole", plan, problem)
    cut = cut_run(whole, tmp_path / "cut", CUT_AFTER)
    assert len((cut / ledger.LEDGER_NAME).read_bytes().split(b"\n")) == CUT_AFTER + 2

    spec = config.parse_problem_spec(problem)
    outcome = resume.resume(
        cut,
        root=REPO_ROOT,
        selector=selector.PlanSelector.from_payload(plan, spec),
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
        clock=constant_clock(),
    )

    assert outcome.status == "completed" and outcome.appended > 0
    for name in (ledger.LEDGER_NAME, *REDUCED):
        assert (cut / name).read_bytes() == (whole / name).read_bytes(), name
    events = ledger.read(cut / ledger.LEDGER_NAME).events
    keys = [ledger.event_key(event) for event in events]
    assert len(keys) == len(set(keys))
