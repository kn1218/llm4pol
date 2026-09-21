"""``python -m llm4pol.evaluate --request <json> [--root <repo>] [--cache <jsonl>] [--evals-limit <n>]`` (CONTEXT D-07).

Reads one request, validates it against ``protocol/schemas/eval-request.json``,
answers it from the candidate parquet under ``<root>/data/processed/`` and
prints the response JSON on stdout. ``--cache`` names an append-only JSONL
file replayed before the request and appended after it (D-04, R-4);
``--evals-limit`` refuses a request whose distinct uncached ``ok`` candidates
would exceed it (a single-request meter: the CLI starts from ``BudgetMeter()``
every run, so the limit is per invocation).

Exit codes:

======  ==================================================================
0       success (a missing or mismatched parquet is *not* an error exit:
        every backend-reaching result is ``error`` and the response is
        printed -- the ``error`` status is the retryable signal, D-02)
2       an unreadable or schema-invalid request, a bad registry, or an
        unreadable / malformed ``--cache`` file (``ERROR:`` on stderr)
3       ``BudgetExceeded`` (``BUDGET:`` on stderr; nothing cached, no file
        written)
======  ==================================================================

Paths are opened as given by the local user running the developer CLI
(threat T-03-13, accepted).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from llm4pol.data import snapshot
from llm4pol.data.registry import RegistryError
from llm4pol.evaluate.backends.table import TableBackend
from llm4pol.evaluate.budget import BudgetExceeded
from llm4pol.evaluate.cache import CacheError, JsonlCache
from llm4pol.evaluate.contract import RequestError, parse_request
from llm4pol.evaluate.evaluator import Evaluator
from llm4pol.evaluate.registry import PropertyTable

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_BUDGET = 3


def _non_negative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError(f"must be a non-negative integer, got {text!r}")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m llm4pol.evaluate", description=__doc__)
    parser.add_argument(
        "--request",
        type=Path,
        required=True,
        help="path of the request JSON (protocol/schemas/eval-request.json)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=snapshot.DEFAULT_ROOT,
        help="repository root holding data/processed/ (default: this checkout)",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=None,
        help="append-only JSONL result cache, replayed before and appended after the request",
    )
    parser.add_argument(
        "--evals-limit",
        type=_non_negative_int,
        default=None,
        help="refuse the request (exit 3) when its distinct ok candidates would exceed this",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    request_path: Path = args.request
    root: Path = args.root
    cache_path: Path | None = args.cache
    evals_limit: int | None = args.evals_limit
    try:
        request = parse_request(json.loads(request_path.read_text(encoding="utf-8")))
        properties = PropertyTable.load()
        cache = JsonlCache(cache_path)
    except (OSError, json.JSONDecodeError, RequestError, RegistryError, CacheError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INPUT
    backend = TableBackend(
        snapshot.candidates_parquet(snapshot.processed_dir(root)), properties=properties
    )
    evaluator = Evaluator(backend, properties, cache=cache, evals_limit=evals_limit)
    try:
        response = evaluator.evaluate(request)
    except BudgetExceeded as exc:
        print(f"BUDGET: {exc}", file=sys.stderr)
        return EXIT_BUDGET
    except (OSError, CacheError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INPUT
    print(json.dumps(response.to_json(), indent=2, sort_keys=True, allow_nan=False))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
