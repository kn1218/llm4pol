"""Structural guards for the governance layer.

These promote rules that would otherwise be prose in ``docs/governance/`` into
checks that fail the gate: the charter and its subordinate documents exist, the
ADR log is well formed and contiguous, every committed configuration file is
paired with a schema, and run outputs stay out of version control.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
GOV = DOCS / "governance"
ADR_DIR = GOV / "ADR"

REQUIRED_DOCS = (
    DOCS / "MASTER-PLAN.md",
    DOCS / "ENGINEERING-OPERATING-MODEL.md",
    GOV / "ADR" / "0000-template.md",
    GOV / "AMENDMENTS.md",
    GOV / "CHANGE-POLICY.md",
    GOV / "DECISIONS-LOG.md",
    GOV / "GENERATED-DOC-CORRECTIONS.md",
    GOV / "INVARIANTS.md",
    GOV / "PROGRESS-TRACKING.md",
    GOV / "REVIEW-CHECKLIST.md",
)

REQUIRED_DIRS = (
    DOCS / "audit",
    DOCS / "reference",
    DOCS / "research",
    ROOT / "config",
    ROOT / "protocol" / "prompts",
    ROOT / "protocol" / "schemas",
    ROOT / "experiments",
)

ADR_NAME = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
VALID_STATUS = ("Accepted", "Proposed", "Rejected", "Superseded")


def test_required_documents_exist() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED_DOCS if not p.is_file()]
    assert not missing, f"missing governance documents: {missing}"


def test_required_directories_exist() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED_DIRS if not p.is_dir()]
    assert not missing, f"missing directories: {missing}"


def test_adr_filenames_are_well_formed() -> None:
    bad = [p.name for p in ADR_DIR.glob("*.md") if not ADR_NAME.match(p.name)]
    assert not bad, f"ADR filenames must be NNNN-kebab-case.md: {bad}"


def test_adr_numbers_are_contiguous_and_unique() -> None:
    numbers = sorted(int(m.group(1)) for p in ADR_DIR.glob("*.md") if (m := ADR_NAME.match(p.name)))
    assert numbers, "no ADRs found"
    assert numbers[0] == 0, "ADR numbering starts at 0000 (the template)"
    assert numbers == list(range(len(numbers))), f"ADR numbers must be contiguous: {numbers}"


def test_every_adr_declares_status_and_date() -> None:
    offenders: list[str] = []
    for path in sorted(ADR_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        has_status = any(s in text for s in VALID_STATUS)
        has_date = re.search(r"\*\*Date:\*\*", text) is not None
        if not (has_status and has_date):
            offenders.append(path.name)
    assert not offenders, f"every ADR needs a Status and a Date line: {offenders}"


def test_every_config_file_has_a_schema() -> None:
    """config/README.md: a configuration file without a sibling schema is a defect."""
    config = ROOT / "config"
    unpaired = [
        p.name
        for p in config.glob("*.json")
        if not p.name.endswith(".schema.json")
        and not p.with_suffix("").with_suffix(".schema.json").is_file()
    ]
    assert not unpaired, f"config files with no *.schema.json sibling: {unpaired}"


def test_experiments_directory_is_ignored_except_readme() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "experiments/*" in gitignore, "run outputs must be git-ignored (ADR-0001)"
    assert "!experiments/README.md" in gitignore, "experiments/README.md must stay tracked"
    assert (ROOT / "experiments" / "README.md").is_file()


def test_data_directories_are_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for rule in ("data/raw/", "data/interim/", "data/processed/"):
        assert rule in gitignore, f"{rule} must be git-ignored (ADR-0001, invariant R-1)"


CHARTER_STATUS = re.compile(r"^- \*\*Status:\*\*\s*(\S+)", re.MULTILINE)


def _charter_status() -> str:
    charter = (DOCS / "MASTER-PLAN.md").read_text(encoding="utf-8")
    match = CHARTER_STATUS.search(charter)
    assert match, "docs/MASTER-PLAN.md must carry a '- **Status:** <value>' line"
    return match.group(1)


def _production_modules() -> list[str]:
    package = ROOT / "src" / "llm4pol"
    return sorted(
        str(p.relative_to(package))
        for p in package.rglob("*.py")
        if p.name != "__init__.py" or p.parent != package
    )


def test_charter_status_gates_production_code() -> None:
    """Invariant R-5 (ADR-0005): production code exists only under an approved charter.

    Anything in ``src/llm4pol`` beyond the top-level ``__init__.py`` counts as
    production code. It may exist only while the charter declares
    ``Status: Approved``; a charter in any other state must sit over a scaffold.
    """
    status = _charter_status()
    modules = _production_modules()
    if status != "Approved":
        assert not modules, (
            f"charter status is {status!r}, so src/llm4pol must be a scaffold; found {modules}"
        )
