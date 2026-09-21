"""``python -m llm4pol.data fetch | load | validate`` (CONTEXT D-10).

Exit codes: 0 success, 1 a validator finding or a manifest mismatch, 2 an I/O
error (missing input, unreadable manifest, download failure). No child
process is started anywhere in this package.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from llm4pol.data import fetch, load, validate
from llm4pol.data.snapshot import DEFAULT_ROOT

_COMMANDS = (
    ("fetch", "verify the pinned files against data/MANIFEST-open.sha256; download if absent"),
    ("load", "write the row-level and candidate parquets into data/processed/"),
    ("validate", "reproduce the snapshot's numbers and write the validation report"),
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m llm4pol.data", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in _COMMANDS:
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument(
            "--root",
            type=Path,
            default=DEFAULT_ROOT,
            help="repository root (default: this checkout)",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    # Tool output can contain characters outside the console's default
    # encoding (the ellipsis in the verified line, the em dash in the report
    # title); reconfigure as scripts/check.py does.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    root: Path = args.root
    try:
        if args.command == "fetch":
            return fetch.fetch(root)
        if args.command == "load":
            load.load(root)
            return 0
        return validate.run(root)
    except (load.LoaderError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
