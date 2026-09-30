"""The problem spec and the run directory (RUN-01, RUN-06; CONTEXT D-01, D-05; A-6).

``parse_problem_spec`` is the only place a caller-supplied problem enters the library and it
follows the order of ``llm4pol.evaluate.contract.parse_request`` (RESEARCH Pattern 6):
validate against ``protocol/schemas/problem-spec.json`` first, refuse what a schema cannot
express, and only then build the frozen dataclasses (threat T-04-01). ``load_problem_spec``
reads through ``jsonio.loads_strict`` so ``NaN`` and a repeated key never reach the validator
(F-39, F-54).

``create_run_dir`` is the A-6 precondition: ``mkdir(exist_ok=False)`` turns an existing run
directory into ``RunExists`` instead of a second run written over the first.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import jsonschema
from jsonschema.exceptions import best_match

from llm4pol.data.snapshot import DEFAULT_ROOT
from llm4pol.run import ids
from llm4pol.run.jsonio import StrictJsonError, loads_strict

SCHEMA_DIR = DEFAULT_ROOT / "protocol" / "schemas"
PROBLEM_SCHEMA_PATH = SCHEMA_DIR / "problem-spec.json"

RUN_EXISTS_MESSAGE = "run exists; use replay"


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
    return jsonschema.Draft202012Validator(schema)


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

    Raises ``ProblemSpecError`` carrying the JSON pointer of the best-matching violation.
    """
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
    except StrictJsonError as exc:
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
    return run_dir
