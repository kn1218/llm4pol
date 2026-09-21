# Engineering Operating Model

How this project is run. This file describes process, not science; the science lives in
`MASTER-PLAN.md`.

## Two planes

| Plane | What it covers | Who runs it |
|---|---|---|
| **Build plane** | Repository, environment, quality gate, CI, planning artifacts, code | ORCA ADE, GSD Core, Claude Code, git worktrees |
| **Science plane** | Problem definition, oracles, experiments, metrics, claims | The owner, with agents as instruments |

The build plane never decides a science question. The science plane never edits a build
artifact without going through the gate.

## Tool roles

| Tool | Role | Not its role |
|---|---|---|
| **GSD Core** (per-project, `.claude/`) | Methodology, planning, dependency management, state persistence, verification | Defining the project's purpose. GSD artifacts are subordinate to `MASTER-PLAN.md` |
| **ORCA ADE** | Coding sessions, git worktrees, parallel execution | Deciding what is worth parallelising |
| **Claude Code** | Primary engineering runtime | Approving its own work; review is a separate pass |

## Build order principle

Stable foundations first, then explicit interfaces, then independently testable components,
then integration, then product behaviour.

**Runtime data flow and build order are different things.** The component that runs first at
runtime is not necessarily the component to build first. Schema, identity, configuration,
persistence, protocol and core interfaces come first because other components depend on them.

## Cheap-first evaluation ladder

A decision of this project, stated by the owner: the system is developed and validated on a
**cheap lookup mode first**, and expensive physics is layered on only after the agents,
prompts, feedback and metrics have been exercised there. See `governance/ADR/0003`.

Consequences that are already binding:

- Every component that touches the oracle goes behind one interface, so the cheap and
  expensive oracles are interchangeable without a loop change.
- No component may assume the oracle is deterministic or noise-free.
- Cost and wall-clock are reported in two currencies, evaluation count and compute hours,
  never merged into one number.

## Deterministic guards over prose

A rule that matters is moved out of documentation and into a test, a validator, a schema or a
CI check as soon as it is stable. Documentation states the reason; the guard enforces the
rule. `governance/INVARIANTS.md` tracks which invariants are enforced and which are still
prose.

## One source of truth

A fact is written down once. If a number appears in two files, one of them cites the other.
Generated documents carry a marker and are never hand-edited.

## Review

Authoring and review are separate passes. Nothing is self-approved in the context that wrote
it. See `governance/REVIEW-CHECKLIST.md`.
