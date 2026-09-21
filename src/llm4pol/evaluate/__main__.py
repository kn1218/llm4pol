"""``python -m llm4pol.evaluate --request <json> [--root <repo>]`` (CONTEXT D-07).

Reads one request, validates it against ``protocol/schemas/eval-request.json``,
answers it from the candidate parquet under ``<root>/data/processed/`` and
prints the response JSON on stdout. Exit codes: 0 success, 2 a request that
fails the schema, an unreadable input or a bad registry. A missing or
mismatched parquet is not exit 2: every result is ``error`` and the exit code
is 0 (D-02; the ``error`` status is the retryable signal). Plan 03-02 adds
``--cache`` / ``--evals-limit`` and exit 3.
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
from llm4pol.evaluate.contract import RequestError, parse_request
from llm4pol.evaluate.evaluator import Evaluator
from llm4pol.evaluate.registry import PropertyTable


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    request_path: Path = args.request
    root: Path = args.root
    try:
        request = parse_request(json.loads(request_path.read_text(encoding="utf-8")))
        properties = PropertyTable.load()
    except (OSError, json.JSONDecodeError, RequestError, RegistryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    backend = TableBackend(
        snapshot.candidates_parquet(snapshot.processed_dir(root)), properties=properties
    )
    response = Evaluator(backend, properties).evaluate(request)
    print(json.dumps(response.to_json(), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
