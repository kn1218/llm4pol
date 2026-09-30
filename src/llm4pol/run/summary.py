"""``run_summary.json``: the mapping derived from a ledger and its rows (ADR-0008 item 6; D-39).

``summary_of`` is a pure function of a parsed ``Ledger``, the rows ``reduce.reduce`` gave for it and
the two hashes the caller computed from bytes: it holds no clock and no file, and every field is
in the ledger or derived from its bytes, so ``replay`` reproduces the file exactly. It sits in a
module of its own because ``reduce.py`` is at the line limit of the package; ``reduce`` imports it
and applies ``protocol/schemas/run-summary.json`` before a file is opened. The module imports
nothing of ``reduce`` at run time (the row type is a type-check import only), and no dataframe,
parquet or array library.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from llm4pol.run.ledger import Ledger

if TYPE_CHECKING:
    from llm4pol.run.reduce import Row

SUMMARY_SCHEMA_VERSION = 1
_OPEN = "open"


def _points(rows: Sequence[Row], value: Callable[[Row], Any]) -> list[dict[str, Any]]:
    return [{"iteration": row.iteration, "value": value(row)} for row in rows]


def summary_of(
    ledger: Ledger, rows: Sequence[Row], *, ledger_sha256: str, results_sha256: str
) -> dict[str, Any]:
    """The eight keys of ``run_summary.json``.

    ``status`` is ``open`` until a ``run_closed`` event, then its reason; ``completed_iterations``
    counts the ``iteration_closed`` events. There is one trend entry per beam, in the order the
    beams first appear in the ledger, and population, in the order of ``run_opened``; each point
    carries its iteration number, the percentile is ``pct_of_population`` (null when the cell has
    no value) and the count is ``n_selected``.
    """
    events = ledger.events
    opened = next(event for event in events if event.event == "run_opened")
    closing = [event for event in events if event.event == "run_closed"]
    beams = list(dict.fromkeys(row.beam for row in rows))
    populations = [str(population["name"]) for population in opened.payload["populations"]]
    trends = []
    for beam in beams:
        for population in populations:
            own = [r for r in rows if (r.beam, r.population) == (beam, population)]
            trends.append(
                {
                    "beam": beam,
                    "population": population,
                    "percentile_trend": _points(own, lambda r: r.pct_of_population),
                    "count_trend": _points(own, lambda r: r.n_selected),
                }
            )
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "run_id": ledger.header.run_id,
        "status": str(closing[0].payload["reason"]) if closing else _OPEN,
        "completed_iterations": sum(1 for event in events if event.event == "iteration_closed"),
        "primary_population": str(opened.payload["primary"]),
        "trends": trends,
        "ledger_sha256": ledger_sha256,
        "results_sha256": results_sha256,
    }
