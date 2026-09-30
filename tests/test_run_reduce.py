"""The column definitions of ADR-0008 item 4 and the two-currency ``usage.json`` (plan 04-07).

Guards RUN-04 and RUN-05 (CONTEXT D-04, R-2, R-3, D-39; charter section 13 M3 (3); A-3). The
tracer of plan 04-02 computed the columns on one header, and a literal would pass that test; here
the same recorded events are reduced under three other headers, and small ledgers are built by
hand so every number can be checked on paper (tables in the plan objective). Tests 3 to 7 need no
candidate table. Every id and value is invented.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from conftest import REPO_ROOT, make_synthetic_root
from llm4pol.data import load
from llm4pol.run import __main__ as cli
from llm4pol.run import jsonio, ledger, reduce
from run_support import (
    REFERENCE_RESULTS_CSV,
    REFERENCE_RESULTS_SHA256,
    REFERENCE_USAGE_JSON,
    REFERENCE_USAGE_SHA256,
    candidate_ids,
    cut_run,
    feasible_population,
    hand_ledger,
    ledger_under,
    population_payload,
    problem_variant,
    recorded_event_lines,
    reference_run,
)

SCHEMA_PATH = REPO_ROOT / "protocol" / "schemas" / "run-usage.json"
EXAMPLE_PATH = REPO_ROOT / "protocol" / "examples" / "run-usage.example.json"
HEADER = (
    "iteration,beam,population,n_selected,n_ok,median_objective,feasible_frac,"
    "n_population,pct_of_population,hits_top10,hits_top1\n"
)
CURRENCY_KEYS = {"schema_version", "evals", "cpu_hours", "tokens", "usd"}
PROPERTIES = ("thermal_conductivity", "dielectric_const_dc", "tg")


@pytest.fixture(scope="module")
def reference(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The run directory of the uninterrupted reference campaign (plan 04-05)."""
    root = make_synthetic_root(tmp_path_factory.mktemp("reduce-table"))
    load.load(root)
    return reference_run(root, tmp_path_factory.mktemp("reduce-reference") / "experiments")


def _rows(raw: bytes) -> Any:
    return reduce.reduce(ledger.parse_bytes(raw)).rows


def _csv(raw: bytes) -> str:
    return reduce.render_csv(reduce.reduce(ledger.parse_bytes(raw))).decode("utf-8")


def _values(thermal: float | None, eps: float | None = 2.0, tg: float | None = 500.0) -> Any:
    return dict(zip(PROPERTIES, (thermal, eps, tg), strict=True))


def test_reference_rows_match_the_hand_derivation(reference: Path) -> None:
    data = reduce.render_csv(reduce.reduce(ledger.read(reference / ledger.LEDGER_NAME)))
    assert data == REFERENCE_RESULTS_CSV
    assert len(data) == 453
    assert hashlib.sha256(data).hexdigest() == REFERENCE_RESULTS_SHA256
    assert (reference / reduce.RESULTS_NAME).read_bytes() == REFERENCE_RESULTS_CSV


# The four (iteration, beam) rows of the reference campaign, in ledger order; the two
# populations are equal on the shared fixture, so each tail is written once and used twice.
_BEAMS = ((1, "full"), (1, "random"), (2, "full"), (2, "chem"))
_HEADERS = [
    pytest.param(
        {"eps_max": 2.4, "tg_min": 250.0},
        (
            "2,2,0.235,0.5,4,75.0,1,1",
            "3,1,0.22,0.0,4,75.0,0,0",
            "2,2,0.2575,1.0,4,75.0,1,1",
            "0,0,,,4,,0,0",
        ),
        id="eps<=2.4,tg>=250,max",
    ),
    pytest.param(
        {"direction": "min"},
        (
            "2,2,0.235,0.0,4,25.0,0,0",
            "3,1,0.22,0.0,4,25.0,0,0",
            "2,2,0.2575,0.5,4,25.0,0,0",
            "0,0,,,4,,0,0",
        ),
        id="charter,min",
    ),
    pytest.param(
        {"eps_max": 1.0, "tg_min": 400.0},
        (
            "2,2,0.235,0.0,4,75.0,,",
            "3,1,0.22,0.0,4,75.0,,",
            "2,2,0.2575,0.0,4,75.0,,",
            "0,0,,,4,,,",
        ),
        id="eps<=1,tg>=400,max: no feasible member",
    ),
]


@pytest.mark.parametrize(("variant", "tails"), _HEADERS)
def test_thresholds_direction_and_constraints_come_from_the_header(
    reference: Path, variant: dict[str, Any], tails: tuple[str, ...]
) -> None:
    """The 17 recorded event lines, reduced under a header of another problem (T-04-34)."""
    raw = ledger_under(problem_variant(**variant), recorded_event_lines(reference))
    expected = HEADER + "".join(
        f"{iteration},{beam},{population},{tail}\n"
        for (iteration, beam), tail in zip(_BEAMS, tails, strict=True)
        for population in ("check_tc", "readme_triple")
    )
    # rows are listed per selection event, both populations side by side
    assert _csv(raw) == expected


def _ceiling_rows(m: int) -> Any:
    ids = candidate_ids(3)
    top = [float(m - 2), float(m - 1), float(m)]
    evaluated = {ids[i]: _values(top[i]) for i in range(3)}
    raw = hand_ledger(problem_variant(), [feasible_population("check_tc", m)], ids, evaluated)
    (row,) = _rows(raw)
    return row


@pytest.mark.parametrize(
    ("m", "top10_index", "top10_hits", "top1_index", "top1_hits"),
    [(10, 1, 1, 1, 1), (11, 2, 2, 1, 1), (100, 10, 3, 1, 1), (101, 11, 3, 2, 2)],
)
def test_top_indices_use_integer_ceiling(
    m: int, top10_index: int, top10_hits: int, top1_index: int, top1_hits: int
) -> None:
    assert (m + 9) // 10 == top10_index and (m + 99) // 100 == top1_index
    row = _ceiling_rows(m)
    assert row.n_population == m and row.n_selected == row.n_ok == 3
    assert (row.hits_top10, row.hits_top1) == (top10_hits, top1_hits)


def test_ties_are_not_worse() -> None:
    ids = candidate_ids(2)
    population = population_payload("check_tc", [0.2, 0.2, 0.2, 0.3])
    raw = hand_ledger(
        problem_variant(),
        [population],
        ids,
        {ids[0]: _values(0.2), ids[1]: _values(0.2)},
    )
    (row,) = _rows(raw)
    assert row.median_objective == 0.2 and row.pct_of_population == 0.0
    # Under `min` a value is worse when it is strictly above the median.
    raw = hand_ledger(
        problem_variant(direction="min"),
        [population],
        ids,
        {ids[0]: _values(0.3), ids[1]: _values(0.3)},
    )
    (row,) = _rows(raw)
    assert row.median_objective == 0.3 and row.pct_of_population == 0.0


def test_missing_values_are_neither_ok_nor_feasible() -> None:
    a, b, c, d = candidate_ids(4)
    evaluated = {
        a: _values(None),  # objective missing, constraints ok: the event is charged 1
        b: _values(4.0, tg=None),  # a missing constraint: not feasible
        d: _values(4.0),  # everything ok and feasible
    }  # c is selected and has no evaluation event
    raw = hand_ledger(
        problem_variant(),
        [feasible_population("check_tc", 4)],
        [a, b, c, d],
        evaluated,
        closed=False,
    )
    events = ledger.parse_bytes(raw).events
    charged = [e.payload["cost"]["evals"] for e in events if e.event == "evaluation"]
    assert charged == [1, 1, 1], "the event of the candidate with no objective is charged"
    (row,) = _rows(raw)
    assert row.n_selected == 4
    assert row.n_ok == 2, "a candidate with no objective value adds nothing to n_ok"
    assert row.median_objective == 4.0
    # feasibility looks at the constraint results only: a and d are feasible, b has a missing
    # constraint value and c has no evaluation event, so it is neither ok nor feasible
    assert row.feasible_frac == 0.5
    assert (row.n_population, row.pct_of_population) == (4, 75.0)
    assert (row.hits_top10, row.hits_top1) == (1, 1)


def test_null_population_values() -> None:
    (x,) = candidate_ids(1)
    population = population_payload(
        "check_tc",
        [1.0, None, 3.0, 4.0],
        eps=[2.0, 2.0, None, 2.0],
    )
    raw = hand_ledger(problem_variant(), [population], [x], {x: _values(3.0)})
    (row,) = _rows(raw)
    assert row.n_population == 3, "the member with a null objective is left out"
    # worse than 3.0 among the objectives 1.0, 3.0 and 4.0: one of three (four would give 25.0)
    assert row.pct_of_population == pytest.approx(100 / 3, rel=1e-12)
    # feasible members: 1.0 and 4.0 (the member with a null constraint is not one); m = 2
    assert (row.hits_top10, row.hits_top1) == (0, 0), "the threshold is 4.0, the candidate has 3.0"


def test_render_csv_bytes() -> None:
    plain = reduce.Row(1, "full", "check_tc", 3, 3, 1e-07, 0.30000000000000004, 4, 75.0, 0, 0)
    empty = reduce.Row(2, "chem", "check_tc", 0, 0, None, None, 4, None, None, None)
    data = reduce.render_csv(reduce.Reduced(rows=(plain, empty)))
    assert (
        data
        == (
            HEADER + "1,full,check_tc,3,3,1e-07,0.30000000000000004,4,75.0,0,0\n"
            "2,chem,check_tc,0,0,,,4,,,\n"
        ).encode()
    )
    assert b"\r" not in data and not data.startswith(b"\xef\xbb\xbf")
    assert data.split(b"\n")[0].decode() == ",".join(reduce.COLUMNS) and data.endswith(b"\n")
    for text in (b"nan", b"None", b"inf"):
        assert text not in data
    not_finite = reduce.Row(1, "full", "check_tc", 1, 1, math.nan, None, 4, None, None, None)
    with pytest.raises(reduce.ReduceError, match="finite"):
        reduce.render_csv(reduce.Reduced(rows=(not_finite,)))


def _ledger_costs(events: Any) -> list[dict[str, Any]]:
    return [e.payload["cost"] for e in events if e.event == "evaluation"]


def test_usage_equals_the_ledger_sums_in_two_currencies(reference: Path) -> None:
    parsed = ledger.read(reference / ledger.LEDGER_NAME)
    usage = reduce.usage_of(parsed)
    assert set(usage) == CURRENCY_KEYS
    assert usage == {"schema_version": 1, "evals": 5, "cpu_hours": 0.0, "tokens": 0, "usd": 0.0}
    assert type(usage["evals"]) is int and type(usage["cpu_hours"]) is float
    by_result = sum(
        item["cost"]["evals"]
        for e in parsed.events
        if e.event == "evaluation"
        for item in e.payload["results"]
    )
    by_event = sum(cost["evals"] for cost in _ledger_costs(parsed.events))
    assert usage["evals"] == by_result == by_event == 5
    assert (reference / reduce.USAGE_NAME).read_bytes() == REFERENCE_USAGE_JSON
    assert hashlib.sha256(REFERENCE_USAGE_JSON).hexdigest() == REFERENCE_USAGE_SHA256
    assert len(REFERENCE_USAGE_JSON) == 89

    # ten evaluation events of 0.1 compute hours: fsum gives 1.0, a running sum 0.9999999999999999
    ids = candidate_ids(10)
    evaluated = {i: _values(0.2) for i in ids}
    raw = hand_ledger(
        problem_variant(), [feasible_population("check_tc", 4)], ids, evaluated, cpu_hours=0.1
    )
    ten = reduce.usage_of(ledger.parse_bytes(raw))
    assert sum([0.1] * 10) == 0.9999999999999999
    assert ten["cpu_hours"] == 1.0 and ten["evals"] == 10 and type(ten["evals"]) is int


def test_usage_refuses_an_event_cost_that_is_not_the_sum_of_its_results() -> None:
    (x,) = candidate_ids(1)
    raw = hand_ledger(
        problem_variant(), [feasible_population("check_tc", 4)], [x], {x: _values(1.0)}
    )
    doctored = ledger.parse_bytes(raw)
    lines = raw.split(b"\n")[:-1]
    for index, line in enumerate(lines):
        record = json.loads(line)
        if record.get("event") == "evaluation":
            record["payload"]["cost"]["evals"] = 2
            lines[index] = jsonio.canonical_bytes(record)[:-1]
    bad = ledger.parse_bytes(b"\n".join(lines) + b"\n")
    assert reduce.usage_of(doctored)["evals"] == 1
    with pytest.raises(ledger.LedgerIntegrityError, match="cost"):
        reduce.usage_of(bad)


def _usage_schema() -> dict[str, Any]:
    loaded = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _refused(mapping: dict[str, Any]) -> bool:
    validator = jsonschema.Draft202012Validator(_usage_schema())
    return any(True for _ in validator.iter_errors(mapping))


def test_usage_schema_pins_names_and_types(
    reference: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    schema = _usage_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False and set(schema["required"]) == CURRENCY_KEYS

    good = json.loads(REFERENCE_USAGE_JSON)
    assert not _refused(good)
    assert not _refused(json.loads((reference / reduce.USAGE_NAME).read_text(encoding="utf-8")))
    assert not _refused(json.loads(EXAMPLE_PATH.read_text(encoding="utf-8")))

    merged = {k: v for k, v in good.items() if k not in ("evals", "cpu_hours")} | {"budget": 5.0}
    refusals = {
        "a fifth currency key": good | {"cost": 1.0},
        "without cpu_hours": {k: v for k, v in good.items() if k != "cpu_hours"},
        "evals as a float": good | {"evals": 5.5},
        "evals as a bool": good | {"evals": True},
        "a negative tokens": good | {"tokens": -1},
        "tokens as a float": good | {"tokens": 1.5},
        "a negative usd": good | {"usd": -0.5},
        "a negative cpu_hours": good | {"cpu_hours": -1.0},
        "schema_version 2": good | {"schema_version": 2},
        "one number for both currencies": merged,
    }
    for name, mapping in refusals.items():
        assert _refused(mapping), name

    # `write_outputs` applies the schema before a file is opened
    target = cut_run(reference, tmp_path / "experiments", 17)
    monkeypatch.setattr(reduce, "usage_of", lambda _ledger: good | {"cost": 1.0})
    with pytest.raises(reduce.ReduceError, match="usage"):
        reduce.write_outputs(target)
    assert not (target / reduce.USAGE_NAME).exists()
    assert not (target / reduce.RESULTS_NAME).exists()


def test_usage_is_written_beside_the_results_and_never_overwritten(
    reference: Path, tmp_path: Path
) -> None:
    target = cut_run(reference, tmp_path / "experiments", 17)
    sums = reduce.write_outputs(target)
    assert sums == {
        reduce.RESULTS_NAME: REFERENCE_RESULTS_SHA256,
        reduce.USAGE_NAME: REFERENCE_USAGE_SHA256,
    }
    assert reduce.write_outputs(target) == sums, "an equal file is left as found"
    (target / reduce.USAGE_NAME).write_bytes(
        jsonio.pretty_bytes({**json.loads(REFERENCE_USAGE_JSON), "evals": 6})
    )
    doctored = (target / reduce.USAGE_NAME).read_bytes()
    with pytest.raises(ledger.LedgerIntegrityError, match="usage"):
        reduce.write_outputs(target)
    assert (target / reduce.USAGE_NAME).read_bytes() == doctored


def _experiments_with(reference: Path, tmp_path: Path) -> Path:
    """A copy of the reference run, its outputs included, under a fresh experiments directory."""
    experiments = tmp_path / "experiments"
    shutil.copytree(reference, experiments / reference.name)
    return experiments


def test_usage_verb_prints_the_sums_and_compares_the_file(
    reference: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    experiments = _experiments_with(reference, tmp_path)
    run_dir = experiments / reference.name
    argv = ["usage", "--run", reference.name, "--experiments", str(experiments)]
    assert cli.main(argv) == 0
    assert capsys.readouterr().out == REFERENCE_USAGE_JSON.decode("utf-8")

    doctored = jsonio.pretty_bytes({**json.loads(REFERENCE_USAGE_JSON), "evals": 6})
    (run_dir / reduce.USAGE_NAME).write_bytes(doctored)
    assert cli.main(argv) == 4
    assert capsys.readouterr().out == "ERROR: ledger integrity check failed\n"
    assert (run_dir / reduce.USAGE_NAME).read_bytes() == doctored

    open_experiments = tmp_path / "open"
    cut_run(reference, open_experiments, 7)
    open_argv = ["usage", "--run", reference.name, "--experiments", str(open_experiments)]
    assert cli.main(open_argv) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["evals"] == 3 and printed["cpu_hours"] == 0.0
    assert not (open_experiments / reference.name / reduce.USAGE_NAME).exists()


def test_committed_usage_example_is_the_reference_usage() -> None:
    assert EXAMPLE_PATH.read_bytes() == REFERENCE_USAGE_JSON


def test_the_reducer_never_combines_the_currencies() -> None:
    """No expression in the module puts `evals` and `cpu_hours` in one arithmetic or comparison."""
    tree = ast.parse((REPO_ROOT / "src" / "llm4pol" / "run" / "reduce.py").read_text("utf-8"))
    names = {"evals", "cpu_hours", "tokens", "usd"}

    def mentioned(node: ast.AST) -> set[str]:
        found: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in names:
                found.add(child.id)
            if isinstance(child, ast.Constant) and child.value in names:
                found.add(str(child.value))
        return found

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp | ast.Compare | ast.BoolOp | ast.AugAssign):
            assert len(mentioned(node)) <= 1, ast.unparse(node)
