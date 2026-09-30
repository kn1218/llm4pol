"""IN-06: the ledger is checked against its own header, and a missing constraint array is an error.

``_holds`` read a missing constraint array as "value None", so every member counted as infeasible
and the reduction silently reported ``hits_* = None``. A hand-edited or foreign-writer ledger could
pass ``read`` with populations whose constraint keys were not the problem's. The reader now
compares the constraint keys of every population with the problem in the header, and the reducer
raises for an array it cannot find.
"""

from __future__ import annotations

import copy
import dataclasses
from typing import Any

import pytest

from llm4pol.run import ledger, reduce
from run_support import (
    CANDIDATE_A,
    canonical_line,
    charter_problem,
    feasible_population,
    hand_ledger,
    valid_event,
    valid_header,
)


def _ledger_bytes(mutate: Any = None) -> bytes:
    populations = [feasible_population("check_tc", 4), feasible_population("readme_triple", 4)]
    if mutate is not None:
        mutate(populations)
    values = {"thermal_conductivity": 0.3, "dielectric_const_dc": 2.0, "tg": 500.0}
    return hand_ledger(
        charter_problem(1, 3, 2), populations, [CANDIDATE_A], {CANDIDATE_A: values}, closed=True
    )


def test_the_control_ledger_with_the_problem_constraint_keys_reads() -> None:
    assert ledger.parse_bytes(_ledger_bytes()).closed


@pytest.mark.parametrize(
    "mutate",
    [
        lambda populations: populations[0]["constraints"].pop("tg"),
        lambda populations: populations[1]["constraints"].pop("dielectric_const_dc"),
        lambda populations: populations[0]["constraints"].update(extra=[1.0] * 4),
        lambda populations: populations[0].update(constraints={}),
    ],
    ids=["tg missing", "dielectric missing in the second", "extra key", "no constraints"],
)
def test_the_reader_refuses_constraint_keys_that_are_not_the_problems(mutate: Any) -> None:
    with pytest.raises(ledger.LedgerFormatError, match="constraint"):
        ledger.parse_bytes(_ledger_bytes(mutate))


def test_the_reducer_raises_for_a_missing_constraint_array() -> None:
    parsed = ledger.parse_bytes(_ledger_bytes())
    opened = parsed.events[0]
    payload = copy.deepcopy(dict(opened.payload))
    del payload["populations"][0]["constraints"]["tg"]
    broken = dataclasses.replace(parsed, events=(dataclasses.replace(opened, payload=payload),))
    with pytest.raises(reduce.ReduceError, match="tg"):
        reduce.reduce(broken)


def test_a_header_only_problem_change_is_seen_against_the_populations() -> None:
    header = canonical_line(valid_header(charter_problem(1, 3, 2)))
    event = canonical_line(valid_event("run_opened", 1))
    problem = charter_problem(1, 3, 2)
    problem["constraints"][1]["property"] = "refractive_index"
    other_header = canonical_line(valid_header(problem))
    assert len(ledger.parse_bytes(header + event).events) == 1
    with pytest.raises(ledger.LedgerFormatError, match="constraint"):
        ledger.parse_bytes(other_header + event)
