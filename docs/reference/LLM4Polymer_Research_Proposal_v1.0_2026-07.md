> **Pre-charter concept document (LLM4Polymer v1.0, July 2026).** Copied verbatim on 2026-09-11 from the owner's Dropbox (`Paper review/raw/LLM4Polymer/LLM4Polymer_Research_Proposal.md`) as an INPUT to the LLM4POL charter.
> It is not an approved plan: nothing in it is binding, and it will be superseded by `docs/MASTER-PLAN.md` once that is written and approved.
> The verified data facts it should be read against are in `docs/audit/DATA-FOUNDATION-REPORT.md`.

---

# LLM4Polymer: Interpretable, Regime-Aware Inverse Design of Polymers

**A closed-loop framework coupling LLM reasoning, intelligent surrogate selection, and diagnostic-beam attribution**

---

| | |
|---|---|
| **Version** | 1.0 — Concept / Pre-proposal |
| **Date** | July 2026 |
| **Status** | Draft for discussion |
| **Primary dataset** | 13,725 homopolymers (PSMILES + canonical SMILES + 8 properties) |
| **Phase 1 target** | Glass transition temperature (Tg) |
| **Phase 2 target** | PFAS-filtering polymers |

---

## 1. Executive Summary

LLM4Polymer is a closed-loop system for **interpretable** inverse design of polymers. Where most existing systems optimize for prediction accuracy or end-to-end generation, LLM4Polymer optimizes for **mechanistic understanding**: it reveals *which* chemical factors (aromaticity, backbone rigidity, hydrogen bonding, free volume, etc.) drive a target property, and by how much.

The framework rests on three ideas that, in combination, are not present in the current literature:

1. **Diagnostic-beam attribution** adapted from LLM4MOF — instead of testing one structure many ways, the system runs controlled "beams" that vary one chemical factor at a time to expose causal contribution rather than correlation.
2. **A surrogate meta-loop** — before the main design loop runs, an LLM agent explicitly selects, validates, and ranks candidate ML surrogates against held-out data, and flags extrapolation risk. This prevents silent failure when a surrogate is applied outside its valid domain (e.g., using a bulk-Tg model to guess PFAS adsorption).
3. **Regime-aware modeling** — borrowing the laminar/turbulent boundary concept from chemical engineering, the design space is partitioned into chemical *regimes*. Each regime carries its own minimal descriptor set, its own trusted surrogates, and its own complexity budget. This keeps the LLM reasoning at the *right level of abstraction* instead of drowning it in a universal ontology.

The project is staged: a low-cost proof-of-concept on an existing labeled database (Tg), followed by a harder, sparse-data extension (PFAS filtering), with optional molecular-dynamics validation at the end.

---

## 2. Motivation

### 2.1 Why polymers are harder than MOFs

The direct inspiration, LLM4MOF, works because a MOF is fully specified by a small discrete choice — metal node, linker, topology — that can be serialized to a CIF file and simulated cheaply. Polymers break every one of those assumptions.

| Aspect | MOF | Polymer |
|---|---|---|
| Specification | Node + linker + topology (fully discrete) | Repeat unit + chain length (Mn) + dispersity + tacticity + morphology (mixed discrete/continuous) |
| Simulatable artifact | CIF, deterministic | Amorphous cell built by MD; conformation is emergent, not given |
| Evaluation cost | Seconds (GCMC) | Hours (all-atom MD) — or milliseconds via ML surrogate |
| Structure→property | Geometry largely determines adsorption | Multiscale: chemistry → conformation → morphology → bulk property; processing history matters |
| Data | Large, clean (CoRE, hMOF, QMOF) | Sparse, heterogeneous (PolyInfo-derived) |

A single repeat-unit SMILES is therefore **not** a full material specification. "Polyethylene" can be a wax or a structural plastic depending on Mn; polypropylene can be a rigid crystalline solid or a soft rubber depending on tacticity. Any serious design framework has to decide *which layer it is optimizing* and be explicit about it.

### 2.2 The interpretability gap

Modern polymer ML predicts Tg well (R² ≈ 0.85 with transformer models), but the prediction is a black box: it does not say whether a high-Tg candidate wins on aromatic content, backbone rigidity, or hydrogen bonding. That gap matters because chemists iterate on *reasons*, and because mechanistic rules transfer to new chemistry while point predictions do not.

---

## 3. Related Work and the Novelty Gap

**LLM-driven polymer design (recent):**

- **PolyAgent / Polymer-Agent (2026)** — closed-loop inverse design; generates SMILES for target properties via latent-space optimization. *No mechanistic attribution.*
- **PolyJarvis (2026)** — couples an LLM with the RadonPy MD pipeline for end-to-end property prediction. *Powerful but simulation-heavy; no attribution layer.*
- **PolySea (2025)** — a domain-specific fine-tuned polymer LLM for prediction and inverse design. *Model-centric, not loop-centric.*

**Interpretable design in adjacent domains:**

- **LLM4MOF (2026)** — diagnostic beams for causal attribution, but only for MOFs.
- **Dangayach et al. (2025)** — ML inverse design for polymeric membranes including PFAS removal, but single-surrogate and no beam attribution.

**Where LLM4Polymer is new:** No published system combines (a) diagnostic-beam attribution for polymers, (b) an explicit surrogate-selection meta-loop with validation and extrapolation-risk flagging, and (c) regime boundaries that control the abstraction level of LLM reasoning. Any one of these is incremental; together they define the contribution.

---

## 4. Objectives and Specific Aims

**Primary objective:** Develop an interpretable, regime-aware, closed-loop inverse-design framework for polymers that produces not just candidate structures but the causal reasoning behind them.

- **Aim 1 — Proof of concept (beams on Tg).** Show that diagnostic beams over the 13.7k database reveal causal factor contributions to Tg, validated by cross-validation.
- **Aim 2 — Surrogate meta-loop.** Build the descriptor ontology + dependency map and a meta-loop that selects and validates surrogates; show it lowers surrogate-failure rate versus a naive single-surrogate baseline.
- **Aim 3 — Regime-aware sparse-data extension (PFAS).** Curate a small PFAS-adsorption dataset, and show that regime-aware modeling handles the sparse, out-of-distribution regime more safely than a universal model.
- **Aim 4 — (Optional) MD validation.** Ground-truth the top candidates via RadonPy/PolyJarvis and check whether beam-derived mechanistic claims survive contact with simulation.

---

## 5. The Regime Concept (Core Design Principle)

Chemical engineering does not model every flow with the full Navier–Stokes equations; it uses the Reynolds number to declare a regime (laminar vs. turbulent) and then applies the appropriate simplified treatment. LLM4Polymer applies the same philosophy to chemistry: **partition polymers into regimes, and let each regime fix its own descriptor set, trusted surrogates, and complexity budget.** This is what keeps the LLM at the right level of abstraction.

| Regime | Representative polymers | Minimal descriptor set | Complexity | Trusted oracle | Reliable properties |
|---|---|---|---|---|---|
| **R1 — Saturated hydrocarbons** | PE, PP, PB | backbone flexibility, Mn | Low | Fast tree model | Tg, Tm, density |
| **R2 — Aromatic / engineered** | PS, PEEK, polyimide | aromaticity, backbone rigidity, heteroatom fraction | Medium | Transformer or tree | Tg, modulus, thermal stability |
| **R3 — Polar / H-bonding** | polyamide, PU, PC | H-donors, H-acceptors, polarity, aromatic content | Medium–High | Domain model | Tg, modulus, solvent resistance |
| **R4 — Functional / separation** | PFAS adsorbents, ion-exchange | free volume, pore structure, surface chemistry, polarity | High | ML surrogate + MD validation | adsorption capacity, permeability |
| **R5 — Complex architectures** | block copolymers, thermosets, dendrimers | architecture, branching, crosslink density, segment interaction | Very High | Mostly simulation | phase behavior, mechanical, processing |

**Boundary conditions** define when a design problem crosses from one regime into the next (e.g., appearance of aromatic rings moves R1 → R2; a hard requirement on adsorption selectivity forces R4 and triggers MD validation). The agent's *first* decision is always "which regime is this?" — and that decision determines everything downstream.

---

## 6. System Architecture

```
USER QUERY
    |
    v
[1] REGIME CLASSIFICATION  ── which regime? sets descriptor set + complexity budget
    |
    v
[2] META-LOOP: SURROGATE SELECTION
       - consult descriptor ontology + dependency map for this regime
       - propose candidate surrogates
       - validate each on held-out data (R2, coverage, extrapolation risk)
       - rank; keep only those above confidence threshold
    |
    v
[3] MAIN LOOP: HYPOTHESIS TESTING (diagnostic beams)
       Agent 1: propose N chemical hypotheses
       Agent 2: translate each to descriptor constraints; build 4 beams/hypothesis
                (beams vary ONE factor at a time)
       score all candidates through the selected surrogate(s)
       compare beams -> attribute causal contribution of each factor
       (inner descriptor-relaxation loop refines constraints)
    |
    v
[4] (OPTIONAL) MD VALIDATION on top candidates (RadonPy / PolyJarvis)
    |
    v
REPORT: candidate structures + per-factor attribution + confidence + validation status
```

### 6.1 Two nested loops (a design clarification)

- **Inner — descriptor-constraint reasoning:** within a single hypothesis, the LLM tightens/relaxes individual descriptor thresholds and observes the effect (fast, interpretable). This is the LLM4MOF-style constraint move.
- **Outer — surrogate meta-selection:** *before* the main loop, the LLM reasons about *which model to trust at all* for this regime and objective. These loops are orthogonal and complementary; the framework uses both.

---

## 7. Descriptor Ontology and Dependency Map

The ontology is deliberately shallow — a few families, each with a handful of descriptors — so the LLM reasons over descriptor *families* (Level 2) and only drills into individual descriptors (Level 3) when a regime demands it. Level 4 metadata (interaction terms, per-paper confidence, non-drivers) is stored but **not** shown to the agent during reasoning; it is used for validation and reporting only.

```
POLYMER DESCRIPTORS
├── Structural — backbone     : aromaticity, backbone rigidity, conjugation length
├── Structural — sidechains   : sidechain bulk, sidechain polarity, heteroatom fraction
├── Interactions              : H-bond donors, H-bond acceptors, dipole, polarizability
├── Topology                  : molecular weight, branching, crosslink density
└── Emergent                  : free volume, packing fraction, crystallinity
```

Each descriptor carries: definition, units, typical range, and an RDKit (or simulation) extraction method. The **dependency map** links descriptors to properties with a direction (positive/negative), a qualitative strength, and a provenance tag. Crucially, each entry is dual-sourced:

- **hand-curated** from a literature pass, and
- **empirical**, from SHAP / permutation importance on surrogates trained on the 13.7k database.

Disagreements between the two are flagged for human review rather than silently averaged. This dual sourcing is also what feeds the regime definitions and the meta-loop's relevance scoring.

---

## 8. Data

### 8.1 Primary database (in hand)

13,725 homopolymers, each with a PSMILES repeat unit and canonical SMILES, plus eight properties. Coverage is uneven and this shapes the staging:

| Property | Coverage | Notes |
|---|---|---|
| Tg | ~56% (7,733) | Richest, cleanest → Phase 1 anchor |
| Melting temp | ~27% (3,696) | Secondary target |
| Density | ~12% (1,651) | Tertiary |
| Volume resistivity | ~9% | Sparse |
| Electrical conductivity | ~9% | Sparse |
| Elongation at break | ~8% | Sparse **and unit-labeling issue** |
| Tensile modulus | ~7% | Sparse |
| Tensile stress at break | ~8% | Sparse **and physically implausible tail** |

Sparsity is severe per-row: most polymers carry only one property; only ~200 carry five or more. Joint multi-property optimization is therefore data-starved and is deliberately deferred.

### 8.2 Known data-quality actions (before modeling)

1. **Fix mechanical-property units.** "Elongation at break" is labeled in GPa but ranges up to ~3000 — elongation is a strain/percentage, not a stress. "Tensile stress at break" reaches ~64 GPa, which is unphysical for a neat polymer; the high tail is mislabeled or fiber/composite data. Audit and clip.
2. **Aggregate duplicate structures.** ~100 duplicate canonical SMILES (repeated measurements) → aggregate to a per-structure median before any training.

### 8.3 Secondary dataset (to build, Phase 2)

A curated PFAS-adsorption set (~200–500 polymers) from literature, storing structure, measured capacity, PFAS species, selectivity, and experimental conditions. This is the sparse, out-of-distribution regime the meta-loop and regime logic are designed to handle safely.

---

## 9. Phased Plan

### Phase 1 — Proof of concept (Weeks 1–4)
Pool-based, no simulation. Compute RDKit descriptors over the 13.7k; implement 5 Tg hypotheses × 4 beams; aggregate Tg per beam; produce a causal attribution ("aromaticity + rigidity synergize for high Tg"). Validate factor contributions with cross-validation. *Deliverable: working beam-attribution pipeline on Tg.*

### Phase 2 — Ontology + meta-loop + regimes (Weeks 5–8)
Build the ontology and dependency map; implement regime classification; implement the surrogate meta-loop (train XGBoost baseline on the 7.7k Tg labels; optionally fine-tune a pretrained polymer transformer). Curate the PFAS set and extend into regime R4, using the meta-loop to expose extrapolation risk. *Deliverable: regime-aware, surrogate-validated closed loop working for Tg and a first PFAS pass.*

### Phase 3 — Multi-property (Weeks 9–12)
Add Tm and density surrogates; let the meta-loop pick per-objective surrogates with per-objective confidence. Handle sparse labels with uncertainty quantification. *Deliverable: multi-objective, still-interpretable loop.*

### Phase 4 — MD validation (optional, post-MVP)
Send top candidates to RadonPy/PolyJarvis; compare surrogate predictions and beam-derived mechanistic claims to MD ground truth; feed results back to recalibrate surrogates and regime boundaries.

---

## 10. Evaluation

- **Attribution validity (Aim 1):** do beam-attributed factor contributions agree with held-out cross-validation and with SHAP importances? Are single-factor beams' effects reproducible?
- **Meta-loop value (Aim 2):** surrogate-failure rate and prediction error, meta-loop vs. naive single-surrogate baseline; does the loop correctly down-rank an irrelevant surrogate (e.g., modulus for PFAS)?
- **Regime safety (Aim 3):** on the sparse PFAS regime, does regime-aware modeling reduce confident-but-wrong predictions relative to a universal model? Is extrapolation risk flagged before it causes a bad recommendation?
- **Ground-truth agreement (Aim 4):** MD-vs-surrogate error on top candidates; survival of mechanistic claims under simulation.

---

## 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Repeat-unit SMILES omits Mn/tacticity/morphology | Fix processing variables explicitly in Phase 1; treat morphology as emergent and only resolve it at the MD-validation stage |
| PFAS properties absent from primary DB | Literature-mined secondary dataset + proxy descriptors; regime R4 forces MD validation for finalists |
| Sparse labels → unreliable surrogates | Meta-loop validation gate + extrapolation-risk flagging; refuse to over-trust thin models |
| Ontology too detailed → LLM overload | Regime-scoped, family-level (Level 2) reasoning by default; deep descriptors only when the regime requires |
| Data-quality errors (units, duplicates) | Mandatory cleaning pass (Section 8.2) before any training |
| MD too expensive for a loop | Two-tier oracle: fast surrogate inner loop, MD reserved for a handful of finalists |

---

## 12. Summary of Contributions

1. First adaptation of diagnostic-beam causal attribution from MOFs to polymers.
2. An explicit LLM surrogate meta-loop with validation and extrapolation-risk flagging.
3. Regime boundaries that control the abstraction level of LLM reasoning — a chemical analogue of laminar/turbulent regimes.
4. A staged, resource-aware path from an existing labeled database (Tg) to a hard, sparse, application-driven target (PFAS filtering), with optional MD grounding.

---

*Draft for discussion. Sections 5–7 (regimes, architecture, ontology) are the conceptual core and the most likely to evolve as Phase 1 results come in.*
