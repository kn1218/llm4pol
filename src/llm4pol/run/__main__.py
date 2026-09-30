"""``python -m llm4pol.run {run|resume|replay|usage} ...`` (CONTEXT D-07; RUN-01..RUN-05).

``run --problem <spec> --selector plan --plan <plan> [--root <repo>] [--experiments <dir>]``
validates the problem and the plan before it creates anything, opens ``experiments/<run id>/``
with ``meta.json`` and the ledger header, drives the run to its close and prints ``run_id:``,
``evals:``, ``cpu_hours:`` and ``results_sha256:``. ``resume --run <id> --selector plan --plan
<plan> [--root <repo>] [--experiments <dir>]`` continues a recorded run from its ledger alone; it
takes the problem from the ledger header and has no option that accepts other code, snapshot or
registry version. ``replay --run <id> [--experiments <dir>] [--out <dir>]`` regenerates
``results.csv``, ``usage.json`` and ``run_summary.json`` from ``ledger.jsonl`` alone, and prints
``ledger_sha256:``, ``results_sha256:`` and last ``result_sha256:``, the sha256 of the three files
laid end to end. On a closed run it writes a file that is absent and refuses, with exit 4 and
nothing written, one that differs; on an open run it writes nothing into the run directory; with
``--out`` it writes the three files there. It has no way to name a data root, compares no code
version, and loads neither the population code nor a dataframe library. ``usage --run <id> [--experiments <dir>]`` prints
``usage.json`` as the ledger sums it (``evals`` and ``cpu_hours`` apart; ADR-0008 item 7): it
compares no code version, loads no table, and writes nothing; on an open run it prints the sums of
what is recorded.

Exit codes:

======  ==================================================================
0       success
2       the record cannot be read as a ledger (a torn final line, a line that does not parse or
        validate) or another input defect: an invalid problem or plan, a malformed or unknown run
        id, an existing run directory, an absent or mismatched table, a ``meta.json`` mapping the
        schema refuses (stdout ``ERROR: input refused``)
3       the evaluation budget refused a request and this call recorded the end of the run
        (stdout ``BUDGET: evaluation budget exhausted``)
4       a readable ledger that cannot be trusted or continued: a ``seq`` gap, a repeated event
        key, the lifecycle order, a header that names other code, snapshot, registry version or
        selector than the running ones, a recorded selection the selector does not give, or a
        ``results.csv`` or ``usage.json`` that is not what the ledger yields (stdout ``ERROR:
        ledger integrity check failed``)
======  ==================================================================

Stdout carries one generic line for every refusal; the detail goes to stderr as one line
starting ``detail:`` and never carries an environment value (RESEARCH Pattern 6, T-04-09).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from llm4pol.data import snapshot
from llm4pol.data.registry import RegistryError
from llm4pol.run import ids, reduce
from llm4pol.run.config import (
    CodeIdentityError,
    MetaError,
    ProblemSpecError,
    RunExists,
    code_identity,
    load_problem_spec,
)
from llm4pol.run.jsonio import StrictJsonError
from llm4pol.run.ledger import LEDGER_NAME, LedgerError, LedgerIntegrityError, read
from llm4pol.run.selector import PlanError, PlanSelector

if TYPE_CHECKING:  # importing `resume` loads the dataframe stack, which `replay` never does
    from llm4pol.run.resume import Outcome

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_BUDGET = 3
EXIT_INTEGRITY = 4

INPUT_LINE = "ERROR: input refused"
BUDGET_LINE = "BUDGET: evaluation budget exhausted"
INTEGRITY_LINE = "ERROR: ledger integrity check failed"

DEFAULT_EXPERIMENTS = snapshot.DEFAULT_ROOT / "experiments"


class _Refused(Exception):
    """An input defect found by a handler itself."""


# The errors of `population` and `resume` are translated inside `_run`: importing those modules
# here would load the dataframe stack for `replay`.
_INPUT_ERRORS: tuple[type[Exception], ...] = (
    ProblemSpecError,
    PlanError,
    RegistryError,
    ids.RunIdError,
    RunExists,
    MetaError,
    CodeIdentityError,
    LedgerError,
    StrictJsonError,
    reduce.ReduceError,
    OSError,
    _Refused,
)


def _detail(exc: BaseException) -> str:
    return "detail: " + " ".join(str(exc).split())


def _fail(code: int, line: str, exc: BaseException) -> int:
    print(line)
    print(_detail(exc), file=sys.stderr)
    return code


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m llm4pol.run",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    verbs = parser.add_subparsers(dest="verb", required=True)

    run = verbs.add_parser("run", help="open a run and drive it to its close")
    run.add_argument("--problem", type=Path, required=True, help="the problem spec JSON")
    run.add_argument("--selector", choices=("plan",), required=True, help="the selector")
    run.add_argument("--plan", type=Path, default=None, help="the selection plan (selector plan)")
    run.add_argument("--root", type=Path, default=snapshot.DEFAULT_ROOT, help="repository root")
    run.add_argument(
        "--experiments", type=Path, default=DEFAULT_EXPERIMENTS, help="the runs directory"
    )
    run.set_defaults(handler=_run)

    again = verbs.add_parser("resume", help="continue a recorded run from its ledger alone")
    again.add_argument("--run", required=True, help="the run id")
    again.add_argument("--selector", choices=("plan",), required=True, help="the selector")
    again.add_argument("--plan", type=Path, default=None, help="the selection plan (selector plan)")
    again.add_argument("--root", type=Path, default=snapshot.DEFAULT_ROOT, help="repository root")
    again.add_argument(
        "--experiments", type=Path, default=DEFAULT_EXPERIMENTS, help="the runs directory"
    )
    again.set_defaults(handler=_resume)

    replay = verbs.add_parser("replay", help="regenerate the three reduced files from the ledger")
    replay.add_argument("--run", required=True, help="the run id")
    replay.add_argument(
        "--experiments", type=Path, default=DEFAULT_EXPERIMENTS, help="the runs directory"
    )
    replay.add_argument(
        "--out", type=Path, default=None, help="write the three files under this dir"
    )
    replay.set_defaults(handler=_replay)

    usage = verbs.add_parser("usage", help="print the two budget currencies summed from the ledger")
    usage.add_argument("--run", required=True, help="the run id")
    usage.add_argument(
        "--experiments", type=Path, default=DEFAULT_EXPERIMENTS, help="the runs directory"
    )
    usage.set_defaults(handler=_usage)
    return parser


def _run(args: argparse.Namespace) -> int:
    from llm4pol.run import population, resume  # deferred: loads the dataframe stack

    problem = load_problem_spec(args.problem)
    if args.plan is None:
        raise _Refused("--plan is required with --selector plan")
    selector = PlanSelector.from_file(args.plan, problem)
    code = code_identity()
    try:
        run_dir = resume.open_run(
            args.experiments,
            problem,
            selector,
            root=args.root,
            now=ids.utc_now(),
            token=ids.random_token(),
            code=code,
        )
        print(f"run_id: {run_dir.name}", flush=True)
        outcome = resume.drive(run_dir, root=args.root, selector=selector, clock=ids.utc_now)
    except (population.PopulationError, resume.DriveError) as exc:
        raise _Refused(str(exc)) from exc
    return _report(outcome)


def _resume(args: argparse.Namespace) -> int:
    from llm4pol.run import population, resume  # deferred: loads the dataframe stack

    run_dir: Path = args.experiments / ids.require_run_id(args.run)
    recorded = read(run_dir / LEDGER_NAME)  # the problem is the header's (CONTEXT D-02)
    if args.plan is None:
        raise _Refused("--plan is required with --selector plan")
    selector = PlanSelector.from_file(args.plan, recorded.problem)
    try:
        outcome = resume.resume(
            run_dir,
            root=args.root,
            selector=selector,
            code=code_identity(),
            clock=ids.utc_now,
        )
    except (population.PopulationError, resume.DriveError) as exc:
        raise _Refused(str(exc)) from exc
    return _report(outcome)


def _report(outcome: Outcome) -> int:
    """Print the cost and the results hash; exit 3 when this call recorded a budget refusal."""
    print(f"evals: {outcome.evals}")
    print(f"cpu_hours: {outcome.cpu_hours!r}")
    print(f"results_sha256: {outcome.results_sha256}")
    if outcome.status == "budget_exhausted" and outcome.appended:
        closing = outcome.closing
        print(BUDGET_LINE)
        print(
            f"detail: requested {closing['requested']} evals, {closing['remaining']} remaining "
            f"of limit {closing['limit']}",
            file=sys.stderr,
        )
        return EXIT_BUDGET
    return EXIT_OK


def _replay(args: argparse.Namespace) -> int:
    run_dir: Path = args.experiments / ids.require_run_id(args.run)
    if args.out is not None and args.out.resolve() == run_dir.resolve():
        raise _Refused("--out must not be the run directory")
    outputs = reduce.render_outputs((run_dir / LEDGER_NAME).read_bytes())
    if outputs.closed:  # raises LedgerIntegrityError, before anything is written, on a difference
        reduce.write_outputs(run_dir, outputs)
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        for name, data in outputs.files().items():
            (args.out / name).write_bytes(data)
    print(f"ledger_sha256: {outputs.ledger_sha256}")
    print(f"results_sha256: {outputs.results_sha256}")
    print(f"result_sha256: {reduce.result_sha256(outputs.results, outputs.usage, outputs.summary)}")
    return EXIT_OK


def _usage(args: argparse.Namespace) -> int:
    run_dir: Path = args.experiments / ids.require_run_id(args.run)
    data = reduce.render_usage(read(run_dir / LEDGER_NAME))
    recorded = run_dir / reduce.USAGE_NAME
    if recorded.exists() and recorded.read_bytes() != data:
        return _fail(
            EXIT_INTEGRITY,
            INTEGRITY_LINE,
            _Refused(f"{reduce.USAGE_NAME} differs from what the ledger sums to"),
        )
    print(data.decode("utf-8"), end="")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except LedgerIntegrityError as exc:
        return _fail(EXIT_INTEGRITY, INTEGRITY_LINE, exc)
    except _INPUT_ERRORS as exc:
        return _fail(EXIT_INPUT, INPUT_LINE, exc)


if __name__ == "__main__":
    sys.exit(main())
