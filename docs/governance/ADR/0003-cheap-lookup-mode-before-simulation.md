# ADR-0003: Develop on a cheap lookup oracle first, layer simulation on top

- **Status:** Accepted
- **Date:** 2026-09-11
- **Deciders:** owner (stated explicitly)
- **Relates to:** `docs/ENGINEERING-OPERATING-MODEL.md`, ADR-0004

## Context

The owner's instruction: agents, prompts and the surrounding machinery are exercised first in
a cheap table-lookup mode, and physics simulation is layered on afterwards. This mirrors how
LLM4MOF was developed, where a database mode using precomputed property tables ran the whole
loop with no simulation at all.

Two measured facts make this decisive for polymers rather than merely convenient:

- A lookup-mode campaign in the LLM4MOF codebase takes roughly 353 s and about one US dollar,
  so prompts and feedback can be revised dozens of times per day.
- The polymer simulation tier is far more expensive than the MOF one. An all-atom MD glass
  transition costs on the order of 4,000-20,000 CPU-hours per candidate and carries a
  systematic +40 to +120 K offset versus experiment, against minutes for a GCMC uptake.
  Density is the cheapest quantitatively validated MD property at roughly 300-2,000
  CPU-hours. Source: `docs/research/POLYMER-LANDSCAPE.md` section 1.6.

## Decision

The oracle is an interface. Development and all prompt, feedback and metric work happen
against a cheap implementation of that interface. Expensive implementations are added behind
the same interface later, without changing the loop.

## Alternatives considered

| Option | Why not |
|---|---|
| Build against the simulation oracle from the start | At 4,000-20,000 CPU-hours per candidate, a single prompt revision would cost weeks |
| Skip simulation entirely | Removes the only route to a claim about materials that are not already in a table |
| Use an ML surrogate as the development oracle | A surrogate's errors would be learned as if they were physics; the cheap tier must be measured values or a declared null, not a model |

## Consequences

- No component may assume the oracle is cheap, deterministic, or noise-free. The cheap tier
  has measurement replicate noise; the expensive tier has replicate and systematic error.
- Budget is reported in two currencies, evaluation count and compute hours, never merged.
- **Guard:** an import-linter contract forbidding the loop packages from importing any
  simulation package, to be added when the architecture is frozen. Prose only for now.
