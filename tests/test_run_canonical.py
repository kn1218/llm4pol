"""WR-02: the strict reader holds every line to the canonical byte form it documents.

``ledger_sha256`` is taken over raw bytes, so two semantically identical ledgers with different
bytes give different ``run_summary.json`` files. A CRLF-converted copy, a pretty-printed or
reordered line, a number written another way (``0.1550``, ``1E5``) or an integer field written
``1.0`` must therefore be refused, not read. Every value is an invented fixture fact.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from llm4pol.run import __main__ as cli
from llm4pol.run import jsonio, ledger
from run_support import FIXED_RUN_ID, canonical_line, valid_event, valid_header

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "run" / "reference-ledger.jsonl"


def _lines() -> list[bytes]:
    events = [valid_event("run_opened", 1), valid_event("iteration_opened", 2)]
    return [canonical_line(valid_header()), *(canonical_line(event) for event in events)]


def _refused(raw: bytes) -> None:
    with pytest.raises(ledger.LedgerFormatError):
        ledger.parse_bytes(raw)


def test_the_control_ledger_and_the_pinned_fixture_read() -> None:
    assert len(ledger.parse_bytes(b"".join(_lines())).events) == 2
    parsed = ledger.parse_bytes(FIXTURE.read_bytes())
    assert len(parsed.events) == 17


def test_a_crlf_converted_ledger_is_refused() -> None:
    _refused(b"".join(_lines()).replace(b"\n", b"\r\n"))


@pytest.mark.parametrize("index", [0, 1, 2])
def test_a_spaced_or_reordered_line_is_refused(index: int) -> None:
    lines = _lines()
    record = json.loads(lines[index])
    spaced = json.dumps(record, sort_keys=True).encode() + b"\n"  # ", " and ": " separators
    reordered = json.dumps(dict(reversed(list(record.items()))), separators=(",", ":")).encode()
    for variant in (spaced, reordered + b"\n"):
        assert variant != lines[index]
        _refused(b"".join([*lines[:index], variant, *lines[index + 1 :]]))


def test_a_number_written_another_way_is_refused() -> None:
    lines = _lines()
    for old, new in ((b"0.155", b"0.1550"), (b"2.6", b"2.60"), (b"250.0", b"2.5e2")):
        assert old in lines[1]
        _refused(b"".join([lines[0], lines[1].replace(old, new, 1), lines[2]]))


def test_an_integer_field_written_as_a_float_is_refused() -> None:
    lines = _lines()
    header = lines[0].replace(b'"seed":0', b'"seed":0.0')
    assert header != lines[0]
    _refused(b"".join([header, *lines[1:]]))
    event = lines[1].replace(b'"seq":1', b'"seq":1.0')
    assert event != lines[1]
    _refused(b"".join([lines[0], event, lines[2]]))


def test_the_strict_integer_rule_does_not_touch_a_number_field() -> None:
    record = valid_event("evaluation", 1)
    record["payload"]["cost"]["cpu_hours"] = 0  # a number field accepts an integer
    record["payload"]["results"][0]["cost"]["cpu_hours"] = 0
    ledger._check(record, "event", "event")


def test_replay_exits_2_on_a_crlf_ledger_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = tmp_path / FIXED_RUN_ID
    run_dir.mkdir()
    (run_dir / ledger.LEDGER_NAME).write_bytes(FIXTURE.read_bytes().replace(b"\n", b"\r\n"))
    capsys.readouterr()
    code = cli.main(["replay", "--run", FIXED_RUN_ID, "--experiments", str(tmp_path)])
    assert code == cli.EXIT_INPUT
    assert sorted(p.name for p in run_dir.iterdir()) == [ledger.LEDGER_NAME]


def test_the_canonical_form_is_what_the_writer_emits() -> None:
    record = valid_event("run_opened", 1)
    assert canonical_line(record) == jsonio.canonical_bytes(record)
