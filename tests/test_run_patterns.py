"""WR-07: run ids, timestamps and ids of the run record are ASCII, and ``$`` admits no trailing LF.

``\\d`` in a Python ``str`` pattern matches any Unicode digit, and the schemas' ``^...$`` matched
under ``re.search`` also accepts a value ending in an LF. A run id such as ``２０２６...`` reached the
file system and the ledger header, and a candidate id ``"0123456789abcdef\\n"`` passed the ledger
schema. The gate and the schemas now agree on ASCII, and every pattern is a full match.
"""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from conftest import REPO_ROOT
from llm4pol.run import config, ids, ledger, selector
from run_support import (
    FIXED_CODE_SHA,
    FIXED_RUN_ID,
    FIXED_TS,
    TRACER_PLAN,
    canonical_line,
    charter_problem,
    valid_event,
    valid_header,
)

SCHEMAS = REPO_ROOT / "protocol" / "schemas"
FULLWIDTH = "２０２６０９３０T120000Z-abcdef01"
RUN_ID_SCHEMAS = ("ledger-event.json", "run-meta.json", "run-summary.json")


def _patterns(name: str) -> list[str]:
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("pattern"), str):
                found.append(node["pattern"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(json.loads((SCHEMAS / name).read_text(encoding="utf-8")))
    return found


@pytest.mark.parametrize("text", [FULLWIDTH, FIXED_RUN_ID + "\n", "٢٠٢٦٠١٠١T000000Z-00000000"])
def test_require_run_id_refuses_non_ascii_digits_and_a_trailing_lf(text: str) -> None:
    with pytest.raises(ids.RunIdError):
        ids.require_run_id(text)
    assert ids.require_run_id(FIXED_RUN_ID) == FIXED_RUN_ID


def test_no_schema_pattern_uses_a_unicode_class() -> None:
    for path in SCHEMAS.glob("*.json"):
        assert "\\\\d" not in path.read_text(encoding="utf-8"), path.name  # `\d` in the JSON text


def test_the_schemas_and_the_code_share_one_run_id_pattern() -> None:
    assert "\\d" not in ids.RUN_ID_PATTERN.pattern
    expected = "^" + ids.RUN_ID_PATTERN.pattern + "$"
    for name in RUN_ID_SCHEMAS:
        run_id_patterns = [p for p in _patterns(name) if "T" in p and "Z-" in p]
        assert run_id_patterns == [expected], name


def _refused_header(mutate: Any) -> None:
    header = copy.deepcopy(valid_header())
    mutate(header)
    with pytest.raises(ledger.LedgerFormatError):
        ledger.parse_bytes(canonical_line(header))


HEADER_DEFECTS = {
    "fullwidth run id": lambda h: h.update(run_id=FULLWIDTH),
    "run id with LF": lambda h: h.update(run_id=FIXED_RUN_ID + "\n"),
    "snapshot with LF": lambda h: h["provenance"].update(
        snapshot=h["provenance"]["snapshot"] + "\n"
    ),
    "code sha with LF": lambda h: h["provenance"].update(code_git_sha=FIXED_CODE_SHA + "\n"),
    "table with LF": lambda h: h["problem"].update(table=h["problem"]["table"] + "\n"),
}


@pytest.mark.parametrize("name", list(HEADER_DEFECTS))
def test_the_ledger_reader_refuses_each_header_defect(name: str) -> None:
    _refused_header(HEADER_DEFECTS[name])


def _refused_event(mutate: Any, kind: str = "selection") -> None:
    events = [
        valid_event("run_opened", 1),
        valid_event("iteration_opened", 2),
        valid_event(kind, 3),
    ]
    mutate(events[2])
    raw = canonical_line(valid_header()) + b"".join(canonical_line(e) for e in events)
    with pytest.raises(ledger.LedgerFormatError):
        ledger.parse_bytes(raw)


def test_the_ledger_reader_refuses_a_candidate_id_or_timestamp_with_a_trailing_lf() -> None:
    _refused_event(lambda e: e["payload"]["candidates"].__setitem__(0, "0123456789abcdef\n"))
    _refused_event(lambda e: e.update(ts=FIXED_TS + "\n"))
    _refused_event(lambda e: e.update(ts="２０２６-01-01T00:00:00Z"))
    _refused_event(lambda e: e["payload"]["candidates"].__setitem__(0, "０123456789abcdef"))


def test_the_meta_and_problem_schemas_refuse_a_trailing_lf() -> None:
    problem = charter_problem(1, 3, 2)
    problem["table"] += "\n"
    with pytest.raises(config.ProblemSpecError):
        config.parse_problem_spec(problem)
    meta = config.build_meta(
        run_id=FIXED_RUN_ID,
        created_at=FIXED_TS,
        problem=config.parse_problem_spec(charter_problem(1, 3, 2)),
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
        snapshot="polyomics:general_polymers@041e5834",
        snapshot_sha256="0" * 64,
        registry_version="v1",
        selector="plan:sha256:" + "0" * 64,
        environ={},
    )
    config.validate_meta(meta)
    for key in ("run_id", "created_at"):
        broken = {**meta, key: meta[key] + "\n"}
        with pytest.raises(config.MetaError):
            config.validate_meta(broken)


def test_the_plan_schema_refuses_a_candidate_id_or_beam_name_with_a_trailing_lf() -> None:
    problem = config.parse_problem_spec(charter_problem(1, 3, 2))
    for path, value in (("candidates", "7ec8cb49ff317efc\n"), ("beam", "full\n")):
        plan = copy.deepcopy(TRACER_PLAN)
        beam = plan["iterations"][0]["beams"][0]
        if path == "candidates":
            beam["candidates"][0] = value
        else:
            beam["beam"] = value
        with pytest.raises(selector.PlanError):
            selector.PlanSelector.from_payload(plan, problem)
