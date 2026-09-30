"""The run id, strict JSON, the problem spec and the run directory (plan 04-01, task 1).

Guards RUN-01 and RUN-06 and the A-6 preconditions (CONTEXT D-01, D-05): a rerun gets a new run
id, a run directory cannot be taken twice, and a problem spec is validated against
``protocol/schemas/problem-spec.json`` before any typed object exists (RESEARCH Pattern 6).
Test names starting ``test_a6_`` are cited by ``docs/governance/INVARIANTS.md``.

Plan 04-06 adds the refusal matrix of the problem spec, the names-and-types guard of
``meta.json``, redaction by key name and the scope of ``dirty`` (RUN-01, RUN-06, D-39).
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT
from history_secret_scan import PATTERNS
from llm4pol.run import config, ids, jsonio
from run_support import (
    FIXED_CODE_SHA,
    FIXED_NOW,
    FIXED_RUN_ID,
    FIXED_TS,
    SNAPSHOT_ID,
    charter_problem,
)

SCHEMAS = REPO_ROOT / "protocol" / "schemas"


def _load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    return data


# --------------------------------------------------------------------------
# jsonio: two byte forms fixed by their separators (CONTEXT D-02; F-29, F-39)
# --------------------------------------------------------------------------


def test_canonical_and_pretty_bytes() -> None:
    record = {"b": 1, "a": [0.5, None]}

    canonical = jsonio.canonical_bytes(record)
    assert canonical == b'{"a":[0.5,null],"b":1}\n'
    assert len(canonical) == 23

    pretty = jsonio.pretty_bytes(record)
    assert len(pretty) == 45
    assert pretty.endswith(b"}\n") and not pretty.endswith(b"\n\n")
    lines = pretty.decode("utf-8").split("\n")
    assert len(lines) == 8 and lines[-1] == ""
    assert lines[1] == '  "a": ['
    assert b"\r" not in pretty

    for form in (jsonio.canonical_bytes, jsonio.pretty_bytes):
        with pytest.raises(jsonio.StrictJsonError):
            form({"x": float("nan")})
        with pytest.raises(jsonio.StrictJsonError):
            form({"x": float("inf")})


def test_strict_json_refuses_repeated_keys_and_non_finite_constants() -> None:
    assert jsonio.loads_strict('{"a": [1, 2.5, null]}') == {"a": [1, 2.5, None]}

    with pytest.raises(jsonio.StrictJsonError):
        jsonio.loads_strict('{"seq": 1, "seq": 2}')
    for constant in ("NaN", "Infinity", "-Infinity"):
        with pytest.raises(jsonio.StrictJsonError):
            jsonio.loads_strict(f'{{"x": {constant}}}')
    with pytest.raises(jsonio.StrictJsonError):
        jsonio.loads_strict("{not json")
    assert issubclass(jsonio.StrictJsonError, ValueError)


# --------------------------------------------------------------------------
# problem spec (RUN-06; CONTEXT D-05, RESEARCH Pattern 6, F-54, F-58)
# --------------------------------------------------------------------------


def test_problem_spec_is_validated_before_it_is_typed(tmp_path: Path) -> None:
    payload = charter_problem(1, 3, 2)
    spec = config.parse_problem_spec(payload)
    assert isinstance(spec, config.ProblemSpec)
    assert spec.evals_limit == 6
    assert spec.property_keys() == ("thermal_conductivity", "dielectric_const_dc", "tg")
    assert spec.to_json() == payload

    without_version = {k: v for k, v in payload.items() if k != "schema_version"}
    pareto = {**payload, "form": "pareto"}
    extra = {**payload, "note": "x"}
    for bad in (without_version, pareto, extra):
        with pytest.raises(config.ProblemSpecError):
            config.parse_problem_spec(bad)

    nan_threshold = {
        **payload,
        "constraints": [{"property": "tg", "op": ">=", "value": float("nan")}],
    }
    with pytest.raises(config.ProblemSpecError):
        config.parse_problem_spec(nan_threshold)

    path = tmp_path / "problem.json"
    path.write_bytes(jsonio.pretty_bytes(payload))
    assert config.load_problem_spec(path) == spec
    text = path.read_text(encoding="utf-8").replace("2.6", "NaN")
    path.write_text(text, encoding="utf-8")
    with pytest.raises(config.ProblemSpecError):
        config.load_problem_spec(path)


def test_problem_spec_refuses_a_repeated_or_shared_property() -> None:
    payload = charter_problem(1, 3, 2)
    repeated = {
        **payload,
        "constraints": [
            {"property": "tg", "op": ">=", "value": 400.0},
            {"property": "tg", "op": "<=", "value": 500.0},
        ],
    }
    objective_as_constraint = {
        **payload,
        "constraints": [{"property": "thermal_conductivity", "op": ">=", "value": 0.2}],
    }
    for bad in (repeated, objective_as_constraint):
        with pytest.raises(config.ProblemSpecError):
            config.parse_problem_spec(bad)


def test_problem_spec_property_enum_equals_the_registry_schema_enum() -> None:
    registry = _load("property-registry.json")["properties"]["properties"]["propertyNames"]["enum"]
    spec = _load("problem-spec.json")["properties"]
    assert spec["objective"]["properties"]["property"]["enum"] == registry
    assert spec["constraints"]["items"]["properties"]["property"]["enum"] == registry
    assert spec["form"]["enum"] == ["constrained_single"]


# --------------------------------------------------------------------------
# run id and run directory (RUN-01; CONTEXT D-01; A-6)
# --------------------------------------------------------------------------


def test_a6_a_rerun_gets_a_new_run_id() -> None:
    run_id = ids.new_run_id(FIXED_NOW, "00000000")
    assert run_id == "20260101T000000Z-00000000"
    assert len(run_id) == 25
    assert ids.RUN_ID_PATTERN.fullmatch(run_id)
    assert ids.new_run_id(FIXED_NOW, "0000000a") != run_id

    for token in ("0000000", "000000000", "0000000G", "0000000A", ""):
        with pytest.raises(ids.RunIdError):
            ids.new_run_id(FIXED_NOW, token)

    assert ids.require_run_id(run_id) == run_id
    for text in ("../20260101T000000Z-00000000", "a/b", "a\\b", "..", "x..y", "", run_id + "\n"):
        with pytest.raises(ids.RunIdError):
            ids.require_run_id(text)

    assert ids.format_ts(FIXED_NOW) == "2026-01-01T00:00:00Z"
    assert ids.RUN_ID_PATTERN.fullmatch(ids.new_run_id(ids.utc_now(), ids.random_token()))


def test_a6_run_directory_refuses_to_be_created_twice(tmp_path: Path) -> None:
    experiments = tmp_path / "experiments"
    run_dir = config.create_run_dir(experiments, FIXED_RUN_ID)
    assert run_dir == experiments / FIXED_RUN_ID
    assert run_dir.is_dir()

    marker = run_dir / "marker.txt"
    marker.write_text("kept", encoding="utf-8")
    with pytest.raises(config.RunExists) as excinfo:
        config.create_run_dir(experiments, FIXED_RUN_ID)
    assert str(excinfo.value) == "run exists; use replay"
    assert marker.read_text(encoding="utf-8") == "kept"
    assert sorted(p.name for p in run_dir.iterdir()) == ["marker.txt"]

    with pytest.raises(ids.RunIdError):
        config.create_run_dir(experiments, "../escape")
    assert not (tmp_path / "escape").exists()


# --------------------------------------------------------------------------
# Plan 04-06, task 1: the refusal matrix of the problem spec (RUN-06; CONTEXT D-05; A-7)
# --------------------------------------------------------------------------

# The barred static permittivity key is written from fragments, as in tests/test_data_registry.py.
BARRED_KEY = "static_" + "dielectric_const"
NON_FINITE_TEXTS = ("NaN", "Infinity", "-Infinity")

Change = Callable[[dict[str, Any]], dict[str, Any]]


def _tracer() -> dict[str, Any]:
    return charter_problem(1, 3, 2)


def _with(**changes: Any) -> Change:
    def apply(payload: dict[str, Any]) -> dict[str, Any]:
        return {**payload, **changes}

    return apply


def _edit(mutate: Callable[[dict[str, Any]], object]) -> Change:
    def apply(payload: dict[str, Any]) -> dict[str, Any]:
        clone = copy.deepcopy(payload)
        mutate(clone)
        return clone

    return apply


def _drop(key: str) -> Change:
    return lambda payload: {k: v for k, v in payload.items() if k != key}


REFUSALS: dict[str, Change] = {
    "no_schema_version": _drop("schema_version"),
    "schema_version_2": _with(schema_version=2),
    "form_pareto": _with(form="pareto"),
    "form_weighted_sum": _with(form="weighted_sum"),
    "barred_key_as_objective": _edit(lambda p: p["objective"].update(property=BARRED_KEY)),
    "barred_key_as_constraint": _edit(
        lambda p: p["constraints"].append({"property": BARRED_KEY, "op": "<=", "value": 3.0})
    ),
    "unregistered_key": _edit(lambda p: p["objective"].update(property="melting_point")),
    "direction_up": _edit(lambda p: p["objective"].update(direction="up")),
    "op_strictly_less": _edit(lambda p: p["constraints"][0].update(op="<")),
    "threshold_as_string": _edit(lambda p: p["constraints"][0].update(value="2.6")),
    "iterations_zero": _edit(lambda p: p["budget"].update(iterations=0)),
    "candidates_per_beam_zero": _edit(lambda p: p["budget"].update(candidates_per_beam=0)),
    "beams_zero": _edit(lambda p: p["budget"].update(beams=0)),
    "seed_negative": _with(seed=-1),
    "seed_boolean": _with(seed=True),
    "table_of_another_dataset": _with(table="polyinfo:general_polymers@041e5834"),
    "extra_top_level_key": _with(note="x"),
    "extra_key_in_objective": _edit(lambda p: p["objective"].update(weight=1)),
    "extra_key_in_constraint": _edit(lambda p: p["constraints"][0].update(weight=1)),
    "extra_key_in_budget": _edit(lambda p: p["budget"].update(workers=2)),
    "repeated_constraint_property": _edit(
        lambda p: p["constraints"].append({"property": "tg", "op": "<=", "value": 500.0})
    ),
    "objective_is_also_constrained": _edit(
        lambda p: p["constraints"].append(
            {"property": "thermal_conductivity", "op": ">=", "value": 0.2}
        )
    ),
    "constraints_not_a_list": _with(constraints={"tg": 400.0}),
}


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_problem_spec_refusals(case: str) -> None:
    with pytest.raises(config.ProblemSpecError):
        config.parse_problem_spec(REFUSALS[case](_tracer()))


def test_problem_spec_refuses_a_payload_that_is_not_an_object() -> None:
    for bad in ([_tracer()], "text", 7, None):
        with pytest.raises(config.ProblemSpecError):
            config.parse_problem_spec(bad)


def test_the_refusal_matrix_leaves_the_charter_example_parsing() -> None:
    spec = config.parse_problem_spec(_tracer())
    assert spec.form == "constrained_single"
    assert spec.evals_limit == 6


@pytest.mark.parametrize("constant", NON_FINITE_TEXTS)
def test_problem_spec_text_refusals(constant: str, tmp_path: Path) -> None:
    path = tmp_path / "problem.json"
    pretty = jsonio.pretty_bytes(_tracer()).decode("utf-8")
    text = pretty.replace("2.6", constant)
    assert constant in text
    path.write_text(text, encoding="utf-8")
    with pytest.raises(config.ProblemSpecError):
        config.load_problem_spec(path)

    repeated = pretty.replace('"seed": 0', '"seed": 0,\n  "seed": 1')
    assert repeated.count('"seed"') == 2
    path.write_text(repeated, encoding="utf-8")
    with pytest.raises(config.ProblemSpecError):
        config.load_problem_spec(path)

    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(config.ProblemSpecError):
        config.load_problem_spec(path)


def test_pareto_is_refused_with_a_message_naming_the_gate() -> None:
    with pytest.raises(config.ProblemSpecError) as excinfo:
        config.parse_problem_spec({**_tracer(), "form": "pareto"})
    message = str(excinfo.value)
    assert "pareto" in message
    assert "reserved" in message
    assert "D-16" in message


# --------------------------------------------------------------------------
# Plan 04-06, task 1: meta.json pins names and types, and never holds a key value (D-39, D-01)
# --------------------------------------------------------------------------

META_SCHEMA_PATH = SCHEMAS / "run-meta.json"
DOTENV_EXAMPLE = REPO_ROOT / (".env" + ".example")
SELECTOR_ID = "plan:sha256:" + "0" * 64


def _meta(environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    return config.build_meta(
        run_id=FIXED_RUN_ID,
        created_at=FIXED_TS,
        problem=config.parse_problem_spec(_tracer()),
        code=config.CodeIdentity(FIXED_CODE_SHA, False),
        snapshot=SNAPSHOT_ID,
        snapshot_sha256="0" * 64,
        registry_version="v1",
        selector=SELECTOR_ID,
        environ={} if environ is None else environ,
    )


def _control(class_name: str) -> str:
    """The scanner's own synthetic positive control of a class; built at run time, never a literal."""
    return next(p.positive_control for p in PATTERNS if p.name == class_name)


def _scanner_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in PATTERNS:
        for match in pattern.regex.finditer(text):
            if pattern.extra_validate is None or pattern.extra_validate(match):
                hits.append(pattern.name)
    return hits


META_REFUSALS: dict[str, Change] = {
    "extra_key": _with(note="x"),
    "dirty_as_string": _with(dirty="false"),
    "dirty_as_integer": _with(dirty=0),
    "seed_as_boolean": _with(seed=True),
    "seed_negative": _with(seed=-1),
    "schema_version_2": _with(schema_version=2),
    "sha_of_39_characters": _with(code_git_sha="0" * 39),
    "sha_of_uppercase": _with(code_git_sha="A" * 40),
    "snapshot_sha256_of_63_characters": _with(snapshot_sha256="0" * 63),
    "provider_as_number": _with(provider=7),
    "model_as_number": _with(model=7),
    "provider_key_configured_as_string": _with(provider_key_configured="true"),
    "run_id_of_another_shape": _with(run_id="not-a-run-id"),
    "prompt_versions_with_a_number": _with(prompt_versions={"hypothesis": 1}),
    "problem_with_an_extra_key": _edit(lambda m: m["problem"].update(note="x")),
    "snapshot_of_another_dataset": _with(snapshot="polyinfo:general_polymers@041e5834"),
}


def test_meta_schema_pins_names_and_types(tmp_path: Path) -> None:
    schema = json.loads(META_SCHEMA_PATH.read_text(encoding="utf-8"))
    meta = _meta()
    assert sorted(meta) == sorted(schema["required"])
    assert len(meta) == 15

    for key in schema["required"]:
        run_dir = tmp_path / f"missing-{key}"
        run_dir.mkdir()
        with pytest.raises(config.MetaError):
            config.write_meta(run_dir, {k: v for k, v in meta.items() if k != key})
        assert not (run_dir / config.META_NAME).exists()

    for case, refuse in META_REFUSALS.items():
        run_dir = tmp_path / case
        run_dir.mkdir()
        with pytest.raises(config.MetaError):
            config.write_meta(run_dir, refuse(meta))
        assert not (run_dir / config.META_NAME).exists(), case

    good = tmp_path / "good"
    good.mkdir()
    written = config.write_meta(good, meta)
    assert json.loads(written.read_text(encoding="utf-8")) == meta


def test_provider_key_is_recorded_as_a_boolean_only(tmp_path: Path) -> None:
    value = _control("openai_secret_key")
    meta = _meta({"OPENAI_API_KEY": value})
    assert meta["provider_key_configured"] is True
    assert _meta({})["provider_key_configured"] is False
    assert _meta({"LLM_PROVIDER": "openai"})["provider_key_configured"] is False

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    text = config.write_meta(run_dir, meta).read_bytes().decode("utf-8")
    assert value not in text
    assert _scanner_hits(text) == []

    names = [
        line.split("=", 1)[0].strip()
        for line in DOTENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if line.split("=", 1)[0].strip().endswith("_API_KEY")
    ]
    assert list(config.PROVIDER_KEY_NAMES) == names
    assert len(names) == 3


SECRET_SHAPED_NAMES = (
    "openai_api_key",
    "OPENAI_API_KEY",
    "api_key",
    "CLAUDE_API_KEY",
    "GEMINI_API_KEY",
    "hf_token",
    "password",
    "secret",
)
PLAIN_NAMES = (
    "tokens",
    "max_tokens",
    "token_budget",
    "key",
    "candidate_id",
    "code_git_sha",
    "provider_key_configured",
)


def test_redaction_rule_by_key_name() -> None:
    assert config.REDACTED == "***REDACTED***"
    for name in SECRET_SHAPED_NAMES:
        assert config.redact({name: "value-1", "other": 1}) == {name: config.REDACTED, "other": 1}
    for name in PLAIN_NAMES:
        assert config.redact({name: 12345}) == {name: 12345}, name

    nested = {
        "usage": {"tokens": 812, "items": [{"api_key": "x", "n": 3}, {"hf_token": "y"}]},
        "outer": ({"secret": "z"},),
    }
    before = copy.deepcopy(nested)
    result = config.redact(nested)
    assert result == {
        "usage": {
            "tokens": 812,
            "items": [{"api_key": config.REDACTED, "n": 3}, {"hf_token": config.REDACTED}],
        },
        "outer": [{"secret": config.REDACTED}],
    }
    assert nested == before
    assert result is not nested and result["usage"] is not nested["usage"]


def test_write_meta_never_writes_a_secret_shaped_value(tmp_path: Path) -> None:
    value = _control("openai_secret_key")
    meta = {**_meta(), "prompt_versions": {"hypothesis_api_key": value, "hypothesis": "v1"}}
    assert _scanner_hits(json.dumps(meta)) != []  # the control is a real hit before redaction

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    written = config.write_meta(run_dir, meta)
    text = written.read_bytes().decode("utf-8")
    assert value not in text
    assert _scanner_hits(text) == []
    stored = json.loads(text)
    assert stored["prompt_versions"] == {"hypothesis_api_key": config.REDACTED, "hypothesis": "v1"}
    config.validate_meta(stored)
    assert meta["prompt_versions"]["hypothesis_api_key"] == value  # the argument is not mutated


# --------------------------------------------------------------------------
# Plan 04-06, task 1: dirty reads the paths that define behaviour only (Pitfall 9)
# --------------------------------------------------------------------------

_GIT_IDENTITY = ("-c", "user.name=scratch", "-c", "user.email=scratch@example.invalid")


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *_GIT_IDENTITY, "-c", "commit.gpgsign=false", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _scratch_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "scratch"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _run_git(repo, "init", "--quiet")
    _run_git(repo, "add", "src/module.py")
    _run_git(repo, "commit", "--quiet", "--message", "first revision")
    return repo


def _touch(repo: Path, relative: str, text: str = "x\n") -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_behaviour_paths_are_the_ones_the_plan_names() -> None:
    assert config.BEHAVIOUR_PATHS == (
        "src",
        "protocol",
        "config",
        "pyproject.toml",
        "env/pixi.toml",
        "env/pixi.lock",
    )


def test_dirty_reads_the_paths_that_define_behaviour_only(tmp_path: Path) -> None:
    repo = _scratch_repo(tmp_path)
    identity = config.code_identity(repo)
    assert re.fullmatch(r"[0-9a-f]{40}", identity.sha)
    assert identity.dirty is False

    _touch(repo, ".planning/notes.md")
    _touch(repo, f"experiments/{FIXED_RUN_ID}/meta.json")
    _touch(repo, "docs/note.md")
    assert config.code_identity(repo).dirty is False

    _touch(repo, "src/module.py", "VALUE = 2\n")
    assert config.code_identity(repo).dirty is True
    _run_git(repo, "checkout", "--", "src/module.py")
    assert config.code_identity(repo).dirty is False

    for relative in (
        "src/new_module.py",
        "protocol/schemas/new.json",
        "config/new.yaml",
        "pyproject.toml",
    ):
        _touch(repo, relative)
        assert config.code_identity(repo).dirty is True, relative
        (repo / relative).unlink()
        assert config.code_identity(repo).dirty is False, relative


def test_code_identity_of_a_directory_that_is_not_a_repository_is_refused(tmp_path: Path) -> None:
    with pytest.raises(config.CodeIdentityError):
        config.code_identity(tmp_path)


# --------------------------------------------------------------------------
# Plan 04-06, task 1: the run id sources (RUN-01)
# --------------------------------------------------------------------------


def test_run_id_sources() -> None:
    first, second = ids.random_token(), ids.random_token()
    assert re.fullmatch(r"[0-9a-f]{8}", first)
    assert re.fullmatch(r"[0-9a-f]{8}", second)
    assert first != second

    now = ids.utc_now()
    assert now.tzinfo is not None
    offset = now.utcoffset()
    assert offset is not None and offset.total_seconds() == 0
    assert now.microsecond == 0

    assert ids.format_ts(FIXED_NOW) == "2026-01-01T00:00:00Z"
