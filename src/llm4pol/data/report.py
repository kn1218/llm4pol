"""The validation report model, its markdown rendering and the exit code.

CONTEXT D-07 (the report is the authority for numbers), D-10 (every count
names its population -- ``CountTable`` refuses a header without one), R-5
(two finding classes: ``reproduce`` must equal the expected value exactly;
``documented`` is a stated difference within a tolerance). The rendering
carries no timestamp and no git sha so the file is byte-reproducible, and it
emits no ``*`` so the aggregates-only grep for SMILES-like tokens (charter
section 10, plan 02-05) has nothing to hit: table titles are level-3 headings.
"""

from __future__ import annotations

from dataclasses import dataclass

REPRODUCE = "reproduce"
DOCUMENTED = "documented"
POPULATION = "population"

Value = int | float | str

# Floats print with this many decimals unless the expectation says otherwise.
DEFAULT_DIGITS = 4
# A non-zero float below this magnitude prints in scientific notation with
# two significant digits (identity residuals, F-14).
SCIENTIFIC_BELOW = 1e-3


@dataclass(frozen=True)
class Expected:
    """An expected value with its finding class (``reproduce`` | ``documented``)."""

    cls: str
    value: Value
    tolerance: float | None = None
    note: str = ""
    digits: int | None = None


@dataclass(frozen=True)
class Finding:
    """One evaluated expectation."""

    finding_id: str
    cls: str
    population: str
    expected: Value
    observed: Value | None
    tolerance: float | None
    note: str
    status: str
    digits: int | None = None


@dataclass(frozen=True)
class CountTable:
    """A markdown table whose header must name a ``population`` column (D-10)."""

    title: str
    header: tuple[str, ...]
    rows: list[tuple[str, ...]]

    def __post_init__(self) -> None:
        if POPULATION not in self.header:
            raise ValueError(
                f"CountTable {self.title!r}: header {self.header} has no "
                f"{POPULATION!r} column (D-10: every count names its population)"
            )
        for row in self.rows:
            if len(row) != len(self.header):
                raise ValueError(f"CountTable {self.title!r}: row {row} does not fit the header")


@dataclass(frozen=True)
class Section:
    title: str
    intro: str
    tables: list[CountTable]


@dataclass(frozen=True)
class Report:
    snapshot: str
    revision: str
    sections: list[Section]
    findings: list[Finding]


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def evaluate_finding(
    finding_id: str, expected: Expected, observed: Value | None, population: str
) -> Finding:
    """Compare ``observed`` with ``expected`` under its finding class."""
    if observed is None:
        status = "MISSING"
    elif expected.cls == REPRODUCE:
        status = "reproduced" if observed == expected.value else "FAILED"
    elif expected.cls == DOCUMENTED:
        if _is_number(observed) and _is_number(expected.value) and expected.tolerance is not None:
            within = abs(float(observed) - float(expected.value)) <= expected.tolerance
            status = DOCUMENTED if within else "FAILED"
        elif isinstance(observed, str) and observed:
            status = DOCUMENTED
        else:
            status = "FAILED"
    else:
        raise ValueError(f"finding {finding_id!r}: unknown class {expected.cls!r}")
    return Finding(
        finding_id=finding_id,
        cls=expected.cls,
        population=population,
        expected=expected.value,
        observed=observed,
        tolerance=expected.tolerance,
        note=expected.note,
        status=status,
        digits=expected.digits,
    )


def format_int(value: int) -> str:
    return f"{value:,}"


def format_float(value: float, digits: int = DEFAULT_DIGITS) -> str:
    if 0.0 < abs(value) < SCIENTIFIC_BELOW:
        return f"{value:.1e}"
    return f"{value:,.{digits}f}"


def format_pct(value: float, digits: int = 2) -> str:
    """``value`` is a fraction in [0, 1]; rendered as a percentage."""
    return f"{100.0 * value:.{digits}f} %"


def format_value(value: Value | None, digits: int | None = None) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return format_int(value)
    if isinstance(value, float):
        return format_float(value, DEFAULT_DIGITS if digits is None else digits)
    return value


def format_finding_values(finding: Finding) -> tuple[str, str]:
    """``(expected, observed)`` rendered with the finding's digits."""
    return (
        format_value(finding.expected, finding.digits),
        format_value(finding.observed, finding.digits),
    )


def _render_table(table: CountTable) -> list[str]:
    lines = [f"### {table.title}", ""]
    lines.append("| " + " | ".join(table.header) + " |")
    lines.append("|" + "---|" * len(table.header))
    for row in table.rows:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return lines


def render_markdown(report: Report) -> str:
    """Render the report; every table header includes ``population`` by construction."""
    lines = [
        f"# PolyOmics general_polymers validation report — {report.snapshot}",
        "",
        f"Revision `{report.revision}`. Generated by `python -m llm4pol.data validate`; "
        "this file is the authority for every PolyOmics number cited in this repository "
        "(charter section 10). Every count names the population it is drawn from (D-10). "
        f"Finding classes (R-5): `{REPRODUCE}` must equal the expected value exactly; "
        f"`{DOCUMENTED}` is a stated difference within a tolerance. "
        "Aggregates only; no row of the dataset is reproduced here.",
        "",
    ]
    for section in report.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        if section.intro:
            lines.append(section.intro)
            lines.append("")
        for table in section.tables:
            lines.extend(_render_table(table))
    lines.append("## Findings")
    lines.append("")
    lines.append("| finding | population | expected | observed | class | status |")
    lines.append("|---|---|---|---|---|---|")
    for finding in report.findings:
        expected, observed = format_finding_values(finding)
        lines.append(
            f"| {finding.finding_id} | {finding.population} | {expected} "
            f"| {observed} | {finding.cls} | {finding.status} |"
        )
    lines.append("")
    noted = [finding for finding in report.findings if finding.note]
    if noted:
        lines.append("### Finding notes")
        lines.append("")
        lines.append("| finding | population | tolerance | note |")
        lines.append("|---|---|---|---|")
        for finding in noted:
            tolerance = "—" if finding.tolerance is None else f"{finding.tolerance:g}"
            lines.append(
                f"| {finding.finding_id} | {finding.population} | {tolerance} | {finding.note} |"
            )
        lines.append("")
    return "\n".join(lines)


def exit_code(findings: list[Finding]) -> int:
    """1 if any finding is ``FAILED`` or ``MISSING``, else 0."""
    return 1 if any(f.status in ("FAILED", "MISSING") for f in findings) else 0
