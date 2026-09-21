# LLM4POL

**Status: pre-charter (2026-09-11).** No charter has been approved and no production code
exists. This repository holds the audited data foundation, the research that will feed the
charter, the governance documents, the quality gate and the tooling scaffold, so that
engineering can start the moment the charter is approved.

## What this project is

An LLM-agent system for polymer design, whose **architecture is designed from the polymer
problem**. LLM4MOF ("Interpretable Inverse Design of Metal-Organic Frameworks with Large
Language Model Agents", Nam, Han, Kim, KAIST) contributes two things and only two:

1. **Ideas** — a closed hypothesis-to-evidence loop, a split between a stateful hypothesis
   agent and a stateless constraint translator, controlled comparison arms that attribute a
   gain to a design axis, and a bounded factual memory.
2. **A development methodology** — exercise the agents, prompts, feedback and metrics on a
   cheap lookup oracle first, then layer expensive physics on top of an unchanged loop
   (ADR-0003).

It does **not** contribute an architecture to copy. Polymers differ from MOFs in ways that
change the design: a repeat unit does not determine a material, the oracle is noisy rather
than deterministic, composition is a continuous axis, the property tables are sample-level
with replicates, and there is no cheap simulation equivalent of a GCMC uptake for the thermal
properties the data is richest in. `docs/research/PORTING-MAP.md` studies what the parent
system does and what could be reused; it is a study, not the plan.

**The problem this system solves is not yet fixed.** That decision is open (D-08) and blocks
the charter.

## Repository layout

```
.github/workflows/ci.yml     check gate on windows-latest + ubuntu-latest, via pixi
.claude/                     per-project GSD Core install (72 commands, 35 agents, 28 hooks)
.planning/                   GSD planning artifacts; created by GSD after the charter exists
CLAUDE.md                    precedence and standing rules for agents working here
config/                      committed machine configuration, each file paired with a schema
data/                        README + MANIFEST.sha256; raw/interim/processed are git-ignored
docs/MASTER-PLAN.md          the charter; a placeholder until it is written and approved
docs/ENGINEERING-OPERATING-MODEL.md   how the project is run: planes, tool roles, build order
docs/governance/             ADRs, invariants, change policy, decisions log, review checklist
docs/audit/                  verified data-foundation audit (2026-09-11)
docs/research/               LLM4MOF study, polymer landscape, porting study, fact-checks
docs/reference/              input documents (the July 2026 concept proposal)
env/pixi.toml, pixi.lock     the locked multi-platform environment
experiments/                 run outputs; git-ignored except the README
protocol/prompts/            agent prompts as sent, versioned; a prompt is an interface
protocol/schemas/            JSON Schema for every payload that crosses a component boundary
pyproject.toml               package metadata, ruff / mypy / import-linter configuration
scripts/check.py             the single local check command
src/llm4pol/                 the package; a scaffold until the charter is approved
tests/                       pytest suite: manifest, layout and governance checks
```

## Running the check gate

```
pixi install --manifest-path env/pixi.toml
pixi run --manifest-path env/pixi.toml check
```

`check` runs, in order: `ruff check`, `ruff format --check`, `mypy --strict` on `src/`,
`import-linter` (no contracts until the architecture is frozen), and `pytest`. CI runs the
same invocation on Windows and Linux; there is no CI-only variant.

## Data policy

PoLyInfo-derived files are **never committed**. The NIMS MatNavi terms forbid redistribution
of the data and of derived data. `data/raw/`, `data/interim/` and `data/processed/` are
git-ignored; `data/MANIFEST.sha256` records the sha256, byte size and original filename of
each expected raw file, and `tests/test_manifest.py` verifies any file that is present. See
`data/README.md` for how to place the files locally, and ADR-0001 for why.

## Where to start reading

| To understand | Read |
|---|---|
| What is decided and what is still open | `docs/governance/DECISIONS-LOG.md` |
| What the data actually is, and what is wrong with it | `docs/audit/DATA-FOUNDATION-REPORT.md` |
| How LLM4MOF really works, verified against the submission and the code | `docs/research/LLM4MOF-ANATOMY.md` |
| What exists in polymer computation for each role an architecture will need | `docs/research/POLYMER-LANDSCAPE.md` |
| How the project is run | `docs/ENGINEERING-OPERATING-MODEL.md` |
| What must hold, and what enforces it | `docs/governance/INVARIANTS.md` |
