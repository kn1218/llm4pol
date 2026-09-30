"""Structural guards for the governance layer.

These promote rules that would otherwise be prose in ``docs/governance/`` into
checks that fail the gate: the charter and its subordinate documents exist, the
ADR log is well formed and contiguous, every committed configuration file is
paired with a schema, the four run summaries of ADR-0007 are trackable while the
ledger stays out of version control, and a tracked run is a PolyOmics run.
"""

from __future__ import annotations

import json
import re
import subprocess
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


RUN_DIR = "experiments/20260101T000000Z-00000000"
RUN_ID_DIR = re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{8}")
TRACKED_RUN_FILES = ("meta.json", "usage.json", "results.csv", "run_summary.json")


def _is_ignored(relative_path: str) -> bool:
    """Ask git whether a path is ignored: exit 0 is ignored, exit 1 is trackable (RESEARCH F-66).

    ``--no-index`` judges the pattern alone, so a path that is not on disk (or
    already tracked) is answered the same way. Any other exit code is an error.
    """
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", relative_path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in (0, 1), (relative_path, result.returncode, result.stderr)
    return result.returncode == 0


def test_run_summaries_are_trackable_and_the_ledger_is_ignored() -> None:
    """ADR-0007: four names inside a run directory are tracked, everything else is not.

    The test asks git instead of reading ``.gitignore`` as text: a re-include
    placed after ``experiments/*`` does nothing because the run directory itself
    is excluded (RESEARCH F-64), and a text check stays green over it (F-67).
    """
    assert (ROOT / "experiments" / "README.md").is_file()
    assert not _is_ignored("experiments/README.md")
    for name in TRACKED_RUN_FILES:
        assert not _is_ignored(f"{RUN_DIR}/{name}"), f"{name} must be trackable (ADR-0007)"
    for name in ("ledger.jsonl", "cache.jsonl", "nested/meta.json"):
        assert _is_ignored(f"{RUN_DIR}/{name}"), f"{name} must stay untracked (ADR-0007)"
    assert _is_ignored("experiments/stray.txt")


def _tracked_experiments_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "experiments"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_tracked_run_summaries_are_polyomics_runs() -> None:
    """ADR-0007 second paragraph, ADR-0001: a run on PoLyInfo-derived data is never tracked.

    Every tracked path under ``experiments/`` is the README or one of the four
    summary names directly inside a run-id directory, and every tracked
    ``meta.json`` names a ``polyomics:`` snapshot. Holds with zero tracked runs.
    """
    offenders: list[str] = []
    for tracked in _tracked_experiments_files():
        parts = tracked.split("/")
        if tracked == "experiments/README.md":
            continue
        if len(parts) == 3 and RUN_ID_DIR.fullmatch(parts[1]) and parts[2] in TRACKED_RUN_FILES:
            if parts[2] == "meta.json":
                meta = json.loads((ROOT / tracked).read_text(encoding="utf-8"))
                snapshot = meta.get("snapshot")
                if not (isinstance(snapshot, str) and snapshot.startswith("polyomics:")):
                    offenders.append(f"{tracked}: snapshot {snapshot!r} is not a polyomics: run")
            continue
        offenders.append(f"{tracked}: not a tracked file of ADR-0007")
    assert not offenders, offenders


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
