# Change policy

## Mutability levels

| Level | Applies to | To change it |
|---|---|---|
| **Frozen** | The problem definition, success criteria and frozen invariants in `MASTER-PLAN.md` | Owner decision, recorded as an amendment in `AMENDMENTS.md`. Never edited silently |
| **Charter-owned** | Architecture, component boundaries, major interfaces | An ADR that supersedes the relevant one, plus a charter edit |
| **Plan-owned** | Milestones, task breakdown, sequencing | GSD artifacts, checked against the charter for drift |
| **Free** | Implementation detail inside a component whose interface is unchanged | Normal change; the gate must pass |

## Interface freezing

An interface is frozen at the exit of the milestone that defines it. After that, changing it
requires an ADR. Each milestone states which interfaces it freezes. A milestone that freezes
nothing says so explicitly.

## Generated documents

Generated blocks carry a marker and are never hand-edited. A correction to generated content
is recorded in `GENERATED-DOC-CORRECTIONS.md` and fixed at the generator.

## Numbers

A number is published in one place. Everywhere else it appears, it cites that place. A number
that came from an unverified transcription is labelled as such until a second source confirms
it.
