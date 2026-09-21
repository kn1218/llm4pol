# ADR-0002: MASTER-PLAN is the charter; GSD artifacts are subordinate

- **Status:** Accepted
- **Date:** 2026-09-11
- **Deciders:** owner (stated as the project operating protocol)
- **Relates to:** `CLAUDE.md`, `docs/MASTER-PLAN.md`, `docs/ENGINEERING-OPERATING-MODEL.md`

## Context

The owner's operating protocol for this project fixes an order: a PROJECT FOUNDATION PROPOSAL
is written and approved first, it becomes an authoritative charter, and only then is the
project initialised in GSD using that charter as the input. GSD's generated planning
artifacts are then checked against the charter for drift before implementation begins.

GSD Core 1.13.0 is installed per-project under `.claude/` (72 commands, 35 agents, 28 hooks),
matching the CALF20 installation. `/gsd-new-project` has deliberately not been run.

## Decision

`docs/MASTER-PLAN.md` is the highest source of truth. GSD planning artifacts are derived from
it and may not redefine the project's purpose. GSD is initialised only after the charter is
approved, with the charter as its input.

## Alternatives considered

| Option | Why not |
|---|---|
| Run `/gsd-new-project` now and let GSD interview out the requirements | GSD would become the de-facto definition of the project; the owner's protocol explicitly forbids this |
| Skip GSD and plan by hand | Loses dependency management, state persistence and verification that GSD provides |
| Global GSD install | CALF20 installs per-project; per-project keeps versions pinned with the repository |

## Consequences

- The repository is deliberately unplanned until the charter exists. `.planning/` does not
  exist yet.
- After GSD generates `PROJECT.md`, `REQUIREMENTS.md` and `ROADMAP.md`, a drift review against
  the charter is a required step, not an optional one.
- **Guard:** prose only for now. A CI check that fails when a GSD artifact contradicts the
  charter is not yet implementable and is deferred until the charter exists.
