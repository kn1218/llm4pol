"""WR-01: strict JSON refuses what it documents, and every refusal is the module's own error.

``json.loads`` lets ``1e999`` overflow to ``inf``, raises a bare ``ValueError`` on a 5000-digit
integer and ``RecursionError`` on deep nesting, and ``.encode`` of a lone surrogate raises
``UnicodeEncodeError`` outside the ``try`` of ``_dumps``. A non-UTF-8 problem or plan file raises
``UnicodeDecodeError``. None of these may reach the command line as a traceback (exit 2).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm4pol.run import __main__ as cli
from llm4pol.run import config, jsonio, ledger, selector
from run_support import TRACER_PLAN, charter_problem, valid_event, valid_header

BAD_TEXTS = {
    "overflowing float": '{"x": 1e999}',
    "overflowing float in a list": "[1.0, [-1e999]]",
    "huge integer": '{"x": ' + "9" * 5000 + "}",
    "long integer below the interpreter limit": '{"x": ' + "9" * 200 + "}",
    "deep nesting": "[" * 100_000 + "]" * 100_000,
    "deep object nesting": '{"a":' * 100_000 + "1" + "}" * 100_000,
}


@pytest.mark.parametrize("name", list(BAD_TEXTS))
def test_loads_strict_refuses_with_its_own_error(name: str) -> None:
    with pytest.raises(jsonio.StrictJsonError):
        jsonio.loads_strict(BAD_TEXTS[name])


def test_loads_strict_still_reads_what_it_should() -> None:
    text = '{"a": [1, -2, 2.5, 1e5, 0.0, null, true], "b": "x"}'
    assert jsonio.loads_strict(text) == {"a": [1, -2, 2.5, 1e5, 0.0, None, True], "b": "x"}
    assert jsonio.loads_strict('{"n": ' + "9" * 18 + "}") == {"n": int("9" * 18)}


def test_a_lone_surrogate_is_a_strict_json_error_on_the_way_out() -> None:
    parsed = jsonio.loads_strict('{"a": "\\ud800"}')  # parses; it cannot be written as UTF-8
    with pytest.raises(jsonio.StrictJsonError):
        jsonio.canonical_bytes(parsed)
    with pytest.raises(jsonio.StrictJsonError):
        jsonio.pretty_bytes(parsed)


def test_a_deep_structure_cannot_be_written_either() -> None:
    nested: list[object] = []
    for _ in range(100_000):
        nested = [nested]
    with pytest.raises(jsonio.StrictJsonError):
        jsonio.canonical_bytes({"a": nested})


def test_a_non_utf8_problem_or_plan_file_is_the_modules_own_error(tmp_path: Path) -> None:
    binary = tmp_path / "binary.json"
    binary.write_bytes(b'{"a": "\xff\xfe"}')
    problem = config.parse_problem_spec(charter_problem(1, 3, 2))
    with pytest.raises(config.ProblemSpecError):
        config.load_problem_spec(binary)
    with pytest.raises(selector.PlanError):
        selector.PlanSelector.from_file(binary, problem)


def test_a_ledger_line_of_that_kind_is_a_format_error() -> None:
    header = jsonio.canonical_bytes(valid_header())
    for name in ("overflowing float", "huge integer", "deep nesting"):
        raw = header + BAD_TEXTS[name].encode("utf-8") + b"\n"
        with pytest.raises(ledger.LedgerFormatError):
            ledger.parse_bytes(raw)
    event = jsonio.canonical_bytes(valid_event("run_opened", 1))
    surrogate = event.replace(b'"check_tc"', b'"\\ud800"', 1)
    with pytest.raises(ledger.LedgerError):
        ledger.parse_bytes(header + surrogate)


def _write(path: Path, content: str | bytes) -> Path:
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return path


@pytest.mark.parametrize("name", [*BAD_TEXTS, "not utf-8"])
def test_the_cli_exits_2_for_each_of_them_without_a_traceback(
    name: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    content: str | bytes = b"\xff\xfe\x00" if name == "not utf-8" else BAD_TEXTS[name]
    plan = _write(tmp_path / "plan.json", json.dumps(TRACER_PLAN))
    for problem_text, plan_path in (
        (content, plan),
        (json.dumps(charter_problem(1, 3, 2)), _write(tmp_path / "bad-plan.json", content)),
    ):
        problem = _write(tmp_path / "problem.json", problem_text)
        capsys.readouterr()
        code = cli.main(
            [
                "run",
                "--problem",
                str(problem),
                "--selector",
                "plan",
                "--plan",
                str(plan_path),
                "--experiments",
                str(tmp_path / "experiments"),
            ]
        )
        captured = capsys.readouterr()
        assert code == cli.EXIT_INPUT
        assert captured.out == "ERROR: input refused\n"
        assert "Traceback" not in captured.err
    assert not (tmp_path / "experiments").exists()


def test_the_cli_replay_exits_2_on_a_ledger_holding_an_overflowing_number(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_id = valid_header()["run_id"]
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    (run_dir / ledger.LEDGER_NAME).write_bytes(
        jsonio.canonical_bytes(valid_header()) + b'{"seq": 1e999}\n'
    )
    capsys.readouterr()
    assert cli.main(["replay", "--run", run_id, "--experiments", str(tmp_path)]) == cli.EXIT_INPUT
    assert "Traceback" not in capsys.readouterr().err
