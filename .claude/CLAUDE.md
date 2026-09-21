<!-- GSD:project-start source:PROJECT.md -->

## Project

**LLM4POL**

A closed hypothesis-to-evidence loop for polymer design: an LLM proposes chemistry hypotheses,
a deterministic evaluator scores them against a hidden simulated-property table (PolyOmics
`general_polymers`), and controlled comparison arms attribute any gain to a design axis. The
first target is a thermally conductive electrical insulator designed at the repeat-unit level
(charter §1). Built for the owner as a research instrument whose results become a paper.

**Core Value:** The loop must attribute a measured gain to a design axis under a matched evaluation budget —
if that attribution is not reproducible, nothing else the system produces is a result
(charter §1, success layers L1–L5).

### Constraints

- **Precedence**: charter > REQUIREMENTS.md > CLAUDE.md > generated blocks — conflicts are flagged, never silently resolved (ADR-0002)
- **Data**: no data file of either layer is committed; PoLyInfo by licence, PolyOmics by size (ADR-0001, charter §10)
- **Gate**: `pixi run --manifest-path env/pixi.toml check` passes before any commit (R-4)
- **Interfaces**: every cross-component payload has a JSON Schema in `protocol/schemas/`; prompts that produced a result are never edited in place (A-5)
- **Blindness**: nothing sent to a hosted LLM carries row ids, table size, percentiles, thresholds or global statistics (A-4, D-19)
- **Budget**: evaluation count and compute hours are separate currencies (A-3)
- **Review**: authoring and review are separate passes (`REVIEW-CHECKLIST.md`)
- **Completion**: a milestone is done when its charter §13 exit criterion is reproduced, not when tasks close

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
