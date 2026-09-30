"""The problem spec, the run directory and ``meta.json`` (RUN-01, RUN-06; CONTEXT D-01, D-05, D-39; A-6).

``parse_problem_spec`` is the only place a caller-supplied problem enters the library and it
follows the order of ``llm4pol.evaluate.contract.parse_request`` (RESEARCH Pattern 6):
validate against ``protocol/schemas/problem-spec.json`` first, refuse what a schema cannot
express, and only then build the frozen dataclasses (threat T-04-01). ``load_problem_spec``
reads through ``jsonio.loads_strict`` so ``NaN`` and a repeated key never reach the validator
(F-39, F-54).

``create_run_dir`` is the A-6 precondition: ``mkdir(exist_ok=False)`` turns an existing run
directory into ``RunExists`` instead of a second run written over the first.

``meta.json`` (D-01, D-39): ``build_meta`` assembles the fifteen keys, ``validate_meta`` checks
them against ``protocol/schemas/run-meta.json`` and ``write_meta`` writes the pretty form once,
after validation. A provider key is recorded as the boolean ``provider_key_configured`` decided by
membership of its name in the environment; no value is read (charter section 12, F-50).
``write_meta`` renders ``redact(meta)`` before it validates: the closed schema is the first defence
(no key of ``meta.json`` can hold an environment value), the key-name and value-shape rules of
``llm4pol.run.redaction`` the second, for the one open mapping the schema admits
(``prompt_versions``) and for what Phase 6 adds (D-01, F-48, WR-05).
"""

from __future__ import annotations

import functools
import math
import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jsonschema.exceptions import best_match

from llm4pol.data.snapshot import DEFAULT_ROOT
from llm4pol.run import atomic, ids
from llm4pol.run.jsonio import StrictJsonError, loads_strict, pretty_bytes
from llm4pol.run.redaction import REDACTED as REDACTED  # noqa: PLC0414  (re-exported)
from llm4pol.run.redaction import redact as redact  # noqa: PLC0414  (re-exported)
from llm4pol.run.strictschema import validator_class

SCHEMA_DIR = DEFAULT_ROOT / "protocol" / "schemas"
PROBLEM_SCHEMA_PATH = SCHEMA_DIR / "problem-spec.json"
META_SCHEMA_PATH = SCHEMA_DIR / "run-meta.json"
META_NAME = "meta.json"
META_SCHEMA_VERSION = 1

# The provider key names of `.env.example`; a name is only ever looked up, never its value.
PROVIDER_KEY_NAMES: tuple[str, ...] = ("OPENAI_API_KEY", "GEMINI_API_KEY", "CLAUDE_API_KEY")

RUN_EXISTS_MESSAGE = "run exists; use replay"

# The paths that define behaviour: `dirty` is read over these only (RESEARCH Pitfall 9, F-52).
BEHAVIOUR_PATHS: tuple[str, ...] = (
    "src",
    "protocol",
    "config",
    "pyproject.toml",
    "env/pixi.toml",
    "env/pixi.lock",
)

PARETO_MESSAGE = (
    "/form: 'pareto' is reserved for the D-16 gate (objective form, fixed at the Phase 7 "
    "pre-registration) and is not accepted by problem spec schema version 1"
)


class ProblemSpecError(ValueError):
    """A problem spec that violates ``problem-spec.json`` (the message names the JSON pointer)."""


class RunExists(FileExistsError):
    """The run directory is already taken; a rerun gets a new run id (A-6)."""


@dataclass(frozen=True, slots=True)
class Objective:
    property: str
    direction: str

    def to_json(self) -> dict[str, object]:
        return {"property": self.property, "direction": self.direction}


@dataclass(frozen=True, slots=True)
class Constraint:
    property: str
    op: str
    value: float

    def to_json(self) -> dict[str, object]:
        return {"property": self.property, "op": self.op, "value": self.value}


@dataclass(frozen=True, slots=True)
class Budget:
    iterations: int
    candidates_per_beam: int
    beams: int

    def to_json(self) -> dict[str, object]:
        return {
            "iterations": self.iterations,
            "candidates_per_beam": self.candidates_per_beam,
            "beams": self.beams,
        }


@dataclass(frozen=True, slots=True)
class ProblemSpec:
    """The typed problem; it exists only after the schema has accepted the payload."""

    objective: Objective
    constraints: tuple[Constraint, ...]
    form: str
    budget: Budget
    table: str
    seed: int
    schema_version: int = 1

    @property
    def evals_limit(self) -> int:
        """The evaluation budget of the whole run: iterations x candidates x beams."""
        b = self.budget
        return b.iterations * b.candidates_per_beam * b.beams

    def property_keys(self) -> tuple[str, ...]:
        """The objective key followed by the constraint keys, in spec order."""
        return (self.objective.property, *(c.property for c in self.constraints))

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "objective": self.objective.to_json(),
            "constraints": [c.to_json() for c in self.constraints],
            "form": self.form,
            "budget": self.budget.to_json(),
            "table": self.table,
            "seed": self.seed,
        }


@functools.cache
def problem_validator() -> Any:
    """The Draft 2020-12 validator of ``problem-spec.json`` (built once)."""
    schema = loads_strict(PROBLEM_SCHEMA_PATH.read_text(encoding="utf-8"))
    return validator_class()(schema)


def _refuse_what_a_schema_cannot_say(payload: Mapping[str, Any]) -> None:
    """Non-finite thresholds (F-54), a repeated constraint, an objective that is constrained."""
    constraints = payload["constraints"]
    seen: set[str] = set()
    for index, item in enumerate(constraints):
        if not math.isfinite(item["value"]):
            raise ProblemSpecError(f"/constraints/{index}/value: not a finite number")
        if item["property"] in seen:
            raise ProblemSpecError(f"/constraints/{index}/property: repeated constraint property")
        seen.add(item["property"])
    if payload["objective"]["property"] in seen:
        raise ProblemSpecError("/constraints: the objective property is also a constraint")


def parse_problem_spec(payload: object) -> ProblemSpec:
    """Validate ``payload`` against the schema, then build the typed spec.

    Raises ``ProblemSpecError`` carrying the JSON pointer of the best-matching violation. A payload
    whose ``form`` is ``pareto`` is refused first, by name: the form is reserved for the D-16 gate.
    """
    if isinstance(payload, Mapping) and payload.get("form") == "pareto":
        raise ProblemSpecError(PARETO_MESSAGE)
    error = best_match(problem_validator().iter_errors(payload))
    if error is not None:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise ProblemSpecError(f"{pointer}: {error.message}")
    fields = cast(Mapping[str, Any], payload)
    _refuse_what_a_schema_cannot_say(fields)
    budget = fields["budget"]
    return ProblemSpec(
        schema_version=int(fields["schema_version"]),
        objective=Objective(**fields["objective"]),
        constraints=tuple(
            Constraint(property=c["property"], op=c["op"], value=float(c["value"]))
            for c in fields["constraints"]
        ),
        form=str(fields["form"]),
        budget=Budget(
            iterations=int(budget["iterations"]),
            candidates_per_beam=int(budget["candidates_per_beam"]),
            beams=int(budget["beams"]),
        ),
        table=str(fields["table"]),
        seed=int(fields["seed"]),
    )


def load_problem_spec(path: Path) -> ProblemSpec:
    """Read ``path`` strictly, then ``parse_problem_spec``; any defect is ``ProblemSpecError``."""
    try:
        payload = loads_strict(path.read_text(encoding="utf-8"))
    except (StrictJsonError, UnicodeDecodeError) as exc:
        raise ProblemSpecError(f"{path.name}: {exc}") from exc
    return parse_problem_spec(payload)


def create_run_dir(experiments: Path, run_id: str) -> Path:
    """Create ``experiments/<run_id>``; ``RunExists`` when it is already there (A-6).

    The run id is matched before any path is built (T-04-02); the parent is created when it
    is absent, the run directory itself never is reused.
    """
    ids.require_run_id(run_id)
    experiments.mkdir(parents=True, exist_ok=True)
    run_dir = experiments / run_id
    try:
        run_dir.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise RunExists(RUN_EXISTS_MESSAGE) from exc
    atomic.fsync_dir(experiments)
    return run_dir


# --------------------------------------------------------------------------
# meta.json
# --------------------------------------------------------------------------


class MetaError(ValueError):
    """A ``meta.json`` mapping that violates ``run-meta.json`` (the message names the pointer)."""


class CodeIdentityError(RuntimeError):
    """Git could not name the code the run is made with."""


@dataclass(frozen=True, slots=True)
class CodeIdentity:
    """The code checkout of a run: its commit and whether the tree differs from it."""

    sha: str
    dirty: bool


def _git(repo: Path, *args: str) -> str:
    try:
        done = subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as exc:
        raise CodeIdentityError(f"git could not be run: {exc}") from exc
    if done.returncode != 0:
        raise CodeIdentityError(f"git {args[0]} failed in {repo}")
    return done.stdout


def code_identity(repo: Path = DEFAULT_ROOT) -> CodeIdentity:
    """``git rev-parse HEAD`` and ``git status --porcelain`` of the code checkout ``repo``.

    ``dirty`` is any porcelain output over ``BEHAVIOUR_PATHS`` only, so an untracked file inside
    them counts and a planning file or a tracked run summary does not (RESEARCH Pitfall 9, F-52).
    ``repo`` is the code checkout, never the data root given to ``--root``.
    """
    sha = _git(repo, "rev-parse", "HEAD").strip()
    dirty = bool(_git(repo, "status", "--porcelain", "--", *BEHAVIOUR_PATHS).strip())
    return CodeIdentity(sha=sha, dirty=dirty)


def provider_key_configured(environ: Mapping[str, str]) -> bool:
    """True when a provider key name is a member of ``environ``; no value is read (F-50)."""
    return any(name in environ for name in PROVIDER_KEY_NAMES)


def build_meta(
    *,
    run_id: str,
    created_at: str,
    problem: ProblemSpec,
    code: CodeIdentity,
    snapshot: str,
    snapshot_sha256: str,
    registry_version: str,
    selector: str,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """The fifteen keys of ``meta.json``; ``prompt_versions`` empty, ``provider``/``model`` null."""
    env = os.environ if environ is None else environ
    return {
        "schema_version": META_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": created_at,
        "problem": problem.to_json(),
        "code_git_sha": code.sha,
        "dirty": code.dirty,
        "prompt_versions": {},
        "provider": None,
        "model": None,
        "seed": problem.seed,
        "snapshot": snapshot,
        "snapshot_sha256": snapshot_sha256,
        "registry_version": registry_version,
        "selector": selector,
        "provider_key_configured": provider_key_configured(env),
    }


@functools.cache
def _meta_validator() -> Any:
    return validator_class()(loads_strict(META_SCHEMA_PATH.read_text(encoding="utf-8")))


def validate_meta(meta: Mapping[str, Any]) -> None:
    """Refuse a mapping the ``run-meta.json`` schema refuses; ``MetaError`` names the pointer."""
    error = best_match(_meta_validator().iter_errors(meta))
    if error is not None:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise MetaError(f"{pointer}: {error.message}")


def write_meta(run_dir: Path, meta: Mapping[str, Any]) -> Path:
    """Redact ``meta``, validate the result, then write ``run_dir/meta.json`` once, exclusively.

    ``MetaError`` before any file is opened; ``FileExistsError`` when the file is already there,
    its bytes untouched. The argument is not changed.
    """
    safe = redact(meta)
    validate_meta(safe)
    path = run_dir / META_NAME
    data = pretty_bytes(safe)
    atomic.write_new(path, data)
    return path
