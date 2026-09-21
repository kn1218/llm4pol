"""The evaluator contract (charter section 7, frozen at M2; CONTEXT D-01, D-02, D-05).

Frozen, pydantic-free dataclasses mirroring ``protocol/schemas/eval-request.json``
and ``eval-response.json``, the ``Backend`` protocol every backend implements,
and ``parse_request`` -- the only place caller-supplied structure enters the
library, validated against the request schema before any dataclass is built
(threat T-03-01). ``EvalResult.from_json`` type-checks every field so a
replayed cache line (plan 03-02) can never smuggle a wrong type in (T-03-05).

Status taxonomy (D-02): ``ok`` (candidate known, key registered, median
non-null), ``unsupported`` (key not in the registry), ``missing`` (median null
-- ``value_absent`` -- or candidate not in the snapshot -- ``candidate_unknown``),
``error`` (the backend raised; ``reason`` is the exception class name; retryable).
"""

from __future__ import annotations

import functools
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, cast, get_args, runtime_checkable

import jsonschema
from jsonschema.exceptions import best_match

from llm4pol.data.snapshot import DEFAULT_ROOT

Status = Literal["ok", "unsupported", "missing", "error"]
STATUSES: frozenset[str] = frozenset(get_args(Status))

MissingReason = Literal["value_absent", "candidate_unknown"]
MISSING_REASONS: frozenset[str] = frozenset(get_args(MissingReason))

SCHEMA_DIR = DEFAULT_ROOT / "protocol" / "schemas"
REQUEST_SCHEMA_PATH = SCHEMA_DIR / "eval-request.json"
RESPONSE_SCHEMA_PATH = SCHEMA_DIR / "eval-response.json"


class RequestError(ValueError):
    """A request payload that violates ``eval-request.json`` (the message names the JSON pointer)."""


def parse_status(value: str) -> Status:
    """Narrow a string to ``Status`` (F-38); ``ValueError`` on anything else."""
    if value in STATUSES:
        return cast(Status, value)
    raise ValueError(f"unknown status {value!r}")


@dataclass(frozen=True, slots=True)
class Cost:
    """Two currencies that are never merged into one number (charter A-3)."""

    evals: int
    cpu_hours: float

    def to_json(self) -> dict[str, object]:
        return {"evals": self.evals, "cpu_hours": self.cpu_hours}

    @classmethod
    def from_json(cls, obj: object) -> Cost:
        fields = _mapping(obj, "cost")
        return cls(evals=_int(fields, "evals"), cpu_hours=_float(fields, "cpu_hours"))


@dataclass(frozen=True, slots=True)
class Lookup:
    """What a backend knows about one (candidate, property): the facts, no cost."""

    status: Status
    value: float | None = None
    unit: str | None = None
    n_replicates: int | None = None
    spread: float | None = None
    reason: str | None = None


@runtime_checkable
class Backend(Protocol):
    """The one interface every evaluator backend implements (D-05).

    ``name`` is the backend identifier written into every result (``table``);
    ``source`` the snapshot it answers from; ``provenance_tier`` the tier of
    its values (``md_simulated`` for the table).
    """

    @property
    def name(self) -> str: ...

    @property
    def source(self) -> str: ...

    @property
    def provenance_tier(self) -> str: ...

    def lookup(self, candidate_id: str, property_key: str) -> Lookup: ...


@dataclass(frozen=True, slots=True)
class BatchEntry:
    candidate_id: str
    properties: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return {"candidate_id": self.candidate_id, "properties": list(self.properties)}


@dataclass(frozen=True, slots=True)
class EvalRequest:
    run_id: str
    iteration: int
    batch: tuple[BatchEntry, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "iteration": self.iteration,
            "batch": [entry.to_json() for entry in self.batch],
        }


@dataclass(frozen=True, slots=True)
class EvalResult:
    """One result of the response: the twelve contract fields plus the optional ``reason``."""

    candidate_id: str
    property: str
    status: Status
    value: float | None
    unit: str | None
    n_replicates: int | None
    spread: float | None
    backend: str
    source: str
    provenance_tier: str
    cached: bool
    cost: Cost
    reason: str | None = None

    @classmethod
    def from_lookup(
        cls,
        candidate_id: str,
        property_key: str,
        lookup: Lookup,
        backend: Backend,
        *,
        cost: Cost,
    ) -> EvalResult:
        """A fresh (never cached) result carrying the backend's provenance."""
        return cls(
            candidate_id=candidate_id,
            property=property_key,
            status=lookup.status,
            value=lookup.value,
            unit=lookup.unit,
            n_replicates=lookup.n_replicates,
            spread=lookup.spread,
            backend=backend.name,
            source=backend.source,
            provenance_tier=backend.provenance_tier,
            cached=False,
            cost=cost,
            reason=lookup.reason,
        )

    def to_json(self) -> dict[str, object]:
        """The schema shape: ``cost`` nested, ``reason`` present only when set."""
        payload: dict[str, object] = {
            "candidate_id": self.candidate_id,
            "property": self.property,
            "status": self.status,
            "value": self.value,
            "unit": self.unit,
            "n_replicates": self.n_replicates,
            "spread": self.spread,
            "backend": self.backend,
            "source": self.source,
            "provenance_tier": self.provenance_tier,
            "cached": self.cached,
            "cost": self.cost.to_json(),
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload

    @classmethod
    def from_json(cls, obj: object) -> EvalResult:
        """Rebuild a result, type-checking every field; ``ValueError`` on any wrong type."""
        fields = _mapping(obj, "result")
        return cls(
            candidate_id=_str(fields, "candidate_id"),
            property=_str(fields, "property"),
            status=parse_status(_str(fields, "status")),
            value=_float(fields, "value", optional=True),
            unit=_str(fields, "unit", optional=True),
            n_replicates=_int(fields, "n_replicates", optional=True),
            spread=_float(fields, "spread", optional=True),
            backend=_str(fields, "backend"),
            source=_str(fields, "source"),
            provenance_tier=_str(fields, "provenance_tier"),
            cached=_bool(fields, "cached"),
            cost=Cost.from_json(fields.get("cost")),
            reason=_str(fields, "reason", optional=True) if "reason" in fields else None,
        )


@dataclass(frozen=True, slots=True)
class EvalResponse:
    run_id: str
    iteration: int
    results: tuple[EvalResult, ...]
    cost: Cost

    def to_json(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "iteration": self.iteration,
            "results": [result.to_json() for result in self.results],
            "cost": self.cost.to_json(),
        }

    @classmethod
    def from_json(cls, obj: object) -> EvalResponse:
        fields = _mapping(obj, "response")
        results = fields.get("results")
        if not isinstance(results, list):
            raise _wrong_type("results", "a list", results)
        return cls(
            run_id=_str(fields, "run_id"),
            iteration=_int(fields, "iteration"),
            results=tuple(EvalResult.from_json(item) for item in results),
            cost=Cost.from_json(fields.get("cost")),
        )


# --------------------------------------------------------------------------
# Typed field readers for from_json (bool is rejected where int/float is expected).
# --------------------------------------------------------------------------


def _wrong_type(key: str, expected: str, value: object) -> ValueError:
    """The one exception class of the boundary: a wrong-typed field is a bad value.

    ``ValueError`` (not ``TypeError``) on purpose: a malformed record -- from a
    cache line, a file or a caller -- is a bad *payload*, and the CLI and the
    cache replay of plan 03-02 treat every payload defect as one error class.
    """
    return ValueError(f"field {key!r} must be {expected}, got {type(value).__name__}")


def _mapping(obj: object, what: str) -> Mapping[str, Any]:
    if not isinstance(obj, Mapping):
        raise _wrong_type(what, "a JSON object", obj)
    return obj


def _present(fields: Mapping[str, Any], key: str, optional: bool) -> bool:
    if key not in fields:
        raise ValueError(f"missing field {key!r}")
    if fields[key] is None:
        if optional:
            return False
        raise ValueError(f"field {key!r} must not be null")
    return True


def _str(fields: Mapping[str, Any], key: str, *, optional: bool = False) -> Any:
    if not _present(fields, key, optional):
        return None
    value = fields[key]
    if not isinstance(value, str):
        raise _wrong_type(key, "a string", value)
    return value


def _int(fields: Mapping[str, Any], key: str, *, optional: bool = False) -> Any:
    if not _present(fields, key, optional):
        return None
    value = fields[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise _wrong_type(key, "an integer", value)
    return value


def _float(fields: Mapping[str, Any], key: str, *, optional: bool = False) -> Any:
    if not _present(fields, key, optional):
        return None
    value = fields[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _wrong_type(key, "a number", value)
    return float(value)


def _bool(fields: Mapping[str, Any], key: str) -> Any:
    _present(fields, key, False)
    value = fields[key]
    if not isinstance(value, bool):
        raise _wrong_type(key, "a boolean", value)
    return value


# --------------------------------------------------------------------------
# Schemas and request parsing.
# --------------------------------------------------------------------------


def load_schema(path: Path) -> dict[str, Any]:
    """Read a JSON Schema document from ``path``."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise _wrong_type(str(path), "a JSON object (a schema document)", data)
    return data


@functools.cache
def request_validator() -> Any:
    """The Draft 2020-12 validator of ``eval-request.json`` (built once)."""
    return jsonschema.Draft202012Validator(load_schema(REQUEST_SCHEMA_PATH))


@functools.cache
def response_validator() -> Any:
    """The Draft 2020-12 validator of ``eval-response.json`` (built once)."""
    return jsonschema.Draft202012Validator(load_schema(RESPONSE_SCHEMA_PATH))


def parse_request(payload: object) -> EvalRequest:
    """Validate ``payload`` against the request schema, then build the typed request.

    Raises ``RequestError`` carrying the JSON pointer of the best-matching
    violation and the validator's message, e.g.
    ``/batch/0/properties: [...] has non-unique elements``.
    """
    error = best_match(request_validator().iter_errors(payload))
    if error is not None:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise RequestError(f"{pointer}: {error.message}")
    fields = cast(Mapping[str, Any], payload)
    batch = tuple(
        BatchEntry(
            candidate_id=str(entry["candidate_id"]),
            properties=tuple(str(key) for key in entry["properties"]),
        )
        for entry in fields["batch"]
    )
    return EvalRequest(
        run_id=str(fields["run_id"]), iteration=int(fields["iteration"]), batch=batch
    )
