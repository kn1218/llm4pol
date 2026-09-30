"""The ledger: a header line, durable appends, a strict reader and its schema (plan 04-01, task 2).

Guards RUN-02 and the two invariants that charter section 13 M3 freezes: A-6 (a ledger is only
ever created once and only ever grows: after every append the previous bytes are a strict prefix
of the file) and the ledger half of A-3 (the cost of an evaluation is exactly ``evals`` and
``cpu_hours``, never merged). Events are built by hand with the builders of ``run_support``; no
table is needed. Test names starting ``test_a6_`` and ``test_a3_`` are cited by
``docs/governance/INVARIANTS.md``.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT
from llm4pol.run import config, jsonio, ledger
from run_support import (
    CANDIDATE_A,
    EVENT_KINDS,
    FIXED_RUN_ID,
    charter_problem,
    one_event_of_each_kind,
    valid_cost,
    valid_event,
    valid_header,
    valid_payload,
    valid_result,
)

SCHEMAS = REPO_ROOT / "protocol" / "schemas"
NON_POPULATION_KINDS = ("iteration_opened", "selection", "evaluation", "no_match")


def _load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    return data


def _refs(node: object) -> list[str]:
    """Every ``$ref`` value found anywhere in a schema document."""
    if isinstance(node, dict):
        found = [str(v) for k, v in node.items() if k == "$ref"]
        return found + [ref for value in node.values() for ref in _refs(value)]
    if isinstance(node, list):
        return [ref for item in node for ref in _refs(item)]
    return []


def _ledger_with(path: Path, events: list[dict[str, Any]]) -> bytes:
    ledger.create(path, valid_header())
    for event in events:
        ledger.append(path, event)
    return path.read_bytes()


def _five_events() -> list[dict[str, Any]]:
    kinds = ("run_opened", "iteration_opened", "selection", "evaluation", "iteration_closed")
    return [valid_event(kind, seq) for seq, kind in enumerate(kinds, start=1)]


# --------------------------------------------------------------------------
# A-6: created once, only ever grows (CONTEXT D-03 items 1 and 2; F-34, F-40)
# --------------------------------------------------------------------------


def test_a6_ledger_refuses_to_be_created_twice(tmp_path: Path) -> None:
    path = tmp_path / ledger.LEDGER_NAME
    ledger.create(path, valid_header())
    before = path.read_bytes()

    with pytest.raises(ledger.LedgerError):
        ledger.create(path, valid_header())
    assert path.read_bytes() == before

    with pytest.raises(ledger.LedgerFormatError):
        ledger.create(tmp_path / "other.jsonl", {"schema_version": 1})
    assert not (tmp_path / "other.jsonl").exists()


def test_a6_every_append_keeps_the_previous_bytes_as_a_prefix(tmp_path: Path) -> None:
    path = tmp_path / ledger.LEDGER_NAME
    ledger.create(path, valid_header())
    for event in _five_events():
        before = path.read_bytes()
        ledger.append(path, event)
        after = path.read_bytes()
        assert after.startswith(before) and len(after) > len(before)

    raw = path.read_bytes()
    assert raw.count(b"\n") == 6
    assert b"\r" not in raw
    for line in raw.split(b"\n")[:-1]:
        assert line + b"\n" == jsonio.canonical_bytes(jsonio.loads_strict(line.decode("utf-8")))


def test_append_needs_an_existing_ledger_that_ends_in_a_line_feed(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    with pytest.raises(ledger.LedgerError):
        ledger.append(missing, valid_event("run_opened"))
    assert not missing.exists()

    path = tmp_path / ledger.LEDGER_NAME
    raw = _ledger_with(path, [valid_event("run_opened")])
    path.write_bytes(raw[:-1])
    torn = path.read_bytes()
    with pytest.raises(ledger.TornTail):
        ledger.append(path, valid_event("iteration_opened", 2))
    assert path.read_bytes() == torn


# --------------------------------------------------------------------------
# A-3, ledger half: two currencies, never merged (F-56)
# --------------------------------------------------------------------------


def test_a3_ledger_schema_keeps_the_two_currencies_apart(tmp_path: Path) -> None:
    path = tmp_path / ledger.LEDGER_NAME
    ledger.create(path, valid_header())
    ledger.append(path, valid_event("evaluation", 1))
    before = path.read_bytes()

    def evaluation(cost: object) -> dict[str, Any]:
        payload = valid_payload("evaluation")
        payload["cost"] = cost
        return valid_event("evaluation", 2, payload=payload)

    third_field = {"evals": 1, "cpu_hours": 0.0, "score": 1.0}
    without_cpu = {"evals": 1}
    for bad in (third_field, without_cpu, 1, {"evals": 1, "cpu_hours": -0.5}):
        with pytest.raises(ledger.LedgerFormatError):
            ledger.append(path, evaluation(bad))
        assert path.read_bytes() == before

    merged = valid_result()
    merged["cost"] = {"evals": 1, "cpu_hours": 0.0, "combined": 1.0}
    payload = valid_payload("evaluation")
    payload["results"] = [merged]
    with pytest.raises(ledger.LedgerFormatError):
        ledger.append(path, valid_event("evaluation", 2, payload=payload))
    assert path.read_bytes() == before


# --------------------------------------------------------------------------
# read: bytes, the LF rule, strict parse, per-line schema, contiguous seq (Pattern 2)
# --------------------------------------------------------------------------


def test_read_returns_the_header_and_events_and_requires_the_final_lf(tmp_path: Path) -> None:
    path = tmp_path / ledger.LEDGER_NAME
    events = _five_events()
    raw = _ledger_with(path, events)

    led = ledger.read(path)
    assert isinstance(led, ledger.Ledger)
    assert led.header.to_json() == valid_header()
    assert [event.to_json() for event in led.events] == events
    assert led.problem == config.parse_problem_spec(charter_problem(1, 3, 2))
    assert led.header.run_id == FIXED_RUN_ID
    assert not led.closed

    ledger.append(path, valid_event("run_closed", 6))
    assert ledger.read(path).closed

    path.write_bytes(raw[:-1])
    with pytest.raises(ledger.TornTail) as torn:
        ledger.read(path)
    cut = raw[:-1]
    assert torn.value.last_lf_offset == cut.rfind(b"\n")
    assert torn.value.trailing_bytes == len(cut) - cut.rfind(b"\n") - 1

    lines = raw.split(b"\n")
    repeated = b'{"seq":1,"seq":2}'
    non_finite = jsonio.canonical_bytes(valid_event("no_match", 1)).replace(b'"chem"', b"NaN")
    for bad in (repeated, non_finite.rstrip(b"\n")):
        path.write_bytes(b"\n".join([lines[0], bad, *lines[2:]]))
        with pytest.raises(ledger.LedgerFormatError):
            ledger.read(path)

    _ledger_with(tmp_path / "gap.jsonl", [valid_event("run_opened", 1)])
    ledger.append(tmp_path / "gap.jsonl", valid_event("iteration_opened", 3))
    with pytest.raises(ledger.LedgerIntegrityError):
        ledger.read(tmp_path / "gap.jsonl")


def test_read_refuses_a_missing_header_a_second_header_and_a_foreign_run(tmp_path: Path) -> None:
    header = jsonio.canonical_bytes(valid_header())
    event = jsonio.canonical_bytes(valid_event("run_opened", 1))
    foreign = valid_event("iteration_opened", 2)
    foreign["run_id"] = "20260101T000001Z-00000001"

    cases = {
        "empty": (b"", ledger.LedgerFormatError),
        "event first": (event, ledger.LedgerFormatError),
        "second header": (header + header, ledger.LedgerFormatError),
        "foreign run": (
            header + event + jsonio.canonical_bytes(foreign),
            ledger.LedgerIntegrityError,
        ),
    }
    for name, (raw, error) in cases.items():
        path = tmp_path / f"{name.replace(' ', '_')}.jsonl"
        path.write_bytes(raw)
        with pytest.raises(error):
            ledger.read(path)


# --------------------------------------------------------------------------
# The schema (CONTEXT D-02; F-53, F-56, Pitfall 12)
# --------------------------------------------------------------------------


def test_ledger_schema_accepts_one_event_of_each_kind_and_confines_the_populations(
    tmp_path: Path,
) -> None:
    path = tmp_path / ledger.LEDGER_NAME
    events = one_event_of_each_kind()
    assert tuple(event["event"] for event in events) == EVENT_KINDS
    _ledger_with(path, events)
    led = ledger.read(path)
    assert tuple(event.event for event in led.events) == ledger.EVENT_KINDS == EVENT_KINDS

    before = path.read_bytes()
    populations = valid_payload("run_opened")["populations"]
    for kind in ("evaluation", "selection", "run_closed", *NON_POPULATION_KINDS):
        payload = copy.deepcopy(valid_payload(kind))
        payload["populations"] = populations
        with pytest.raises(ledger.LedgerFormatError):
            ledger.append(path, valid_event(kind, 8, payload=payload))
    assert path.read_bytes() == before


def test_ledger_schema_closes_the_envelope_and_the_payload_rules(tmp_path: Path) -> None:
    path = tmp_path / ledger.LEDGER_NAME
    ledger.create(path, valid_header())
    before = path.read_bytes()

    unknown_kind = valid_event("run_opened", 1)
    unknown_kind["event"] = "hypothesis"
    extra_key = valid_event("run_opened", 1)
    extra_key["note"] = "x"
    boolean_seq = valid_event("run_opened", 1)
    boolean_seq["seq"] = True
    run_opened_late = valid_event("run_opened", 1, iteration=2)
    no_beam = valid_event("selection", 1, payload={"candidates": [CANDIDATE_A]})
    repeated_candidate = valid_event(
        "selection", 1, payload={"beam": "full", "candidates": [CANDIDATE_A, CANDIDATE_A]}
    )
    short_id = valid_event("selection", 1, payload={"beam": "full", "candidates": ["abc"]})
    unfinished_budget = valid_event("run_closed", 1, payload={"reason": "budget_exhausted"})
    stray_budget = valid_event("run_closed", 1, payload={"reason": "completed", "limit": 2})
    bad_cost = valid_event(
        "evaluation",
        1,
        payload={**valid_payload("evaluation"), "cost": valid_cost(1, 0.0) | {"usd": 1}},
    )

    for bad in (
        unknown_kind,
        extra_key,
        boolean_seq,
        run_opened_late,
        no_beam,
        repeated_candidate,
        short_id,
        unfinished_budget,
        stray_budget,
        bad_cost,
    ):
        with pytest.raises(ledger.LedgerFormatError):
            ledger.append(path, bad)
        assert path.read_bytes() == before

    budget = {"reason": "budget_exhausted", "requested": 1, "remaining": 0, "limit": 2}
    ledger.append(path, valid_event("run_closed", 1, payload=budget))
    assert ledger.read(path).closed


def test_header_and_event_record_builders_match_the_schema() -> None:
    problem = config.parse_problem_spec(charter_problem(1, 3, 2))
    header = ledger.header_record(
        FIXED_RUN_ID,
        problem,
        selector="plan:sha256:" + "0" * 64,
        code_git_sha="0" * 40,
        snapshot="polyomics:general_polymers@041e5834",
        registry_version="v1",
    )
    assert header == valid_header()
    assert header["provenance"]["seed"] == problem.seed

    record = ledger.event_record(
        1, "2026-01-01T00:00:00Z", FIXED_RUN_ID, 0, "run_opened", valid_payload("run_opened")
    )
    assert record == valid_event("run_opened", 1)


def test_embedded_definitions_equal_their_sources() -> None:
    ledger_schema = _load("ledger-event.json")["$defs"]
    response = _load("eval-response.json")["$defs"]
    assert ledger_schema["cost"] == response["cost"]
    assert ledger_schema["result"] == response["result"]

    spec = _load("problem-spec.json")
    body = {k: v for k, v in spec.items() if k not in ("$schema", "$id", "title", "description")}
    assert ledger_schema["problem"] == body

    assert _refs(_load("ledger-event.json")) and all(
        ref.startswith("#/") for ref in _refs(_load("ledger-event.json"))
    ), "the schema must be self-contained: no cross-file reference (F-53)"
