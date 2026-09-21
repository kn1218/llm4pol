# S1 — FAITHFUL PORT

**LLM4POL as LLM4MOF with the domain layer swapped, running in database mode on the PoLyInfo tables.**

Written 2026-09-11. Angle: change as little of LLM4MOF as possible. Keep the loop, the two agents, the four beams, the ledger, the feedback generator and the evaluation protocol as they are. Replace only: the hidden table, the record matchmaker, the controlled vocabulary, the seven numeric descriptor slots, the stratum key, and the English nouns in the prompts and feedback. Add nothing to the loop.

Sources: `LLM4MOF-ANATOMY.md` + its fact-check packet (claims C1–C25, extra findings E1–E11), `POLYMER-LANDSCAPE.md` + its citation-check packet (REF-101…153), `DATA-FOUNDATION-REPORT.md` §§1–8, `LLM4Polymer_Research_Proposal.md` (treated as input, not as truth). Claims marked **refuted** in the packets are not used; three of them are corrected explicitly below. Numbers I computed myself on the raw files during this pass are marked **[computed 2026-09-11]**.

---

## 0. The thesis in one page

LLM4MOF is two things bolted together: (i) a domain-agnostic **attribution harness** — a fixed ten-iteration loop, a stateful hypothesiser, a stateless translator, four beams that relax one constraint family each, a facts-only ledger, a target-blind feedback renderer, and an evaluation protocol built on hidden-table percentiles; and (ii) a MOF-specific **domain layer** — PORMAKE assembly, Zeo++ geometry, RASPA GCMC, 124 metal/linker tags, three MOF property tables.

The harness is the contribution ("The central contribution is not that a language model can drive MOF search, but that it can do so attributably", Manuscript l. 618-622). The domain layer is the part that has to change for polymers. S1 argues that the right first move is to change **only** the domain layer, and to change it against the cheapest possible evaluator: the measured PoLyInfo property tables, used exactly the way LLM4MOF uses hMOF and QMOF.

Three facts make this the dominant opening:

1. **LLM4MOF's database mode already is a pool-based, record-filtering, table-lookup system.** `hmof_matchmaker.py` (341 lines) and `qmof_matchmaker.py` (225 lines) do whole-record boolean filtering on a flat JSON index with `search_mode ∈ {full, metal_only, linker_only}` driving the beams (verified, anatomy §2.5). There is no assembly, no simulation, no surrogate. A polymer record table drops into that seam with no change to the loop. The PORMAKE path — virtual assembly over 518 nodes × 156 linkers × 952 topologies, MOF2Zeo triage, LAMMPS, Zeo++, RASPA — is the *discovery* path, and it is exactly the part that has no affordable polymer analogue.
2. **The code is MIT-licensed and the older clone runs.** `LICENSE` = "MIT License, Copyright (c) 2026 Nam Kyung-min" (verified on disk). The aide2 clone `f1d731a` (2026-07-18) imports cleanly and carries the evaluation harness the public repo lacks: `--seed`, `--no-feedback`, `LLM4MOF_STRATA_MODE`, and `scripts/precheck/run_battery.py` (233 lines) + `parse_results.py` (213 lines). The newer clone `5adb33e` (2026-09-09) cannot initialise its matchmaker (`UNIFIED_VOCABULARY_PATH` ImportError, deferred to the first `get_approved_vocab()` call) and cannot import its live runner (`core.han_safe_topologies` missing) — verified claims C17/E2.
3. **Database mode is nearly free, and that is the enabling fact.** A ten-iteration DB campaign took a mean of **353 s** wall-clock (n = 160 recorded campaigns, median 348 s, range 247–492 s), **2 LLM calls per iteration / 20 per campaign**, ~0.57 M tokens, **$1.06 ± 0.05** at GPT-5.2 prices (verified C12, C23, anatomy §6). The entire research programme — six backends × seven tasks × five replicates = 210 campaigns — is roughly 20 h of wall-clock and ~$220. Every MD-based alternative is 10⁵–10⁷ CPU-hours (§E below). Cheapness is what buys the statistics that the aide2 review showed LLM4MOF itself lacks.

**What it costs scientifically** is stated in full in §0.3; the short version is that S1 buys Figure 2 of the LLM4MOF paper and forfeits Figures 4–7, and that it inherits every one of the twelve reviewer pressure points the aide2 review found.

### 0.1 What is kept byte-identical

The eight stable interfaces of anatomy §3.2, unchanged in shape: Agent-1 hypothesis JSON (8 fields, 4 validated), Agent-2 constraint JSON (`node_query` / `linker_query` / `global_requirements` / `geometry_filter`), matchmaker result contract, beam/candidate record (`filename, target, <7 descriptor slots>` + chemistry columns; `filter_sets = {z, a, f, total, …}`; `beam_data.csv` with `beam_id ∈ {Z,A,F,R}`), feedback payload, ledger record, experiment metadata, env/CLI toggles. Fixed ten iterations, no early stopping. Temperature 0.0 on both agents. Agent 1 multi-turn, Agent 2 stateless. Halt on malformed JSON after four repair attempts. `FEEDBACK_SAMPLE_SIZE = 10` → 10 × 4 beams × 10 iterations = 400 revealed labels per campaign.

### 0.2 The six deviations — each forced, each justified

No other change to the harness is permitted in Phase 1.

| # | Deviation | Forced by | Cost / benefit |
|---|---|---|---|
| **D-1** | **Suppress structure names and SMILES in the feedback.** Agent 1 sees `POL-17 \| Backbone:[polyester] \| Bkbn:[aromatic, ester, ether] Subs:[methyl] \| Rigidity 0.62 …` and never a name or a SMILES string. | PoLyInfo Terms Art. 10(1)–(3): names and structures are "DATA"; routing them to a hosted API is arguably transmission. Also closes the leak LLM4MOF weakness #6(c) flags (readable names are unique enough to identify building blocks) and narrows the parametric-memory channel that produced the 0.44–0.72 memorisation share. | Removes one input the MOF agent had. Scientifically an improvement, not a loss: it makes "target-blind" stronger. |
| **D-2** | **Inclusive bounds on all seven descriptor slots.** LLM4MOF gates the `di`/`df` pair strictly (`DI_MIN < di < DI_MAX`) and the other five inclusively (verified C6). | Polymer fraction descriptors have mass points at exactly 0.0 and 1.0 (aromatic fraction = 0 for every aliphatic polymer). A strict `0 < arom_frac` silently deletes the entire polyolefin family. Zeo++ pore diameters never land on a round bound; RDKit fractions do. | One-character change in `sensitivity_analyzer.py`. Must be recorded, because it makes Beam 1 slightly wider than the MOF equivalent. |
| **D-3** | **Ten replicates for headline arms** (five for grid arms). | Measured replicate σ of the final Beam-1 percentile is 6.4 / 15.9 / 6.9 points (aide2 W1, n = 10/arm, verified C20). At n = 5 the SEM is 2.9–7.1 points and Table-1-style "within 0.1 points" statements are meaningless. | Doubles campaign count for headline arms; at $1/campaign this is irrelevant. |
| **D-4** | **Hidden table at the replicate-group median, not the raw sample row.** | 56.3 % of Tg rows sit in replicate groups (audit D4); 6,548 rows are exact duplicates on every column but `sample_id`. Per-row tables double-weight and leak across beams. | Copolymer Tg table shrinks from 18,142 raw rows to **10,249 replicate-collapsed groups** [computed 2026-09-11]. |
| **D-5** | **Stratum key changes**: `metal_of()` → `backbone_class_of()` (homopolymer track) and `polymer_id_of()` (copolymer track). | The MOF stratum is metal identity. The polymer identity axis is backbone family. In copolymer mode the same polymer appears at many compositions, so a metal-style key would return ten compositions of one polymer as "ten candidates" — pseudo-replication LLM4MOF cannot have. | Two functions in `sampling_strata.py` (160 lines). Preserves the critical property that the stratifier reads identity only and never the target (verified C7). |
| **D-6** | **Three pre-registered controls added *outside* the loop** (zero LLM calls, zero loop changes): the zero-feedback arm, the supervised-shortcut probe, and the mechanism-edit test (§A.3). | The aide2 review showed LLM4MOF's own weakest points are (1) interpretability asserted not measured, (2) no supervised baseline for the beams, (3) unreported memorisation share. All three are cheap here and two are already implemented in the OLD clone. | Adds ~250 lines of analysis code that never touch `run_experiment.py`. |

### 0.3 What maximal reuse costs, stated plainly

1. **You inherit all twelve reviewer pressure points** (anatomy §5). The architecture of the problems ports with the architecture. D-6 pre-registers the three that can be answered cheaply; the others (metric exposure to matched-set size, budget accounting, hidden-table-equals-filtered-object) must be *disclosed* in the paper rather than fixed, because fixing them means deviating.
2. **The MOF axes are not the polymer axes.** In a MOF, pore geometry is genuinely the mechanism for adsorption, so a geometry window is a mechanistic claim. In a polymer, Tg's mechanism is chain stiffness plus cohesive energy density, which the seven descriptor slots *proxy* rather than *are*. If the descriptors are a good Tg surrogate, Beam 1 beats Beam 2 trivially and the "attribution" is a supervised shortcut — the polymer version of the probe that recovered 94 % of the PORMAKE H2 table from three geometry columns (verified C21). This is the single largest scientific risk of the port and it is why D-6's probe is mandatory and pre-registered, not optional.
3. **The oracle is noisy in a way LLM4MOF's is not.** RASPA on a fixed force field is deterministic: the same structure always gives the same number. A PoLyInfo Tg is a measurement whose within-replicate-group SD has median 7.0 °C and p90 33.1 °C, and whose within-polymer range across samples has median 20.2 °C with 588 ids exceeding 50 °C. **Beam separations below ~7 K are not resolvable.** The honest framing of the task therefore changes: it is *enrichment of a measured landscape*, not *prediction of a physical quantity*. Processing variables PoLyInfo does not carry (Mₙ, dispersity, tacticity, thermal history) are inside that noise and cannot be designed against. The pre-proposal's §2.1 table already says a repeat-unit SMILES is not a full specification; S1's answer is to name the layer explicitly — repeat-unit chemistry only — rather than to build machinery for the rest.
4. **No de novo generation in Phase 1, so no discovery claim.** LLM4MOF's strength in a Nature Communications submission came from Figures 4–7: live-simulated *new* MOFs, budget-matched GA/BO, backend insensitivity, label accounting. S1 delivers the Figure-2/Table-S2 half (enrichment, hit rate, beam attribution, ablations, backend benchmark, budget-matched baselines over the same pool) and defers discovery to a gated Phase 3. A reviewer will ask "did you make anything new?" and the answer in Phase 1 is "no, we recovered the top of a 13,624-structure measured landscape from natural language without a single property label" — which is a weaker but defensible claim, and it is precisely LLM4MOF's abstract claim 6 ("All of this uses not a single property-labeled training structure"), which transfers verbatim.
5. **Comparability is the reason to hold the line.** Every deviation costs a claim of the form "the same loop, unchanged, transfers to a new domain." That claim is stronger and more novel than "we built a polymer agent" — of the thirteen polymer agents surveyed (Polymer-Agent, PolyFusionAgent, PolySea, PolyJarvis, Zhou 2026, Roy 2026, POLYT5, polyBART, PolyTAO, Vogel VAE, Yue benchmark, Kim 2021 GA, Huang MOEA), **none performs controlled diagnostic-beam attribution** (landscape §4). LLM4MOF's own §2.12 claim — "the two operating modes are one implementation… the hypothesis-generating agent receives no signal indicating which mode it is running in" — generalises to "the two *domains* are one implementation," and that is the paper.

---

## A. The scientific question, and what "interpretable inverse design" means here

### A.1 The question

> Given only a natural-language property goal, a closed polymer vocabulary, and no property-labeled training data, can a two-agent loop enrich the top of a measured polymer property landscape within 400 revealed labels — and can each iteration's gain be attributed, by controlled construction, to one of three named design axes: **backbone family**, **side-group chemistry**, or **the numeric descriptor / composition window**?

Sub-questions the design must answer, each with a number attached:

- **Q-A1 (enrichment).** Does the Beam-1 median cross the hidden-table top-10 % threshold, and in how many iterations? Homopolymer Tg thresholds, computable today: median **410 K**, top-10 % **563 K**, top-1 % **657 K**; for the minimisation direction bottom-10 % **277 K**, bottom-1 % **195 K** (n = 7,733 Tg values) [computed 2026-09-11].
- **Q-A2 (attribution).** Is the Beam-1 − Beam-2 gap (descriptor/composition window), the Beam-2 − Beam-3 gap (side-group chemistry) and the Beam-2 − Beam-4 gap (chemistry vs chance) larger than the replicate σ, measured first?
- **Q-A3 (is it a shortcut?).** Do the seven descriptors, fit supervised on the hidden table, already explain it? Pre-registered pass/fail threshold below.
- **Q-A4 (is it memory?).** What fraction of the skill survives when feedback is replaced by an empty stub? LLM4MOF's own floor-corrected memorisation share was 0.44 / 0.44 / 0.72 on three tasks (verified C20); polymer Tg is a canonical textbook quantity and the share may be higher.
- **Q-A5 (does the stated mechanism hold?).** Mechanism-edit test, §A.3.

### A.2 Operational definition of "interpretable"

LLM4MOF's interpretability rests on the JSON being readable and on three narrated trajectories. S1 keeps that and makes it falsifiable with three clauses that cost no LLM calls:

1. **Readability by construction.** Every candidate set Agent 1 ever sees is the exact output of a constraint JSON a polymer chemist can read aloud: `{backbone_query: {families: ["polyester"], linkage: ["aromatic_ester"]}, sidegroup_query: {functional_groups: [...], branches: [...]}, descriptor_filter: {target_rigidity_min: 0.55, …}}`. Nothing between the hypothesis and the candidates is learned.
2. **Decomposition by construction.** The gain is split into three arms *before* it is measured, not attributed after the fact by SHAP. This is the structural difference from every published polymer interpretability paper (REF-131…136), all of which are post-hoc attribution on a fitted model.
3. **Falsifiability by edit** (this is the addition). See A.3.

What "interpretable" explicitly does **not** mean here, and must be said in the paper: it does not mean the model's internal reasoning is inspected; it does not mean the discovered rule is physically true — it is a rule about the PoLyInfo corpus under its own measurement conventions, exactly as LLM4MOF's CO₂ open-metal-site rule turned out to be a property of the hMOF oracle rather than of chemistry (verified C21); and it does not mean the attribution isolates individual descriptors, because a beam relaxes a whole constraint family at once (LLM4MOF has the same limitation and handles it with human-only extra sets, §F.3).

### A.3 The mechanism-edit test (the one scientific addition; 0 LLM calls, 0 loop changes)

Take the final hypothesis of a completed campaign. Mechanically invert exactly one clause of the Agent-2 constraint JSON — swap `target_rigidity_min` for `target_rigidity_max` at the same value; replace the committed backbone family with the family that ranked lowest in that campaign's Beam 3; delete the highest-frequency side-group tag from `include_tags`. Re-run the matchmaker and the evaluator **with no LLM in the loop**, and record whether the Beam-1 median moves in the direction the hypothesis text predicted.

Pre-registered success criterion: **≥ 6 of 10 edits move the median in the predicted direction** (one-sided sign test over ten campaigns, p = 0.055 at 8/10, p = 0.011 at 9/10 — state the exact n and p, not a threshold-chasing claim). This is the direct answer to aide2 pressure point #1, it is the only thing in this strategy that is not in LLM4MOF, and it costs one script and a few minutes of CPU.

Companion pre-registrations, both run before any campaign claim is published:

- **Supervised-shortcut probe (Q-A3).** Gradient boosting on the seven descriptors → out-of-fold R² on the hidden Tg table. **If OOF R² > 0.80, the descriptor-window beam is declared a supervised shortcut in the paper** and the headline attribution claim is restricted to the chemistry arms (Beam 2 vs 3 vs 4). Reference point: the equivalent MOF probe reached OOF R² 0.943 from three geometry columns (verified C21).
- **Zero-feedback arm (Q-A4).** `--no-feedback` (already in the OLD clone) × 10 replicates × every task; report the floor-corrected memorisation share (NF − 50)/(V0 − 50) in the main text, not the SI.

---

## B. The design space — what a candidate *is*

S1 runs pool-based: **the pool is the table**. There is no enumeration step in Phase 1, and that is the single largest cost saving relative to the pre-proposal.

### B.1 Two tracks, both DB mode

| | **Homopolymer track (anchor)** | **Copolymer track** |
|---|---|---|
| A candidate is | one repeat unit | (monomer A, monomer B, composition fraction f_A, basis, architecture tag set) |
| Identity key | trimer ring-closed key, stereo stripped (audit §3.2); `stereo_canon` kept as a linked variant | (key_A, key_B) unordered + f_A + basis + architecture set |
| Pool size | **13,725 rows / 13,624 unique CanonSMILES**; Tg-bearing **7,733 rows / 7,699 unique structures** [computed] | usable core **13,350 rows / 2,735 ids** (both monomers matched to a homopolymer + Tg); composition-parsed subset **6,917 rows / 1,381 ids**; after replicate collapse **10,249 groups** over the full Tg set [computed] |
| LLM4MOF analogue | QMOF (20,373 curated records, one property, smaller) | hMOF (51,163 records, tabulated properties, chemistry tags) |
| Continuous axis | none | f_A ∈ [0,1] |
| Serialisation to the LLM | `POL-i \| Bkbn:[aromatic, ester, ether] Subs:[methyl] \| Rigidity 0.62 \| AromFrac 0.46 \| Ecoh 610 \| FFV 0.128 \| HBd 0.00 \| MW 192 \| SC 1` — no name, no SMILES (D-1) | `COP-i \| A:[acrylate, methyl] B:[vinyl_aromatic] \| f_A 0.62 mol \| alternating \| <7 blended descriptors>` |
| Serialisation to the oracle | pid → row lookup in the hidden index | replicate-group id → collapsed median lookup |

Both tracks reuse the same `filter_sets` schema and the same `beam_data.csv`, so the feedback generator, ledger, analyzer and battery driver do not branch. The track is a config switch, exactly as `is_hmof_mode()` / `is_qmof_mode()` are today.

### B.2 Design-space size, reported honestly

LLM4MOF's SI gives its discovery space as |D| = Σ_c n_c·t_c·L = 80,126 × 156 = **12,499,656**, a connectivity-matched sum — *not* the plain product 518 × 156 × 952 = 76,929,216 (verified extra finding E1; the anatomy states the plain product and it is a 6.2× overstatement). S1 will not repeat that class of error. In database mode the design space **is** the reachable table and nothing else:

- Homopolymer Tg: 7,699 unique structures, of which the reachable set is those carrying ≥ 3 vocabulary tags and all 7 descriptors (measured at M3; report both numbers, as LLM4MOF should have — its PORMAKE tables were silently pre-filtered from 19,997/12,188 to 14,173/9,533 by `build_canonical_db.py`, weakness #6).
- Copolymer Tg with composition: 6,917 samples over 1,381 polymer ids; after replicate collapse and exclusion of truncated terpolymers and same-monomer pairs, report the exact remaining count.

### B.3 Where enumeration lives (not Phase 1)

The PORMAKE analogue for polymers exists and is rule-based virtual forward synthesis: **SMiPoly** (22 rules — 6 chain-growth, 16 step-growth — 1,083 monomers → 169,347 polymers in 7 classes, BSD-3, REF-117) and **OMG** (17 polymerization reactions, 77,281 SCScore-filtered eMolecules reactants → ~12 M CRUs, GPL-3, REF-116). Both are homopolymer-first; a copolymer space is the monomer-pair product × composition grid × architecture tag, which nobody ships. These are the proposal space for a live mode and are named here only so the Phase-3 gate has a concrete target. They are not touched in Phase 1, because a proposal space without an affordable oracle is a generator of unevaluable candidates.

---

## C. The Matchmaker and database analogue

### C.1 Role mapping

| LLM4MOF object | n | LLM4POL object | n | Why this mapping |
|---|---|---|---|---|
| hMOF index (`hmof_index.json`, 66 MB) | 51,163 | **Copolymer sample index** | 6,917 composition-parsed / 13,350 Tg core / 10,249 collapsed groups | Both are many-record tables with per-record tabulated properties *and* per-record chemistry tags; both are filtered whole-record; both have a small identity vocabulary (hMOF: 4 metals; copolymer: ~14 backbone families) |
| QMOF index (`qmof_index_v2.json`, 26 MB) | 20,373 | **Homopolymer index** | 13,725 rows / 13,624 structures | Both are curated single-property-per-record tables of *real* (synthesised) materials, smaller and cleaner than the hypothetical table; QMOF's `sa`/`vf` are absent and the analyzer already falls back (`set_z = set_d`, verified C6) — the identical fallback is needed for polymer records with sparse property columns |
| PORMAKE building-block library + topology whitelist | 518 / 156 / 952 | SMiPoly (169,347) or OMG (~12 M) | — | **Phase 3 only.** Not built, not used. |
| CoRE-MOF | — | — | — | **DROP.** CoRE has a construction directory in the repo but is not a campaign database in any shipped run. |
| — | — | PI1M (1 M), polyVERSE, OPoly26, RadonPy DB | — | Named as future *proposal* pools. PI1M is unlabeled and "academic purpose only", so it can never be a DB-mode hidden table. |

### C.2 Metadata each table provides

This is the polymer Table S3. The rule from SI Note S4 ports exactly: **Layer 1 = deterministic facts, Layer 2 = deterministic SMARTS tags, and both drive filtering; anything an LLM writes is display-only and is never filtered on** (verified: the enrichment step "writes no fields that the Matchmaker filters against").

| Field group | Homopolymer index | Copolymer index | Source |
|---|---|---|---|
| Identity (L1) | `pid`, trimer key, `linear_canon`, `stereo_canon`, `n_star`, `topology_tag` | `polymer_id`, ordered monomer keys, `architecture_tags` / `architecture_set`, `n_components_declared`, `truncated_flag`, `same_monomer_flag` | audit §3.2 |
| Composition (L1) | n/a | `f_A`, `basis ∈ {mol, wt, vol, unknown_u, ratio_r, unknown}`, `value_class ∈ {percent, fraction, partial_or_ratio, count_like, single, none}`, `binding ∈ {by_component_majority, by_position_aligned_only, undetermined, unresolved}` | audit §3.2; **binding is mandatory, see §I** |
| Chemistry tags (L2) | SMARTS hits + `rule_based_counts` + generic-tag propagation | same, per monomer, plus blended union | ported from `5_shared/smarts_library.py` + `4_vocabulary/04_build_vocab_mapping.py` |
| Numeric descriptors (L2) | the 7 slots of §D.2 | the 7 slots, composition-blended | RDKit + van-Krevelen group contributions |
| Property columns | Tg 7,733; Tm 3,696; density 1,651; ρ_v 1,268; σ_e 1,296; ε_b 1,059; E 1,003; σ_b 1,064 | Tg 18,142 raw → 10,249 collapsed; Tm 8,713; density 3,104; E 3,709; σ_b 5,046; ε_b 5,072; n_D 684; ρ_v/σ_e 4,031/4,060 (strings) | audit §1.5, §1.9 |
| Display-only | `iupac` / `polymer_name`, NFKC-normalised | same | **never sent to the agent** (D-1); used in the human report only |
| Quality flags | `duplicate_structure_conflict` (91 groups, 30 with conflicting Tg, max spread 169 K), range warnings | `exact_duplicate_of`, `replicate_group_id`, `row_alignment_class`, `garbage_row` | audit §4 invariants I19–I27 |

### C.3 The Matchmaker itself

`hmof_matchmaker.py` is the template, not `matchmaker.py`. Port map:

| hMOF concept | Polymer concept |
|---|---|
| `metals` OR-match (`"Any"` wildcard) | `backbone_family` OR-match, same wildcard semantics |
| `topology` (MOFid, 75 % `pcu`) optional filter | `architecture_set` optional filter (`alternating` 9,346 / `random` 6,821 / `block` 6,814 / `graft` 2,740 / `statistical` 471 / `periodic` 10 exploded rows; `['unspecified']` alone is 20,843 rows = 49.0 %) |
| `has_open_metal_sites` boolean | `has_hbond_donor` boolean (the nearest structural analogue: a single binary chemistry flag the agent can commit to) |
| AND tags / OR tags / `exclude_tags` / `linker_branches` (OR-of-ANDs) / categorized groups | **identical machinery, identical semantics**, new tag set |
| numeric range filters (`lcd`, `pld`, `sa`, `vf`, `density`) | the 7 descriptor slots + `f_A` window |
| `search_mode ∈ {full, metal_only, linker_only}` | `search_mode ∈ {full, backbone_only, sidegroup_only}` |
| structured error `{"status":"error","reason":"no_matching_nodes"}` | unchanged shape; new reasons |

Two semantics from SI Note S2 that must be implemented deliberately because they are what makes the constraint language safe (verified extra finding E9):

- **Default-permissive.** "Any constraint left unset by Agent 2 simply defaults to a pass condition." This is what makes the prompt's "OPTIONAL ≠ EXCLUDE" rule safe.
- **No silent defaults.** "An empty or malformed constraint query is rejected with a structured error, automatically halting the iteration rather than silently substituting default values."
- **Cross-database tag portability.** The generic-tag propagation hierarchy is applied to every database "so that an identical Agent 2 constraint maps consistently across all three databases." For LLM4POL this is the guarantee that one constraint JSON works on both the homopolymer and the copolymer index — it is the thing that lets the two tracks share a loop.

---

## D. The descriptor layer, the vocabulary, and the MOF2Zeo question

### D.1 MOF2Zeo has no Phase-1 analogue — DROP

This is the most consequential mapping decision in S1, and it is the one the pre-proposal gets wrong.

MOF2Zeo exists for exactly one reason: in *discovery* mode, geometry is emergent from assembly, so satisfying a geometry hypothesis "would otherwise require assembling and relaxing every combination" of 12.5 M candidates. It is a learned surrogate (545,107 train / 84,228 valid, average R² 0.99) used **only to pre-rank Beam 1**; every gate uses recomputed Zeo++ values (verified C10). **LLM4MOF does not use MOF2Zeo in database mode at all.**

The polymer analogue of **Zeo++** — a deterministic, offline-computed, non-target structural descriptor set — is RDKit + group contributions. The polymer analogue of **MOF2Zeo** — a learned predictor that triages before an expensive build — is a Tg/density surrogate, and it is needed only when there is something expensive to triage. In Phase 1 there is not.

Consequence: the pre-proposal's "surrogate meta-loop" (its contribution #2) is **not a Phase-1 component in S1**. It solves a problem that database mode does not have, and it would introduce the failure mode that database mode uniquely avoids — the loop optimising surrogate error rather than truth (the audit's own F4 risk: "the oracle is only as good as F1/F2, so the loop optimises surrogate error; without an external validation channel success is unfalsifiable"). If and only if a live mode is gated open (§E.3), a single surrogate returns, in exactly MOF2Zeo's role and with exactly its discipline: pre-rank only, margin expanded by the surrogate's own MAE (LLM4MOF's `GEOM_MARGIN_MODE="mae"`, with per-descriptor MAEs di 0.746 Å, df 0.751, sa 50.7 m²/cm³, vf 0.0098, density 0.0152), never gate.

### D.2 The seven descriptor slots (the Zeo++ analogue)

Seven, to match the seven Zeo++ columns and the seven `geometry_filter` min/max pairs in the Agent-2 schema, so the JSON shape is unchanged. Deterministic, computed once offline, never learned. Selected from the mechanistic Tg literature, not from feature search.

| Slot | Replaces | Definition | Mechanistic justification |
|---|---|---|---|
| `rigidity` | `di` | 1 − (rotatable backbone bonds / backbone bonds); rings and unsaturation count as rigid | Chain stiffness — one of the two master variables (REF-112 Karuth/Alesadi/Xia/Rasulev CG parameters; REF-133 SHAP finds NumRotatableBonds strongly negative on 1,261 polyimides) |
| `arom_frac` | `df` | aromatic heavy atoms / heavy atoms in the repeat unit | REF-134 (Miccio): stiff two-phenyl segments raise Tg, linear side-chain segments lower it; REF-131 SHAP ranks ring-fusion descriptors first |
| `ecoh_vk` | `sa` | van-Krevelen cohesive energy density, kJ/cm³, from additive group tables | The second master variable (REF-112); REF-113 is the source table |
| `ffv_proxy` | `vf` | (V_molar − 1.30 · V_vdW)/V_molar, van-Krevelen | Free-volume proxy; the direct analogue of MOF void fraction |
| `hbond_density` | `density` | (H-bond donors + acceptors) / heavy atoms | REF-132: Tg correlates with H-bond count and hydrophobicity |
| `mw_ru` | `dif` | repeat-unit molecular weight | Normalising variable; makes group-contribution sums interpretable |
| `sidechain_len` | `cv` | longest acyclic pendant chain, heavy-atom count | REF-134: side-chain length is the dominant Tg-lowering axis in polyacrylates |

Implementation notes that matter: no pip package ships van-Krevelen or Bicerano tables (landscape open question #1), so `ecoh_vk` and `ffv_proxy` must be coded from the group tables (REF-113, with the Kaggle transcription REF-146 as a cross-check: −CH₂− 158, p-phenylene 2820, −SO₂− 2150, −NHCO− 1510 by molecular weight). For the copolymer track, descriptors are composition-blended linearly on f_A with the *bound* composition (§I), never by column position. All seven are computed in conda base with rdkit 2025.9.6 in minutes over ~18,400 unique structures.

The two "strict" slots become inclusive under D-2.

### D.3 The controlled vocabulary

Target: **the same shape as Table S4** — ~110–125 canonical tags in 10 categories, with an alias map of ~200 entries and ~100 curated SMARTS, built with the same two-layer machinery. LLM4MOF's file is 124 tags / 215 aliases in the SI / 183 alias entries actually built by the loader / 105 SMARTS (verified C4).

Proposed 10 categories (~114 tags):

| Category | ~n | Examples |
|---|---|---|
| Backbone family | 14 | polyolefin, polyester, polyamide, polyimide, polyether, polyurethane, polycarbonate, polysiloxane, vinyl_aromatic, acrylate, polysulfone, fluoropolymer, polyurea, polyphosphazene |
| Main-chain linkage | 12 | ester, amide, imide, ether, carbonate, urethane, sulfone, siloxane, urea, ketone, thioether, carbon_carbon |
| Ring / scaffold | 16 | benzene_ring, naphthalene, biphenyl, anthracene, cyclohexane, norbornene, adamantane, spiro, fused_bicyclic, … |
| Heterocycle | 14 | pyridine, imidazole, thiophene, furan, oxazole, triazine, benzoxazole, … |
| Functional group | 28 | hydroxyl, carboxyl, nitrile, amine_primary, amide_NH, sulfonate, phosphate, epoxide, ketone, nitro, … |
| Substituent | 8 | methyl, ethyl, isopropyl, tert_butyl, phenyl, benzyl, long_alkyl, alkoxy |
| Halogen | 6 | fluoro, chloro, bromo, iodo, perfluoroalkyl, CF3 |
| Architecture | 7 | homopolymer, random, statistical, alternating, block, graft, periodic |
| Interaction role | 4 | hbond_donor, hbond_acceptor, electron_rich, electron_deficient |
| Descriptor axis | 5 | rigidity, aromaticity, cohesive_energy, free_volume, sidechain_bulk |

Seed sources, in order of licence safety: the **PoLyInfo ontology** (CC BY 4.0, MDR DOI 10.48505/nims.5395) — note carefully that the *ontology* is CC BY even though the *data* is not, which makes the vocabulary the one PoLyInfo-derived artefact the project can publish; HAPPY/FORGE subgroups mined from ~10,000 PoLyInfo repeat units (REF-136, arXiv:2512.06301); PolyBench-LLM's SME descriptor set; RDKit functional-group SMARTS; and PolyTAO's 15 descriptors (REF-127). The M/AD/SD monomer-substitution taxonomy for copolymer Tg deviation (REF-148, Huang 2022) is attractive as an architecture-adjacent tag family, but the citation-check could not read the taxonomy from any accessible abstract — **verify it against the PDF before hard-coding it**.

Ported directly from the MOF pipeline: `canon()` (lowercase, `-`/space → `_`, alias resolution), `TAG_HIERARCHY` generic propagation (~152 entries in MOFs; e.g. `benzene_ring → aromatic, aryl, ring`), the backbone/substituent split by pattern category, multiplicity counting (`rule_based_counts`, which drives the `Counts[…]` feedback block), and the rule that unrecognised positive tags warn and are still applied (they match nothing) while unrecognised negative tags are dropped.

One MOF rule is deleted, not adapted: the PORMAKE "BINDING TERM HANDOVER" (coordination tags must go into `node_query.ligand_chemistry`, not into linker branches) and `strip_coordination_tags_from_branches`. There is no coordination chemistry here. The `{DATABASE_MODE_RULES}` block that injects it becomes two polymer blocks: `HOMOPOLYMER_MODE_RULES` and `COPOLYMER_MODE_RULES`, the latter carrying the composition-window and architecture rules.

---

## E. The oracle

### E.1 Database mode — the ground truth is a measurement

The evaluator is `SensitivityAnalyzer` on a hidden table: a lookup, zero simulations, exactly as in hMOF/QMOF mode. Cost per 10-iteration campaign: **~350 s wall-clock, 20 LLM calls, ~0.55 M tokens, ~$1**, on the Windows laptop (i5-14600K, 14P/20L cores). Dependencies: pandas 2.3.3, numpy 2.3.5, scipy 1.16.3 — all present in conda base; plus the LLM SDK. rdkit 2025.9.6 is needed only for the offline descriptor/vocabulary build. **No torch, no GPU, no HPC, no CUDA.** This matters: no environment on the machine has a CUDA-enabled torch, and the RTX 5050 (8,151 MiB, driver-level CUDA 13.3, Blackwell) would need a new wheel. S1 does not depend on it.

Estimated total Phase-1/2 compute: M6's battery is 4 arms × 5 tasks × 10 replicates = 200 campaigns ≈ **20 h** at 6 concurrent, ≈ **$210**. The backend benchmark adds 6 × 5 × 5 = 150 campaigns ≈ 15 h, ≈ $160 (less for cheaper backends).

### E.2 The "oracle is only as good as the surrogate" problem

**In database mode it does not arise, and that is the central argument for S1.** There is no surrogate between the candidate and the score: the score is a measured Tg. The problem the pre-proposal's meta-loop was built to solve is dissolved by the choice of mode rather than solved by machinery.

What *does* arise, and must be handled by disclosure rather than by code:

1. **The hidden table is the object the matchmaker filters.** LLM4MOF has the same structure (weakness #6) and additionally pre-filtered its PORMAKE tables to the proposable space. S1 makes this explicit: the hidden table is *defined* as the reachable set (every row carries ≥ 3 tags and all 7 descriptors), the before/after counts are published, and "top-1 % of the database" is always written as "top-1 % of the reachable table, n = N".
2. **Oracle scope must be stated per task.** The design rule a campaign produces is a rule about PoLyInfo's Tg measurements under their reporting conventions — DSC vs DMA, unrecorded heating rates, unrecorded Mₙ and tacticity. Within-polymer Tg range across samples has median 20.2 °C. The paper must contain a sentence of the same kind as LLM4MOF's one honest scope statement ("The force field used here does not represent the π-complexation"), and must contain it for every task, not one.
3. **The descriptor slots could be a shortcut.** Pre-registered probe, §A.3, with a stated fail action.
4. **Conflicting duplicates cap the achievable resolution.** 91 XLSX duplicate-structure groups, 30 with conflicting Tg, max spread 169 K. These must be aggregated or excluded by an explicit user decision (§L), and whichever is chosen, the count is reported.

### E.3 Live mode — the arithmetic, and the gate

Live mode is added **only if** a credible oracle exists. The landscape's cost table says it does not, at LLM4MOF's beam widths:

| Oracle | Cost per candidate | Accuracy | LLM4MOF-width campaign (40/iteration × 10 × 5 reps ≈ 2,000 candidates) |
|---|---|---|---|
| All-atom MD **Tg** (3–10 replicates, 260–400 ns each) | **4,000–20,000 CPU-h** | systematic **+40 to +120 K** offset (Afzal +79.1 K mean, slope 1.30; Gudla & Zhang "80 to 120 K"; Martí constant +105.02 K; PolyJarvis +38 to +47 K); single replicate 95 % CI ≈ 60–80 K, **≥ 10 replicates needed for CI < 20 K** | **10⁷–4×10⁷ CPU-h** — infeasible by four orders of magnitude |
| All-atom MD **density** | 300–2,000 CPU-h (~1 day on 32 cores) | R² **0.890** vs PoLyInfo on 1,001 polymers (RadonPy's own validation) — the one quantitatively validated cheap MD quantity, i.e. the true Zeo++ analogue | 6×10⁵–4×10⁶ CPU-h — still infeasible |
| MD **top-k validator** on ≤ 10 finalists per task | 4×10⁴–2×10⁵ CPU-h per task | as above, calibrated | **feasible**: weeks on a dirac allocation. This is what Zhou 2026 (8 copolymers, 4.17 % mean relative error) and Bhati 2026 (50 candidates) do |

At ~4,000–20,000 CPU-h per Tg candidate, a 256-core dirac allocation delivers **0.3–1.5 Tg candidates per day**. Therefore:

- **Phase 1 and 2: no live mode.** The word "discovery" does not appear in the Phase-1 claims.
- **Phase 3 (gated): a top-k validation *channel*, not a live mode.** MD Tg on ≤ 10 finalists per task, ≥ 3 replicates each, with the offset stated as a calibration (Tg = 0.77·Tg_calc + 21.08 K, REF-104) and the *rank* comparison — not the absolute value — as the claim.
- **Phase 4 (further gated): a one-iteration live probe on density**, 40 candidates, to demonstrate that the mode switch works, mirroring LLM4MOF's claim that both modes are one implementation.

Gate criteria that must all be true before Phase 3 starts: a confirmed dirac allocation ≥ 50,000 core-hours; RadonPy (BSD-3) + LAMMPS ≥ 3Mar20 + **Psi4 ≥ 1.5** installed on dirac (Psi4 is the RESP-charge dependency and is not pip-installable — the single largest install risk); a measured wall-clock for one density candidate on dirac; and reproduction of three published RadonPy densities within 5 %. Route everything through the hpc-submit skill's mandated convention (`config/hpc.json` + `scripts/submit.py` + `transport.py`), never raw ssh/qsub. Note that dirac GPU availability is **unknown** (the skill file has zero occurrences of gpu/cuda; only a `cuda100/111` module on dirac1 is recorded in CALF20's notes) and that the skill warns Dropbox file locks corrupt ledgers — which is a reason to keep the repo off Dropbox.

The HPC job contract ports unchanged and is worth keeping even though nothing uses it in Phase 1: `batch_manifest.json {version, experiment_id, iteration, n_jobs, config{…}, jobs[…]}` → per-job `<filename>.json` + `<filename>.DONE` sentinel → `batch_results.json {n_success, n_fail, n_missing, total_wall_seconds, results[]}` (verified C24). Also worth keeping: `SimCache` (append-only `sim_cache.jsonl` keyed by the candidate identity) and the "real iteration" accounting that only counts iterations which produced results.

---

## F. The four beams, re-defined

### F.1 Definitions

| Beam | LLM4MOF (DB mode) | LLM4POL homopolymer | LLM4POL copolymer |
|---|---|---|---|
| **1 / Z** full hypothesis | chemistry ∩ strict Di/Df window ∩ inclusive sa/vf/density/dif/cv | backbone family ∩ side-group tags ∩ 7-descriptor window | backbone families of both monomers ∩ side-group tags ∩ architecture tags ∩ 7-descriptor window ∩ **f_A window** |
| **2 / A** chemistry only | chemistry, geometry window removed | backbone family ∩ side-group tags | monomer chemistry ∩ architecture tags, **no descriptor and no composition window** |
| **3 / F** primary identity only | node metals + connectivity + ligand chemistry; linker and geometry free | **backbone family only**; side-groups, descriptors free | **backbone family of monomer A only**; B, composition, architecture, descriptors free |
| **4 / R** random baseline | entire hidden table, metal-stratified sample | entire reachable table, **backbone-class-stratified** | entire reachable table, **polymer-id-stratified** |

Set containment Z ⊆ A ⊆ F ⊆ total holds by construction and is an M4 acceptance test.

Adjacent comparisons, unchanged in meaning and unchanged in the hint sentences the feedback carries:
- **Beam 1 vs 2** → contribution of the numeric window (descriptors, and in the copolymer track composition).
- **Beam 2 vs 3** → contribution of side-group chemistry (and of the second monomer).
- **Beam 2 vs 4** → is the chemistry better than chance.
- The `geometry_null` guard ports verbatim: when the window is all-null, the feedback prints "Beam 1 = Beam 2 (no window was active). This comparison does NOT measure window contribution."

One LLM4MOF asymmetry ports as a **fix**, not as fidelity: `_build_beam_specs` keeps `geometry_filter` in the metal-only beam in live mode (verified C25). In DB mode the analyzer does not, so DB mode is already clean and the polymer port inherits the clean version.

### F.2 Causal attribution when one axis is continuous

The honest answer, and it is LLM4MOF's own answer: **a beam relaxes a constraint *family*, never a single variable.** LLM4MOF's Beam 1 vs Beam 2 comparison confounds all seven geometry descriptors into one window; it does not and cannot say "vf contributed 3 g/L of the gain." Its per-descriptor isolation lives in the analyzer's extra filter sets B…S (chem + Di, chem + Df, geometry-only E/E2, linker-only G, single-descriptor H…N, chem + one-descriptor O…S) which are computed every iteration and written to `Sensitivity_Report_iterN.csv` — and which are explicitly **human-only**, never shown to the agent ("Purpose: Human analysis ONLY - NOT shared with Agent 1").

So the continuous composition axis needs no new beam and no new machinery:

1. **Composition is a window slot**, structurally identical to a descriptor window: `target_fA_min` / `target_fA_max`, Float-or-Null, default-permissive. Beam 1 vs Beam 2 therefore measures "did committing to a composition range help", which is exactly the question a copolymer chemist asks.
2. **Per-axis isolation goes to the human-only extra sets.** Add the composition-only set and the chem+composition set to the existing B…S machinery. Nothing new is shown to the agent.
3. **One new human-only statistic that continuity makes available and MOFs cannot have:** the within-polymer composition slope. For every polymer id in Beam 1's matched set with ≥ 3 same-basis compositions, compute Spearman ρ(target, f_A) and report the median |ρ| and its sign distribution. There is a ready-made reference set: 378 ids have ≥ 5 distinct same-basis compositions summing to 99–101, with median |ρ| = **0.868** (234 ids above 0.7, 67 below 0.3). If the agent commits to "raise f_A of the rigid comonomer" and the matched set's slopes are negative, that is a measured contradiction of the stated mechanism — a second, free instance of the mechanism-edit idea, and the only genuinely new form of attribution the polymer domain offers.

### F.3 The metric hazard that continuity makes worse

LLM4MOF's plotted beam median is the median of the *entire* matched set, whose size swung from Z = 1 at iteration 1 to Z = 43 / A = 257 / F = 3,591 / R = 9,533 at iteration 10 in a recorded campaign (verified C23). A hypothesis that admits one structure yields a "median" of one structure. A continuous window makes this strictly worse: a narrow f_A window over a small monomer pair can match three samples.

Mitigations, all inside existing machinery:
- **Report n per beam per iteration in every figure.** LLM4MOF's `source_data` carries the counts but the paper's plots do not show them. This is free and closes pressure point #5.
- The analyzer already flags statistics as unreliable below N = 30; surface that flag in the figure, never in the agent's feedback.
- Report both the matched-set median (LLM4MOF's metric, for comparability) and the median of the ≤ 10 *shown* candidates (the quantity the hit-rate/enrichment table already uses, and the one that is budget-honest). Where they disagree, say so.
- Keep D-4 (replicate-collapsed rows) so a "matched set" of 10 is 10 polymers, not 10 measurements of one.

---

## G. Feedback payload and memory ledger

### G.1 Feedback generator — the smallest possible edit

Structure unchanged, in order: ledger block → `*** EXPERIMENT: 4-BEAM DIAGNOSTIC ***` with four tables + chemistry profile + pattern summary + per-beam hint → descriptor profile → diagnostic footer when Beam 1 is empty. What changes:

| Element | Change |
|---|---|
| Table columns | `Structure \| Tg (K) \| Rigidity \| AromFrac \| Ecoh (kJ/cm³) \| FFV \| HBondDens \| MW_RU \| SideChain` (+ `f_A`, `Basis`, `Arch` in copolymer mode) |
| Row describer | `POL-i` / `COP-i`; tag profile `Bkbn:[…] Subs:[…]`; **no name, no SMILES** (D-1) |
| Pattern summary | top-3 backbone families / backbone tags / substituents / features as `name(pct%)`, "Minority (informational, do NOT require as mandatory)", descriptor ranges `min–max (med)`, 500-char cap — all ported verbatim |
| `GEOMETRY PROFILE` block | → `DESCRIPTOR PROFILE OF YOUR CHEMISTRY (observational, not prescriptive)`: min/max/median of the top-5 of Beam 1 (falling back to Beam 2/4), with the same "suggest target_x_min: 0.9 × lo" phrasing; withheld when Beam 1 is empty |
| `Counts[…]` block | ported as-is; driven by `rule_based_counts` from the SMARTS layer |
| Hint sentences | reworded, same logic: "Compare with Beam 2: does your descriptor/composition window improve or hurt?", "If Beam 2 >> Beam 3, your side-group choice is adding value", "If Beam 2 >> Beam 4, your chemistry is better than random" |
| Diagnostic footer | ported; new reasons (backbone family empty / side-group tags empty / window too narrow / composition window empty) |

What is **never** sent, ported verbatim: database identity, record ids, table size, global distribution, percentiles, thresholds, the sensitivity report.

### G.2 Memory ledger — PORT-AS-IS with two renames

`memory_ledger.py` (673 lines) changes in exactly two places: `_GEOMETRY_COLS` → the seven descriptor slot names (+ `f_A` in copolymer mode), and `_struct_label` → `POL-i` / `COP-i`. Everything else is unchanged: `global_best`, top-K frontier (K = 10, deduped by identity), `geometry_envelope` → `descriptor_envelope` (per-slot [min, max, median] over the frontier, slots with zero spread dropped), per-iteration `history[]`, direction-awareness via `LEDGER_DIRECTION` (needed immediately — the Tg-minimisation task is one of the anchor tasks).

Two behaviours must be ported *exactly as the code does them*, not as the SI describes them:

- **The random beam is ingested.** `MemoryLedger.ingest` iterates all four beams to record `beam_medians` and to run the outside-promising detector; only `global_best` / `frontier` / `descriptor_envelope` are restricted to the three hypothesis beams (verified correction to claim C8). Nothing leaks, because `render_facts_only` prints neither `beam_medians` nor `outside_promising`. Port the code, not the prose.
- **`render_facts_only`, never `render_for_agent`.** The legacy prescriptive renderer ("CONCENTRATE… do NOT switch families", "GRAFT it") was found to hurt rare-peak tasks and is not used. Keep it in the tree as a dead ablation arm, as LLM4MOF does.

**The transcript fact that must not be "fixed"** (verified extra finding E4): SI Note S1 claims Agent 1 receives the verbose report only for the immediately preceding iteration while older observations are compressed into the ledger. **The shipped code does no such compression** — `LLMClient(multi_turn=True)` appends every message and re-sends the whole list; there is no trim, window or eviction anywhere, which the SI's own cost note confirms ("the conversational context that must be re-sent grows monotonically", $0.03 → $0.19 per iteration). The ledger is therefore an *addition on top of* an unbounded transcript, and the Note-S11 ablation measures "ledger on top of full history". A port that implements the SI's described design will not reproduce the ablation. S1 ports the code behaviour, documents it in one sentence, and budgets ~$1/campaign accordingly.

**The no-match fact that must not be "fixed"** (verified extra finding E5): SI Note S1 says a zero-match iteration is retried and not counted. That is true only in live mode. In DB mode `run_experiment.py` auto-continues with empty beams and the counter advances, so a no-match iteration consumes one of the ten. With backends at 24.6 % and 34.9 % no-match rates, this plausibly explains much of the 79.5-vs-91.3 backend gap that Table 1 reports without connecting the two. S1 ports the code behaviour and promotes **no-match rate per arm to a first-class reported metric**, as Table 1 already does (2.3 %–34.9 %). Polymer constraints with a narrow composition window will produce a higher no-match rate than MOF constraints; measuring it is part of the result.

---

## H. Metrics, baselines, budget matching

### H.1 Metrics (ported verbatim, plus three additions)

| Metric | Definition | Polymer value available today |
|---|---|---|
| Per-iteration beam median | median of the full matched set, mean ± SEM over replicates, with reference lines at table median / top-10 % / top-1 % | Homopolymer Tg: **410 / 563 / 657 K**; minimisation **410 / 277 / 195 K**. Copolymer collapsed Tg: **333.9 / 463.1 / 619.1 K**. Tm: 461.8 / 613 / 768 K. Density: 1.230 / 1.450 / 1.868 g/cm³ [all computed 2026-09-11] |
| Final-iteration table percentile of the Beam-1 median | Table-1 analogue | — |
| Iterations to top-10 % | — | LLM4MOF reference 3.7–4.8 |
| Hit rate / enrichment | fraction of the **≤ 10 shown per beam per iteration**, pooled over replicates, above the table's top-1 % threshold; enrichment = Beam 1 ÷ Beam 4 | LLM4MOF: 4.3×–18× on eight tasks, 162× on CH₄ where the baseline had 1 hit in 500 (verified C16). **Do not quote a ratio whose denominator is 1** — report the counts |
| No-match rate | share of iterations whose constraints match nothing | first-class, see §G.2 |
| **n per beam per iteration** *(addition)* | — | closes pressure point #5 |
| Human-only sensitivity report | EF@1/5/10 %, one-sided Mann-Whitney vs the total set, top-5/worst-5 means, unreliable flag below N = 30 | unchanged |
| **Composition-slope diagnostic** *(addition, copolymer only)* | median \|Spearman ρ(target, f_A)\| within matched polymer ids | reference set 378 ids, median \|ρ\| 0.868 |
| **AUC over iterations, memorisation share, replicate σ** *(aide2 additions)* | (NF − 50)/(V0 − 50); σ of the final percentile | LLM4MOF reference σ 6.4 / 15.9 / 6.9; memorisation 0.44 / 0.44 / 0.72 |

### H.2 Baselines — all five, same evaluator, same reachable pool

| Baseline | Port | Notes |
|---|---|---|
| **Random** | Beam 4 | free |
| **GA** (Note S6) | ported literally: 40 evaluations/iteration × 10 iterations, 5 replicates, 40 random initial, surrogate retrained each iteration on categorical features, population 200, 20 generations, mutation 0.2, top-80 surrogate-ranked submitted, ≤ 40 accepted | Categorical genome: `(monomer_key)` homopolymer; `(key_A, key_B, composition_bin, architecture)` copolymer. LLM4MOF's GA surrogate had held-out R² ≈ 0 — i.e. it was random search with extra steps, which the authors concede. A polymer GA on a 7-descriptor surrogate will be **stronger**, which is good for credibility and bad for the headline. Report it either way. |
| **BO** (Note S7) | latent-variable GP (Comlek), 2-d latent per categorical, ARD-RBF, constant mean, EI; 40 random initial; fixed enumeration | The copolymer track gives BO a genuine continuous input (f_A), so mixed categorical-continuous BO is a *fairer and stronger* baseline than the MOF case. Say so. |
| **Fox equation** *(copolymer only, new)* | 1/Tg = w₁/Tg₁ + w₂/Tg₂ with homopolymer Tg from the XLSX; rank the whole reachable pool, take top-40/iteration | Published PoLyInfo-copolymer reference: **R² 0.835 / RMSE 42.6 °C** (vs 0.921 / 24.45 °C for the best GNN). The audit's own linear-mixing test gives median \|ΔTg\| ≈ 14 °C when composition is correctly bound. This is the domain-knowledge baseline LLM4MOF never had and the one a polymer reviewer will demand. |
| **Group contribution** *(new)* | van-Krevelen Tg from the group tables; rank the pool | In-sample MAE ≈ 10 K, out-of-sample R² 0.71 (Roy 2026: GC 0.71 vs single-LLM 0.67 vs ChemCrow 0.66 vs their agent 0.78). Must be coded from REF-113/146 — no pip package exists. |
| **polyBERT-guided** *(optional)* | embeddings + GP/GBDT trained on N revealed labels, used to rank | Tg RMSE 37.9–38.4 K. CPU inference only (no CUDA torch). Licence: GTRC academic-research-use; read it before download. Optional because it is the only baseline that needs an external model and a licence decision. |

### H.3 Budget-matching protocol

Port LLM4MOF's definition exactly — **a "label" is a property value revealed to the optimiser**, nominal cap 400 per campaign (10 shown × 4 beams × 10 iterations) — and then fix the two accounting problems the aide2 review found, because both are free to fix and both will be raised by a reviewer:

1. **Report realised counts per arm, not nominal.** LLM4MOF realised GA 327–368 and BO 212–265 against a nominal 400, and counted the shortfall against the baselines. Every arm reports realised labels, and any arm below 90 % of nominal is re-run or flagged.
2. **Report the free work.** In DB mode, filtering the table touches every row; the matched set can be 9,533 rows while only 10 are revealed. LLM4MOF's own "label accounting" excludes property-agnostic pre-training for every method including its own geometry surrogate. S1's statement: **the loop reads zero property values outside the 400 revealed; the analyzer reads the whole table but only to compute human-only statistics that are never fed back.** That is auditable and should be audited — add an assertion that the feedback string never contains a property value outside the sampled rows.
3. **State the LLM budget too**: 20 calls, ~0.55 M tokens, ~$1 per campaign, disclosed alongside the label budget. LLM4MOF's Note S8 does this; keep it.

---

## I. How the audit's defects constrain this strategy

This section is binding. Every item below changes what the hidden table *is*.

| Defect | Severity | Binding constraint on S1 |
|---|---|---|
| **D1 — composition/component order swap.** `composition_i` belongs to `component_i`, never to `smiles_i`. Row classes: aligned 15,409, swapped 2,221, half_aligned 5,309, half_swapped 881, neither 433, one_id 190, no_ids 18,114. ~30 % of resolvable rows are swapped. The Tg linear-mixing test on swapped rows gives 13.7 °C error under component binding vs 56.8 °C under SMILES-slot binding. | S1 | **The copolymer hidden table may contain only rows with `binding ∈ {by_component_majority, by_position_aligned_only}`.** Building it by column position gives a sign-flipped composition effect on a third of the rows, which would corrupt the composition window, the Fox baseline, the composition-slope diagnostic, and every dominant-component rule. The 5,309 half_aligned rows are *excluded*, not guessed — the mixing test there actually favours the reverse binding (23.4 vs 15.4 °C), so they are worse than random. |
| **D4 — replicates and duplicates.** 56.3 % of Tg rows in replicate groups (SD median 7.0 °C, p90 33.1, p99 120); 6,548 exact duplicates except `sample_id`. | S2 | Deviation **D-4**: the table is replicate-collapsed. Removing exact duplicates leaves **36,009 rows**; Tg rows fall 18,142 → **17,346**; grouping to (polymer_id, comp1, comp2) gives **10,249 groups** [computed 2026-09-11]. Splits and "beam sets" are over groups. **Beam separations below ~7 K are inside the measurement noise and must not be claimed.** |
| **D5 — 42.6 % of rows have no composition** (18,116 rows; 3,323 of 7,385 ids never have one; 1,878 of 4,578 Tg-bearing ids never have one). | S2 | If Beam 4 could draw from composition-less rows that Beam 1 can never reach, Beam 1 would be structurally handicapped. **The copolymer hidden table is therefore defined as the composition-parsed, both-monomers-matched core (6,917 rows / 1,381 ids), and all four beams filter that same object** — LLM4MOF's `build_canonical_db.py` principle ("the hidden table is restricted to what the proposer can reach"), applied deliberately and disclosed, instead of silently as in the MOF paper. |
| **D6 — terpolymers truncated to two slots**, 4,243 rows / 548 ids conservative (7,389 / 1,320 liberal); `component3..5` empty; `x`/`N−x` compositions are the algebraic residue of a dropped third unit; 4,023 rows sum below 99. | S2 | `truncated_flag` rows are **excluded** from the copolymer table. A two-component composition that sums to 84 is not an error to be normalised — it is a third monomer the table cannot represent. |
| **D10/D11 — structure identity and same-monomer pairs.** 116 attachment-point variants; the ring-closing "periodic" key falsely merges 5 XLSX + 2 CSV + 1 cross-file pair; `smiles1 == smiles2` in 3,952 rows / 713 ids (4,756 at key level); 386 rows / 27 ids carry a homopolymer name. | S3 | Primary key is the **trimer ring-closed key** (which separates every known false merge), with `stereo_canon` as a linked variant. `same_monomer_flag` rows are **excluded** from the copolymer table — they are homopolymers wearing a copolymer id and would let Beam 1 win trivially on a "copolymer" task. |
| **D2/D3 — encoding and electrical strings.** UTF-8 with 3 damaged sequences (not cp949; a cp949 read mangles 16 cells); P908185 swallows two records and P908186 is lost; `1/(ohm*cm)` makes a greedy regex read `2e-16` as `2e-161` in 2,061 of 4,048 strings. | S1 | Loader rules §3.4 of the audit, in order, with invariants I1/I2/I7 as hard gates. Electrical properties, if ever used as a task, are log₁₀ of one column, not two. |
| **D8/D15 — units and outliers.** `Elongation_at_break_GPa` is percent; XLSX Tg/Tm in K, CSV in °C; 78 CSV rows have Tg > Tm; 91 XLSX duplicate-structure groups with 30 conflicting Tg (max spread 169 K). | S2/S4 | Everything stored in SI (K) with `unit_assumed` flags where the audit could not confirm; invariants I17–I19 run before the table is emitted. The 30 conflicting groups need a user decision (§L-6). |
| **D13 — `copolymer_type` semantics.** 27.7 % multi-tag; 49.0 % are the single tag `['unspecified']`; 4,033 rows carry `alternating` without `-alt-` in the name. | S3 | Architecture is a **multi-label** tag family, not a class. `unspecified` is dropped from multi-tag lists and treated as "unknown", never as a value the agent can require. Any architecture-conditioned claim is restricted to the rows where name and tag agree, and the count is reported. |
| **D16 — `copolymer.zip` is entirely NUL bytes.** | S1 (scope) | Whatever it held is unavailable. Nothing in S1 depends on it; re-obtaining it (§L-8) would enlarge the copolymer table but is not on the critical path. |

### I.2 Licensing — four binding constraints

PoLyInfo/MatNavi Terms Art. 9.2 license the data "only for use by themselves"; Art. 10(1)–(3),(5) prohibit copying, derivative use, distribution, redistribution of "the DATA or Processed DATA", and bulk acquisition. The sole carve-out is "publication of deliverables of research and development". Consequences that change the repository's shape from commit 1:

1. **The hidden tables can never be committed.** LLM4MOF ships `hmof_index.json` (66 MB) and `qmof.csv` (21 MB) in its public repo; LLM4POL cannot ship the equivalents. The repo must have a git-ignored `data/` plus `data/MANIFEST.sha256` and a `scripts/build_indexes.py` that regenerates them from the user's own local export. Design this at M0, not later; retrofitting it after a commit is a history-rewrite.
2. **`source_data/` can carry aggregates only.** Beam medians, percentiles, counts, hit rates and enrichment are statistics (fine). Per-structure property values are DATA (not fine). LLM4MOF's Table-S1-style "representative best structure with its measured value" reveals one datum per task — nine data points may be de-minimis but it is the user's call (§L-2).
3. **What the agent sees is what leaves the machine.** D-1 (no names, no SMILES) exists partly for this. After D-1, what a hosted API receives per iteration is: anonymous labels, vocabulary tags, and numeric descriptors computed from structures — arguably Processed DATA, and still a decision the user must take (§L-2).
4. **The vocabulary and the descriptor definitions are publishable.** The PoLyInfo *ontology* is CC BY 4.0 even though the data is not, and RDKit SMARTS and van-Krevelen tables are ours or the literature's. So the releasable artefacts are: the code, the vocabulary JSON, the SMARTS library, the descriptor definitions, the prompts, the reasoning traces (after name suppression), and the aggregate source data. **The loop trains nothing**, so there is no weights-licensing question at all — LLM4MOF's abstract claim "not a single property-labeled training structure" transfers verbatim and is, here, also a legal asset. Only the baselines (GA surrogate, BO GP, GC, polyBERT head) train on the data, and none of them needs to be released.

---

## J. Component map

Verdicts: **PORT-AS-IS** (copy, rename strings) · **ADAPT** (keep the shape, replace the domain content) · **REPLACE** (a polymer-specific module takes its place) · **DROP** · **NEW**.

| LLM4MOF component | Polymer equivalent | Action | Rationale |
|---|---|---|---|
| **Agent 1** (`agent1_handler.py`, 242 l.; `agent1_v3.0_production.md`) — stateful, multi-turn, T = 0, 8-field JSON of which 4 validated | Same handler, same 8 fields, same 4 validated; prompt toolbox swapped: `df/di/vf/sa/density/dif/cv` → the 7 slots; "ditopic linkers only" and "do NOT select a topology" → "repeat-unit chemistry only" and "do NOT name a specific polymer"; axis menu (pore geometry / decoration / electronic structure) → (descriptor window & composition / side-group decoration / backbone family) | **PORT-AS-IS** (handler) + **ADAPT** (prompt) | The handler is domain-free. The prompt's skeleton — stateless-execution rule, stagnation trap → exploration phase (≥ 3 untried families, ≥ 2 new branches), COMMIT-to-REDUCE, READ-THE-EVIDENCE, first-iteration-no-numbers — is the behavioural contract that makes the beams interpretable and must survive. Note the coupling honestly: the prompt dictates the decision procedure, and a reviewer can ask how much of the "design rule" is the prompt's (pressure point #12). |
| **Agent 2** (`agent2_handler.py`, 345 l.; `agent2_v4.1.md`, 336 l.) — stateless, T = 0, soft validation (only 3 top keys + `metals_include` hard) | Same, `metals_include` → `families_include`; `{DATABASE_MODE_RULES}` becomes `HOMOPOLYMER_MODE_RULES` / `COPOLYMER_MODE_RULES` | **ADAPT** | Statelessness at T = 0 is what makes the constraint translation reproducible given a hypothesis. The mode-rule injection point already exists for exactly this purpose. Keep default-permissive semantics and the structured-error halt (E9). |
| **Controlled vocabulary** (124 tags / 10 categories / 215 aliases / 105 SMARTS; `unified_vocabulary.json`) | ~114 polymer tags / 10 categories / ~200 aliases / ~100 SMARTS; seeded from PoLyInfo ontology (CC BY 4.0), HAPPY/FORGE subgroups, PolyBench-LLM descriptors, RDKit SMARTS | **REPLACE** (content) + **PORT-AS-IS** (machinery: `canon`, alias map, `TAG_HIERARCHY`, backbone/substituent split, `rule_based_counts`) | `constraint_utils.py` (686 l.) is entirely domain-free once the JSON is swapped. Delete only the PORMAKE coordination-tag handover and `strip_coordination_tags_from_branches`. No published polymer counterpart exists (landscape §5) — this file *is* a contribution. |
| **Matchmaker** — PORMAKE assembly path (`matchmaker.py`, 668 l.) | — | **DROP** (Phase 1) | Virtual assembly of node × edge × topology has no Phase-1 polymer analogue; its Phase-3 analogue is SMiPoly/OMG enumeration. Keep the file unimported as the Phase-3 template (the five-phase structure — topology filter, node search, linker search, virtual assembly, categorized filter — maps onto polymerization-rule filtering). |
| **Matchmaker** — record path (`hmof_matchmaker.py` 341 l. / `qmof_matchmaker.py` 225 l.) | `copolymer_matchmaker.py` / `homopolymer_matchmaker.py`; `search_mode ∈ {full, backbone_only, sidegroup_only}` | **ADAPT** | This is the real port target. Tag AND/OR/exclude + numeric ranges + `search_mode` is already exactly the polymer requirement; only the field names change. |
| **Building-block library** (518 nodes, 156 linkers, with metadata) | The monomer table: 4,792 unique CSV monomer SMILES (4,782 RDKit-valid, 4,666 distinct backbones after `*` removal) + 13,624 XLSX repeat units, keyed by trimer key | **REPLACE** | Same role (the atoms of the design space), different construction: derived from the data rather than curated for assembly. |
| **Topology library** (952 single-node topologies, `pormake_topo_dictionary_v3.json`, `sim_safe_topologies.py`) | Architecture tag set (homopolymer / random / statistical / alternating / block / graft / periodic) | **REPLACE** (7 tags for 952 topologies) | Chain architecture is the only structural degree of freedom above the repeat unit that the data carries. It is categorical and tiny, so it lives as a tag in `global_requirements`, not as a separate library. |
| **hMOF / QMOF / CoRE** | copolymer sample index / homopolymer index / — | **ADAPT** / **ADAPT** / **DROP** | §C.1. CoRE is not a campaign database in any shipped run. |
| **MOF2Zeo** (`core/mof2zeo/*`, `filter_candidate.py` 840 l., 78 MB ckpt, torch + lightning) | — in Phase 1. In a gated live mode: a GBDT Tg/density surrogate used to pre-rank Beam 1 only, with an MAE-expanded window | **DROP** (Phase 1) / **NEW** (Phase 3 only) | LLM4MOF does not use MOF2Zeo in DB mode either. Its role is triage before assembly; there is no assembly. Dropping it also removes the torch dependency, which matters because no environment on this machine has a CUDA torch. |
| **Zeo++ descriptors** (`di, df, sa, vf, density, dif, cv`) | the 7 RDKit / van-Krevelen slots of §D.2 | **REPLACE** | Both are deterministic, offline, non-target structural descriptors — the same epistemic status. This is the correct analogue, not MOF2Zeo. |
| **Four diagnostic beams** (`sensitivity_analyzer.run_analysis`, sets A…S + Z + total) | Same four beams, redefined per §F.1; extra human-only sets gain a composition-only and a chem+composition set | **PORT-AS-IS** (structure) + **ADAPT** (column names, D-2 inclusive bounds) | The beam construction is the contribution. The only code change is which columns the numeric gate reads and `<` → `<=`. |
| **Sampling strata** (`sampling_strata.py` 160 l., metal round-robin, identity-only, target never read) | `backbone_class_of()` (homopolymer) / `polymer_id_of()` (copolymer) | **ADAPT** (D-5) | Config calls stratification "the only fully cross-app-validated universal lever" and the SI credits it as "the primary mechanism for raising the absolute performance ceiling". The copolymer key change additionally prevents pseudo-replication. OLD's multi-key `STRATA_MODE` (metal / uniform / pore_quartile / topology / edge) ports as an ablation axis. |
| **Memory ledger** (`memory_ledger.py` 673 l.) | Same; `_GEOMETRY_COLS` and `_struct_label` renamed | **PORT-AS-IS** | Verbatim, including the random-beam ingestion for `beam_medians` and the `render_facts_only` choice. §G.2. |
| **Feedback generator** (`feedback_generator.py` 910 l.) | Same structure; columns, row describer, pattern keys and hint sentences rewritten; `readable_name` suppressed (D-1) | **ADAPT** | The assembly order and the target-blindness rules are the contribution; every English sentence is MOF-specific. |
| **`feedback_live_adapter.py`** (245 l., oracle results → beam DataFrames) | Kept unused in Phase 1 as the seam for any future oracle | **ADAPT** (Phase 3) | This is the correct insertion point for an MD oracle; nothing else needs to know where numbers come from. |
| **Oracle: PORMAKE → LAMMPS/UFF → Zeo++ → RASPA3 GCMC** (5,000 + 5,000 cycles, 12.8 Å cutoff, 380 ± 2 runs/campaign) | **Phase 1:** the measured property in the hidden table (table lookup, 0 simulations). **Phase 3 (gated):** RadonPy/LAMMPS MD on ≤ 10 finalists, calibrated | **REPLACE** | §E. The MD arithmetic (4,000–20,000 CPU-h/Tg candidate, +40–120 K offset) forbids an in-loop oracle by four orders of magnitude. |
| **HPC runner** (`run_live_experiment.py` 1,988 l., `hpc/run_mof_sim.py` 949 l., `prepare_batch.py`, `collect_results.py`, `submit_iteration*.sh`, PBS-over-SSH) | Unused in Phase 1; in Phase 3 the *contract* (manifest → per-job JSON + `.DONE` → aggregate → adapter) is reimplemented behind the hpc-submit skill's mandated `config/hpc.json` + `scripts/submit.py` | **ADAPT** (contract) / **DROP** (body) | The job-array contract is a clean, reusable pattern (verified C24) and dirac is also PBS. The MOF simulation body is worthless here, and the NEW clone's live runner does not even import. |
| **GA baseline** (Note S6) | Same protocol; categorical genome over monomer keys / (pair, composition bin, architecture) | **ADAPT** | Same evaluator, same pool, same budget. Expect a *stronger* GA than LLM4MOF's (whose surrogate had R² ≈ 0). |
| **BO baseline** (Note S7, LVGP + EI) | Same, plus f_A as a genuine continuous dimension in the copolymer track | **ADAPT** | Mixed categorical-continuous BO is a fairer baseline than the all-categorical MOF case. |
| **Fox / group-contribution baselines** | Fox 1/Tg = Σ wᵢ/Tgᵢ (copolymer); van-Krevelen Tg (both tracks) | **NEW** | Mandatory domain baselines with published numbers (Fox R² 0.835 / RMSE 42.6 °C on PoLyInfo copolymers; GC out-of-sample R² 0.71). LLM4MOF had no domain-knowledge baseline; a polymer reviewer will require one. |
| **polyBERT-guided baseline** | embeddings + GP/GBDT ranking | **NEW** (optional) | Tg RMSE 37.9–38.4 K; CPU-only; GTRC academic licence must be read first. |
| **EGMOF generative comparison** | polyBART / POLYT5 / PolyTAO / CharRNN-RL as a label-demand comparison | **DROP** (Phase 1) | LLM4MOF's own note says the halves "are never compared numerically" because they use different oracles. A polymer version has the same problem and no shared evaluator. Defer. |
| **Evaluation protocol** (10 iterations, 5 replicates, hidden-table percentiles, hit rate/enrichment, ablation-one-at-a-time, label accounting) + OLD's battery driver (`run_battery.py` 233 l., `parse_results.py` 213 l., `--seed`, `--no-feedback`, `arms_*.json`) | Same, with D-3 (10 replicates for headline arms), n-per-beam reporting, and D-6's three controls | **PORT-AS-IS** | This is the most valuable single artefact in the OLD clone and the thing LLM4MOF's own public repo lacks. It is what makes the statistics credible. |
| **Backend benchmark** (6 backends × 7 tasks × 5 replicates, Agent 2 pinned, first attempt only) | 4–6 backends × 5 tasks × 5 replicates, Agent 2 pinned, first attempt only | **PORT-AS-IS** | Directly transferable and cheap (~150 campaigns ≈ $160). **But `llm_client.py` has only openai and gemini branches and never references claude or `agent_backend` (verified C18) — the Claude arms of Table 1 were produced by a client not in the repo. The Anthropic branch must be written.** Also fix the `LLM2POR_*` vs `LLM4MOF_*` env-toggle mismatch (verified C19) before any reproducibility claim. |
| **`config.py`** (840 l.) | Same skeleton; metric/unit registry → Tg K, Tm K, density g/cm³, log₁₀σ; adsorbate registry, HPC block, RASPA block deleted | **ADAPT** | Keep the provider block, env toggles, experiment-dir layout, cost logging and the direction-aware metric registry (needed immediately for Tg-minimisation). |
| **`run_experiment.py`** (675 l.) | Same loop; keyword→database routing replaced by property+track routing | **ADAPT** | The loop skeleton is exactly what is needed. Take OLD's `--seed` / `--no-feedback` / `FEEDBACK_SAMPLE_SIZE` additions. |
| **`name_resolver.py`** (125 l.) | Deleted in the agent path (D-1); a human-side resolver for reports only | **REPLACE** | Names never reach the agent. |
| **`database_construction/` pipelines** (`5_shared/smarts_library.py`, `4_vocabulary/04_build_vocab_mapping.py`, LLM enrichment that writes display-only fields) | `build_polymer_indexes.py` + `build_polymer_vocabulary.py` on top of the audit's §3.4 loader and §4 validator | **ADAPT** | The two-layer philosophy (deterministic facts + deterministic SMARTS drive filtering; LLM writes only display fields) is directly reusable and is what keeps the pipeline auditable. |
| **`scripts/build_canonical_db.py`** (61 l., pre-filters tables to the reachable set) | `build_reachable_table.py`, with before/after counts published | **ADAPT** | The idea is right and S1 does it deliberately and discloses it, instead of silently. |
| **`requirements.txt`** | pandas, numpy, scipy, python-dotenv, requests, openai/anthropic + rdkit for the offline build | **ADAPT** | DB mode needs six pure-Python packages plus rdkit. Drop torch, lightning, pormake, ase, lammps-interface, PACMAN-charge. |

---

## K. Milestones and exit criteria

Parallel-safety is marked **∥** (can run concurrently with the milestones listed) or **seq** (blocking).

| # | Milestone | Measurable exit criteria | Parallel |
|---|---|---|---|
| **M0** | Repository, loader, validator | Repo exists outside Dropbox with `data/` git-ignored + `MANIFEST.sha256`; loader reproduces **42,557 rows, exactly 9 U+FFFD, 7,385 polymer_ids, 13,725 XLSX rows, 13,624 unique CanonSMILES**; all 27 audit invariants evaluated, every **hard** one passing, every **warn** one counted; single `check.py` gate green | **seq** — everything depends on it |
| **M1** | Fork, rename, smoke-test on MOFs | Fork of `f1d731a` with MIT header preserved; `UNIFIED_VOCABULARY_PATH` fixed; Anthropic branch added to `llm_client.py`; env toggles unified; **one 3-iteration hMOF campaign completes on the original data**, 6 LLM calls, `beam_data.csv` written | ∥ M2, M3 — proves the harness before the domain is touched |
| **M2** | Descriptor layer + vocabulary | 7 descriptors computed for 13,624 XLSX + 4,792 CSV structures; RDKit failures ≤ the known 10; vocabulary ≥ 100 canonical tags / ≥ 150 aliases / ≥ 80 SMARTS; **≥ 95 % of structures carry ≥ 3 tags**; `TAG_HIERARCHY` propagation implemented and unit-tested; **supervised-shortcut probe run and its OOF R² recorded** | ∥ M1, M3 |
| **M3** | Hidden tables | Homopolymer Tg index (7,699 structures) and copolymer Tg index (composition-parsed core, replicate-collapsed) emitted; reachable-set counts published before/after tag filtering; thresholds frozen (**410 / 563 / 657 K** homopolymer; **333.9 / 463.1 / 619.1 K** copolymer); zero hard-invariant violations; excluded-row counts reported for `binding`, `truncated_flag`, `same_monomer_flag` | ∥ M1, M2 |
| **M4** | Polymer matchmaker + analyzer wiring | `search_mode` returns id lists for all three modes; **set containment Z ⊆ A ⊆ F ⊆ total holds on 20 hand-written constraint JSONs**; a zero-match constraint returns the structured error and fires the diagnostic footer; default-permissive semantics unit-tested on all-null queries | seq after M2 + M3 |
| **M5** | Prompts + first campaigns | 10-iteration homopolymer Tg-max campaign completes with exactly 20 LLM calls and ≤ $1.50; Beam-1 final median above the table median in **≥ 8 of 10 replicates**; wall-clock per campaign recorded and compared with the MOF reference (353 s) | seq after M4 |
| **M6** | Evaluation battery | 4 arms (V0, `--no-feedback`, no-ledger, no-stratification) × 5 tasks (Tg-max, Tg-min, Tm-max, density-max, copolymer Tg-max) × 10 replicates = **200 campaigns**; replicate σ reported **before** any effect claim; memorisation share computed per task; MDE stated; **n per beam per iteration in every figure** | seq after M5; ∥ M7, M8 |
| **M7** | Baselines | Random, GA, BO, Fox, GC (+ optional polyBERT) on the same evaluator and the same reachable pool; **realised label counts reported per arm, every arm ≥ 90 % of nominal 400**; Fox reproduces a PoLyInfo-copolymer R² in the published neighbourhood (0.835 ± 0.05) as a sanity check | ∥ M6 (after M4) |
| **M8** | Mechanism-edit test + backend benchmark | ≥ 6 of 10 mechanical hypothesis inversions move the Beam-1 median in the predicted direction (exact n and sign-test p reported); 4–6 backends × 5 tasks × 5 replicates with Agent 2 pinned, first attempt only; **no-match rate per backend reported** | ∥ M6, M7 (after M5) |
| **M9** | Write-up: Figure-2 / Table-S1 / Table-S2 analogues | Every figure carries n per beam; oracle scope stated per task; hidden-table construction disclosed with before/after counts; licence position stated; `source_data/` contains aggregates only | seq after M6–M8 |
| **M10** | *(Gated)* Live-mode feasibility | Gate: dirac allocation ≥ 50,000 core-h confirmed; RadonPy + LAMMPS + **Psi4** installed on dirac; three published RadonPy densities reproduced within 5 %; measured wall-clock per density candidate. **If any gate fails, Phase 3 does not start and the paper ships as a database-mode result.** | seq; independent of M6–M9 |

Critical path: M0 → (M1 ∥ M2 ∥ M3) → M4 → M5 → M6 → M9. M7 and M8 hang off M4/M5 and are fully parallel. M10 is independent and can be pursued by a different person at any time.

---

## L. Decisions only the user can make

| # | Decision | Why it cannot be settled here | Default S1 assumes if unanswered |
|---|---|---|---|
| **L-1** | **Anchor task and direction.** Homopolymer Tg-max? Tg-min? Copolymer Tg? Tm? A Pareto pair? | Every number in §H is direction-aware and the Agent-1 prompt's axis menu depends on it. | Homopolymer **Tg-max** as the anchor (richest: 7,733 values, cleanest units, strongest literature baselines), with Tg-min as the second task to test direction-awareness. |
| **L-2** | **PoLyInfo release and transmission policy.** Can the vocabulary/descriptors/aggregate source data be published? May anonymised tags + descriptors be sent to a hosted LLM API (Art. 10(1))? May nine representative-best structures be named in a paper? Was the export itself permitted under Art. 10(5)? | The Terms prohibit redistribution and say nothing about models or API transmission; only the owner knows the export history. | Publish code + vocabulary + descriptors + aggregates; **suppress names and SMILES from the agent** (D-1); do not name representative structures until answered. |
| **L-3** | **LLM provider and key.** No API key is set in any scope. GPT-5.2 (maximum comparability with LLM4MOF's Table 1 and cost figures) or Claude (the Claude branch must be written either way, verified C18)? | Not a technical question; it is a budget and comparability choice. | Assume one OpenAI-compatible key; write the Anthropic branch regardless so the backend benchmark can run both. |
| **L-4** | **Fidelity vs the name-suppression deviation (D-1).** LLM4MOF shows readable names; S1 does not. | A pure-fidelity reviewer could object. The counter-argument (leak closure + licence) is strong but it is a judgement call. | Suppress, and run one 10-replicate arm *with* names as an ablation to quantify the cost — which incidentally also measures the memorisation channel. |
| **L-5** | **Replicate budget.** 5 (LLM4MOF-faithful) or 10 (statistically adequate at the measured σ of 6.4–15.9 points)? | Cost is negligible either way; the choice is about what claims are defensible. | 10 for headline arms, 5 for grid cells (D-3). |
| **L-6** | **Data policy decisions the audit lists as owner-only:** the 5,309 undetermined-binding rows (drop vs resolve from a fuller export); the 30 conflicting XLSX duplicate-structure Tg groups (average / keep / drop); cis-trans and tacticity variants (distinct monomers or merged); the 42.6 % composition-less rows. | Preference/policy, no data-internal answer. | Drop undetermined bindings; drop conflicting duplicate groups and report the count; merge stereo variants at the trimer key with `stereo_canon` linked; exclude composition-less rows from the copolymer table only. |
| **L-7** | **Repository location and engineering stack.** LLM4POL is currently a non-git Dropbox folder. Adopt the CALF20 conventions (pixi + `src/` layout + single `check.py` gate + MADR ADRs + GSD per-project with OMC disabled) or LLM4MOF's flat layout? | hpc-submit warns Dropbox file locks corrupt ledgers; CALF20 is the house style and lives on the Desktop. | Repo outside Dropbox; CALF20 conventions; keep LLM4MOF's `experiments/` artefact layout verbatim so the battery parser works unmodified. |
| **L-8** | **Is a fuller PoLyInfo export obtainable?** `component3..5` for the 4,243–7,389 truncated rows, the per-sample component records that would resolve 5,309 bindings, a canonical component-id → SMILES table, a non-corrupt `copolymer.zip`, and the XLSX aggregation rule. | Missing data; no amount of inference recovers a dropped third monomer. | Proceed without; the copolymer table shrinks accordingly and the shrinkage is reported. |
| **L-9** | **Relationship to the LLM4MOF authors.** The repo owner (`kn1218`) and this account are the same GitHub login. Is this a sanctioned port, a companion paper, or an independent submission? | "The same loop, unchanged, transfers" is the paper's central claim; whether that reads as elegance or as self-repetition depends entirely on how the relationship is declared. | Assume sanctioned companion; declare the fork and the MIT provenance in the first paragraph of the methods. |
| **L-10** | **Does Phase 3 (MD validation) and the PFAS Phase 2 of the pre-proposal survive?** | Phase 3 needs a dirac allocation the project does not have. PFAS has **no public SMILES-labelled polymer-adsorbent dataset**: the best structured sets are 457 points on 21 PFAS × 16 polyamide membranes and a 43-PFAS resin screen with bulk descriptors, and the pre-proposal's cited Dangayach 2025 is a *review*, not a dataset. | Phase 3 gated on M10. **PFAS deferred out of S1 entirely** — it is a literature-mining project with a different data foundation, and it would double the scope before the harness is proven. |

---

## M. Risks

| # | Risk | Likelihood | Impact | Concrete mitigation / trigger |
|---|---|---|---|---|
| **R-1** | **The descriptor window is a supervised shortcut.** If GBDT on the 7 slots reaches OOF R² > 0.80 on the Tg table, Beam 1 beats Beam 2 by construction and the "attribution" is a rediscovery of an obvious filter — the polymer twin of the MOF probe that reached OOF R² 0.943 from three geometry columns. | **High** (Tg *is* largely stiffness + cohesion, which is what the slots encode) | Guts the headline | Pre-registered probe at M2, before any campaign. If it fires: restrict the headline attribution claim to the chemistry arms (Beam 2 vs 3 vs 4), report the probe prominently, and consider swapping two slots for less Tg-predictive ones. Decide this at M2, not after M6. |
| **R-2** | **Measurement noise swamps the beam separations.** Within-replicate-group Tg SD has median 7.0 °C and p90 33.1 °C; within-polymer range median 20.2 °C. | **High** | Effects unclaimable | D-4 (replicate collapse) + D-3 (10 replicates) + measure replicate σ before claiming anything. Pre-register the rule: no separation below the p50 within-group SD is reported as an effect. |
| **R-3** | **Memorisation share is higher than in MOFs.** Polymer Tg is textbook knowledge; the MOF band-gap task already showed a 0.72 share because the model knew the chemistry outright. | **High** | Weakens "blind to the landscape" | `--no-feedback` arm at M6 on every task, reported in the main text. D-1 (no names, no SMILES) narrows the channel. If the share exceeds ~0.7, reframe the claim as "the loop adds X points over parametric memory" and report X. |
| **R-4** | **Constraints match nothing too often.** A narrow composition window over a 6,917-row table will produce a higher no-match rate than MOF constraints over 51,163 records; DB-mode no-match iterations are **not** retried and consume one of ten. | **Medium-high** | Wasted iterations, unfair backend comparison | Report no-match rate as a first-class metric (LLM4MOF's own range is 2.3–34.9 %); tune the Agent-2 prompt's "do not guess numbers" rule; keep first-iteration-no-numeric-bounds. Do **not** silently switch to the SI's retry rule, or DB and live modes diverge. |
| **R-5** | **The copolymer table is too small for ten iterations of narrowing.** 6,917 composition-parsed rows over 1,381 ids, less truncated and same-monomer exclusions. Beam 1 can collapse to n = 1–3. | **Medium** | Metric becomes meaningless on that track | Anchor on the homopolymer track (7,699 structures). Report n per beam. Use the analyzer's N < 30 unreliable flag in figures. If Beam 1 medians are routinely on n < 5, report the ≤ 10-shown median as the primary metric on that track. |
| **R-6** | **Binding resolution is wrong for some rows**, flipping the composition effect's sign. The audit resolves ~1,964 of ~2,635 ids by majority vote; 5,309 rows stay undetermined and the mixing test there favours the *reverse* binding. | **Medium** | Corrupts the composition axis | Exclude undetermined rows entirely (§I). Validate against the 378-id monotonicity set (median \|ρ\| 0.868) and the near-homopolymer consistency check (invariant I24, \|Tg − Tg_hom\| ≤ 40 K, currently 56.7 % within 20 °C on N = 254). |
| **R-7** | **Licensing blocks publication of the very artefacts a reviewer will ask to see.** Nature-portfolio reviewers ask for the data behind the figures; the hidden tables cannot ship. | **Medium** | Publication friction | Design M0 around it (git-ignored `data/` + manifest + rebuild script); ship aggregates, vocabulary, SMARTS, prompts, code and traces; state the PoLyInfo constraint in the data-availability statement with the required NIMS acknowledgement sentence; resolve L-2 before submission, not after. |
| **R-8** | **"Same loop, unchanged" reads as incremental** rather than as the point. | **Medium** | Reviewer framing | Lead with the transfer claim plus the three measurements LLM4MOF lacks (mechanism-edit test, supervised probe, zero-feedback floor). The differentiator is not the loop; it is that S1 measures what LLM4MOF asserted. Also lead with the fact that no polymer system performs controlled-arm attribution at all. |
| **R-9** | **Prompt-harness coupling.** The Agent-1 prompt dictates the axis menu, the exploration trigger, the commit-to-reduce rule and the read-the-evidence procedure; several were tuned empirically. A reviewer asks how much of the "design rule" is the prompt's decision procedure. | **Medium** | Interpretability claim | Ship both prompt builds as LLM4MOF does; run one arm with the axis menu removed as an ablation; report that the hint sentences in the feedback tell the agent how to read the beams, so the narrated reasoning partly echoes the harness. Disclose rather than defend. |
| **R-10** | **No API key, no CUDA torch, no git repo, no HPC config.** The project starts from zero infrastructure. | **Low-medium** (all are small tasks) | Schedule | DB mode needs only six pure-Python packages plus rdkit, all present in conda base. Do not let any Phase-1 deliverable depend on the RTX 5050 or on dirac. M0 creates the repo; L-3 supplies the key. |
| **R-11** | **Fork drift and inherited bugs.** The public repo's HEAD cannot import its own matchmaker or live runner; env toggles are misnamed across clones; the Claude backend is not wired; a stale "15-candidate quota" string is sent to the agent in live feedback. | **Low** (all verified and enumerated) | Debug time | Fork the OLD clone (verified to import cleanly and to carry the battery harness); fix the four known defects at M1 and record them in an ADR; add a smoke test that runs a 3-iteration MOF campaign on every CI run so harness regressions are caught against a known-good reference. |
| **R-12** | **Phase 3 never opens**, and the paper is Figure 2 without Figures 4–7. | **Medium-high** (the MD arithmetic is brutal) | Scope of the claim | Decide at M10's gate, early and explicitly. If it fails, the paper is a database-mode transfer study with a measured interpretability test — which is a complete result, and is what the milestone plan is built to deliver regardless. Do not begin M10 work before M6 is done. |

---

## Appendix — numbers used, with provenance

| Quantity | Value | Source |
|---|---|---|
| CSV shape / keys | 42,557 rows × 29 cols; 7,385 polymer_ids; 42,559 physical records; P908186 lost | audit §1.1 [V] |
| CSV unique monomer SMILES | 4,792 (4,782 RDKit-valid; 4,666 distinct backbones after `*` removal) | audit §1.4 |
| CSV Tg | 18,142 rows / 4,578 ids; in K: min 121.8, p50 325.7, p90 456.1, p99 611.1, max 728.1 | audit §1.5; **[computed 2026-09-11]** |
| CSV after exact-duplicate removal | 36,009 rows; Tg rows 17,346; replicate-collapsed groups 10,249 (p50 333.9 K, p90 463.1 K, p99 619.1 K) | **[computed 2026-09-11]** |
| CSV composition | 18,116 rows (42.6 %) have none; mol 16,207 / wt 5,738 / vol 228 / unknown 2,268; 79.6 % of same-basis pairs sum to exactly 100 | audit §1.2 |
| CSV alignment classes | aligned 15,409 / swapped 2,221 / half_aligned 5,309 / half_swapped 881 / neither 433 / one_id 190 / no_ids 18,114 | audit §1.3 |
| Usable copolymer core | 13,350 rows / 2,735 ids (both monomers matched + Tg); 6,917 rows / 1,381 ids with parsed compositions | audit §1.10 |
| Replicate scatter | Tg within-group SD p50 7.0 / p90 33.1 / p99 120 °C; within-id range p50 20.2 °C, 588 ids > 50 °C | audit §1.6 |
| XLSX | 13,725 rows; 13,624 unique CanonSMILES; 7,699 unique structures with Tg | audit §1.8; **[computed 2026-09-11]** |
| XLSX Tg_K | n = 7,733; min 138, p1 195, p10 277, p50 410, p90 563, p99 657, max 768 | **[computed 2026-09-11]** |
| XLSX Tm_K / density | Tm n = 3,696, p50 461.8, p90 613, p99 768; density n = 1,651, p50 1.230, p90 1.450, p99 1.868 | **[computed 2026-09-11]** |
| XLSX duplicate structures | 91 groups, 33 with ≥ 2 Tg, 30 conflicting, max spread 169 K; 2,338 rows (17.0 %) property-free | audit §1.8, §1.9 |
| Architecture tags | `['unspecified']` alone 20,843 rows (49.0 %); alternating 9,346 / random 6,821 / block 6,814 / graft 2,740 / statistical 471 / periodic 10 (exploded); multi-tag 11,779 rows (27.7 %) | audit §1.7 |
| Composition monotonicity set | 378 ids with ≥ 5 same-basis compositions summing 99–101; median \|Spearman ρ\| 0.868 | audit §1.10 |
| LLM4MOF campaign cost | 20 LLM calls (2/iteration; 22 in 2 of 5 replicates), ~0.57 M tokens, $1.06 ± 0.05, 380 ± 2 GCMC | verified C12, E10b |
| LLM4MOF DB-mode wall-clock | 10-iteration campaign mean 353 s (n = 160, median 348, range 247–492) | verified C23 |
| LLM4MOF vocabulary | 124 canonical tags / 10 categories / 215 aliases in the SI (183 built by the loader) / 105 SMARTS | verified C4 |
| LLM4MOF beam set sizes (recorded) | iteration 10: Z 43 / A 257 / F 3,591 / R 9,533; iteration 1: Z 1 / A 1 / F 3 | verified C23 |
| LLM4MOF enrichment | 4.3×–18× on eight tasks; 162× on CH₄ (baseline 1 hit in 500); Beam-1 n 155–473 vs 500 | verified C16 |
| LLM4MOF backend benchmark | 91.3 / 91.3 / 91.2 / 86.7 / 86.6 / 79.5; no-match 2.3–34.9 % | verified C14 |
| aide2 W1 | NF 69.5 / 64.3 / 78.4 vs V0 94.8 / 82.2 / 89.5; memorisation share 0.44 / 0.44 / 0.72; σ 6.4 / 15.9 / 6.9 (n = 10/arm) | verified C20 |
| aide2 probe | PORMAKE H2-vol 100 bar OOF R² 0.943 from vf/sa/density; hMOF CO₂ gives no reward to open metal sites | verified C21 |
| aide2 W2 | 210 campaigns = 42 cells × 5 reps (8 variants × 2 budgets × 3 tasks); no variant beat V0 (max +1.80 σ, Holm p = 1.0) | verified C22 (with the grid correction) |
| LLM4MOF design space | \|D\| = Σ_c n_c·t_c·L = 80,126 × 156 = 12,499,656 — **not** 518 × 156 × 952 | verified E1 |
| MD Tg cost / offset | 4,000–20,000 CPU-h/candidate; +79.1 K (Afzal), +105.02 K (Martí), 80–120 K (Gudla & Zhang), +38 to +47 K (PolyJarvis); ≥ 10 replicates for CI < 20 K (Suter) | REF-104/105/106/102/110 |
| MD density | 300–2,000 CPU-h; R² 0.890 vs PoLyInfo on 1,001 polymers | REF-101 |
| Fox / GC baselines | Fox R² 0.835 / RMSE 42.6 °C on PoLyInfo copolymers (vs 0.921 / 24.45 for WCS-GCN); GC in-sample MAE ≈ 10 K, out-of-sample R² 0.71 | prior-art REF-26; REF-115/125 |
| Enumerated libraries | SMiPoly 22 rules / 1,083 monomers → 169,347 polymers (BSD-3); OMG 17 reactions / 77,281 reactants → ~12 M CRUs (GPL-3) | REF-117, REF-116 |
| Environment | i5-14600K 14P/20L, 31.7 GB RAM, RTX 5050 8,151 MiB, **no CUDA torch anywhere**; conda base py3.13.9 with pandas 2.3.3 / numpy 2.3.5 / scipy 1.16.3 / sklearn 1.7.2 / rdkit 2025.9.6; **no API keys set**; dirac PBS via hpc-submit, GPU availability unknown | audit §5 |
| LLM4MOF licence | MIT, Copyright (c) 2026 Nam Kyung-min | verified on disk |

**Corrections carried from the verification packets and deliberately honoured in this strategy:** the design space is the connectivity-matched sum, not the plain product (E1); the ledger ingests the random beam for `beam_medians` and the outside-promising detector but not for the frontier (C8 correction); the multi-turn transcript is never compressed, so the ledger is an addition on top of unbounded history (E4); DB-mode no-match iterations are not retried (E5); the Claude backend is absent from the shipped client (C18); the aide2 W2 grid is 42 cells × 5 reps, not 14 × 3 × 2 (C22); the SF6 "7.7 vs 2.8" headline pair mixes an iteration-10 statistic with a pooled reference (E7) — S1 fixes its own estimator per metric and states it.

**Landscape citation corrections adopted:** REF-112's first author is Karuth, not Alesadi; REF-134's sole author is Miccio; REF-105's R² 0.83 belongs to the ML surrogate fit on MD values, not to MD-vs-experiment agreement; REF-137 (Dangayach 2025) is a review, not a PFAS dataset — the pre-proposal's §3 description of it is wrong and is not repeated here; REF-140's mechanism is inverted in the landscape text (electrostatics/H-bonding drive short-chain PFAS, fluorophilicity drives long-chain); REF-141 is unverifiable at the cited URL and exists under a different title in Energy & Environmental Materials 2026.
