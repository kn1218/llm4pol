"""The committed examples of the run record (plan 04-04; RUN-01, RUN-02, RUN-06; D-39; A-5).

Eleven files under ``protocol/examples/``: the problem spec and the selection plan (the two inputs
of the tracer run), ``meta.json`` of that run, and the ledger header and one event of each of the
seven kinds (lines of that run). The ledger and meta examples are what the code wrote under an
injected clock, token, code identity and an empty environment, so the tests compare them with a
fresh run instead of trusting that nobody edited them by hand. Every id and value is an invented
fixture fact of ``conftest._CORE`` (charter section 10).
"""

from __future__ import annotations

import functools
import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from conftest import REPO_ROOT
from llm4pol.run import config, jsonio, ledger, resume, selector
from run_support import (
    EVENT_KINDS,
    FIXED_CODE_SHA,
    FIXED_NOW,
    FIXED_TOKEN,
    PE,
    POM,
    PP_ATA,
    PP_ISO,
    PS,
    PVF,
    TRACER_PLAN,
    charter_problem,
    constant_clock,
)

EXAMPLES = REPO_ROOT / "protocol" / "examples"
SCHEMAS = REPO_ROOT / "protocol" / "schemas"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

PROBLEM_EXAMPLE = EXAMPLES / "problem-spec.example.json"
PLAN_EXAMPLE = EXAMPLES / "selection-plan.example.json"
META_EXAMPLE = EXAMPLES / "run-meta.example.json"
HEADER_EXAMPLE = EXAMPLES / "ledger-header.example.json"


def _event_example(kind: str) -> Path:
    return EXAMPLES / f"ledger-event.{kind}.example.json"


RUN_RECORD_EXAMPLES = (
    PROBLEM_EXAMPLE,
    PLAN_EXAMPLE,
    META_EXAMPLE,
    HEADER_EXAMPLE,
    *(_event_example(kind) for kind in EVENT_KINDS),
)
FIXTURE_IDS = {PE, PP_ISO, PP_ATA, PS, POM, PVF}
# An id is a JSON string of 16 hex digits; the quotes keep the scan from reading the fractional
# digits of a float such as 2.6100000000000003 as one.
CANDIDATE_ID_TOKEN = re.compile(r'"([0-9a-f]{16})"')


def _schema(name: str) -> dict[str, Any]:
    loaded = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _validate(instance_path: Path, schema_name: str) -> None:
    schema = _schema(schema_name)
    jsonschema.Draft202012Validator(schema).validate(jsonio.loads_strict(_text(instance_path)))


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", newline="")


def _tracer_run(
    root: Path, experiments: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    """Open and drive the tracer run under the fixed identity; return ledger lines and meta.

    ``meta.json`` records whether a provider key name is a member of the environment, so the run
    is opened with an empty mapping standing for it (RESEARCH F-50; threat T-04-21).
    """
    monkeypatch.setattr(resume, "build_meta", functools.partial(config.build_meta, environ={}))
    problem = config.parse_problem_spec(charter_problem(1, 3, 2))
    chosen = selector.PlanSelector.from_payload(TRACER_PLAN, problem)
    run_dir = resume.open_run(
        experiments,
        problem,
        chosen,
        root=root,
        now=FIXED_NOW,
        token=FIXED_TOKEN,
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
    )
    resume.drive(run_dir, root=root, selector=chosen, clock=constant_clock())
    raw = (run_dir / ledger.LEDGER_NAME).read_bytes()
    assert raw.endswith(b"\n") and b"\r" not in raw
    lines = [jsonio.loads_strict(line.decode("utf-8")) for line in raw.split(b"\n")[:-1]]
    meta = jsonio.loads_strict((run_dir / config.META_NAME).read_text(encoding="utf-8"))
    return run_dir, lines, meta


def test_run_record_schemas_are_valid_draft_2020_12() -> None:
    for name in ("problem-spec.json", "ledger-event.json", "selection-plan.json", "run-meta.json"):
        schema = _schema(name)
        jsonschema.Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == DRAFT_2020_12, name


def test_committed_run_examples_validate_against_their_schemas() -> None:
    _validate(PROBLEM_EXAMPLE, "problem-spec.json")
    _validate(PLAN_EXAMPLE, "selection-plan.json")
    _validate(META_EXAMPLE, "run-meta.json")

    ledger_files = sorted(EXAMPLES.glob("ledger-*.example.json"))
    expected = sorted([HEADER_EXAMPLE, *(_event_example(kind) for kind in EVENT_KINDS)])
    assert ledger_files == expected, "one header and one event of each of the seven kinds"
    for path in ledger_files:
        _validate(path, "ledger-event.json")
    for kind in EVENT_KINDS:
        assert jsonio.loads_strict(_text(_event_example(kind)))["event"] == kind
    header = jsonio.loads_strict(_text(HEADER_EXAMPLE))
    assert "event" not in header and header["run_id"]


def test_committed_ledger_examples_equal_the_tracer_run_lines(
    synthetic_candidates: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, lines, _ = _tracer_run(synthetic_candidates, tmp_path / "experiments", monkeypatch)
    header, events = lines[0], lines[1:]
    assert jsonio.pretty_bytes(header) == HEADER_EXAMPLE.read_bytes()
    for kind in EVENT_KINDS:
        first = next(line for line in events if line["event"] == kind)
        committed = _event_example(kind).read_bytes()
        assert jsonio.pretty_bytes(first) == committed, kind


def test_committed_problem_and_plan_examples_are_the_tracer_inputs() -> None:
    for path, expected in (
        (PROBLEM_EXAMPLE, charter_problem(1, 3, 2)),
        (PLAN_EXAMPLE, TRACER_PLAN),
    ):
        assert jsonio.loads_strict(_text(path)) == expected, path.name
        assert path.read_bytes() == jsonio.pretty_bytes(expected), path.name


def test_committed_meta_example_equals_the_tracer_meta(
    synthetic_candidates: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, meta = _tracer_run(synthetic_candidates, tmp_path / "experiments", monkeypatch)
    committed = jsonio.loads_strict(_text(META_EXAMPLE))
    # `snapshot_sha256` is the sha256 of the synthetic CSV, and pandas writes that file with the
    # line terminator of the platform, so the two CI platforms disagree on it (RESEARCH F-28).
    # It is left out of the comparison; both values must still be a sha256 in hex.
    hex64 = re.compile(r"[0-9a-f]{64}")
    assert hex64.fullmatch(meta["snapshot_sha256"])
    assert hex64.fullmatch(committed["snapshot_sha256"])
    assert {k: v for k, v in meta.items() if k != "snapshot_sha256"} == {
        k: v for k, v in committed.items() if k != "snapshot_sha256"
    }
    assert committed["provider_key_configured"] is False
    assert committed["dirty"] is False and committed["code_git_sha"] == FIXED_CODE_SHA


def test_every_id_in_the_examples_is_a_fixture_id() -> None:
    found: set[str] = set()
    for path in RUN_RECORD_EXAMPLES:
        found.update(CANDIDATE_ID_TOKEN.findall(_text(path)))
    assert found, "the examples name at least one candidate"
    assert found <= FIXTURE_IDS, sorted(found - FIXTURE_IDS)
