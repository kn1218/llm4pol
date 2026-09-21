"""The evaluator (charter section 7 contract; charter section 6 package boundary).

Every property lookup goes through one contract -- ``EvalRequest`` in,
``EvalResponse`` out -- served by one ``Backend``. This package imports
``llm4pol.data`` (registry, snapshot paths) and never ``llm4pol.loop``,
``llm4pol.llm`` or ``llm4pol.run`` (A-1; enforced by import-linter in plan
03-03). The package root exports the contract only: the caller imports a
backend as ``llm4pol.evaluate.backends.<name>`` itself, never through this
module, so a layers contract on the loop can never be dragged through the
package root (RESEARCH F-49).
"""

from __future__ import annotations

from llm4pol.evaluate.contract import (
    MISSING_REASONS,
    REQUEST_SCHEMA_PATH,
    RESPONSE_SCHEMA_PATH,
    SCHEMA_DIR,
    STATUSES,
    Backend,
    BatchEntry,
    Cost,
    EvalRequest,
    EvalResponse,
    EvalResult,
    Lookup,
    MissingReason,
    RequestError,
    Status,
    load_schema,
    parse_request,
    parse_status,
    request_validator,
    response_validator,
)
from llm4pol.evaluate.evaluator import Evaluator
from llm4pol.evaluate.registry import PropertyTable

__all__ = [
    "MISSING_REASONS",
    "REQUEST_SCHEMA_PATH",
    "RESPONSE_SCHEMA_PATH",
    "SCHEMA_DIR",
    "STATUSES",
    "Backend",
    "BatchEntry",
    "Cost",
    "EvalRequest",
    "EvalResponse",
    "EvalResult",
    "Evaluator",
    "Lookup",
    "MissingReason",
    "PropertyTable",
    "RequestError",
    "Status",
    "load_schema",
    "parse_request",
    "parse_status",
    "request_validator",
    "response_validator",
]
