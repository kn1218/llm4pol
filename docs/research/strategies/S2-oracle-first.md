# S2 — ORACLE-FIRST: porting LLM4MOF to polymers by sizing the loop to the physics budget

**Strategy name:** Oracle-First LLM4POL — *a two-tier physics ladder with a pre-registered MD audit, driven by a generated copolymer space*
**Written:** 2026-09-11 · **Status:** one of N competing strategies; input to the LLM4POL foundation proposal, not an approved plan
**Inputs read in full:** `llm4mof/LLM4MOF-ANATOMY.md` (+ its fact-check packet, 25 claims: 22 confirmed / 3 refuted, 11 extra findings), `landscape/POLYMER-LANDSCAPE.md` (+ its citation-check packet, REF-101..153: 48 confirmed / 4 refuted / 1 unverifiable, 21 extra findings), `audit/DATA-FOUNDATION-REPORT.md` §§1,2,3,5,6,7,8, `LLM4Polymer_Research_Proposal.md` v1.0.
**Arithmetic:** reproducible in `scratchpad/oracle_budget.py` and `scratchpad/space.py` (both written by this lane, read-only w.r.t. all source data).

---

## 0. The thesis, in one page

LLM4MOF's epistemics rest on a fact that does not survive the port: **its ground truth is cheap, deterministic, and fully specified by the candidate.** RASPA3 GCMC on a UFF-relaxed PORMAKE frame costs ≲2 h of one core, has no run-to-run noise beyond MC sampling, and 380 ± 2 of them fit in a $1.06 campaign (SI Note S8; confirmed C12, recomputed from `figure6_token_usage_and_cost.csv`: GCMC 376/381/379/386/378, cost 0.877–1.140 USD). Everything else in the paper — four beams, ten iterations, five replicates, six backends, Table S2 enrichment — is downstream of that one cheap oracle.

In polymers there is no such oracle. The all-atom MD analogue of one GCMC run costs, on the numbers below, **288 core-h for a single-replicate density/free-volume measurement and 1,997 core-h for a 3-replicate Tg** at a 3,600-atom cell, rising to 1,065 / 7,395 core-h at 10,000 atoms. A literal port — 380 target evaluations per campaign, 5 replicates, 4 tasks — costs **356 to 9,147 days on 256 cores**. It is not a budget problem to be optimised around; it is a different science.

Worse, the cheap substitute is poisoned. If the inner-loop oracle is an ML surrogate trained on the same PoLyInfo Tg table the matchmaker filters, the loop is a closed circle with no ground truth anywhere in it, and the aide2 probe already showed what happens even when there *is* a physics oracle: a gradient-boosting model recovers 94.3 % of the PORMAKE H2-100 bar table (OOF R² = 0.943) from three geometry columns, and the celebrated hMOF CO₂ "open-metal-site pivot" is an artefact of the oracle's labels, not a chemical discovery (confirmed C21; OMS median 4.49 < non-OMS 5.14). A polymer reviewer will ask one question — **"is the property real?"** — and a surrogate-in, surrogate-out loop has no answer.

**So invert the design order.** Fix the oracle ladder first; derive the loop size, the beam definitions, the metric set and the claim set from what the ladder can actually pay for. Concretely:

| | |
|---|---|
| **Loop tier (free)** | T0 analytic (van Krevelen group contribution + Fox) and T1 ML surrogate + PolyNet-G descriptor surrogate. Runs every iteration, all four beams, ≤10 candidates shown each. Produces the beam plots and the attribution narrative. **Never produces a reported number.** |
| **Physics tier (paid)** | T2 MD measures the *descriptor gate* (ρ, CED, FFV, C∞) — 8 runs/iteration, 4 from Beam 1 and 4 from Beam 4, paired. T3 MD measures the *target* (Tg, 3 replicates) on a **pre-registered 30-candidate audit** drawn 10 Beam-1 / 10 Beam-4 / 10 max-disagreement, written into the campaign manifest *before* any job is submitted. |
| **Campaign cost** | 80 × 288 + 30 × 1,997 = **82,905 core-h ≈ 13.5 days on 256 cores**; five replicates ≈ 68 days; two replicates ≈ 27 days. |
| **Headline claim** | not "LLM4POL finds high-Tg polymers" but **"the median calibrated MD Tg of the full-hypothesis beam's audit sample exceeds the random beam's by Δ K (Mann–Whitney one-sided, n = 10 vs 10, per-candidate CI ± ~40 K from 3 replicates)"** — a physics-measured effect, not a table look-up. |

Three structural consequences follow immediately, and they are what makes this a *strategy* and not a re-skin:

1. **Candidates are generated, not pool-selected.** With MD as the truth channel there is no reason to restrict proposals to 7,385 PoLyInfo polymer ids — and every reason not to, since PoLyInfo entries are exactly what a pretrained LLM has memorised (aide2 measured memorisation share 0.44/0.44/**0.72** on MOFs with no feedback at all; confirmed C20). The design space is a mechanism-matched enumeration over monomer pairs × composition grid × architecture, built on SMiPoly/OMG templates so that synthesizability holds by construction — the exact role PORMAKE's 518/156/952 curated library plays.
2. **The gated descriptor must be recomputed by the oracle, never predicted at gate time.** This is the one thing LLM4MOF got exactly right and it is the whole reason the method is not circular: MOF2Zeo predicts geometry for *triage*, Zeo++ recomputes it for *gating*, RASPA measures the *target* (confirmed C10, "all gating uses recomputed Zeo++ values"). The polymer mapping is exact if and only if the gate is a physical descriptor vector **G = (ρ, CED, FFV, C∞)** that T2 MD recomputes — not a predicted Tg. Gate on predicted Tg and the gate *is* the oracle, and the four beams measure nothing.
3. **The "label-free" claim cannot be ported as stated and must be earned differently.** LLM4MOF claims "not a single property-labeled training structure" (Manuscript abstract). A T1 surrogate trained on 7,733 PoLyInfo Tg labels breaks that. Either drop the claim, or run the headline configuration with **T0-only in the loop** (group contribution + Fox: analytic, zero fitted PoLyInfo labels) and keep T1 as a stronger comparison arm. This strategy recommends the second: it is the single cheapest way to make the port *more* defensible than the original.

---

## 1. (a) The scientific question, and what "interpretable inverse design" means for polymers here

### 1.1 The question

> **Can a language-model agent, given only a natural-language objective and no property labels, propose copolymer compositions whose advantage over random search is confirmed by independent all-atom molecular dynamics — and can the mechanism it claims be attributed to a specific design axis by controlled comparison rather than asserted?**

The two halves are deliberate. The first half is the **falsifiability** half and is where the oracle-first angle bites: LLM4MOF's discovery-mode advantage is measured with the same RASPA pipeline that ranks the candidates, which is fine because RASPA is the ground truth; ours must be measured by a channel that the loop did not use to select. The second half is the **attribution** half, and it is the part with no polymer precedent at all — of the twelve 2024–2026 polymer agents and generative systems surveyed (Polymer-Agent, PolyFusionAgent, PolySea, PolyJarvis, POLYT5, polyBART, PolyTAO, Zhou 2026, Roy 2026, Vogel VAE, Kim 2021 GA, Huang MOEA), **none runs controlled comparison arms**; interpretability is uniformly post-hoc SHAP / attention / Integrated Gradients (REF-131…136).

### 1.2 What "interpretable" means — an operational definition, because LLM4MOF's is not one

LLM4MOF's interpretability is asserted, not measured: the evidence is three narrated trajectories and beam-separation plots, there is no metric of explanation quality, and the feedback text literally instructs the agent how to read the beams ("If Beam 2 >> Beam 3, your linker choice is adding value"), so the "reasoning" partly echoes the harness (anatomy §5.1, §5.12). A polymer port that inherits this inherits the weakest part of the paper.

In this strategy, **a design rule is interpretable if and only if all four of the following hold**, each of which is a computed number in the artefact set:

| Criterion | Test | Passing value |
|---|---|---|
| **I1 — Attributable** | The claimed axis shows a beam contrast larger than the replicate noise band, with *n* per beam reported: Δ(Z−A) for the gate, Δ(A−F) for the comonomer/side-group chemistry, Δ(F−R) for the backbone commitment | \|Δ\| > 2× the table's replicate-SD band (7.0 K median, 33 K p90) and > 1 SEM over ≥5 campaign replicates |
| **I2 — Not a shortcut** | A supervised probe fit on the *gated descriptors alone* does not already explain the hidden table (the aide2 obvious-filter probe, pre-registered) | report OOF R²; if > 0.90 the "rule" is the descriptor table and the paper must say so, as LLM4MOF did not (C21) |
| **I3 — Not memorised** | Zero-feedback arm (`--no-feedback`) and floor-corrected memorisation share (NF−50)/(V0−50) | reported, not thresholded; MOF values were 0.44/0.44/0.72 (C20) and polymer Tg is more memorisable, so this is the load-bearing control |
| **I4 — Physically real** | The rule survives the T3 MD audit: the calibrated MD Tg of the Beam-1 audit sample beats the Beam-4 audit sample, and the descriptor the rule names moves in the predicted direction in the T2 measurements | Mann–Whitney one-sided p and effect size, with the per-candidate 3-replicate CI stated |

I4 is the oracle-first contribution and has no counterpart in LLM4MOF. I2 and I3 are pre-registered controls that LLM4MOF's own internal review found and the manuscript does not report.

### 1.3 What is explicitly *not* claimed

- Not "Tg predicted accurately": absolute MD Tg carries a systematic +40 to +120 K offset (Afzal 2021 mean +79.1 K, fit slope 1.30, calibration Tg = 0.77·Tg_calc + 21.08 K, REF-104 confirmed; Martí 2024 constant +105.02 K, REF-105 confirmed; Gudla & Zhang 2024 "overestimation averaging between 80 and 120 K", REF-106 confirmed; PolyJarvis +38 to +47 K on PE/aPS/PEG, REF-102 confirmed). Every MD Tg is reported **twice**, raw and calibrated, with the calibration measured on our own protocol.
- Not "beats the state of the art at Tg prediction": the T1 surrogate is a tool, not a result. Literature-normal is 31.7–41 K RMSE (polyGNN 31.7 ± 1.5, PolyFusion 33.7 ± 0.6, polyBERT 37.9–38.4, LLaMA-3 LoRA 39.5).
- Not "label-free" unless the T0-only arm is the headline (see §0, point 3).

---

## 2. (b) The design space — what a candidate *is*

### 2.1 The candidate object

```json
{
  "cand_id": "sha256(canonical_tuple)[:12]",
  "mode": "copolymer",                       // or "homopolymer"
  "monomers": [
    {"slot": "A", "monomer_key": "<trimer ring-closed key, stereo stripped>",
     "linear_canon": "*CC(c1ccccc1)*", "stereo_canon": null, "n_star": 2,
     "poly_class": "chain_growth_vinyl_radical", "source": "smipoly|omg|pli"},
    {"slot": "B", "...": "..."}
  ],
  "f_A": 0.30, "basis": "mol",               // composition grid point
  "architecture": "random",                  // random|alternating|block|graft|gradient
  "dp_target": 60, "n_chains": 10, "n_atoms_target": 3600,
  "provenance_tier_of_target": null          // filled only by T2/T3
}
```

A candidate is therefore **(monomer A, monomer B, f_A, basis, architecture, chain-size band)** — the Aldeghi–Coley / Vogel–Weber representation (REF-150 confirmed: "monomer ensembles with stoichiometry and chain architecture", MIT-licensed reference implementation), extended with the explicit chain-size band that the pre-proposal correctly identified as the thing a repeat-unit SMILES omits.

The homopolymer sub-mode is the same object with `B = A, f_A = 1.0, architecture = "homopolymer"` — this matters because the audit found 3,952 CSV rows / 713 ids already have `smiles1 == smiles2` and 4,756 rows share one key (D11): those are not junk, they are the **f→0 and f→1 endpoints that Fox and Gordon–Taylor need**, and the schema must represent them natively rather than dropping them.

### 2.2 Which library, and how it is enumerated

Two tiers, mirroring LLM4MOF's PORMAKE-whitelist discipline (`config.py:96-104` calls the vocabulary files "the SINGLE source of truth"; `matchmaker.py` refuses to propose outside them):

| Tier | Source | Size | Licence | Role |
|---|---|---|---|---|
| **A — in-table** | audited PoLyInfo inventory: 4,792 unique CSV monomer SMILES (4,782 RDKit-valid, 4,666 distinct backbones after `*` deletion) + 13,725 XLSX repeat units (13,624 linear-canonical keys) | 1,725 CSV monomers bridge to an XLSX homopolymer; **1,059 of those carry a homopolymer Tg** (from 1,776 bridge rows, 1,059 with Tg) | PoLyInfo — **not redistributable** | DB mode; Fox/GC anchors; the memorisation-exposed set |
| **B — rule-generated** | **SMiPoly** (BSD-3-Clause, 22 rules = 6 chain-growth + 16 step-growth, 1,083 monomers → 169,347 polymers in 7 classes; REF-117 fully confirmed) and **OMG** (GPL-3.0, 17 reactions, eMolecules → 77,281 SCScore-filtered reactants → ~12 M CRUs; REF-116 confirmed) | ≥10⁵ monomers, ≥10⁶ pairs | BSD-3 / GPL-3 (licence-compatibility decision: §13-D7) | Discovery mode; the novel, non-memorised, redistributable space |

Tier B is the PORMAKE analogue and the reason the space is *synthesizable by construction*: template membership is currently the only polymer synthesizability guarantee with a route attached (SMiPoly/OMG rules, pvfsga SMARTS, polyRETRO). SA score is **reported, never trusted** — Trepalin 2026 is the first dedicated study of SA score as a polymer filter (REF-122) and it is a 2026 result, not a settled tool.

### 2.3 How the space is *counted* — and the LLM4MOF trap to avoid

The anatomy states the discovery space as "518 nodes × 156 linkers × 952 topologies = 12,499,656". **That equation is false and the fact-check confirmed it (C5 refuted):** 518 × 156 × 952 = 76,929,216. The SI's 12,499,656 is the *connectivity-matched* sum |D| = Σ_c n_c t_c L = 80,126 × 156 — a 6.15× difference. A port that copies the naive form overstates its own design space by a factor of six.

So the polymer space is defined as a **mechanism-matched sum**, never a product:

> **|D| = Σ_c [ C(n_c, 2) + n_c ] × |F| × |A_c|**
>
> where *c* ranges over polymerization mechanism classes (SMiPoly's 7 product classes / OMG's 17 reactions), *n_c* = monomers polymerizable by class *c*, the `+ n_c` term admits the homopolymer endpoints, |F| = composition grid size, |A_c| = architectures reachable by mechanism *c* (free-radical/RAFT → random, alternating, block, graft = 4; A-A/B-B step-growth → alternating only, plus random for a 3-monomer feed = 2; ROP → random, block, gradient = 3).

Two monomers form a valid copolymer only if both polymerize by the **same** mechanism. That is the literal analogue of "node connectivity must match topology connectivity", and it is what prevents the 6× overstatement.

Worked numbers on the Tg-anchored Tier-A set (n = 1,059), composition grid |F| = 9 (10–90 mol% in 10 % steps, matching the 79.6 % of PoLyInfo composition pairs that sum to exactly 100):

| Quantity | Value |
|---|---|
| unordered distinct pairs C(1059,2) | 560,211 |
| **naive** product C(n,2) × 9 × 4 | 20,167,596 |
| **mechanism-matched** (illustrative 55/28/17 % class split, |A_c| = 4/2/3) | 7,312,734 — a **2.76×** naive overstatement |
| same for all 1,725 bridged monomers | 19,443,996 matched vs 53,530,200 naive |
| same for all 4,782 valid CSV monomers | 149,493,204 matched vs 411,529,356 naive |

The class split above is **illustrative and must be replaced by the real class assignment produced in milestone M1**; the formula, not the number, is the deliverable. Discovery mode with Tier B is one to two orders larger again.

### 2.4 Serialization — two different serializations, deliberately

**For the LLM** (target-blind, names only, no ids, no values from the hidden table beyond the binned target — see §7.3 for the licence-driven binning):

```
CAND-07 | A poly(methyl methacrylate) unit [ester, alpha-methyl, acrylic backbone]
        | B poly(styrene) unit [phenyl side group, all-carbon backbone]
        | f_A 0.30 mol | random | class chain-growth vinyl (radical)
        | rho 1.13 | CED 385 | FFV 0.161 | C_inf 8.4   [G: T2-measured]
        | Tg 372-379 K  [TABLE, n_rep 4]
```

**For the oracle**: the `candidate.json` of §2.1 → RadonPy's copolymer builder (`RadonPy_Copoly_Ratio`, `RadonPy_Copoly_Type` environment variables in `1_eq.py`; alternating/random/block builders confirmed in the current release, REF-101) → LAMMPS data file → the T2/T3 protocol. `cand_id` is a content hash of the canonical tuple, which makes the `SimCache` pattern (`sim_cache.jsonl`, append-only, keyed by the candidate triple — `live_runner.py:377-414`) port unchanged and makes repeats free across campaigns and replicates. **The MD ledger is keyed on `(cand_id, protocol_hash)`**, so a protocol change never silently reuses stale physics.

---

## 3. (c) The Matchmaker / database analogue

LLM4MOF has three hidden tables with one standardised metadata schema (Table S3) and two filtering styles: building-block search (PORMAKE) and whole-record filtering (hMOF/QMOF, `search_mode ∈ {full, metal_only, linker_only}` — confirmed C6). Both return ids plus a `diagnostics` block plus a structured error; that *interface*, not the body, is what ports (anatomy §3.2 interface #3).

Four polymer tables replace the three MOF ones:

| Table | Plays | Rows | What it provides | Filtering style |
|---|---|---|---|---|
| **PLI-HOMO** (XLSX, audited) | QMOF (clean, whole-record, single value per entity) | 13,725 repeat units; **Tg 7,733**, Tm 3,696, density 1,651, ρ_v 1,268, σ_e 1,296, ε_b 1,059, E 1,003, σ_b 1,064 | trimer key, linear canon, stereo canon, n_star, IUPAC name (13,477 unique of 13,712; 13 null), 43 class codes, SMARTS tag set, GC descriptor vector, T0/T1 predictions | whole-record: tags AND/OR/exclude + numeric ranges + `search_mode` |
| **PLI-COPO** (CSV, audited) | hMOF (large, noisy, one dominant chemistry family) | 42,557 rows / 7,385 ids; **usable Tg core 13,350 rows / 2,735 ids**; with both compositions parsed **6,917 rows / 1,381 ids**; 10,163 Tg replicate groups after grouping by (polymer_id, basis, comp1, comp2) | ordered monomer pair, `CompositionEntry{slot, value, basis, value_class, binding}`, architecture tag set (29 distinct sets, 27.7 % multi-tag), `replicate_group_id`, `truncated_flag`, `same_monomer_flag`, `row_alignment_class` | whole-record + composition-window + architecture-set |
| **GEN-LIB** (SMiPoly/OMG + composition grid) | PORMAKE (the proposable space; no labels) | ≥10⁶ mechanism-matched candidates | monomer keys, mechanism class, SMARTS tags, predicted G, SA score, template provenance | building-block search: class → monomer A set → monomer B set → composition window → architecture set |
| **MD-LEDGER** (grown by the project) | *nothing in LLM4MOF* | starts empty; +110 rows per campaign | `{cand_id, protocol_hash, tier, n_replicates, rho, CED, FFV, C_inf, Tg_raw, Tg_calibrated, CI, wall_seconds, core_hours, status}` | direct key lookup; append-only JSONL + rebuildable index |

**MD-LEDGER is the strategic asset.** The MatNavi Terms (Art. 10(1)-(3),(5)) forbid copying, derivative use and distribution of the DATA and Processed DATA; the sole carve-out is "publication of deliverables of research and development" (audit §6.1). PoLyInfo tables can never be released. **MD results computed on generated, non-PoLyInfo candidates can be.** Being oracle-first is therefore not only the scientifically defensible choice — it is the only route to a releasable quantitative artefact, which is what a Nature-portfolio reviewer will ask for when experimental validation is declined (as LLM4MOF declined it, `ResponseToEditor.txt` l. 71-75, releasing building blocks, force fields and traces instead).

**Cross-table constraint portability is a hard requirement, not a nicety.** SI Note S2 states that the generic-tag propagation hierarchy is applied to hMOF/QMOF as well as PORMAKE "so that an identical Agent 2 constraint maps consistently across all three databases" (extra finding E9c). The same constraint JSON must select consistently across PLI-HOMO, PLI-COPO and GEN-LIB, or the DB-mode results cannot be compared with the discovery-mode results. The `TAG_HIERARCHY` mechanism (~152 entries in LLM4MOF, e.g. `benzene_ring → aromatic, aryl, ring`) ports directly.

**Constraint semantics to port verbatim** (E9a/E9b, both confirmed against the SI): the language is **default-permissive** — "any constraint left unset by Agent 2 simply defaults to a pass condition" — which is what makes the "OPTIONAL ≠ EXCLUDE" rule safe; and an empty or malformed constraint query is **rejected with a structured error that halts the iteration rather than silently substituting defaults**.

---

## 4. (d) The descriptor layer and the MOF2Zeo analogue

### 4.1 G — the gated descriptor vector

LLM4MOF gates on seven Zeo++ descriptors (`di, df, sa, vf, density, dif, cv`) that (i) are *emergent from the assembled structure*, (ii) are *not the target*, and (iii) are *recomputed by the oracle at gate time*. All three properties must be preserved or the beams stop measuring anything.

**G = (ρ, CED, FFV, C∞)** — mass density at 300 K (g/cm³), cohesive energy density (MPa, equivalently the Hildebrand δ), fractional free volume, and the characteristic ratio / Kuhn length as the chain-stiffness measure. Optionally α_glass and α_rubber (the volumetric expansion coefficients above and below the knee) from the T2 ramp.

Why exactly these four: the mechanistic Tg literature reduces to **chain stiffness × cohesive energy** as the two master variables — Karuth, Alesadi, Xia & Rasulev (2021) map a 100-polymer QSPR onto exactly three coarse-grained parameters, cohesive energy, chain stiffness and grafting density (REF-112 confirmed, *note the author list was wrong in the landscape and is corrected here*); free volume and rotatable-bond count are the dominant SHAP descriptors in the interpretable-ML literature (Huo 2025: NumRotatableBonds strongly negative on 1,261 polyimides, CatBoost R² 0.895, REF-133 fully confirmed; Uddin & Fan 2024: BalabanJ/fr_bicyclic ring-fusion descriptors dominate 7,174 samples, REF-131 confirmed). A "target G window" is therefore a genuine mechanistic hypothesis in the same sense that a pore-size window is for H₂ uptake — not a cosmetic mapping.

All four are **RadonPy/LAMMPS-computable** and all four come out of one T2 run. That is the exact Zeo++ role.

Two free, deterministic descriptors ride alongside and never need MD: `n_rot_per_heavy_atom` and `backbone_aromatic_fraction`.

### 4.2 PolyNet-G — the MOF2Zeo analogue

| | MOF2Zeo | **PolyNet-G** |
|---|---|---|
| Inputs | categorical (topology, node, edge) embeddings, 128-d | monomer-pair fingerprint + composition + architecture one-hot + mechanism class |
| Outputs | 7 Zeo++ descriptors | 4 G descriptors |
| Training data | 545,107 / 84,228 assembled structures, avg R² 0.99 | bootstrap: van Krevelen GC (cold start, zero fitted data) → RadonPy's published density/CED set → the project's own MD-LEDGER (grows 80 rows/campaign) |
| Use | pre-rank Beam 1 only; window expanded by per-descriptor MAE (di 0.746 Å, df 0.751, dif 0.828, sa 50.7, vf 0.0098, density 0.0152) | identical: pre-rank Beam 1 only; window expanded by measured per-descriptor MAE |
| Gating | **never** — recomputed Zeo++ gates | **never** — recomputed T2 MD gates |

The cold-start answer is the elegant part: **van Krevelen group contribution *is* the cold-start PolyNet-G.** Molar attraction constants give CED directly, van der Waals volume gives packing/FFV, and the molar Tg function Y_g/M gives the T0 target prediction — all analytic, all interpretable, all zero-training. The 4th-edition group tables are canonical (REF-113 confirmed: Part II "Transition temperatures", Part VII "Survey of group contributions in additive molar quantities"); no pip-installable implementation exists, so it must be coded from the book tables or the Kaggle transcription (REF-146 confirmed verbatim: −CH₂− 158, p-phenylene 2820, −SO₂− 2150, −NHCO− 1510 by molecular weight).

Also spike, but do not depend on: **SimPoly + PolyArena** (arXiv:2510.13696) — an ML force field that predicts polymer density *and* Tg from first principles without fitting to experimental data, shipped with a benchmark of 130 polymers' experimental bulk properties. If it works on dirac it is a genuine middle rung between T1 and T2 and PolyArena is a ready-made standardised evaluation. Treated as an M2 spike with a go/no-go, never as a plan dependency (it was not verified locally by either input lane).

### 4.3 The controlled chemical vocabulary

LLM4MOF: 124 canonical tags in 10 categories + a 215-entry alias map; 105 curated SMARTS, matched bond-order-agnostically; a ~152-entry generic-tag propagation hierarchy; a backbone/substituent split hard-coded by pattern category; plus an LLM enrichment step that writes **only** human-facing fields the Matchmaker never filters against (confirmed C4; SI Note S4). There is **no published polymer counterpart** (landscape §5, confirmed); the nearest reusable sources are the PoLyInfo ontology (CC BY 4.0, and note the public SPARQL graph carries only taxonomy classes — 0 `P######` polymer ids), PolyBench-LLM's SME descriptors, and HAPPY's FORGE-mined subgroups (REF-136 confirmed for the CI-LLM architecture; the FORGE name and the ~10,000-unit corpus are body-text, unverified).

**Target: 85–105 canonical tags in 10 categories + ≥150 aliases**, built with LLM4MOF's own machinery (`5_shared/smarts_library.py`, `4_vocabulary/04_build_vocab_mapping.py` — both explicitly reusable per the anatomy's module map).

| # | Category | ~n | Examples |
|---|---|---|---|
| 1 | Backbone class | 10 | all-carbon vinyl, polyester, polyamide, polyether, polyurethane, polyimide, polysiloxane, polycarbonate, polysulfone, poly(vinyl ether) |
| 2 | Backbone rigidity motif | 8 | p-phenylene, m-phenylene, biphenyl, naphthalene, fused aromatic, in-chain cycloaliphatic, in-chain alkyne, imide/ladder ring |
| 3 | Side-group class | 14 | methyl, ethyl, n-alkyl C3–C8, n-alkyl >C8, isopropyl, tert-butyl, phenyl, benzyl, cyclohexyl, methoxy, ester-alkyl, nitrile, halide, siloxy |
| 4 | Hydrogen bonding | 6 | amide N–H, urethane N–H, urea, hydroxyl, carboxylic acid, lactam |
| 5 | Polar non-HB | 7 | ester, ether, ketone, nitrile, sulfone, sulfoxide, carbonate |
| 6 | Halogen | 5 | F, Cl, Br, perfluoroalkyl, fluoroaryl |
| 7 | Backbone heteroatom | 5 | O, N, S, Si, P |
| 8 | Monomer substitution class | 3 | **M / AD / SD** (mono-, asymmetric di-, symmetric di-substituted) |
| 9 | Architecture | 6 | random, alternating, block, graft, gradient, homopolymer-limit |
| 10 | Polymerization mechanism | 7–17 | SMiPoly's 7 product classes or OMG's 17 reactions |

Plus the generic propagation tier (`aromatic, aliphatic, ring, polar, hb_donor, hb_acceptor, bulky, flexible`) which is what makes cross-table portability work.

**Category 8 carries an explicit verification gate.** The M/AD/SD taxonomy and the "destruction of locally rigid or dynamically flexible conformational structures" mechanism come from Huang, Du, Zhang & Liu (Macromolecules 2022, 55, 3189) — the paper, authors and the three-case classification of Tg composition dependence are confirmed, but **the specific M/AD/SD taxonomy was not visible in any accessible abstract and the fact-check explicitly flags "verify it against the PDF before hard-coding"** (REF-148, partially confirmed). Milestone M1 must read the PDF before these three tags enter the vocabulary. They are strategically valuable precisely because they are the only published mechanistic rule that *predicts the sign of the Fox deviation*, which is this strategy's headline diagnostic (§6.4).

Layer discipline is ported verbatim: Layer 1 deterministic facts (formula, MW, n_star, ring sizes, rotatable bonds, canonical SMILES, trimer key) + Layer 2 deterministic SMARTS tags with multiplicity counts and generic propagation **drive filtering**; any LLM-written `readable_name` / `design_hints` is display-only. One LLM4MOF wart **not** to port: `check_negative_tags` bounces on the LLM-written `readable_name` substring (anatomy §2.4) — a filter that depends on generated text. Drop it.

---

## 5. (e) The oracles — database mode, live mode, cost, placement, and the circularity problem

### 5.1 The ladder

| Rung | What it computes | Cost per candidate | Where | Role |
|---|---|---|---|---|
| **T0** van Krevelen GC + Fox/Gordon–Taylor | Tg, CED, V_w, FFV proxy | ~1 ms, CPU | laptop | interpretable baseline; cold-start PolyNet-G; **the label-free loop oracle** |
| **T1** descriptor/fingerprint GBDT (+ cached polyBERT embeddings) | Tg, Tm, ρ | ~1 ms, CPU | laptop | Beam-1 triage only; **never a reported number** |
| **PolyNet-G** | G = (ρ, CED, FFV, C∞) | ~1 ms, CPU | laptop | MOF2Zeo role: pre-rank Beam 1 against the G window widened by measured MAE |
| **T2** all-atom MD, 1 replicate: build + 21-step compression + NPT equilibration + 300 K production + coarse 8-point ramp | **measured** G, plus a coarse Tg | **288 core-h** @3,600 atoms; 1,065 @10,000 | dirac PBS | the **Zeo++ role**: recomputes the gate; 8 runs/iteration (4 Beam-1 + 4 Beam-4, paired) |
| **T3** all-atom MD, 3 replicates, Suter concurrent-temperature protocol (15 T × 6 ns each) | **measured** Tg + CI | **1,997 core-h** @3,600 atoms; 7,395 @10,000 | dirac PBS | the **RASPA role**: the pre-registered 30-candidate audit |

### 5.2 The cost arithmetic, from first principles

Basis: LAMMPS single-core throughput **228.197 katom-step/s** on a 32,000-atom rhodopsin CHARMM + long-range-electrostatics benchmark, and that figure is size-independent — 226–232 katom-step/s across 32 k–864 k atoms (REF-143 confirmed; *the landscape's quoted band "219–232" is slightly wider than the published table and is tightened here*). Converting at 1 fs and taking realistic MPI efficiency:

| Cell | Job shape | core-h/ns | ns/day/job |
|---|---|---|---|
| 10,000 atoms | 32 cores, 60 % eff | **20.3** | 37.9 |
| 3,600 atoms | 8 cores, 80 % eff | **5.5** | 35.1 |
| 3,600 atoms | 32 cores, 50 % eff | 8.8 | 87.6 |

A 3,600-atom cell on 8 cores is **3.7× cheaper per ns** than a 10,000-atom cell on 32 cores and delivers the same ns/day — because at 10,000/32 ≈ 310 atoms/core you are near the LAMMPS efficiency knee while at 3,600/8 = 450 atoms/core you are above it. PolyJarvis used 3,600–10,900-atom cells with 8–10 chains and passed 18 of 25 property comparisons (Tg within 50 K on 7/9, density within 5 % on 5/9; REF-102 confirmed), so 3,600 atoms is defensible. **M2 must measure the finite-size error on 3 anchors at both sizes; this is the single highest-leverage measurement in the project.**

Stage breakdown (core-h):

| Stage | ns | @10 k | @3.6 k |
|---|---|---|---|
| Psi4 RESP charges (per *new monomer*, cached across every candidate that uses it) | — | ~120 | ~120 |
| build + 21-step Larsen compression | 1.5 | 30 | 8 |
| NPT equilibration (mid of 10–50 ns) | 30 | 609 | 164 |
| T2 production 300 K (ρ, CED, FFV, C∞) | 5 | 101 | 27 |
| T2 coarse ramp, 8 T × 2 ns | 16 | 325 | 88 |
| T3 Suter concurrent-T, 15 T × 6 ns, per replicate | 90 | 1,826 | 493 |
| **T2 total (1 replicate)** | | **1,065** | **288** |
| **T3 total (3 replicates)** | | **7,395** | **1,997** |

Sanity check against the only published anchor: RadonPy reports "more than 30–50 h" on a 40-core dual Xeon Gold 6148 for one equilibrium MD run = 1,200–2,000 core-h (REF-101, quoted verbatim and confirmed). Our 10 k-atom build+equilibration is 639 core-h for 31.5 ns, consistent if RadonPy's figure covers 70–130 ns of total equilibration plus DFT/RESP overhead. The two estimates agree to within the uncertainty of the protocol, which is the most one can claim without measuring on dirac.

Why the Suter protocol: ensembles of **at least ten replicas** are required for a 95 % CI below 20 K, and the optimal protocol is 4 ns burn-in + 2 ns production per temperature run concurrently across all temperatures, "significantly reducing wall-clock time from days to several hours" (REF-110 confirmed). At our 3-replicate budget the CI scales as N^−0.5 to roughly **±35–45 K** — and the landscape's "single-replica 95 % CI ≈ 60–80 K" is an extrapolation, not a quotation (fact-check caveat on REF-110), so it is used here only as a consistency argument. **Operational consequence: a single MD candidate may not be claimed to beat another by less than ~40 K.** Choose discovery tasks with large expected effects; the XLSX Tg range is 138–768 K, so 50–150 K beam separations are physically available.

### 5.3 Throughput and the campaign that actually fits

| Allocation | core-h/day | T2 @3.6 k | T2 @10 k | T3 @3.6 k | T3 @10 k |
|---|---|---|---|---|---|
| 128 cores | 3,072 | 10.7/day | 2.9/day | 1.54/day | 0.42/day |
| **256 cores** | **6,144** | **21.4/day** | 5.8/day | **3.08/day** | 0.83/day |
| 512 cores | 12,288 | 42.7/day | 11.5/day | 6.15/day | 1.66/day |

(The landscape's independent estimate was 0.3–1.5 Tg candidates/day on 256 cores; this reproduces it at the 10 k-atom cell and shows the 3.6 k cell buys a factor of 3.7.)

**The campaign design that the budget permits:**

| Component | Runs | Unit cost | Total |
|---|---|---|---|
| In-loop T2 physics audit — 4 Beam-1 + 4 Beam-4 per iteration × 10 iterations | 80 | 288 core-h | 23,006 core-h |
| End-of-campaign T3 target audit — 10 Beam-1 / 10 Beam-4 / 10 max-disagreement | 30 | 1,997 core-h | 59,899 core-h |
| **Per campaign** | **110 MD runs** | | **82,905 core-h** |

| Allocation | 1 campaign | 2 replicates | 5 replicates |
|---|---|---|---|
| 128 cores | 27.0 days | 54.0 days | 134.9 days |
| **256 cores** | **13.5 days** | **27.0 days** | **67.5 days** |
| 512 cores | 6.7 days | 13.5 days | 33.7 days |

**And the naive port, for contrast** — 380 target evaluations per campaign as LLM4MOF does, 5 replicates × 4 tasks:

| Oracle for those 380 | per campaign | 5 reps × 4 tasks on 256 cores |
|---|---|---|
| T2 @3.6 k | 109,281 core-h (17.8 days) | **356 days** |
| T2 @10 k | 404,743 core-h (65.9 days) | 1,318 days |
| T3 @3.6 k | 758,719 core-h (123.5 days) | 2,470 days |
| T3 @10 k | 2,810,072 core-h (457.4 days) | **9,147 days** |

This table is the entire argument for the strategy. *One* discovery task with five replicates costs one quarter of a 256-core allocation under the audit design; the literal port costs one to twenty-five years.

**Iterations feasible per campaign: 10, unchanged** — the iteration count is set by the *loop* tier (free), not by the physics tier. What changes is how many candidates per iteration get real physics: **8, not 190 builds + 40 GCMC.** The loop's job is no longer "filter a table" but "allocate 8 MD slots per iteration and 30 at the end so that the campaign's claim is falsifiable."

### 5.4 Database mode vs live mode

**Database mode** ("table mode"). Ground truth = the audited PoLyInfo table, deduped to replicate-group medians. Three properties matter and none of them is true of LLM4MOF's hidden tables:

1. **It has measurement noise.** 56.3 % of Tg rows sit in replicate groups; within-group SD p25/p50/p75/p90/p95/p99 = 2.1 / **7.0** / 15.7 / 33.1 / 52.4 / 120 K; 872 groups span > 20 K and 355 span > 50 K; the within-id Tg range has median 20.2 K across 2,667 ids; and the XLSX has 91 duplicate-structure groups of which **30 carry conflicting Tg, max spread 169 K**. A beam-median difference smaller than 7 K is not a result. **Every beam plot carries the replicate-SD band as a horizontal ribbon.** LLM4MOF's oracle is deterministic and has no such band; a polymer reviewer will demand one on sight.
2. **The hidden table and the searchable space are the same object** — LLM4MOF's weakness #6, and worse here. LLM4MOF additionally pre-filtered the PORMAKE H2 tables to what the matchmaker can propose (`build_canonical_db.py`), so "top-1 % of the database" means top-1 % of the *reachable* set, and the paper reports the filtered counts (14,173 / 9,533) without saying so (`DATABASE_CONDITIONS.md` gives 19,997 / 12,188 before filtering). **Fix: report both percentiles, of the full table and of the reachable subset, on every figure, and state the reachable-set size.**
3. **It is licensed.** See §9.4.

DB-mode task slate (five tasks, three tables):

| # | Table | Task | n |
|---|---|---|---|
| DB1 | PLI-HOMO | maximise Tg | 7,733 |
| DB2 | PLI-HOMO | minimise Tg (the direction-aware arm; LLM4MOF's band-gap<0.1 analogue) | 7,733 |
| DB3 | PLI-HOMO | maximise Tm | 3,696 |
| DB4 | PLI-COPO | maximise copolymer Tg | 13,350 rows / 2,735 ids (10,163 groups) |
| DB5 | PLI-COPO | **maximise the Fox residual** δ(f) = Tg − Tg_Fox(f) | 6,917 rows / 1,381 ids with parsed compositions |

DB5 is the strategically important one and is discussed in §6.4 and §14-R2.

**Live/discovery mode.** Ground truth = T2 for G, T3 for Tg. Candidates generated from GEN-LIB. Two discovery tasks maximum in a first paper: **maximise Tg** (large effect available) and **maximise the Fox residual** (the analytic null model cannot, by construction, win at its own residual).

### 5.5 Where each rung runs

| Rung | Machine | Justification |
|---|---|---|
| T0, T1, PolyNet-G, the whole loop | laptop (i5-14600K, 14 physical / 20 logical cores, 31.7 GB) | LLM4MOF's DB campaigns took **353 s mean wall-clock** for 10 iterations (median 348, range 247–492, n = 160 recorded campaigns); a polymer table mode is the same shape |
| polyBERT embedding cache | laptop CPU, one-off | 4,792 + 13,661 ≈ 18,500 unique strings; cache once to parquet |
| T2 / T3 MD | **dirac PBS, via the `hpc-submit` skill** | the skill mandates the project provide `config/hpc.json` + `scripts/submit.py` and "if either is missing, say so and stop"; CALF20's HPC-01/ADR-0007 is the precedent to copy |
| RTX 5050 (8 GB, driver CUDA 13.3) | **protocol development and spot checks only** | no environment on the machine has a CUDA-enabled torch (both installs report `cuda.is_available() == False`); a Blackwell card needs a CUDA 12.8+/13.x wheel; LAMMPS GPU throughput on this card is unmeasured; one Tg replicate ≈ a week (unverified). Never in the campaign critical path. |

**Do not** plan a GPU-dependent surrogate. The T1 and PolyNet-G designs are deliberately sklearn/numpy-class models so the loop runs today on the base conda environment (pandas 2.3.3, numpy 2.3.5, scipy 1.16.3, scikit-learn 1.7.2, **rdkit 2025.9.6**, pyarrow 21.0.0 all present; torch absent).

### 5.6 The circularity problem — "the oracle is only as good as the surrogate"

Six mechanisms, all of them producing a reported number:

1. **Provenance-tier invariant (enforced in the check gate).** Every candidate record carries `provenance.tier ∈ {TABLE, T0, T1, T2, T3}`. Any record with tier `T0` or `T1` that reaches a `figure_*.csv` or a manuscript table **fails the build**. This is a 20-line test and it is the single most valuable line of defence, because it makes the discipline mechanical rather than cultural.
2. **Pre-registered audit sampling.** The 30 T3 candidates are drawn 10/10/10 (Beam-1 / Beam-4 / maximum T0-vs-T1 disagreement or maximum T1 predictive variance) and the draw is **written into the campaign manifest, hashed, and committed before a single MD job is submitted**. This is the direct answer to "you only simulated your winners" — which is exactly what LLM4MOF does (`nlargest(10, 'target')` in live mode, confirmed C7) and exactly what a polymer reviewer will notice.
3. **Held-out oracle.** A second surrogate with different features and a different split (trimer-key scaffold-held-out) is frozen at M3, never used in the loop, and scores every candidate at the end. Hit rate is reported under it as well as under the table.
4. **Pre-registered supervised-shortcut probe.** Fit a GBDT on the hidden table from the gated descriptors G alone and publish the OOF R² before the first campaign. The aide2 probe got **0.943** on PORMAKE H2-100 bar from vf/sa/density and **Spearman 0.829** on hMOF Xe/Kr with a textbook PLD argmax at 4.9 Å (confirmed C21). If the polymer number is similarly high, the honest framing is "the agent recovers the descriptor structure of the table", and saying so first is far better than having a referee say it.
5. **The gate is never the target** (§4.1). Structural, not procedural.
6. **Calibration is measured, never assumed.** Build a 12–20 polymer anchor set **by structure key, not by pid** — the audit found the primary pids of PE/PS/PMMA/PVC/PET/PEO/PLA/PCL carry 0 of 8 properties while PS (P322231, Tg 367 K), PDMS (P374137, Tg 151 K, ρ 0.97), PTFE (P350006) and PVDF (P350007) carry data under a *second* pid (D12). Fit Tg_exp = a·Tg_MD + b with its CI on that set; report every MD Tg raw and calibrated; never compare raw MD Tg to PoLyInfo. Additional free gate from Odegard 2022: accurate Tg without a cooling-rate correction requires the model density to match experiment within **2 %** (REF-111, both halves confirmed verbatim) — so any candidate whose T2 density deviates by more than 2 % from its GC/experimental expectation is flagged `tg_unreliable`. That is the polymer analogue of LLM4MOF's physical sanity gates (H₂ > 71 g/L, SF₆ > 1,880 g/L rejected).

Worth stealing later: the "Scaling Law of Sim2Real Transfer Learning" work from the RadonPy lineage (arXiv:2408.04042) quantifies how much simulated data is needed to calibrate to experiment — a strictly better treatment of the offset than a constant or linear map.

---

## 6. (f) The four beams, redefined — and attribution on a continuous axis

### 6.1 Mapping the three axes

LLM4MOF's axes are **metal identity** (primary, coarse, few values, committed first), **linker chemistry** (secondary decoration), and the **geometry window** (a quantitative second-stage gate). The polymer mapping:

| LLM4MOF | LLM4POL |
|---|---|
| metal identity | **backbone class of the majority monomer** (10 values, coarse, stratifying, committed first) |
| linker chemistry | **side-group / functional-group decoration of both monomers + the comonomer identity** |
| geometry window (7 Zeo++ descriptors) | **the G window (ρ, CED, FFV, C∞) + the composition window f_A ∈ [f_min, f_max] + the architecture set** |

### 6.2 The beams

| Beam | Constraint | Isolates |
|---|---|---|
| **Z / Beam 1** — full hypothesis | backbone class ∧ side-group tags ∧ comonomer tags ∧ **G window** ∧ **f window** ∧ architecture set | — |
| **A / Beam 2** — chemistry only | same tags; **G window, f window and architecture set dropped** | **Z − A = the value of the quantitative gate** |
| **F / Beam 3** — backbone only | backbone class of monomer A only; comonomer, side groups, composition, architecture all free | **A − F = the value of the comonomer + side-group chemistry** |
| **R / Beam 4** — random | uniform over the mechanism-matched space, **backbone-class-stratified** | **A − R = chemistry vs chance; F − R = the backbone commitment alone** |

Four fixes to LLM4MOF's beam machinery, each forced by a verified finding:

- **Beam 3 must drop the numeric gate.** LLM4MOF's `_build_beam_specs` pops only the linker fields and `global_requirements` and its comment says "keep metals and geometry", so `geometry_filter` survives in the metal-only beam (confirmed C25). Harmless there because only Beam 1 is geometry-gated in practice, but in a polymer port where the f-window is the interesting gate this would silently destroy the A−F contrast. Drop it.
- **Zero-match iterations are retried, never consumed.** SI Note S1 states the rule unconditionally, but it holds only in discovery mode: in DB mode a zero-match iteration auto-continues with empty filter sets and the counter advances (confirmed C1 with caveat; extra finding E5). With no-match rates of 2.3–34.9 % across backends, this plausibly explains much of the 79.5-vs-91.3 Table-1 gap. Implement the SI's stated rule in both modes and log `no_match_retries` per campaign.
- **No fallback fill of Beam 1.** In discovery mode LLM4MOF promotes best-scoring candidates that *fail* the strict Zeo++ gate into Beam 1 to fill the quota, flagged in a `GeoFilter` column (confirmed C25) — so "Beam 1 = full hypothesis" is sometimes false. Either do not fill, or keep the fallbacks in a separate `Z_fallback` set excluded from the Beam-1 statistic.
- **n is reported on every point.** LLM4MOF plots the median of the *entire* matched set, whose size swings from 1 to 9,533: a recorded campaign had iteration-1 counts Z 1 / A 1 / F 3 / R 9,533 and iteration-10 counts Z 43 / A 257 / F 3,591 / R 9,533 (confirmed C23). **Hard rule: a beam median on n < 10 is plotted as an open marker and excluded from the campaign statistic.**

### 6.3 The fifth beam: the composition sweep (Beam 1c)

Once per iteration, for the single best (A, B, architecture) triple of that iteration, evaluate the **entire f grid** (9 points in DB mode, 19 at 5 mol% in discovery mode) rather than a sample. This produces a *curve*, not a point.

This beam has no MOF counterpart and it is the right invention, because the entire copolymer-Tg literature is about the shape of that curve: Fox 1/Tg = w₁/Tg₁ + w₂/Tg₂, Gordon–Taylor with one fitted K, and Kwei with an interaction term, compared against experiment by Brostow, Chiu, Kalogeras & Vassilikou-Dova (Mater. Lett. 62:3152, 341 citations; REF-147 fully confirmed verbatim). Cost: free at T1; 9 × 288 = 2,592 core-h at T2, affordable **once per campaign**, not per iteration.

### 6.4 What causal attribution means when the axis is continuous

For the three discrete axes, attribution is a **matched-set median contrast** — LLM4MOF's construction, ported unchanged with the noise band and *n* added.

For the composition axis it is not, and pretending otherwise is the trap. Three mechanisms:

**(i) Discretise the axis, keep the estimand continuous.** f_A lives on a fixed grid (9 points in DB mode — justified because 79.6 % of same-basis composition pairs sum to exactly 100 and 80.1 % fall in 99–101; 19 points in discovery mode where we choose f ourselves). A "composition window" is then a *set of grid points*, i.e. a boolean filter, so every line of LLM4MOF's matchmaker and beam machinery ports unchanged. The estimand remains a derivative.

**(ii) The attribution statistic is a residual slope against an analytic null, not a raw slope.** Reporting dTg/df is uninformative because **Fox already predicts most of it**: Fox reaches R² 0.835 / RMSE 42.57 °C on PoLyInfo binary copolymers (vs 0.921 / 24.45 °C for the best GNN), and the audit's own linear-mixing test gives median |ΔTg| ≈ 14 °C when the composition is bound to the correct component. So define

> **δ(f) = Tg_measured(f) − Tg_Fox(f; Tg_A, Tg_B)**

and attribute on δ, not on Tg. The agent's chemistry is credited only with what it explains **beyond ideal mixing**. Three consequences, all good:
- The claim is falsifiable against a 70-year-old analytic baseline that every polymer referee knows.
- Fox stops being a competitor (which it would win — it is free and R² 0.835) and becomes the **null model**, which is the correct role for it.
- It connects directly to a mechanistic literature that can supply vocabulary tags: negative deviation for mono-substituted + asymmetric-di-substituted pairs, positive for mono + symmetric-di (Huang 2022, REF-148 — *subject to the PDF verification gate of §4.3*); and UCST-tending comonomer pairs give negative deviation, LCST-tending positive, with the effect **strengthening with alternation** because of bond-induced forced mixing (Branham-Ferrari & Simmons, confirmed verbatim; now published in Macromolecules 2026, doi 10.1021/acs.macromol.6c00630 — cite that, not the arXiv id).

**(iii) The empirical prior and the regression test.** The audit's 378-id monotonicity set (ids with ≥5 distinct same-basis compositions summing 99–101) has **median |Spearman ρ(Tg, composition₁)| = 0.868**, with 234 ids above 0.7 and 67 below 0.3 (EVA P900016 ρ = 0.20, SAN P900007 ρ = −0.06 are physically flat/mixed-order). That set is (a) the empirical prior for what dTg/df looks like when the binding is correct, and (b) a **regression test with a hard threshold**: any loader or binding change that drops the median |ρ| below 0.85 fails the check gate. Given that D1 flips the composition slope's sign on ~30 % of resolvable rows, this test is the difference between a working composition axis and a fabricated one.

**Reported attribution block per campaign:**

```
Δ_gate      = median(Z) − median(A)            [K]   n_Z, n_A, noise band
Δ_chem      = median(A) − median(F)            [K]   n_A, n_F
Δ_backbone  = median(F) − median(R)            [K]   n_F, n_R
Δ_f         = slope of δ(f) over Beam 1c       [K per unit f]   with 95 % CI
Δ_MD        = median(Tg_cal | Z-audit) − median(Tg_cal | R-audit)   n=10 vs 10, MW p
```

Only `Δ_MD` may appear in the abstract.

---

## 7. (g) Feedback payload and memory ledger

### 7.1 The one change that matters most: fix the context, then measure it

SI Note S1 claims Agent 1 "receives the complete, verbose feedback report only for the immediately preceding iteration, while older empirical observations are compressed into a fixed-size Memory Ledger." **The shipped code does no such compression** (extra finding E4, verified): `LLMClient(multi_turn=True)` appends every user and assistant message and re-sends the whole list; there is no trim, window or eviction anywhere; the SI's own cost note confirms it ("the conversational context that must be re-sent grows monotonically", $0.03 → $0.19 per iteration). The ledger is an **addition on top of an unbounded transcript**, which means Note S11's ledger ablation (9 tasks × 5 replicates; +41.7 mol/kg on gravimetric H₂ 100 bar, +9.3 on Xe/Kr, net-neutral-to-slightly-negative on the single-peak metric; confirmed C9) measures "ledger on top of full history" and does **not** transfer.

For LLM4POL: **implement the design the SI describes** (verbose feedback for iteration i−1 only; everything older reaches the agent solely through the ledger), and run both arms. This is a free, publishable methodological correction and it also caps token cost, which matters because polymer beam tables are wider than MOF ones.

### 7.2 Beam table schema

```
Candidate | Tg | Src  | rho  | CED | FFV   | C_inf | f_A  | basis | arch  | class | Gate
CAND-07   | 375| TAB4 | 1.13 | 385 | 0.161 | 8.4   | 0.30 | mol   | rand  | CGV-R | PASS
CAND-12   | 412| MD3  | 1.09 | 402 | 0.148 | 11.2  | 0.55 | mol   | alt   | CGV-R | PASS
CAND-19   | 361| T1   | 1.15 | 370 | 0.170 | 7.1   | 0.20 | wt    | block | CGV-R | fail:FFV
```

Two columns LLM4MOF never needed:
- **`Src`** — the provenance tier of the target value: `TABn` (table, n replicates), `MDn` (T3, n replicates), `T1` (surrogate). LLM4MOF's targets are homogeneous; ours are not, and an agent that cannot tell a measured value from a predicted one will chase surrogate noise.
- **`Gate`** — PASS or `fail:<descriptor>`, ported from the live `GeoFilter` column. (Port the column, not the bug: the shipped Beam-1 hint tells the agent fallbacks were promoted to fill "the 15-candidate quota" while `LIVE_SIM_Z_RASPA_TOP = 10` — a stale number in text the agent actually reads, extra finding E10a.)

### 7.3 Text blocks

1. **Ledger block** (`render_facts_only`, ported): best-so-far with its provenance and CI, top-K cutoff and median, top-5 best-first, G ranges of the frontier, cutoff trajectory.
2. **Four beam tables** + a **monomer profile** per beam (top-3 backbone classes / side-group tags / H-bond tags / architectures as `name(pct%)`, plus min–max(median) of f_A and of the four G descriptors) + a **pattern summary** with the "Minority (informational, do NOT require as mandatory)" guard ported verbatim.
3. **A Fox-residual line per beam** — `median δ(f) over this beam = +12 K (n = 41)`. This is the single most informative sentence you can hand a polymer chemist, and it is the diagnostic that has no MOF counterpart.
4. **A noise-floor footer.** `Values within ±7 K are not distinguishable in this table (median replicate SD); ±33 K at the 90th percentile. MD values carry ±~40 K at 3 replicates.` LLM4MOF never tells the agent its oracle's noise because its oracle has none; hiding ours invites overfitting to replicate scatter.
5. **G profile** (the `_generate_suggested_geometry` analogue), observational not prescriptive, withheld when Beam 1 is empty.
6. **Diagnostic footer** on empty Beam 1, using matchmaker diagnostics to say which stage failed.

### 7.4 Target-blindness, plus one new leak channel

Port the full withholding list: no database identity or size, no record ids, no global distribution, no percentiles, no thresholds, no sensitivity report (EF@1/5/10 %, Mann–Whitney p are "Purpose: Human analysis ONLY"). Port the identity-only stratified sampling that never reads the target (`sampling_strata.py:76-100`).

**New for polymers: never show Tg_Fox itself, only δ.** Fox is invertible — an agent shown Tg_Fox(f) at two compositions can solve for Tg_A and Tg_B, i.e. recover homopolymer values from the hidden table that it was never shown. LLM4MOF had no analytic mixing law and so no such channel. Show the residual, never the prediction.

**Licence-driven binning.** Bin the reported target to the replicate noise floor (7 K) before it enters the feedback text: `Tg 372–379 K` not `Tg 375.4 K`. This is simultaneously (a) a mitigation for the Art. 10(1) transmission question — a binned, anonymised, ≤10-row-per-beam derivative is much harder to characterise as distributing "the DATA or Processed DATA" than exact values are — and (b) honest, because the third significant figure is below the noise floor anyway. A modest change to `_generate_table_with_samples`.

### 7.5 Memory ledger

Port `MemoryLedger` almost unchanged. Substitutions: `_GEOMETRY_COLS → ["rho","ced","ffv","c_inf","f_A"]`; `_struct_label` → the candidate name string.

Keep the beam asymmetry **and document it correctly**, because the anatomy's condensed description of it is wrong (C8 refuted): the ledger *does* ingest the sampled random beam — `_ALL_BEAMS = ['z','a','f','total']` drives `beam_medians` in `history[]` and the `_detect_outside_promising` check — and only `global_best`, `frontier` and `geometry_envelope` are restricted to `_HYPOTHESIS_BEAMS = ['z','a','f']`. Nothing leaks to the agent because `render_facts_only` prints neither `beam_medians` nor `outside_promising`.

**One new ledger field: `md_refs`.** Each frontier entry records whether it has a T2/T3 measurement, with how many replicates and what CI. Rendered as:

```
Best so far  471 K  [MD, 3 reps, ±38 K]  CAND-12, iter 6, Beam 1
Runner-up    468 K  [T1 surrogate, ±31 K RMSE]  CAND-33, iter 8, Beam 2
```

Without this the agent cannot distinguish a measured lead from a surrogate artefact, and will spend its remaining iterations chasing the latter.

Also port the empirical finding, not just the code: the legacy prescriptive renderer ("CONCENTRATE… do NOT switch families", "GRAFT it") **hurt** rare-peak tasks and was replaced by the facts-only renderer (`memory_ledger.py:544-556`, confirmed C8). Do not reinvent it.

---

## 8. (h) Metrics, baselines, and the budget-matching protocol

### 8.1 Metrics

**Ported, with fixes:**

| Metric | Fix relative to LLM4MOF |
|---|---|
| Per-iteration beam median, mean ± SEM over replicates | **+ n annotated per point; + replicate-noise ribbon; open marker and exclusion when n < 10** |
| Final-iteration percentile of the Beam-1 median | **+ reported twice: percentile of the full table and of the reachable subset** |
| Iterations to top-10 % | unchanged |
| Hit rate / enrichment vs top-1 % (Table S2 style) | **+ raw hit counts and Wilson intervals instead of bare ratios.** LLM4MOF's "162×" enrichment on CH₄ rests on a baseline of **1 hit in 500** (confirmed C16); quoting two significant figures for such a ratio is indefensible |
| Discovery statistics | Mann–Whitney one-sided on pooled candidates + sign test at replicate level. **Note that a one-sided sign test on 5/5 replicates gives p = 0.031, which is the minimum possible p at n = 5** — report it as such, not as strong evidence |
| Estimator consistency | **Never pair an iteration-10 statistic with a pooled-over-all-iterations reference.** LLM4MOF's "SF₆ 7.7 vs 2.8 mol/kg" does exactly that: Beam 1 at iteration 10 is 7.689, but the random reference at iteration 10 is **2.55**, while 2.8 is the pooled figure (extra finding E7) |

**New, and load-bearing:**

| Metric | Why |
|---|---|
| **Δ_MD — the audit effect size**: median calibrated MD Tg of the 10 Beam-1 audit candidates vs the 10 Beam-4 audit candidates, Mann–Whitney one-sided, per-candidate CI from 3 replicates | the answer to "is the property real?"; the only number allowed in the abstract |
| **Surrogate-vs-MD calibration per campaign**: R², RMSE, Spearman of T1 predictions against the campaign's MD ledger, tracked by iteration | if it degrades as iterations proceed, the loop is walking off-domain — this is the implementable, measured version of the pre-proposal's "extrapolation-risk flagging", replacing a meta-loop that cannot be validated with a number that can |
| **Novelty**: trimer-key novelty vs 13,624 XLSX + 4,792 CSV keys; pair-level novelty vs the 5,322 observed SMILES pairs | required for a generated space; also bounds the memorisation channel |
| **Validity / synthesizability**: two-star rule; template membership (SMiPoly/OMG class); SA score reported, not gated | field-standard (PolyTAO 99.27 % validity over ~200 k; Yue 2025 MOSES metrics with the two-star rule) |
| **Memorisation share**: `--no-feedback` arm, (NF−50)/(V0−50), pre-registered | aide2 measured 0.44 / 0.44 / **0.72** on MOFs (C20). Polymer Tg is *more* memorisable — every frontier LLM knows PS ≈ 100 °C. This is the control most likely to decide whether the paper is publishable, and it must be run before anything else |
| **Supervised-shortcut probe** OOF R² from G alone, pre-registered | aide2 got 0.943 on PORMAKE H₂ (C21) |
| **Replicate σ** of the final percentile, measured *before* any effect is claimed | aide2 W1: σ = 6.4 / 15.9 / 6.9 percentile points (n = 10/arm); W2: across **210 seeded campaigns (42 cells × 5 replicates, 8 variant labels × 2 budgets × 3 tasks — note the anatomy's "14 variants × 3 tasks × 2 budgets" grid description is wrong, C22 refuted)**, no variant beat the hand-tuned production configuration at Holm-corrected significance (max +1.80 σ, p_holm = 1.0), and common-random-number pairing did not reduce variance because LLM non-determinism dominates even at temperature 0 |
| **Token/cost accounting** | LLM4MOF: exactly 2 model calls per iteration, ~0.57 M tokens, **$1.06 ± 0.05** per campaign — but 2 of 5 replicates spent 22 calls, not 20, because an unproductive iteration was retried (E10b), so "20 per campaign" is not universal. Report per-replicate |

### 8.2 Baselines — all under the same oracle and the same realised budget

| # | Baseline | Notes |
|---|---|---|
| B1 | **Random** (Beam 4) | the floor |
| B2 | **Fox** | the analytic null for copolymers; R² 0.835 / RMSE 42.57 °C on PoLyInfo copolymers. As a *design* baseline: pick the pair/composition maximising Fox-predicted Tg. It will be strong on task DB4 and it cannot, by construction, win on DB5 |
| B3 | **Group contribution (van Krevelen)** | the interpretable design baseline; in-sample MAE ≈ 10 K but "cannot predict motifs outside the data sample" (REF-115, confirmed; cite the Macromolecules DOI 10.1021/acs.macromol.5c00178, **not** arXiv:2411.06461, which carries a different title); out-of-sample R² 0.71 (Roy 2026, REF-125 confirmed: GC 0.71 vs single-LLM 0.67 vs ChemCrow 0.66 vs their agent 0.78 on a 50-polymer Tg benchmark) |
| B4 | **GA** | LLM4MOF Note S6 shape: 40 evaluations/iteration × 10, 5 replicates, 40 random initial, surrogate refit each iteration, population 200, 20 generations, mutation 0.2. **Give it our T1 surrogate.** LLM4MOF's GA surrogate had held-out R² ≈ 0 and MAE 6.2–6.8 g/L (confirmed C13) — it was random search with extra steps, which is why it lost, and a referee will say so. A GA with a working surrogate is a genuinely hard baseline and beating it means something |
| B5 | **BO** | latent-variable GP over the categoricals + a **continuous f dimension**. Note that BO is structurally *advantaged* here relative to the MOF setting, because f is genuinely continuous. Expect BO to be hard to beat on pure optimisation; the claim is about attribution, not about winning. Precedent: SPACIER (RadonPy + BO, synthesized optical polymers past the refractive-index/Abbe Pareto front, REF-103 confirmed) and a second MD-in-the-loop BO system for polymer electrolytes (arXiv:2602.17595) |
| B6 | **polyBERT-guided generate-and-filter** | polyBART's recipe (latent perturbation + GPR property filter + SA ≤ 6). **Licence caveat:** polyBERT weights are under a GTRC academic-research-use licence; settle before any release |
| B7 | **Zero-feedback LLM** | the memorisation floor; not a baseline to beat but the control that calibrates every other number |

### 8.3 The budget-matching protocol

LLM4MOF's version is not tight enough to survive scrutiny: nominal 40 × 10 for all arms, but **realised** GA 327–368 and BO 212–265 versus LLM4MOF's 380 ± 2 (confirmed C13), and the ~190 build + relax + Zeo++ evaluations per iteration are free in the label accounting while a 629,335-record surrogate sits outside it entirely. The aide2 simulation persona priced the uncounted compute at 25–35 %.

**Rules for LLM4POL:**

1. **Two currencies, both reported.** (i) *Oracle calls* = target evaluations at the tier that produced the reported number. (ii) *Core-hours* = everything, including surrogate training, descriptor prediction, failed builds, discarded replicates and the MD audit.
2. **Match on realised, not nominal.** An arm that under-spends keeps drawing until it reaches the cap; realised counts are reported per replicate and must agree within ±5 %.
3. **Label accounting is stricter than LLM4MOF's.** Property-agnostic pretraining is excluded for every method including ours (their rule). But a T1 surrogate trained on 7,733 PoLyInfo Tg labels **sees the property** and is counted — unlike MOF2Zeo, which predicts geometry and is genuinely property-agnostic. Therefore:
   - **Headline configuration: T0-only in the loop** (van Krevelen GC + Fox: analytic, zero fitted PoLyInfo labels) → genuinely label-free, and the claim "no property-labeled training structures" survives intact.
   - **Comparison arm: T1 in the loop** → almost certainly stronger, and reported as *using 7,733 labels*.
   Running both is what turns LLM4MOF's most attackable claim into a measured trade-off.
4. **The MD audit budget is identical across arms.** Each arm's top-10 candidates plus 10 random plus 10 disagreement get the same 30-run T3 audit, or the arms cannot be compared on the only metric that matters.

---

## 9. (i) How the data audit's defects constrain this strategy

### 9.1 D1 — the composition/component swap (S1, the one that could sink the project)

`composition_i` belongs to `component_i`, **never** to `smiles_i`; the ordered component-id pair varies within 277 of 4,008 ids and ~30 % of resolvable rows are swapped relative to the SMILES slots (5,224 of 17,697 by the audit, 5,333 of 17,842 by independent propagation). Row classes: aligned 15,409 / swapped 2,221 / half_aligned 5,309 / half_swapped 881 / neither 433 / one_id 190 / no_ids 18,114. The mixing test is decisive: on swapped rows, component-binding gives 13.7 °C error vs 56.8 °C for SMILES-slot binding.

Constraints this imposes:

- Every composition record carries `binding ∈ {by_component_majority, by_position_aligned_only, undetermined, unresolved}`. **Only the first two enter any oracle.** That admits 15,409 + 2,221 = 17,630 of 24,441 composition rows; 5,309 undetermined + 881 half_swapped + 433 neither are quarantined (and note the mixing test on the half_aligned rows actually favours the *reversed* binding, 23.4 vs 15.4 °C, so they are not safe to default).
- **The composition-aware DB-mode table is 6,917 rows / 1,381 ids.** That is 7.4× smaller than LLM4MOF's smallest hidden table (QMOF 20,373) and 20× smaller than hMOF. Beams will run out of candidates: LLM4MOF already hit Z n = 1 at iteration 1 on a 9,533-row table. **Consequence: composition is a *reported* field in DB mode, gated only on the DB5 task, and the composition axis does its real work in discovery mode where f is ours to choose.**
- Regression test with a hard threshold: the 378-id monotonicity set must keep median |Spearman ρ| ≥ 0.85 (measured 0.868). This is the check that catches a re-introduced swap.

### 9.2 D4, D5, D6, D10, D11, D12 — the rest of the ladder

| Defect | Constraint imposed |
|---|---|
| **D4** replicates/duplicates: 6,548 exact-duplicate rows; 56.3 % of Tg rows in replicate groups (SD p50 7.0 K, p90 33.1 K, p99 120 K) | the DB-mode hidden table is the **group-median table (10,163 Tg groups)**, not the row table; splits are by `polymer_id`; the within-group SD is published as the noise band on every plot and stated in the feedback footer |
| **D5** 42.6 % of rows (18,116) and 45 % of ids have no composition at all; 1,878 of 4,578 Tg-bearing ids never have one | a `composition_unknown` partition, usable by Beams A and F (which have no f-window) and **excluded from Beam Z whenever the hypothesis carries an f-window**. Never default to f = 0.5 |
| **D6** terpolymers truncated to two slots: 4,243 rows / 548 ids conservative, 7,389 / 1,320 liberal; 4,023 rows sum to < 99 because the third unit was dropped | `truncated_flag` excludes from the copolymer oracle; every beam's matched-set count reports how many were excluded |
| **D10** structural identity: attachment-point variants (116 CSV SMILES), the periodic key falsely merging 5 XLSX + 2 CSV + 1 cross-file pair, stereo carried by only 74 CSV / 35 XLSX strings | **trimer ring-closed key, stereo stripped, with `stereo_canon` retained** is the primary key everywhere — dedup, cross-file join, novelty, the MD cache key. Get this wrong and "novel candidate" is meaningless |
| **D11** 3,952 rows / 713 ids with `smiles1 == smiles2`; 4,756 rows sharing one key; 98 rows are 0/100 pairs | **not junk** — these are the f→0/f→1 endpoints Fox needs. Flag `same_monomer_flag` and route to the homopolymer path rather than dropping |
| **D12** XLSX aggregation rule unknown; 2,338 property-free rows including the primary pids of PE/PS/PMMA/PVC/PET/PEO/PLA/PCL | the MD **calibration anchor set is built by structure key, not by pid** (PS/PDMS/PTFE/PVDF carry data under a second pid); the XLSX `aggregation` field is `polymer_aggregate_unknown` and every comparison to it is flagged |
| **D2, D3, D8, D15** encoding, glued units, mislabelled columns, outliers | handled by the §3.4 loader rules; the validator runs before any modelling step consumes the tables |
| **D16** `copolymer.zip` is entirely NUL bytes | the wider export is unavailable; §13-D9 |

### 9.3 What the audit removes from the pre-proposal

The pre-proposal's §8.2 says duplicate canonical SMILES number "~100" and should be aggregated to a per-structure median. The audit's number is **91 duplicate-structure groups (192 rows, 101 excess)**, of which **30 have conflicting Tg with a maximum spread of 169 K** — those are not measurement replicates to be averaged, they are structure/name conflicts (≥10 verified name/SMILES conflicts) and averaging them manufactures a fictitious value. That decision belongs to the owner (§13-D6).

The pre-proposal also cites Dangayach et al. 2025 as a "single-surrogate PFAS removal" system. It is a **review** of ML for polymeric membranes — ACS labels it review-article — not a PFAS dataset paper (REF-137, strongly confirmed, double-sourced). Correct or drop the citation.

### 9.4 Licensing — three architectural consequences, not a compliance footnote

MatNavi Art. 9.2 licenses the DATA "only for use by themselves"; Art. 10(1)-(3),(5) prohibit copying, derivative use, distribution and bulk acquisition; the sole carve-out is "publication of deliverables of research and development"; Art. 9.3 requires a fixed acknowledgement sentence. The words *machine learning*, *model* and *training* occur **zero times**.

1. **No PoLyInfo table in the repo, in a supplementary file, or in a public artefact — ever.** The metrics, the code, the pipelines and the MD ledger are "deliverables"; the tables are not.
2. **Transmission to a hosted LLM API is an unresolved legal question and a blocking decision.** LLM4MOF sends ≤10 rows × 4 beams × 10 iterations = ≤400 records per campaign to OpenAI; at 5 replicates × 5 DB tasks that is 10,000 row-transmissions. Mitigations built into the design: binning to the noise floor, anonymised labels, tag-profile summaries instead of raw rows, and the option to run the entire loop against a **local** model on the RTX 5050 if the answer is no. But the decision must be ratified before M4 (§13-D1).
3. **A released surrogate trained on PoLyInfo needs NIMS written permission** (treat as required; two precedents exist — PolySea and PolyFusionAgent — but neither establishes a right). Therefore the repository must **run end-to-end with T0 only**, so that external reproduction is possible without the licensed table. This is a second, independent reason the T0-only arm is the headline configuration.

Open, redistributable substitutes worth a spike: **OPoly26** (arXiv:2512.23117 — 6.57 M DFT calculations on up to 360-atom polymer-derived clusters, >1.2 billion atoms, varying monomer composition, chain length, **chain architecture** and solvation; open and redistributable, unlike PoLyInfo) and **polyVERSE** (the actual downloadable VFS/ROP virtual-polymer libraries behind Kern 2025 / pvfsga, 1,087,564 entries in Parquet).

---

## 10. (j) Component map

| LLM4MOF component | Polymer equivalent | Action | Rationale |
|---|---|---|---|
| **Agent 1** (hypothesis generator; multi-turn, T = 0.0, 8-field strict JSON of which 4 validated) | same wrapper, polymer schema: `target_property`, `mechanism`, `target_G_window`, `backbone_hypothesis`, `side_group_hypothesis`, `composition_architecture_hypothesis`, `novelty_justification`, `lesson_learnt` | **ADAPT** | `agent1_handler.py` (242 l.) is domain-agnostic; only the required-key list and the wrapper text change. Fix the context growth (E4): verbose feedback for i−1 only. Note that nothing downstream reads Agent 1's `database_constraints` block — Agent 2 reads the prose |
| **Agent 2** (stateless translator, T = 0.0, soft validation, `{DATABASE_MODE_RULES}` injection) | same; the three mode-rule blocks become PLI-HOMO / PLI-COPO / GEN-LIB rules | **PORT-AS-IS** | the stateless-translator pattern with default-permissive semantics, OR-of-ANDs branches, "OPTIONAL ≠ EXCLUDE" and the structured-error halt (E9a/b) is the most transferable idea in the paper |
| **Controlled vocabulary** (124 tags / 10 categories / 215 aliases / 105 SMARTS / TAG_HIERARCHY) | 85–105 polymer tags in 10 categories (§4.3), ≥150 aliases, polymer SMARTS set, propagation hierarchy | **REPLACE (content) / PORT-AS-IS (machinery)** | `constraint_utils.py` (686 l.) and `5_shared/smarts_library.py` port verbatim; the tag content is wholly MOF-specific. Drop the `readable_name` substring bouncer — it filters on LLM-written text |
| **Matchmaker** (PORMAKE: topologies → nodes → linkers → virtual assembly → categorized filter) | **CopolymerMatchmaker**: mechanism class → monomer-A set → monomer-B set → composition window → architecture set → pair-validity check | **REPLACE (body) / PORT-AS-IS (interface)** | the stable part is the contract — `{candidates[], diagnostics{}, preferred_features{}}` or `{status:"error", reason}`. The body is MOF assembly. The `Phase D virtual assembly` step maps exactly onto the mechanism-compatibility check |
| **Building-block library** (518 nodes × 156 linkers, whitelisted from MOF2Zeo vocab files) | Tier A: 4,792 CSV monomers / 13,725 XLSX units; Tier B: SMiPoly (169,347 from 1,083 monomers) + OMG (~12 M CRUs) | **REPLACE** | polymer monomers, not metal nodes. Keep the "single source of truth whitelist" discipline and the refusal to propose outside it |
| **Topology library** (952 single-node topologies, `sim_safe_topologies`) | **architecture × mechanism-class table** (which of random/alternating/block/graft/gradient each mechanism can reach) | **REPLACE** | polymers have no topology in the reticular sense, but they do have a discrete "what can be assembled" axis, and it plays the same combinatorial-gating role. This is why the design-space formula is a *matched sum*, not a product (C5) |
| **hMOF / QMOF / CoRE hidden tables** | PLI-COPO (42,557 rows / 13,350 usable Tg core), PLI-HOMO (13,725 / 7,733 Tg), GEN-LIB (unlabelled) | **REPLACE** | CoRE was not used in the shipped loop. The polymer tables are 4–20× smaller and, unlike the MOF tables, carry measurement noise and licence restrictions |
| **MOF2Zeo** (128-d categorical embeddings → 7 Zeo++ descriptors; 545,107/84,228 train/val; avg R² 0.99; triage only) | **PolyNet-G**: monomer-pair fingerprint + f + architecture → G = (ρ, CED, FFV, C∞); cold-started from van Krevelen GC; trained on the growing MD ledger | **REPLACE** | the *role* — cheap surrogate pre-ranks Beam 1 within a window widened by measured MAE, and never gates — is the most important thing to preserve. The categorical-embedding body does not transfer to SMILES + continuous composition |
| **Four beams** (Z full / A chem / F metal-only / R random) | Z full / A chemistry-only / F backbone-only / R random + **Beam 1c composition sweep** | **ADAPT + NEW** | axis mapping in §6.1; four fixes in §6.2; the composition sweep is new and is what makes a continuous axis attributable |
| **Sampling strata** (metal round-robin, identity only, target never read) | **backbone-class round-robin**, identity only | **ADAPT** | `sampling_strata.py` (160 l.) ports with the stratum key swapped. The config calls metal stratification "the only fully cross-app-validated universal lever" and credits it as "the primary mechanism for raising the absolute performance ceiling" (C9) — keep the discipline, including `SHUFFLE_METAL_ORDER` defaulting off and the OLD clone's multi-key `STRATA_MODE` |
| **Memory ledger** (global_best, top-10 frontier, geometry envelope, per-iteration history, facts-only renderer) | same + **`md_refs`** (provenance and CI per frontier entry) | **PORT-AS-IS + NEW field** | `memory_ledger.py` (673 l.) needs two constant swaps. Document the beam asymmetry correctly (C8 refuted): all four beams feed `beam_medians`/history; only the three hypothesis beams feed best/frontier/envelope |
| **Feedback generator** (4-beam tables, chemistry profile, pattern summary, geometry profile, diagnostic footer, ≤10 sampled per beam) | same structure; new `Src` and `Gate` columns, monomer profile, **Fox-residual line**, **noise-floor footer**, binned values | **ADAPT** | `feedback_generator.py` (910 l.): the scaffolding is domain-agnostic, every column list and hint sentence is MOF-specific |
| **Oracle: PORMAKE → LAMMPS/UFF → Zeo++ → RASPA3 GCMC** | **T0/T1 (loop) + T2 MD for G (Zeo++ role) + T3 MD for Tg (RASPA role)**, RadonPy builder → LAMMPS GAFF2_mod | **REPLACE** | the ladder shape is preserved exactly — predict cheap, recompute the gate, measure the target — but every stage is different software with a 100–1,500× higher unit cost (§5.2) |
| **HPC runner** (batch_manifest.json → per-job JSON + `.DONE` → batch_results.json; PBS over SSH; poll 300 s; 24 h ceiling; SimCache) | same contract, re-expressed through `config/hpc.json` + `scripts/submit.py` per the `hpc-submit` skill and CALF20's ADR-0007 | **ADAPT** | the manifest/DONE/aggregate job-array contract (interface #7) is clean and dirac is also PBS. The skill mandates the config/submit convention and warns that "Dropbox file locks are unreliable → ledger corruption" — which is also why the repo must not live in Dropbox |
| **GA / BO baselines** (Note S6/S7: 40 evals × 10 iters, pop 200, 20 gens, LVGP + EI) | same shapes over the copolymer space, with a **continuous f dimension** for BO and **our T1 surrogate** for GA | **ADAPT** | LLM4MOF's GA surrogate had held-out R² ≈ 0; repeating that makes the comparison worthless. BO gains a real advantage from continuous f and must be expected to be strong |
| **Evaluation protocol** (beam medians, DB percentiles, hit rate/enrichment, 5 replicates, ablation, label accounting) | same + **Δ_MD audit**, noise band, n-per-beam, dual percentiles, Wilson intervals, memorisation share, shortcut probe, two-currency budget | **ADAPT + NEW** | this is where the port must exceed the original; the aide2 battery driver (`run_battery.py` 233 l. + `parse_results.py` 213 l.) is the harness LLM4MOF itself lacks and ports as-is |
| **Backend benchmark** (6 backends × 7 tasks × 5 replicates, Agent 2 pinned, first attempt only) | same design, 3–4 backends × 5 DB tasks × 5 replicates | **ADAPT (descope)** | the result to replicate is the *insensitivity* (91.3 / 91.3 / 91.2 / 86.7 / 86.6 / 79.5; C14 confirmed), but between-arm SD 3.9–13.3 vs within-arm SD 8.3–14.8 percentile points means the ranking is mostly noise, and the no-match-retry bug (E5) confounds the bottom arm. Descope to 3–4 backends and report the no-match rate as a first-class result. Also: the Claude provider used for three Table-1 arms **is not wired into the shipped `llm_client.py`** (C18) — add the Anthropic branch |
| — | **MD-LEDGER** (append-only JSONL, keyed by `(cand_id, protocol_hash)`) | **NEW** | the only redistributable quantitative asset; the PolyNet-G training set; the calibration record |
| — | **Calibration harness** (structure-keyed anchor set → Tg_exp = a·Tg_MD + b with CI; 2 % density gate) | **NEW** | MOF GCMC needs no calibration; MD Tg carries +40 to +120 K |
| — | **Composition grid + Fox/GC layer** | **NEW** | the continuous axis and its analytic null |
| — | **Audit sampler** (pre-registered 10/10/10 draw, hashed into the manifest before submission) | **NEW** | the structural answer to "you only simulated your winners" |
| — | **Provenance-tier guard** (check-gate test) | **NEW** | makes the T1-never-reported rule mechanical |
| `filter_candidate.py`, `run_simulation.py`, `_pacman_worker.py`, `core/simulation/**`, `name_resolver.py` | — | **DROP** | CIF/Zeo++/RASPA/PACMAN/BB-dictionary specific. `name_resolver` is replaced by a monomer-name resolver (PoLyInfo names are already text) |

---

## 11. What LLM4MOF must change so the claims survive "is the property real?"

Ten items. Items 1–4 are structural and are built into this strategy; 5–10 are reporting discipline.

1. **Ground truth must be measured by a channel the loop did not use to select.** LLM4MOF's DB mode filters the very table it scores; its discovery mode ranks with the same RASPA pipeline it reports. → the pre-registered 30-candidate T3 audit, drawn 10/10/10.
2. **The gate must not be the target.** Preserved by gating on G and measuring Tg.
3. **Oracle scope must be stated per task.** LLM4MOF does this exactly once — for C2H6/C2H4, where it admits "the force field used here does not represent the π-complexation" — and nowhere else, which is why the CO₂ open-metal-site "discovery" turned out to be a property of the hMOF labels (C21). → every campaign states: *"Tg by GAFF2_mod all-atom MD at 10⁹–10¹¹ K/s cooling, 3,600-atom cells, 3 replicates, calibrated by Tg_exp = a·Tg_MD + b (a, b, CI given); claims are about this oracle."*
4. **The "label-free" claim must be dropped or earned.** → T0-only headline arm.
5. **Publish the oracle's noise floor.** 7.0 K median replicate SD, 33.1 K p90, 120 K p99, and ±~40 K for a 3-replicate MD Tg. Drawn on every plot.
6. **Report n per beam per point.** Z n went 1 → 43 while R n = 9,533 (C23); a "median" over one candidate is not a median.
7. **Pre-register and publish the supervised-shortcut probe.** 0.943 on MOFs. Saying it first is the difference between a caveat and a rebuttal.
8. **Pre-register and publish the zero-feedback floor.** 0.44 / 0.44 / 0.72 on MOFs; higher expected for polymer Tg.
9. **Account the budget in core-hours, not just oracle calls,** and include the surrogate. LLM4MOF's 190 free relax+Zeo++ per iteration and its 629,335-record surrogate sit outside the accounting.
10. **Replace bare enrichment ratios with counts and intervals,** and never pair an iteration-10 statistic with a pooled reference (E7).

One more, procedural: **use the OLD clone as the runnable reference.** The NEW HEAD (5adb33e, 2026-09-09) cannot run — `config.py` exports `UNIFIED_ONTOLOGY_PATH` while `constraint_utils.py` imports `UNIFIED_VOCABULARY_PATH`, and `live_runner.py` imports the non-existent `core.han_safe_topologies` (C17 confirmed; nuance from E2: the ImportError is deferred to the first *call* of `get_approved_vocab()` at `Matchmaker.__init__` line 78, so a naive import check passes). The two git histories are unrelated. Env toggles are `LLM2POR_*` in NEW's code but `LLM4MOF_*` in its own README and `.env.example` (C19). Take the loop from OLD (f1d731a) and the new domains, prompts and source data from NEW.

---

## 12. (k) Milestones with measurable exit criteria

| ID | Milestone | Exit criteria (all measurable) | Parallel-safe with |
|---|---|---|---|
| **M0** | **Data foundation** — loader + validator implementing §3.4 of the audit | CSV loads UTF-8 with exactly 9 U+FFFD and 42,557 rows; XLSX 13,725 rows; P908186 recorded as a known gap; 10,163 Tg replicate groups; usable cores reproduce at **13,350 rows / 2,735 ids** and **6,917 / 1,381**; 378-id monotonicity set median \|ρ\| ≥ 0.85; trimer key separates all 5 XLSX + 2 CSV + 1 cross-file false merges; validator report emitted before any consumer runs | — (blocks everything) |
| **M1** | **Design-space builder** | SMiPoly reproduces its published **169,347 polymers from its own 1,083 monomers** (installation correctness check); mechanism-class assignment produced for ≥1,059 Tier-A and ≥10⁴ Tier-B monomers; \|D\| computed by the matched-sum formula with real n_c; ≥10⁶ valid candidates; 100 % two-star validity; trimer-key novelty rate vs the 18,500 known keys reported; **Huang 2022 PDF read and the M/AD/SD taxonomy either ratified into the vocabulary or dropped** | M2, M3 |
| **M2** | **MD protocol + measured cost on dirac** — *the gate for the entire campaign design* | `config/hpc.json` + `scripts/submit.py` in place and a job round-trips; **measured core-h/ns on dirac at 3,600 and 10,000 atoms** (predicted 5.5 and 20.3); RadonPy + Psi4 install verified or a documented fallback (PSP/EMC) chosen; end-to-end T3 Tg for 3 anchors (PS, PMMA, PE) × 3 replicates; **measured replicate CI** (predicted ±35–45 K); **measured offset vs experiment** (literature band +38 to +120 K); finite-size error between the two cell sizes quantified; SimPoly/PolyArena spike closed with go/no-go | M1, M3 |
| **M3** | **Oracle ladder** | T0 van Krevelen implementation reproduces the book/Kaggle Tg values for 20 hand-checked polymers within 15 K; T1 surrogate scaffold-held-out RMSE reported (target ≤ 40 K = literature-normal, **not** SOTA); PolyNet-G cold-start MAE per G descriptor recorded; **supervised-shortcut probe OOF R² published**; held-out oracle frozen and hashed | M1, M2 |
| **M4** | **Loop port, DB mode** | a 10-iteration campaign completes in < 10 min wall on the laptop (LLM4MOF's DB campaigns: mean 353 s, n = 160); all 9 stable interfaces implemented and schema-checked; zero-match iterations retried not consumed, with `no_match_retries` logged; n-per-beam in every artefact; provenance-tier guard test passing; token/cost per campaign measured | after M0, M3 |
| **M5** | **Variance, controls, pre-registration** — *no result may be claimed before this closes* | 10 replicates × 3 DB tasks; σ of the final percentile measured (MOF reference 6.4 / 15.9 / 6.9); zero-feedback arm run and memorisation share reported; MDE computed and the replicate count for the main study chosen from it; pre-registration document committed and hashed (audit draw rule, probe, controls, metric definitions) | no |
| **M6** | **Discovery mode + MD audit** | one full campaign: 10 iterations, 80 in-loop T2 runs, 30 pre-registered T3 runs, ≈82,905 core-h; **Δ_MD reported with Mann–Whitney p and per-candidate CI**; surrogate-vs-MD calibration reported per iteration; every MD Tg reported raw and calibrated; `tg_unreliable` flags from the 2 % density gate counted | after M5 |
| **M7** | **Baselines under matched budget** | B1–B7 run; realised budget per replicate within ±5 % across arms; both currencies reported; GA's surrogate held-out R² reported (must not be ≈ 0); T0-only and T1 arms both reported with their label counts | after M5, parallel with M6 |
| **M8** | **Composition-sweep diagnostic** | Fox-residual curves δ(f) measured by T2 for ≥3 winning pairs on the full 9-point grid (9 × 288 = 2,592 core-h each); compared with Fox, Gordon–Taylor and Kwei; sign of δ compared with the M/AD/SD and UCST/LCST predictions | after M6 |

**Parallel-safe sets:** {M1, M2, M3} run concurrently after M0. {M6, M7} run concurrently after M5. M8 follows M6. M2 is the long pole and should start on day one of the parallel phase because its measured core-h/ns can invalidate the entire campaign design.

---

## 13. (l) Decisions only the user can make

| # | Decision | Blocks | Why it cannot be settled from the files |
|---|---|---|---|
| **D1** | **May PoLyInfo-derived rows be transmitted to a hosted LLM API?** (binary) And is NIMS written permission being sought for a released surrogate? | M4, every campaign | Art. 10(1) prohibits distribution of DATA/Processed DATA and is silent on transmission to a third-party inference endpoint; the Terms mention ML zero times. A "no" is survivable (local model + binned feedback) but changes the architecture |
| **D2** | **dirac allocation:** sustained core count, per-job wall limit, queue name, and **does dirac expose GPU nodes?** | M2, and the entire campaign budget | the `hpc-submit` skill has 0 occurrences of gpu/cuda; only a `cuda100/111` module on dirac1 is recorded in CALF20's HPC-ENV.md. At 128 vs 512 cores the five-replicate campaign is 135 vs 34 days |
| **D3** | **Headline property: Tg, or density as the proof-of-concept with Tg as the headline?** | M3, M6 | density is the only cheap MD quantity that is quantitatively validated (R² 0.89–0.95 vs PoLyInfo/Bicerano) and is ~3× cheaper, but has only 1,651 labels vs 7,733 for Tg. Oracle-first logic favours proving the machinery on density |
| **D4** | **Copolymer or homopolymer as the primary mode?** | M1, M4 | the composition axis is the novelty *and* the corrupted axis (D1); the homopolymer path is clean but has no continuous axis and therefore no Beam 1c |
| **D5** | **Headline configuration: T0-only (label-free) or T1-in-loop (stronger)?** | M4, M7, and the abstract | this is the claim-strength vs defensibility trade-off of §8.3 rule 3 |
| **D6** | **Modelling policy:** merge or separate cis/trans and tacticity variants; aggregate replicates to group medians or model at sample level; **average, keep or drop the 30 conflicting XLSX duplicate-structure Tg groups (max spread 169 K)**; drop or model the 42.6 % composition-less rows | M0 | preference choices with no data-internal answer; averaging a 169 K conflict manufactures a value |
| **D7** | **Library licence choice:** SMiPoly (BSD-3) only, or also OMG (**GPL-3.0**, which would make a derived generator copyleft)? | M1 | a release-licence decision |
| **D8** | **Backend and keys:** none of ANTHROPIC/OPENAI/GOOGLE/GEMINI/HF is set in any scope. Which provider, and is a backend benchmark (3–4 backends × 5 tasks × 5 replicates) in scope? | M4 | no key exists on the machine; the benchmark is ~100 campaigns of API spend |
| **D9** | **Can the owner re-export from PoLyInfo?** Specifically: `component3..5` for the 4,243–7,389 truncated terpolymer rows, the per-sample component records that would resolve the 5,309 undetermined bindings, a canonical component-id → SMILES table, the un-truncated P908185/P908186 records, and a non-corrupt `copolymer.zip` | M0 scope, and the size of the composition-aware table | these are missing-data problems; constraint propagation resolves ~1,964 of 2,635 ids and nothing recovers the dropped third components |
| **D10** | **Repo location and stack:** outside Dropbox (the `hpc-submit` skill warns "Dropbox file locks are unreliable → ledger corruption", and the MD ledger is append-only JSONL); adopt CALF20's pixi + `src/` + single `check.py` gate + MADR ADRs + OMC-disabled convention? | M0 | `Dropbox/Work to do/LLM4POL` is not a git repo; CALF20 is the house precedent and lives on the Desktop |
| **D11** | **Create a CUDA torch environment for the RTX 5050?** | polyBERT/GNN surrogate speed only | no environment has CUDA torch; Blackwell needs a CUDA 12.8+/13.x wheel. The strategy is designed not to require it |
| **D12** | **Is a synthesis collaborator available?** | the target venue | every 2025–2026 Nature-portfolio polymer inverse-design paper found carries experimental or MD validation (polyBART, POLYT5, Kern thiocane, Zheng vitrimer, SPACIER); LLM4MOF declined experimental validation and had to release artefacts instead |

---

## 14. (m) Risks

| ID | Risk | Evidence that it is real | Mitigation built into this strategy |
|---|---|---|---|
| **R1** | **MD cost is 2–3× the estimate and the campaign design collapses.** | the cost table is a scaling estimate from LAMMPS documentation and RadonPy's 40-core anchor; nothing has been measured on dirac | **M2 measures before anything is committed**, and is a gate not a task. Fallbacks, in order: 3,600-atom cells (already assumed), density-only target (D3), SimPoly MLFF spike, GPU nodes if D2 says yes |
| **R2** | **The Fox equation wins.** | Fox reaches R² 0.835 / RMSE 42.57 °C on PoLyInfo copolymers, costs nothing, and is 70 years old. If an LLM loop cannot beat Fox + GC on copolymer Tg there is no paper | **reframe the objective so Fox is the null, not the competitor**: task DB5 and discovery task 2 maximise the Fox *residual* δ(f), which Fox by construction cannot optimise. This is the single most important framing decision in the document |
| **R3** | **Memorisation dominates and the loop is a lookup.** | aide2 measured floor-corrected memorisation share 0.44 / 0.44 / **0.72** with feedback entirely removed (C20); the band-gap task was "dominated by parametric memory". Every frontier LLM knows PS Tg ≈ 100 °C, PMMA ≈ 105 °C, PEEK ≈ 143 °C | the discovery space is **generated** (Tier B) and largely absent from PoLyInfo, so there is less to recall; trimer-key novelty is reported; the zero-feedback arm runs in **M5, before any result is claimed** |
| **R4** | **Replicate noise swamps every effect.** | two independent noise sources: the table (SD p50 7.0 K, p90 33.1 K) and MD (±~40 K at 3 replicates); plus campaign-level σ of 6.4–15.9 percentile points and the W2 finding that across 210 seeded campaigns no variant beat the production configuration at Holm significance | M5 precedes all claims and sets the replicate count from a computed MDE; tasks are chosen for large expected effects (Tg spans 138–768 K); the noise band is drawn on every plot and stated to the agent |
| **R5** | **The loop is circular — the surrogate is both proposer and judge.** | the structural risk of any surrogate-in-the-loop design; aide2's probe showed the failure mode concretely even where a physics oracle existed | six mechanisms in §5.6, of which the provenance-tier guard and the pre-registered 10/10/10 audit draw are mechanical rather than cultural |
| **R6** | **Licence blocks the feedback payload or the release.** | Art. 10(1)-(3),(5); zero mentions of ML; the audit's own interpretation is that a released model needs written permission | binned/derived feedback; the loop runs end-to-end with T0 only; the MD ledger on generated candidates is the released asset; D1 is ratified before M4 |
| **R7** | **RadonPy/Psi4 will not install on dirac.** | Psi4 ≥ 1.5 is required for RESP charges and is not pip-installable (REF-101, confirmed) | M2 spike with named fallbacks: PSP (MIT, but homopolymer-only — and note the "homopolymers only" sentence was *not* located in the accessible full text, so verify), EMC (what PolyJarvis uses as primary builder), or Polyply. Charges can also be taken from a library rather than computed |
| **R8** | **The composition axis is unusable because of D1.** | ~30 % of resolvable rows swapped; 5,309 rows undetermined with the mixing test favouring the *reverse* binding; only 6,917 rows / 1,381 ids survive with parsed compositions | DB mode gates on composition only for DB5; the composition axis does its real work in discovery mode where f is chosen, not read; the 378-id monotonicity regression test (≥0.85) guards the loader |
| **R9** | **No referee has a mental model for beam attribution in polymers.** | zero of the twelve surveyed polymer systems does controlled-arm attribution | the Fox-residual framing gives referees a familiar null model; the interpretability criteria I1–I4 are numbers, not narrative |
| **R10** | **The port inherits LLM4MOF's unfixed defects.** | NEW HEAD cannot run (C17/E2); env toggles misnamed between code and docs (C19); the Claude provider used for three Table-1 arms is absent from `llm_client.py` (C18); the Beam-1 hint quotes a stale 15-candidate quota (E10a); MOF2Zeo training data not shipped | build from the OLD clone; add the Anthropic branch; the interface list (§3.2 of the anatomy) is the contract to implement against, not the code |
| **R11** | **Token cost grows without bound.** | the transcript is never trimmed (E4) and cost rose $0.03 → $0.19 per iteration; polymer beam tables are wider (Src, Gate, G columns, noise footer) | implement the compression the SI describes and measure both arms; per-replicate cost is a reported metric |
| **R12** | **The MD audit at n = 10 vs 10 is underpowered.** | with ±40 K per-candidate CI, a one-sided Mann–Whitney at 10 vs 10 detects only large effects | choose large-effect tasks; report the effect size and CI rather than only p; if M2 shows cheaper MD than estimated, the first thing to buy is more audit candidates, not more iterations |
| **R13** | **dirac queue contention makes wall-clock unpredictable.** | LLM4MOF's own discovery wall-clock is unreported ("GCMC dominates the overall wall-clock time"); its poller allows 24 h per round and resubmission was disabled after a cluster-admin request | the T2 audit is 8 small 8-core jobs per iteration (not 190 jobs of 4 h walltime), which is a far gentler queue profile; the `.DONE`-sentinel contract tolerates arbitrary delay; `SimCache` makes re-runs free |

---

## Appendix A — Corrections to the input documents that this strategy relies on

Facts used here that differ from the input reports, all taken from the verification packets:

| Input | Correction |
|---|---|
| Anatomy §2.5 and §6 | design space is **not** 518 × 156 × 952 = 12,499,656. The product is 76,929,216; the SI's figure is the connectivity-matched sum Σ_c n_c t_c × L = 80,126 × 156. 6.15× overstatement if the formula is copied (C5) |
| Anatomy §2.8 | the ledger **does** ingest the sampled random beam (`_ALL_BEAMS` drives `beam_medians` and `_detect_outside_promising`); only best/frontier/envelope are restricted to the three hypothesis beams (C8) |
| Anatomy §2.2, §2.8 | Agent 1's context is **not** compressed; the full transcript is re-sent every iteration and the ledger is an addition on top of it (E4). Note S11's ablation therefore measures "ledger on top of full history" |
| Anatomy §2.1 | zero-match iterations are retried only in discovery mode; DB mode consumes them (C1 caveat, E5) |
| Anatomy §5 | W2's grid is 42 cells × 5 replicates over 8 variant labels × 2 budgets × 3 tasks, not 14 × 3 × 2 (C22) |
| Anatomy §1.2, §1.3, §6 | "SF₆ 7.7 vs 2.8" pairs an iteration-10 statistic with a pooled reference; the iteration-10 random median is 2.55 (E7) |
| Landscape §1.4 take-away | "rank-ordering is reliable (R² 0.83–0.92)" — the 0.83 is Martí's **ML-model-on-MD-values** R², not MD-vs-experiment (REF-105 refuted). Afzal's MD-vs-experiment Tg R² = 0.92 is real and is the figure to cite |
| Landscape §1.5, line 60 | REF-112 authors are **Karuth, Alesadi, Xia, Rasulev** (2021) — "Cao, Li" are not authors |
| Landscape §5, line 179 | REF-134's sole author is **Luis A. Miccio**, not "Borredon, Schwartz et al." |
| Landscape §7 | REF-140's mechanism is inverted: electrostatic and H-bonding drive **short**-chain PFAS adsorption; hydrophobic/fluorophilic improve **long**-chain. URL dead — cite doi 10.1021/jacs.5c04689 |
| Landscape §7 | REF-141 is unverifiable under the quoted title; the peer-reviewed work is Dhamania & Moon, *Energy & Environmental Materials* 2026, doi 10.1002/eem2.70435 |
| Landscape §2.1 | REF-115's arXiv id carries a different title; cite Macromolecules 2025, 58(13), 6407–6417, doi 10.1021/acs.macromol.5c00178 |
| Landscape §1.6 | REF-143's size-independent band is 226–232 katom-step/s, not 219–232 |
| Landscape §2.2 | REF-148's M/AD/SD taxonomy is **not** verified against an accessible source — read the PDF before hard-coding it as vocabulary (M1 exit criterion) |
| Landscape §1.4 | REF-110's "single-replica 95 % CI 60–80 K" is an N^−0.5 extrapolation, not a quotation; REF-106's "≈30 K across 5000→5 K/ns" was not located; REF-102's cooling-rate sentence is not a verbatim quote |

## Appendix B — Reproducing the arithmetic

`scratchpad/oracle_budget.py` — LAMMPS throughput → core-h/ns → per-stage → T2/T3 per candidate → throughput per allocation → campaign totals → the naive-port comparison.
`scratchpad/space.py` — inventory counts → pair counts → naive vs mechanism-matched design space → LLM4MOF's own C5 error → DB-mode table sizes.

Both are read-only with respect to every source file and write nothing under Dropbox.
