# Phase 5: Deterministic End-to-End — Context

**Gathered:** 2026-09-29 (draft written while Phase 4 research ran; finalised after Phase 4 lands)
**Status:** Draft — decisions below were taken by the agent under the owner's delegation of
2026-09-29 and are recorded as development defaults; none fixes a gated parameter.

**Sources, in precedence order**

1. `docs/MASTER-PLAN.md` §1 (L1), §5, §7 (hypothesis → query, four beams), §13 M4 — the authority.
2. **LLM4MOF** (`LLM2POR_Core_20260319/core/{feedback,screening,hierarchy,metrics,pipeline}.py`), read
   directly on 2026-09-29.
3. **LLM4MO** (`Desktop/LLM4MO/src/llm4mo/{vocabulary,random_policy}.py`), read directly.
4. ADR-0004 §5 (intermediate variables), ADR-0006 (candidate identity), D-26 (population 42,733).

<domain>
## Phase Boundary

Charter M4: `llm4pol run --selector deterministic` completes a seed-reproducible 10-iteration,
four-beam campaign on the hidden table with no LLM involved. Freezes the hypothesis, query and tag
vocabulary schemas. The curve it produces is a liveness check, not a research result.
</domain>

<reference_facts>
## What the references do (read, not recalled)

### LLM4MOF Core — `core/feedback.py`
- **Two layers per beam, an information firewall.** *Audit layer*: statistics over the full matched
  set, kept for the experiment log. *Feedback layer*: `sample_n` randomly sampled candidates per
  beam; pattern summaries and the diagnosis text are derived from the sample only.
- Sampling is `candidates.sample(n=min(sample_n, n), random_state=seed + beam_id)` — seeded per beam.
- The random baseline is drawn from the full database with `random_state=seed + 4`.
- An empty beam returns zeros and an empty sample; it is a value, not an exception.
- Core's beams are **per-axis controls** (full / metal-only / linker-only / random): each control
  keeps one axis and relaxes the others. The older build studied in `LLM4MOF-ANATOMY.md` §2.6 used
  **nested relaxation** (full / minus the numeric gate / primary identity only / random).

### LLM4MOF Core — `core/hierarchy.py`
- Tags have canonical forms reached through an alias map; parent tags resolve to their leaf
  descendants before filtering, so filtering only ever matches leaves.
- When a tag returns zero hits the hierarchy can be walked up one level; the caller decides when to stop.

### LLM4MO — `vocabulary.py`
- One JSON file per namespace, `schema_version` pinned; `canon()` resolves an alias by **exact match
  after normalisation** (casefold, collapse whitespace) and raises on anything else — no fuzzy
  matching, no keyword routing, no silent fallback.
</reference_facts>

<decisions>
## Implementation Decisions (development defaults)

### D-01 Beam structure: nested relaxation, as the charter states
`full` (A1+A2+A3) / `chem` (A2+A3) / `primary` (A3) / `random`. Adjacent beams differ by exactly one
axis, so each comparison attributes one axis. LLM4MOF Core's per-axis controls are the recorded
alternative: with three axes they need five beams (50 evaluations per iteration instead of 40) and
measure each axis against random rather than conditionally. Which structure attributes better is an
empirical question for Phase 7; the beam builder takes the structure as data so the alternative can
be run without a code change.

### D-02 Tag vocabulary as protocol
`protocol/tag-vocabulary_v1.yaml` + `protocol/schemas/tag-vocabulary.json` + provenance, in the
`schema-inventory` gate step. Each entry: `id`, `axis` (`A2` | `A3`), `smarts`, `aliases[]`, optional
`parent`. Alias resolution is exact after normalisation (LLM4MO). Parent tags resolve to leaves
before filtering (LLM4MOF). Every SMARTS is compiled by RDKit at load; a pattern that fails to
compile fails the gate. No LLM-written field is ever a filter (charter §7).

### D-03 A3 is one label per candidate, by a stated rule
The backbone is the set of atoms on the shortest path between the two `*` atoms, plus every ring that
path passes through. The A3 label is the highest-priority backbone class whose SMARTS matches inside
that set; the priority order is part of the vocabulary file, so the labelling is deterministic and
reviewable. A2 tags are multi-label and match anywhere in the repeat unit.

### D-04 Tags are computed once per snapshot
`data/processed/tags-041e5834.parquet` (untracked), keyed by `candidate_id`, with the vocabulary
version in its metadata. The report of tag coverage over the population (count per tag, candidates
with no A3 label) is an aggregate and is committed under `docs/audit/`.

### D-05 Query semantics
`{a3: <tag>, a2: {all_of: [...], any_of: [...], none_of: [...]}, a1: {<property>: [min, max]}}`.
A1 windows apply to candidate medians of the intermediate variables (`rg`, `ffv`, `sp_ced`,
`density`). A query is a boolean mask over the population; the mask is never sent anywhere.

### D-06 Sampling
Within a matched set: a seeded uniform sample, seed derived from `(run seed, iteration, beam)`.
The `random` beam is a round-robin over A3 classes (the analogue of LLM4MOF's metal-balanced random
beam), so a dominant backbone class cannot own the baseline. No sampling rule reads a target value.
A beam with no matches is recorded as `no_match` and consumes no budget.

### D-07 The deterministic selector
Charter §13: iteration 1 = one A3 tag and two A2 tags drawn by seed, no A1 window; iteration i > 1 =
the A1 window is the median ± 20 % of `rg` and `ffv` over the five best feasible candidates of the
previous `full` beam. If the previous `full` beam had fewer than five feasible candidates the window
is carried over unchanged, and the carry-over is recorded.

### D-08 Population
The loop searches the `check_tc`-passing candidate-level population (D-26); percentiles are printed
against both populations.
</decisions>

<deferred>
- Tag relaxation on zero hits (LLM4MOF `relax`) → Phase 6, where an agent's over-tight query makes it useful.
- Feedback text, pattern summaries, memory → Phase 6.
</deferred>

---

*Phase: 05-deterministic-end-to-end — draft context*
