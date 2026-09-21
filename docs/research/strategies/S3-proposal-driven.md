# S3 — Proposal-Driven Porting Strategy for LLM4POL

**Angle:** take LLM4Polymer v1.0 (July 2026 pre-proposal) as the intended scientific contribution and work out, component by component, how LLM4MOF's machinery implements it — which parts carry the regimes, the surrogate meta-loop and the beams; what is genuinely new; and where the proposal collides with the data audit or the 2026 literature.

**Strategy name:** *Proposal-Faithful Port with a Deterministic Regime Router and Measured Attribution.*

Written 2026-09-11. Sources: `llm4mof/LLM4MOF-ANATOMY.md` (+ its fact-check packet, claims C1–C25, extra findings E1–E11), `landscape/POLYMER-LANDSCAPE.md` (+ its citation-check packet, REF-101…153), `audit/DATA-FOUNDATION-REPORT.md` §§1–8, and `LLM4Polymer_Research_Proposal.md` v1.0. Only `confirmed` claims from the verification packets are used; `refuted` ones are called out where the parent document would otherwise mislead the port.

---

## 0. Verdict in one page

The pre-proposal names three contributions. LLM4MOF already contains a carrier for two of them and nothing for the third. The port is not "add regimes and a meta-loop to LLM4MOF"; it is **demote two of the three ideas to deterministic machinery that LLM4MOF already proved, and spend the freed budget on the one thing LLM4MOF never did — measuring whether the attribution is true.**

| Pre-proposal claim | LLM4MOF carrier | Verdict for LLM4POL |
|---|---|---|
| **(1) Diagnostic-beam attribution for polymers** | The four beams: `set_z` (chemistry ∧ strict numeric gate), `set_a` (chemistry only), `set_f` (primary identity axis only), `df_total` (whole hidden table) — `sensitivity_analyzer.py:559-701`; live `_build_beam_specs` | **PORT, with two corrections.** The proposal's "beams vary ONE factor at a time" is wrong about the parent: the beams are a *nested relaxation ladder*, not an orthogonal factorial. And LLM4MOF emits **one** hypothesis per iteration, not N; alternatives live inside `linker_branches` as an OR-of-ANDs. "5 hypotheses × 4 beams" multiplies the oracle budget by 5 and destroys budget matching. |
| **(2) Surrogate meta-loop (select, validate, rank surrogates; flag extrapolation risk)** | Two deterministic mechanisms, no LLM: MOF2Zeo **pre-ranks only Beam 1 and never gates** (SI Note S5: "surrogate errors can affect which candidates are tried first, but cannot by themselves determine the final accepted geometry"); and `_apply_mae_slack` widens the constraint window by the surrogate's own per-descriptor MAE (di 0.746 Å, df 0.751, dif 0.828, sa 50.7, vf 0.0098, density 0.0152 — `live_runner.py:107-121`) | **SPLIT AND DEMOTE.** Offline: a pre-registered surrogate bake-off under leakage-aware splits — that is a one-time experiment, not a per-campaign LLM decision. Online: per-regime MAE-slack on the descriptor window, exactly `_apply_mae_slack`. Making surrogate selection an LLM call adds a third model call per campaign whose effect is unseparable from Agent 1's, in a system where aide2's W2 (210 seeded campaigns) already showed no configuration variant beat the hand-tuned baseline at Holm-corrected significance (max effect +1.80 σ, p_holm = 1.0). |
| **(3) Regime-aware modelling (laminar/turbulent analogy)** | `{DATABASE_MODE_RULES}` injected into Agent 2's system prompt at init (`agent2_handler.py:23-63`), plus `config.is_hmof_mode()/is_qmof_mode()` and keyword metric routing (`run_experiment.py:135-146`) | **PORT AS A DETERMINISTIC ROUTER, NOT AS THE AGENT'S FIRST DECISION.** In LLM4MOF the regime is chosen by the harness from the inquiry string and "the hypothesis-generating agent receives no signal indicating which mode it is running in" (SI Note S1). That mode-blindness is one of the design's cleanest controls. Letting an LLM classify the regime first introduces an unmeasured branch upstream of everything. Agent 1 may *propose* a regime; the router validates it against tags computed from the structure, and only the router's answer is binding — the same Layer-1/Layer-2 discipline as the vocabulary (SI Note S4: LLM enrichment "writes no fields that the Matchmaker filters against"). |
| **(not in the proposal, but the whole point)** | Nothing. LLM4MOF's interpretability "rests on the JSON being readable"; the aide2 probe showed OOF R² = 0.943 on the PORMAKE H2-vol 100 bar table from `vf/sa/density` alone, and that the celebrated CO₂ open-metal-site pivot is a property of the hMOF oracle (OMS median 4.49 < non-OMS 5.14) rather than a chemical discovery | **NEW AND HEADLINE.** Polymers have something MOFs do not: a literature-sanctioned, per-group, *numeric* attribution ground truth — van Krevelen group contributions (−CH₂− 158, p-phenylene 2820, −SO₂− 2150, −NHCO− 1510 in the molar glass-transition function) and the Fox mixing law for composition. LLM4POL can therefore **score** its beam attributions against an independent physical baseline. That is the answer to the parent paper's biggest reviewer wound, and it is the reason to do this port at all. |

**One-liner.** Implement LLM4Polymer v1.0 inside LLM4MOF's loop by demoting regimes to a deterministic Agent-2 rule router and the surrogate meta-loop to an offline bake-off plus an online MAE-slack window, keeping one hypothesis and four nested beams per iteration, and earning the word *interpretable* by scoring beam attribution against van Krevelen group contributions and the Fox law — which LLM4MOF structurally could not do.

**The three hard constraints that shape everything below**

1. **There is no cheap GCMC analogue for Tg.** All-atom MD Tg is 4,000–20,000 CPU-hours per candidate with 3–10 replicates and a systematic +40 to +120 K cooling-rate offset. On dirac at 256 cores that is 0.3–1.5 candidates/day. LLM4MOF's discovery mode spends 380 ± 2 GCMC runs plus ~1,900 build/relax/Zeo++ per campaign; the same design with MD Tg is 10⁷–10⁸ CPU-hours. **Database mode is the primary mode for LLM4POL, and that is an upgrade, not a compromise** — the DB-mode oracle is *measured experimental data*, so the "the design rule is an artefact of the force field" critique that lands on LLM4MOF's CO₂ and C₂ results does not exist here.
2. **The polymer memorisation risk is far worse than the MOF one.** aide2's zero-feedback control put the floor-corrected memorisation share at 0.44 / 0.44 / 0.72 (H2-vol, Xe/Kr, band gap) — the band-gap task, the one where the pretrained model already knows the chemistry, is the worst. Polymer Tg is *entirely* a band-gap-like task: any frontier model knows PEEK and polyimides are high-Tg and PDMS is 150 K. A zero-feedback arm and a name-free feedback rendering are not optional extras; they are load-bearing.
3. **The proposal's primary dataset is the smaller half of what is in hand.** The pre-proposal is written on the 13,725-row homopolymer XLSX only. The 42,557-row copolymer CSV — which is the only source of the *continuous composition axis* that makes this port scientifically novel rather than a transplant — is never mentioned, and it carries the audit's single S1 defect (D1) that would sign-flip any composition attribution built naively.

---

## 1. How the pre-proposal's three ideas are actually implemented

### 1.1 Regimes → `RegimeRouter`, a deterministic Agent-2 rule selector

The proposal's R1–R5 table (saturated hydrocarbon / aromatic-engineered / polar-H-bonding / functional-separation / complex-architecture) is, mechanically, the same object as LLM4MOF's `_get_mode_rules()`: a block of translation rules injected into the stateless translator's system prompt, plus a choice of hidden table, plus a choice of which numeric descriptors are meaningful. LLM4MOF has three such blocks (PORMAKE / hMOF / QMOF) and they differ in exactly the way the proposal's regimes differ: which tags are legal, which numeric fields exist, and which handover rules apply (PORMAKE: coordination tags must go to `node_query.ligand_chemistry`, not into linker branches; QMOF: `oxidation_state` and `geometry_preference` are legal, `sa`/`vf` are absent).

**Implementation for LLM4POL.** A regime is a *predicate over deterministic Layer-1 tags*, evaluated by the router, never by a model:

| Regime | Deterministic entry predicate (computed from the trimer key) | Table | Legal numeric gates | Rule block |
|---|---|---|---|---|
| **P1 saturated / polyolefin** | `aromatic_frac == 0` ∧ no heteroatom in backbone ∧ `hbond_density == 0` | HOMO-Tg | rigidity, sidechain_bulk, mw_repeat | side-chain-dominant rules; forbid aromatic tags |
| **P2 aromatic / engineered** | `aromatic_frac > 0` ∧ `hbond_density < 0.05` | HOMO-Tg | + aromatic_frac, ced_proxy | backbone-rigidity rules |
| **P3 polar / H-bonding** | `hbond_density ≥ 0.05` (amide, urethane, carbonate, urea, alcohol) | HOMO-Tg | + hbond_density | cohesive-energy rules; Fedors/HvK CED mandatory |
| **P4 binary copolymer** | two distinct monomer keys ∧ `binding != undetermined` ∧ `truncated_flag == False` | COPO-Tg | + composition window f₁∈[lo,hi] with basis | Fox/Gordon-Taylor rules; composition is a *numeric gate*, not a chemistry tag |
| **P5 architecture-only copolymer** | two monomer keys ∧ composition missing or unbound | COPO-arch | no composition gate | architecture-tag rules only; Fox unavailable |

Two deliberate departures from the proposal's table: (a) the proposal's R4 (PFAS/separation) and R5 (block copolymers, thermosets, dendrimers) are **not regimes of this system** — R4 is a different physics with a different oracle and no dataset (§10.3), and R5's crosslinked/dendritic members are not representable by a two-slot monomer table at all (audit D6: 4,243 rows / 548 ids are already terpolymers truncated into two slots, with `component3..5` empty). (b) The proposal assigns "Fast tree model / Transformer or tree / Domain model" as the per-regime *trusted oracle*; the candidate surrogates differ by ~5 K RMSE (polyGNN 31.7 ± 1.5, PolyFusion 33.7 ± 0.6, polyBERT 37.9–38.4) while the data's own replicate scatter has SD median 7.0 °C and p90 33.1 °C. **Selecting among those models per regime is selecting inside the noise.** The router's job is not to pick the best model; it is to declare the applicability domain and hand the descriptor window its MAE slack.

**How the regime is measured** (the proposal has no test for it): hold out one regime. Train every surrogate and fit the GC table on P1–P3 only, then run a P4 campaign. If regime routing has value, the router's MAE-slack on the P4 window keeps the Beam-1 hit rate above the no-router control; if it does not, the regime idea is reported as null. That is a falsifiable Aim 2 and it costs two extra battery arms.

### 1.2 Surrogate meta-loop → an offline bake-off + `_apply_mae_slack`

The proposal's meta-loop does four things: propose candidate surrogates, validate on held-out data, rank by R²/coverage/extrapolation risk, keep those above a threshold. Three of the four are an **offline experiment run once**, and the fourth is already implemented in LLM4MOF as a table of per-descriptor MAEs.

- *Propose / validate / rank*: a pre-registered bake-off over {Van-Krevelen GC, Fox (copolymer only), fingerprint+GBDT, polyBERT-embedding+MLP, wD-MPNN} on polymer-held-out and trimer-key-family-held-out splits, reported once as a table with the replicate-SD floor printed next to every RMSE. Nothing about that needs an LLM, and running it inside the design loop makes the campaign result a function of an unlogged model choice.
- *Extrapolation risk*: `filter_candidate._apply_mae_slack` with `GEOM_MARGIN_MODE="mae"` — the surrogate's own per-descriptor MAE widens the window it is being asked to satisfy, and everything that gates is recomputed by the real evaluator. Port this verbatim with a polymer MAE table, made **per-regime** (that is the one genuinely new thing the regime idea buys: P3's CED estimate has a different error than P1's, so the slack differs).
- *The invariant that makes all of this safe*: the surrogate reorders, never decides. In DB mode it is not used at all (LLM4MOF's DB mode does not touch MOF2Zeo either); in live mode it pre-ranks the Beam-1 pool only.

The proposal's Aim-2 success criterion — "does the loop correctly down-rank an irrelevant surrogate (e.g. modulus for PFAS)" — survives as a unit test of the router, not as an experiment about LLM reasoning.

### 1.3 Beams on Tg → the nested ladder, one hypothesis per iteration

Detailed in §6. Two facts the proposal gets wrong about the parent, restated here because they change the budget: LLM4MOF runs **1 hypothesis → 1 constraint JSON → 4 beams per iteration, 10 iterations, 2 LLM calls per iteration, 20 per campaign, $1.06 ± 0.05** (verified: `model_calls == 2` in every row of `figure6_token_usage_and_cost.csv`; two of five replicates spent 22 calls because an unproductive iteration was retried). And the beams are nested relaxations whose *adjacent differences* carry the attribution (1v2 = numeric gate, 2v3 = secondary chemistry, 2v4 = chemistry vs chance), not one-factor-at-a-time arms.

---

## 2. (a) The scientific question, and what "interpretable inverse design" means here

**Question.** *Given a natural-language property target over polymers, can a two-agent loop with a fixed 400-evaluation budget enrich top performers in a held-out experimental property table without a single property-labelled training structure — and, for the first time, can the design rules it states be scored against an independent physical attribution baseline rather than merely narrated?*

The first half is LLM4MOF's question with the nouns changed. The second half is the contribution, and it is available only in the polymer domain.

**"Interpretable" is defined operationally, by three pre-registered tests.** LLM4MOF's abstract asserts interpretability; the anatomy's weakness list is blunt that it "is asserted, not measured", that the feedback hints literally tell the agent how to read the beams ("If Beam 2 >> Beam 3, your linker choice is adding value"), and that a supervised probe recovers most of the signal. LLM4POL commits in advance to:

- **T1 — Tag-level attribution fidelity.** For every canonical tag that appears in ≥30 Beam-1 candidates across the battery, compute the beam-implied contribution (the shift in beam median when the tag is in the committed constraint vs when it is not, matched within backbone class) and compare to the van Krevelen group increment for the corresponding group. Report Spearman ρ and the sign-agreement rate over the ≥20 qualifying tags. Pre-registered null: ρ = 0.
- **T2 — Composition-slope fidelity.** For every (monomer A, monomer B) pair inside a beam with ≥3 distinct binding-resolved compositions, fit dTg/df₁ and compare its sign and magnitude to the Fox prediction computed from the two matched homopolymer Tg values. The instrument is sized: **378 ids have ≥5 distinct same-basis compositions summing to 99–101, with median |Spearman ρ(Tg, composition₁)| = 0.868 (234 ids > 0.7, 67 < 0.3)**. Report the fraction of pairs where the beam-implied slope sign matches Fox, and the 67 low-ρ ids separately — those are the physically flat or genuinely non-Fox systems (EVA ρ 0.20, SAN ρ −0.06) and are the interesting cases, not the failures.
- **T3 — Counterfactual sensitivity.** Take ≥50 Agent-1 hypothesis JSONs from completed campaigns; programmatically flip one committed tag or one descriptor bound; re-run Agent 2 + Matchmaker + evaluator; check whether the beam moves in the direction the hypothesis text predicted. Report the hit rate. This is the test LLM4MOF never ran and the one a reviewer will ask for.

**Ceiling statement, published alongside the result.** Before any campaign, fit a gradient-boosting model on exactly the descriptor columns the Matchmaker is able to filter on, and report its out-of-fold R² on each hidden table. In MOF-land that number was 0.943 for PORMAKE H2-vol 100 bar — i.e. three geometry columns were the answer key. If the polymer equivalent is high, the honest claim is "the agent recovers a known structure–property rule efficiently and states it", not "the agent discovered a rule". Saying so first is cheaper than being told.

---

## 3. (b) The design space: what a candidate IS

### 3.1 Canonical candidate record

```json
{
  "candidate_id": "sha1(canonical_form)[:12]",
  "architecture": "homopolymer | random | alternating | block | graft | statistical | periodic",
  "components": [
    {"monomer_key": "<trimer ring-closed key, stereo stripped>",
     "stereo_canon": "<linear canon with / \\ @, or null>",
     "fraction": 0.60, "basis": "mol | wt | vol"},
    {"monomer_key": "...", "fraction": 0.40, "basis": "mol"}
  ],
  "regime": "P1|P2|P3|P4|P5",
  "descriptors": {"rigidity":0.42,"aromatic_frac":0.55,"hbond_density":0.00,
                  "sidechain_bulk":7,"mw_repeat":208.3,"ced_proxy":412.0,"tg_gc":438.1},
  "provenance": {"source":"HOMO-Tg|COPO-Tg|SMiPoly|OMG", "pool_row_id":"...",
                 "binding":"by_component_majority", "truncated_flag":false}
}
```

The MOF analogy is exact: `(topology, node, edge)` → `(architecture, monomer A, monomer B)`, with **composition as a continuous fourth axis that MOFs do not have**. A homopolymer is the degenerate case (one component, fraction 1.0), which keeps one candidate type across both tables — the polymer equivalent of LLM4MOF's requirement that "an identical Agent 2 constraint maps consistently across all three databases" (SI Note S2, verified extra finding E9c).

**Identity key.** The trimer ring-closed key with stereo stripped, per audit §3.2 / invariant I15 — *not* the single-unit periodic key, which falsely merges 5 XLSX pairs, 2 CSV pairs and 1 cross-file pair of topologically different polymers (PPS vs poly(thienylene vinylene); 2-Me-THF vs epoxide). Stereo variants are linked, never merged (I16: 11 CSV + 3 XLSX cases). Attachment-point variants collapse correctly: 4,782 valid CSV SMILES → 4,666 backbones when `*` is deleted and re-canonicalised, i.e. 116 strings are the same monomer cut at a different point.

### 3.2 Serialisation for the LLM — deliberately not a name and not a SMILES

LLM4MOF shows Agent 1 a `readable_name` ("Node: zirconium octahedral node | Linker: butadiyne-bridged benzene linker"), and the anatomy flags this as a leakage channel because "the readable names shown to the agent are unique enough to identify BB ids". For polymers the same choice would be catastrophic: `poly(ether ether ketone)` is not a description, it is the answer. **LLM4POL renders candidates as tag profiles only:**

```
POL-07 | Tg 611 K ±7 (n=3) | Backbone:[aromatic_ether, aryl_ketone] Subs:[none]
        Inter:[conjugated, rigid_backbone] Arch:homopolymer f1=1.00
        rigid 0.71 | arom 0.67 | hbd 0.00 | sc 0 | MW 288.3 | CED 476 | Tg_gc 598
```

No IUPAC name, no SMILES, no pid, no sample id. This is a hardening beyond the parent and it is required twice over: once for the memorisation control, once because sending PoLyInfo rows to a hosted API may itself count as "transmission" under MatNavi Terms Art. 10(1) (audit §6.1, user decision Q6) — a tag profile is derived metadata, an IUPAC name plus a measured Tg is a data record.

### 3.3 The pools, and how they are enumerated

| Pool | Built from | Size | Role |
|---|---|---|---|
| **HOMO-Tg** | XLSX, audit-repaired | 13,725 rows → Tg on **7,733**; after group-median aggregation of the 91 duplicate-structure groups (192 rows, 101 excess) and the duplicate-name decision | DB-mode hidden table, homopolymer regimes P1–P3 |
| **COPO-Tg** | CSV usable core | **13,350 rows / 2,735 ids** (both monomers matched to an XLSX homopolymer *and* a Tg); of which **6,917 rows / 1,381 ids** also have both compositions parsed; of which only the binding-resolved subset is composition-eligible | DB-mode hidden table, regime P4 |
| **COPO-arch** | CSV remainder | rows with two monomers, Tg, but no usable composition (42.6 % of all rows have no composition at all; 3,323 of 7,385 ids never have one; 1,878 of 4,578 Tg-bearing ids never have one) | DB-mode hidden table, regime P5; architecture axis only |
| **SYNTH** | SMiPoly (BSD-3; 22 rules = 6 chain-growth + 16 step-growth; 1,083 monomers → 169,347 homopolymers in 7 classes) × composition grid × architecture | see below | Discovery-mode generative space, the PORMAKE analogue |
| **NOVELTY-REF** | PoLyInfo public counts (19,227 homopolymers, 8,321 copolymers) + PI1M (1 M, academic-only) | — | Novelty check only; never scored, never shown |

**Design-space arithmetic: compute, do not multiply.** LLM4MOF's own SI defines its space as a *connectivity-matched sum* |D| = Σ_c n_c t_c L = 80,126 × 156 = 12,499,656; the plain product 518 × 156 × 952 = 76,929,216 is a 6.2× overstatement (verified refutation **C5**). The polymer equivalent must be a rule-matched sum:

> |D_copo| = Σ_r C(n_r, 2) × |F| × |A|, with n_r = monomers eligible for polymerization rule r, |F| = 9 interior composition points (0.1…0.9 mol), |A| = 3 architectures {random, alternating, block}.

Σ_r n_r ≠ 1,083 because monomers serve several rules, and Σ_r C(n_r, 2) must be read off the rule-eligibility table at build time. **Do not write C(1,083, 2) = 585,903 × 9 × 3.** The homopolymer anchor (1,083 monomers → 169,347 products) is the number to report until the matched sum is computed; the order of magnitude for the copolymer space is 10⁷, and the figure caption must say which formula produced it.

**Synthesizability.** Template membership is the only guarantee available: SMiPoly's 22 rules or OMG's 17 reactions over 77,281 SCScore-filtered eMolecules reactants give it by construction, which is exactly what PORMAKE's curated building-block library gives LLM4MOF. SA score (Ertl, `*`→H) is **reported, not trusted** — it is a small-molecule score every 2025–26 polymer paper reuses without validation (polyBART threshold ≤6, Polymer-Agent SA+SCScore, PolyTAO, Huang 2024), and Trepalin 2026 is the first dedicated study of it as a polymer filter. Licence note: SMiPoly is BSD-3 and is the same group as RadonPy; OMG's code is GPL-3, which is a release decision if any LLM4POL code links it.

---

## 4. (c) The Matchmaker and database analogue

### 4.1 What plays which role

| LLM4MOF | n | Character | LLM4POL analogue | n | Why it is the right analogue |
|---|---|---|---|---|---|
| **PORMAKE** (H2 tasks) | 14,173 / 9,533 after whitelist | Assembled *hypothetical* structures; property emerges from assembly; table pre-filtered to what the matchmaker can propose (`build_canonical_db.py`) | **SYNTH** (SMiPoly/OMG + composition grid) | 169,347 homopolymers, O(10⁷) copolymers | property emerges from the assembled chain exactly as pore geometry emerges from the assembled framework; the pool is likewise restricted to what the proposer can reach |
| **hMOF** | 51,145 / 51,007 / 50,906 | Hypothetical, GCMC-labelled, whole-record filtering, **only 4 metals** so the inquiry must say so | **COPO-Tg** | 13,350 rows / 2,735 ids | whole-record filtering on tags + numeric ranges; the coverage restriction is the same shape (only 77.75 % of two-SMILES rows have both monomers matched, so the inquiry must restrict to the matched monomer set — the direct analogue of "Limit metal nodes to Cu, V, Zn, and Zr only") |
| **QMOF** | 20,373 | DFT records of **synthesised** MOFs, one aggregate value per record | **HOMO-Tg** | 13,725 rows, Tg 7,733 | real published materials, one aggregated value per record, aggregation rule unknown in both cases (QMOF: which functional; XLSX: audit D12, "polymer_aggregate_unknown", Tg integer/half-integer, float noise in the electrical columns) |
| **CoRE-MOF** | — | Experimental reference set | **NOVELTY-REF** | 19,227 + 8,321 public counts; PI1M 1 M | novelty denominator only |

### 4.2 Metadata each table provides

**HOMO-Tg** (per record): `pid`, trimer key, `linear_canon`, `stereo_canon`, class code (43 classes, largest P37 n=2,320 and P43 n=2,224), the 7 descriptors, `tg_gc`, SMARTS tag set, `n_star`/`topology_tag`, and the properties Tg 7,733 / Tm 3,696 / density 1,651 / resistivity 1,268 / conductivity 1,296 / elongation 1,059 / modulus 1,003 / stress 1,064. Quality flags: `duplicate_structure_group` (91 groups, 30 with conflicting Tg, max spread 169 K), `duplicate_name_group` (206 names, 77 conflicting, max 212 K), `property_free` (2,338 rows, 17 %, *including the primary pids of PE, PS, PMMA, PVC, PET, PEO, PLA, PCL*), `zero_star` (3 rows, unusable as repeat units).

**COPO-Tg** (per sample): `polymer_id`, `sample_id` split into `source_id` / `polymer_in_source` / `specimen_idx` / `record_idx`, two `monomer_key`s, two `CompositionEntry` records each with `value`, `basis`, `value_class`, **`binding`**, the `architecture_tags` ordered list + set, `replicate_group_id`, `exact_duplicate_of`, `truncated_flag`, `same_monomer_flag`, per-monomer descriptors plus composition-weighted descriptors, the Fox prediction from the two matched homopolymer Tg values, and the measured Tg with its replicate-group SD.

Three columns above have no MOF counterpart and are the port's real work: **`binding`** (because composition belongs to `component_i`, never to `smiles_i` — §9), **`replicate_group_id`** (because 56.3 % of Tg rows are replicates), and **`basis`** (mol 16,207 / wt 5,738 / vol 228 / unknown 2,268 on composition₁ — a composition constraint is meaningless without it, and mixed-basis pairs are effectively zero, 6 of 24,251, so a per-sample single-basis invariant is enforceable, I11).

### 4.3 The Matchmaker itself

Keep the **interface** and replace the body — the anatomy's own verdict for `matchmaker.py`. The stable contract is: constraint JSON in; `{candidates[], diagnostics{...}, preferred_features{}}` out, or a structured error `{"status":"error","reason":...}`. `core/hmof_matchmaker.py` (whole-record filtering with `search_mode ∈ {full, metal_only, linker_only}` driving the beams) is the closer template than `matchmaker.py`, and it is what LLM4POL should fork for both polymer tables.

Three semantics to port deliberately (verified extra finding **E9**, all three are things the parent's code does but the anatomy shows only piecemeal):

1. **Default-permissive.** "Any constraint left unset by Agent 2 simply defaults to a pass condition." This is what makes the `OPTIONAL != EXCLUDE` rule safe and what stops a half-specified hypothesis from returning zero rows.
2. **No silent defaults.** "An empty or malformed constraint query is rejected with a structured error, automatically halting the iteration rather than silently substituting default values" — distinct from the JSON-parse halt.
3. **Cross-table portability.** The generic-tag propagation hierarchy is applied to every table so an identical Agent-2 constraint maps consistently across all of them. For LLM4POL this is the guarantee that one constraint JSON works against HOMO-Tg, COPO-Tg and SYNTH, and it is testable: M2's exit criterion is that a 50-constraint fixture set returns non-empty matches from both HOMO and COPO for ≥90 % of fixtures.

One parent bug not to reproduce: in DB mode a zero-match iteration is **not** retried — `run_experiment.py:512-537` auto-continues with empty filter sets and the counter advances, so it burns one of the ten, while the SI states the retry rule unconditionally (verified caveat on **C1**, and extra finding **E5**: with backend no-match rates spanning 2.3–34.9 %, this plausibly explains much of the 79.5-vs-91.3 gap in Table 1). LLM4POL makes DB mode retry exactly like live mode, and reports the per-arm no-match rate as a first-class number.

---

## 5. (d) Descriptor layer, controlled vocabulary, and the MOF2Zeo analogue

### 5.1 The seven-descriptor gate (the Zeo++ vector analogue)

LLM4MOF's numeric gate is exactly seven descriptors (`di, df, sa, vf, density, dif, cv`), and that arity is load-bearing: it sets the shape of `geometry_filter` (7 x {min, max}), the MAE-slack table, the ledger's `geometry_envelope`, the feedback table columns, and the "GEOMETRY PROFILE OF YOUR CHEMISTRY" block. Port the arity so all of that machinery moves unchanged.

| # | Descriptor | Definition | Why it earns a slot | Gate? |
|---|---|---|---|---|
| 1 | `rigidity` | non-rotatable backbone bonds / backbone bonds (rings, C=C, C#C, amide) | chain stiffness — one of the two master variables in the CG-MD mapping (cohesive energy, chain stiffness, grafting density); SHAP on 1,261 polyimides puts `NumRotatableBonds` strongly negative on Tg | yes |
| 2 | `aromatic_frac` | aromatic heavy atoms / heavy atoms in the repeat unit | the P1 to P2 regime boundary; Shapley on tokenised polyacrylate SMILES: stiff two-phenyl segments raise Tg, linear side-chain segments lower it | yes |
| 3 | `hbond_density` | (H-bond donors + acceptors) / heavy atoms | the P3 boundary; the cohesive-energy route to Tg | yes |
| 4 | `sidechain_bulk` | heavy-atom count of the largest pendant substituent | side-chain length is the dominant negative axis in the acrylate/methacrylate families | yes |
| 5 | `mw_repeat` | repeat-unit molar mass (g/mol) | normaliser for every additive scheme; the denominator of the van Krevelen molar glass-transition function | yes |
| 6 | `ced_proxy` | Fedors / Hoftyzer-van Krevelen cohesive energy density (J/cm3) | the second master variable | yes |
| 7 | `tg_gc` | van Krevelen group-contribution Tg estimate, K | the interpretable baseline **and** the attribution ground truth | **no — see below** |

**`tg_gc` is computed, displayed, and excluded from the gate in the primary protocol.** Letting Agent 2 gate on a Tg estimate turns Beam 1 into a Tg filter, which is the polymer version of the obvious-filter pathology: the aide2 probe reached OOF R2 0.943 on the PORMAKE H2-vol 100 bar table from three geometry columns, and DB mode already "filters the same table it scores". So `tg_gc` sits in the feedback table (the agent sees it, exactly as it sees MOF2Zeo's predicted geometry) and in the ledger envelope, but `descriptor_filter` has six gateable slots. A labelled **GC-gate arm** with all seven gateable runs in the battery so the effect size is measured rather than assumed.

### 5.2 The controlled vocabulary

LLM4MOF: **124 canonical tags in 10 categories, a 215-entry alias map (183 entries actually built by the loader), 105 curated SMARTS, ~152 TAG_HIERARCHY propagation entries** (`benzene_ring -> aromatic, aryl, ring`), with the hard rule that LLM enrichment writes only human-facing fields the Matchmaker never filters on. No polymer counterpart exists; the closest structural precedent is HAPPY / CI-LLM's subgroup mining from ~10,000 PoLyInfo repeat units with Integrated-Gradients attribution, and the reusable tag sources are the PoLyInfo ontology (CC BY 4.0) and PolyBench-LLM's SME descriptors.

Proposed LLM4POL vocabulary: **~95 canonical tags in 8 categories**, built with the parent's own machinery (`database_construction/5_shared/smarts_library.py`, `4_vocabulary/04_build_vocab_mapping.py`) against a polymer SMARTS set:

| Category | ~n | Examples |
|---|---|---|
| Backbone class | 12 | polyolefin, polyester, polyether, polyamide, polyimide, polyurethane, polycarbonate, polysulfone, polysiloxane, polyacrylate, polystyrenic, polyvinyl |
| Ring / scaffold | 16 | benzene_ring, naphthalene, biphenyl, fluorene, anthracene, cyclohexane, norbornane, adamantane, spiro, triptycene, cardo |
| Heterocycle | 12 | imide_ring, benzoxazole, benzimidazole, triazine, pyridine, thiophene, furan, oxazolidone |
| Functional group | 25 | ester, amide, ether, ketone, sulfone, carbonate, urethane, urea, nitrile, hydroxyl, carboxyl, sulfonate, phosphonate, anhydride |
| Substituent / side chain | 10 | methyl, ethyl, n_alkyl_C4_C8, n_alkyl_gt_C8, isopropyl, tert_butyl, pendant_phenyl, pendant_cyano, pendant_hydroxyl, oligo_ether_pendant |
| Halogen / fluorine | 6 | fluoro, chloro, bromo, perfluoroalkyl, trifluoromethyl, perfluoroether (also the PFAS bridge) |
| Interaction / abstract | 8 | h_bond_donor, h_bond_acceptor, strong_dipole, ionic, conjugated, aromatic, rigid_backbone, flexible_backbone |
| Architecture | 6 | random, alternating, block, graft, statistical, periodic |

The architecture six come straight from the audited `copolymer_type` vocabulary (exploded frequencies: unspecified 28,938; alternating 9,346; random 6,821; block 6,814; graft 2,740; statistical 471; periodic 10), with **`unspecified` dropped from multi-tag lists** and never usable as a positive constraint — it is a filler, present alone in 20,843 rows (49.0 %).

One candidate addition flagged **needs-verification-before-hard-coding**: the M-type / AD-type / SD-type monomer substitution taxonomy for copolymer Tg deviation (mono-substituted + asymmetrically di-substituted gives negative Fox deviation; mono + symmetrically di-substituted gives positive). The paper is real (Macromolecules 2022, 55, 3189) and the three-case framing is confirmed, but the verifier could not see the M/AD/SD naming in any accessible abstract. Read the PDF before writing those three tags into the vocabulary. The related sequence result **is** confirmed and is the physical justification for keeping `architecture` as a first-class design axis: UCST-tending comonomer pairs give negative Tg deviations, LCST-tending give positive, and the effect strengthens with increasing alternation because of bond-induced forced mixing.

Pipeline architecture, ported verbatim: **Layer 1** deterministic facts (formula, MW, ring sizes, rotatable-bond counts, canonical SMILES with `*` handling) plus **Layer 2** SMARTS tags with multiplicity counts, backbone/substituent split and generic-tag propagation — these and only these drive filtering. An **LLM enrichment pass** may write `readable_name`, `design_hints`, `abstract_features`, and as in the parent *the Matchmaker filters on none of them*. One parent flaw not to copy: LLM4MOF's negative-tag bouncer also does a substring check against `readable_name`, an LLM-written field (`constraint_utils.check_negative_tags`, l. 373-403). LLM4POL's bouncer touches deterministic fields only.

### 5.3 MOF2Zeo becomes `PolyRank`

| Property | MOF2Zeo | PolyRank |
|---|---|---|
| Inputs | categorical (topology, node, edge), 128-d embeddings | monomer tag multiset + the 7 descriptors + composition + basis + architecture |
| Outputs | 7 Zeo++ descriptors | the target property (Tg / Tm / density), per regime |
| Training | 545,107 train / 84,228 valid assembled structures, avg R2 0.99, **property-agnostic** | HOMO-Tg / COPO-Tg **training split only**, grouped by trimer key *and* `polymer_uid` (invariant I21) |
| Use | pre-rank the Beam-1 pool of 100; window widened by per-descriptor MAE (di 0.746 A, df 0.751, dif 0.828, sa 50.7, vf 0.0098, density 0.0152); never gates | identical: pre-rank the Beam-1 pool in live mode; per-**regime** MAE slack; never gates; **unused in DB mode** |
| Label accounting | LLM4MOF excludes "label-free, property-agnostic pretraining" for every method, including its own surrogate | PolyRank is **property-labelled**, so its training labels must be counted |

That last row is the most important difference between MOF2Zeo and any polymer surrogate. MOF2Zeo predicts geometry, so LLM4MOF can legitimately exclude its 629,335 records from the label budget. PolyRank predicts the target. Consequence: **live mode is LLM4POL's weakest point against the parent's "not a single property-labeled training structure" claim.** DB mode keeps the claim intact (no surrogate at all); live mode must report "400 loop evaluations + N surrogate training labels" as one number. The alternative that preserves the clean claim is to pre-rank with a property-agnostic model — the SimPoly-class machine-learned force field that predicts density and Tg from first principles without fitting to experimental data, with its PolyArena benchmark of 130 experimental polymers as a ready-made standardised evaluation. Worth a two-week spike before committing to a labelled pre-ranker.

---

## 6. (e) The oracles

### 6.1 The five-tier ladder

| Tier | What | Cost per candidate | Where | Role |
|---|---|---|---|---|
| **T0** | RDKit descriptors + van Krevelen GC + Fox | ~1 ms | laptop CPU | constraint gate + interpretable baseline + attribution ground truth — this is the **Zeo++** role: cheap, deterministic, recomputed, and it is what gates |
| **T1** | PolyRank surrogate (fingerprint+GBDT / wD-MPNN / polyBERT-embedding MLP) | ~1 ms | laptop CPU (GBDT trains in seconds on 7,733 rows) | Beam-1 pre-ranking, live mode only — the **MOF2Zeo** role |
| **T2** | **The hidden PoLyInfo table** | 0 (look-up) | laptop CPU | **DB-mode ground truth, the RASPA3 role.** Measured experimental values. |
| **T3** | RadonPy density; 300-2,000 core-h (anchor: "more than 30-50 h" on 40 cores); R2 0.890 vs PoLyInfo on 1,001 polymers | 0.5-2.5 days on 32 cores | dirac PBS | live-mode physical gate before the expensive property — the true Zeo++ analogue in discovery mode, and the only MD quantity that is both cheap and quantitatively validated |
| **T4** | MD Tg; 4,000-20,000 CPU-h (3-10 replicates; at least ten replicas for a 95 % CI under 20 K) | 5-25 days on 32 cores; **0.3-1.5 candidates/day at 256 cores** | dirac PBS | live-mode target property, at most 10 finalists per task |

**The arithmetic that kills MD-in-the-loop, stated once.** An LLM4MOF discovery campaign is 380 +/- 2 GCMC runs plus ~1,900 build/relax/Zeo++ evaluations, five replicates per task. The same design with MD Tg is 10^7-10^8 CPU-hours. A realistic LLM4POL live campaign is therefore: the DB-mode / surrogate loop converges, 40 pre-finalists get T3 density (12,000-80,000 core-h), 10 finalists get T4 Tg at >= 3 replicates (60,000-90,000 core-h), total ~10^5 core-h, a few weeks on dirac for **one** task. Budget accordingly; do not promise five replicates of a live campaign.

**MD is not ground truth for Tg — PoLyInfo is.** The pre-proposal's Phase 4 says "compare surrogate predictions and beam-derived mechanistic claims to MD ground truth". That is backwards. MD Tg carries a systematic overestimate of +79.1 K (Afzal, 315 polymers, fit slope 1.30; calibrated Tg = 0.77 x Tg_calc + 21.08 K), +105.02 K (Marti, 58 homopolymers + 488 copolymers, 2,184 simulations, 143.052 microseconds), 80-120 K (Gudla and Zhang), +38 to +47 K (PolyJarvis on PE / aPS / PEG). The correct direction of use is: **calibrate MD against PoLyInfo on overlapping polymers, then apply MD only to candidates outside PoLyInfo** — that is, to the discovery-mode novel candidates, which is precisely how LLM4MOF uses RASPA. Every MD number is reported twice (raw and calibrated) with the offset and the replicate count stated.

Two corrections to carry into this tier. RadonPy's current release **does** ship a Tg preset (`sim/preset/tg.py`, `AutoMD_scripts/4_tg.py`) and random / alternating / block copolymer builders — Tg was absent only from the 2022 paper — but that preset has **no published validation against PoLyInfo**, so validating it is itself a deliverable. And the phrase "the intrinsic MD cooling-rate bias rather than agent error" attributed to PolyJarvis is not verbatim; the paper says "The dominant error source is the intrinsic cooling-rate limitation, not agent-introduced inaccuracies." Do not quote the former.

### 6.2 Where things run

| Resource | Verified state | What it can do here |
|---|---|---|
| Laptop CPU (i5-14600K, 14C/20T, 31.7 GB) | conda base Python 3.13.9 already has pandas 2.3.3, numpy 2.3.5, scipy 1.16.3, scikit-learn 1.7.2, **rdkit 2025.9.6**, pyarrow 21.0.0, openpyxl 3.1.5 | T0, T1, T2, the loader/validator, the whole DB-mode program, the battery. **Nothing in milestones M1-M7 needs anything else.** |
| RTX 5050, 8,151 MiB, driver-level CUDA 13.3 (Blackwell) | **no environment on the machine has a CUDA-enabled torch**; both installs report `cuda.is_available() == False`; a CUDA 12.8+ / 13.x wheel is required | nothing today. Needed only for the polyBERT-embedding baseline and GPU LAMMPS spot-checks. Creating the env is a prerequisite task, not an assumption. |
| dirac PBS (via the `hpc-submit` skill) | the skill routes through the project's `config/hpc.json` + `scripts/submit.py` and stops if either is missing; **GPU availability unknown**; the skill warns that Dropbox file locks corrupt its ledger | T3 and T4 only. The repo must live outside Dropbox. |
| API keys | **none set** in process, User or Machine scope | blocking for every LLM arm. |

### 6.3 "The oracle is only as good as the surrogate" — four defences

1. **In DB mode there is no surrogate.** The oracle is measured data. This is the structural reason to make DB mode primary, and it removes the parent's worst wound in one move: LLM4MOF's C2H6/C2H4 task is "ethane-selective by design" because chargeless TraPPE-UA cannot represent pi-complexation, and its CO2 open-metal-site "correction" is a property of the hMOF labels (OMS median 4.49 < non-OMS 5.14; 6.30 < 6.67 after void-fraction control). No equivalent critique lands on a table of measured Tg.
2. **The surrogate reorders, never decides** — MOF2Zeo's invariant ported verbatim, including the per-regime MAE slack and the rule that everything gated is recomputed by T0 / T3.
3. **Held-out-oracle scoring.** Final candidates are scored by a surrogate trained on a disjoint structure-family split that was never used in the loop; the hit rate under that model is the reported number.
4. **The ceiling probe, pre-registered.** The supervised-shortcut GBDT on exactly the Matchmaker-visible descriptor columns, OOF R2 per table, published before the campaign results — plus the replicate-SD floor printed next to every error metric. Within-group Tg SD median 7.0 C, p90 33.1, p95 52.4; 872 groups span more than 20 C and 355 more than 50 C; within-id Tg range median 20.2 C with 588 ids exceeding 50 C. **A surrogate quoting RMSE 20 K on this data sits at the measurement floor, not at a modelling frontier.**

---

## 7. (f) The four beams, redefined — and attribution over a continuous axis

### 7.1 The nested ladder

| Beam | LLM4MOF | LLM4POL | What the adjacent difference attributes |
|---|---|---|---|
| **1 / Z — full hypothesis** | chemistry AND strict Di/Df window AND inclusive sa/vf/density/dif/cv | monomer tags AND architecture tag AND **composition window [f_lo, f_hi] with basis** AND descriptor window (strict on the <= 2 committed descriptors, inclusive on the rest) | — |
| **2 / A — chemistry only** | chemistry, geometry window removed | monomer tags AND architecture; composition and descriptor windows removed | **1 v 2 = the numeric gate** (composition window + descriptor window) |
| **3 / F — primary axis only** | node/metal identity only; linker and geometry free | **backbone class only**; side-group chemistry, architecture, composition and descriptors all free | **2 v 3 = secondary chemistry** (side groups + architecture) |
| **4 / R — random** | whole hidden table, metal-stratified | whole hidden table, **backbone-class-stratified** | **2 v 4 = chemistry vs chance** |

Three deliberate deviations from the parent:

- **Fix the live/DB asymmetry.** LLM4MOF's `_build_beam_specs` keeps `geometry_filter` in the metal-only beam ("keep metals and geometry") while DB mode's `set_f` has no geometry gate. LLM4POL's Beam 3 drops the composition and descriptor windows in **both** modes. Reproducing a disclosed inconsistency buys nothing.
- **Fix the fallback contamination.** In LLM4MOF's discovery mode, Beam-1 candidates that fail the strict Zeo++ gate are still simulated as "fallback" to fill the quota and are shown with a `GeoFilter: fallback(reason)` column, so "Beam 1 = full hypothesis" can contain structures that violate the hypothesis; the live hint text even quotes a 15-candidate quota while `LIVE_SIM_Z_RASPA_TOP = 10`. LLM4POL either fills Beam 1 only with passing candidates, or reports fallback rows as a fifth labelled group — never inside the Beam-1 statistic.
- **Fix the n-exposure.** The parent plots the median of the entire matched set, whose size swings from 1 to 9,533 (a recorded iteration 10: Z 43 / A 257 / F 3,591 / R 9,533; iteration 1: Z 1 / A 1 / F 3) and never reports n per point. LLM4POL's **primary** beam statistic is computed on the fixed-size stratified sample of n = 10 actually shown to the agent — the same population the hit-rate / enrichment metric already uses — and the full-matched-set median is secondary and always printed with n.

Beam-construction detail worth stealing outright: `linker_branches` as an **OR-of-ANDs** is how the parent lets a single hypothesis carry alternatives without spending extra budget. LLM4POL's `monomer_branches` does the same job, and it is the correct answer to the pre-proposal's "Agent 1: propose N chemical hypotheses" — the N alternatives go inside one JSON, not into N campaigns.

### 7.2 Causal attribution when one axis is continuous

This is the genuinely new methodological problem, and the reason the copolymer table matters more than the pre-proposal realises.

**(i) The composition window is a numeric gate, so Beam 1 v Beam 2 already measures it.** Put `f1_min` / `f1_max` + `basis` in `descriptor_filter`, not in the chemistry query. No fifth beam is needed. This mirrors the parent exactly: geometry is "a second-stage evaluation gate", all-null unless the agent supplied numbers, and a `geometry_null` flag prints "Beam 1 = Beam 2 (no geometry gate was active). This comparison does NOT measure geometry contribution." LLM4POL prints the same disclaimer for a null composition window.

**(ii) The within-pair composition-slope statistic — the new instrument.** A beam median over a continuous axis is confounded by which chemistries happen to land in the beam. So for every (monomer A, monomer B) pair present in a beam at >= 3 distinct binding-resolved compositions, fit dTg/df1 and compare it to the Fox prediction computed from the two matched homopolymer Tg values:

> `slope_score = sign_agreement( dTg/df1 |_beam , dTg/df1 |_Fox )`, reported with `delta = |dTg/df1|_beam - |dTg/df1|_Fox`

This is **chemistry-controlled by construction**: the pair is its own control, so the between-pair variance that swamps a raw beam median disappears. The instrument is sized: **378 ids have >= 5 distinct same-basis compositions summing to 99-101, with median |Spearman rho(Tg, composition1)| = 0.868; 234 ids exceed 0.7 and 67 fall below 0.3.** Those 67 low-rho ids are reported separately as the non-Fox systems (EVA rho 0.20, SAN rho -0.06, P900492 rho 0.12) — they are the physically interesting subset, and the literature already predicts the sign of the deviation from comonomer phase behaviour and sequence alternation.

**(iii) Attribution is reported as a decomposition, not a narrative.** Per campaign, per task, one table:

| Axis | Estimator | Independent check |
|---|---|---|
| Backbone class | median(Beam 3) - median(Beam 4) | van Krevelen increment of the class's characteristic group |
| Side-group + architecture chemistry | median(Beam 2) - median(Beam 3) | SHAP on the held-out-oracle surrogate |
| Numeric descriptor window | median(Beam 1) - median(Beam 2) with the composition window null | descriptor-conditioned GBDT partial dependence |
| Composition | within-pair slope score over the beam | Fox slope from the matched homopolymers |

Every cell carries n and the replicate-SD floor. That table, repeated over >= 5 tasks and >= 10 replicates, **is** the interpretability claim — checkable, not narrated.

**A warning specific to this design.** LLM4MOF's feedback hints tell the agent how to read the beams ("If Beam 2 >> Beam 3, your linker choice is adding value"), so the agent's stated reasoning partly echoes the harness. LLM4POL keeps the hints — they are part of the ported design and removing them silently would be an untested change — but adds a **hint-ablation arm**: identical campaigns with the interpretation sentences stripped. If the attribution table is unchanged, the attribution is the data's; if it collapses, it was the prompt's. Two extra arms, and it answers the reviewer question the parent left open.

---

## 8. (g) Feedback payload and memory ledger

### 8.1 The payload, block by block

The parent's assembly order is ledger block, four beam tables, geometry profile, diagnostic footer. Keep the order; replace every string.

1. **Ledger block** (`render_facts_only`): best so far with its structure and iteration, top-K cutoff and median, top-5 best-first, descriptor ranges of the frontier, cutoff trajectory. Facts only — the legacy prescriptive renderer ("CONCENTRATE... do NOT switch families", "GRAFT it") was found to hurt rare-peak tasks and is not used. Port that finding, do not re-litigate it.
2. **Four beam tables**, best-first, at most 10 rows:
   `Polymer | Tg (K) +/- SD (n) | Rigid | Arom | HBond | SideBulk | MW_ru | CED | Tg_gc | f1 (basis) | Arch`
   plus, per beam, a chemistry profile (`POL-i: Backbone:[..] Subs:[..] Inter:[..] Arch:<tag> f1=<0.xx>(<basis>)`) and a pattern summary (top-3 backbone classes / substituents / interaction tags as `name(pct%)`, "Minority (informational, do NOT require as mandatory)", descriptor `min-max (med)`, 500-char cap).
3. **Descriptor profile of your chemistry** (observational, not prescriptive): min / max / median of the six gateable descriptors over the top-5 of Beam 1, falling back to Beam 2 then Beam 4, withheld entirely when Beam 1 is empty.
4. **Diagnostic footer** when Beam 1 is empty: which stage failed (chemistry / composition window / descriptor window / architecture) from the Matchmaker diagnostics.

Three additions with no parent counterpart, each forced by the polymer data:

- **`(N=n)` on every beam, always.** Fixes the parent's unreported-n problem at source.
- **Replicate SD next to every value.** 56.3 % of Tg rows sit in replicate groups (10,163 groups, 2,243 with more than one row = 10,222 rows; SD median 7.0 C, p90 33.1, p95 52.4). Showing `611 K +/- 7 (n=3)` stops the agent chasing a 5 K difference that is inside the measurement. There is no MOF equivalent because GCMC at a fixed seed is deterministic.
- **`basis` printed with every composition.** `f1=0.60(mol)` and `f1=0.60(wt)` are different materials. Composition1 bases: mol 16,207 / wt 5,738 / vol 228 / unknown 2,268.

**What is never sent** (ported verbatim): table identity, record ids, table size, the global distribution, percentiles, thresholds, the sensitivity report. Plus the LLM4POL hardening from section 3.2: **no IUPAC name, no SMILES, no pid, no sample_id.** The parent shows readable names and its own anatomy flags them as identifying; polymer names are strictly worse because they are the answer.

### 8.2 The ledger

Port `core/memory_ledger.py` as-is; swap `_GEOMETRY_COLS` for the six gateable descriptors and `_struct_label` for the tag-profile label. Structure kept: `global_best`, `frontier` (top-K = 10 distinct structures, deduped by candidate_id), `descriptor_envelope` (per-descriptor [min, max, median] over the frontier, descriptors with zero spread dropped), `history[]` per iteration.

Two corrections from the verification packet that a naive port would get wrong:

- **The random beam is not fully excluded.** `MemoryLedger.ingest` iterates all four beams to record `beam_medians{z,a,f,total}` in `history[]` and to run `_detect_outside_promising` on the random beam; only `global_best` / `frontier` / `descriptor_envelope` are restricted to the three hypothesis beams (verified refutation **C8**). Keep exactly this, and keep the firewall that matters: `render_facts_only` prints neither `beam_medians` nor `outside_promising`, so nothing from the random beam reaches Agent 1.
- **The ledger is an addition to an unbounded transcript, not a replacement for one.** The SI claims Agent 1 "receives the complete, verbose feedback report only for the immediately preceding iteration, while older empirical observations are compressed into a fixed-size Memory Ledger". The shipped code does no such compression: `LLMClient(multi_turn=True)` appends every user and assistant message to `conversation_history` and re-sends the whole list, with no trim, window or eviction anywhere — confirmed by the SI's own cost note that the context "grows monotonically" and per-iteration cost rises from about $0.03 to $0.19 (verified extra finding **E4**). So the published ledger ablation measures *ledger on top of full history*. **Decision for LLM4POL:** reproduce the parent (full transcript + ledger) as the default, because that is the configuration that was actually measured, and run the SI's described design (window of 1 + ledger) as a labelled ablation arm. The cost of the default is trivial — the parent's whole campaign is $1.06 and LLM4POL's feedback tables are narrower.

### 8.3 Sampling strata

`sampling_strata.metal_of` becomes `backbone_class_of` (falling back to the regime id when a candidate carries no backbone tag). The properties that matter are ported, not the domain: round-robin over strata, shuffle within stratum, **identity only — the target is never read**, and the stratified random beam applies in DB mode. In MOF-land this was "the only fully cross-app-validated universal lever" and it is credited as "the primary mechanism for raising the absolute performance ceiling" in the ledger ablation; balancing the random beam alone moved its median from 183.1 to 196.6 on the 77 K / 5 bar task. Keep `SHUFFLE_METAL_ORDER`'s polymer equivalent (default off, with the parent's own warning that on a target-sorted table a fixed visiting order means the same strata in every iteration of every run).

One polymer-specific stratum choice to test in the battery: backbone class vs regime vs monomer-family. The old aide2 clone already ships a multi-key `STRATA_MODE` (metal | uniform | pore_quartile | topology | edge) — port that switch and use it, because W2 found no strata variant beat the default at Holm-corrected significance, and there is no reason to believe the polymer answer is the same.

---

## 9. (h) Metrics, baselines, and the budget-matching protocol

### 9.1 Metrics

| Metric | Definition | Why |
|---|---|---|
| **Primary — Beam-1 sample median percentile at iteration 10** | percentile of the median of the **n = 10 shown** Beam-1 candidates against the hidden table's distribution; mean +/- SEM over replicates | the parent's headline metric with the n-exposure flaw removed |
| **Hit rate and enrichment** | fraction of candidates returned to Agent 1 (<= 10 per beam per iteration, pooled over replicates x 10 iterations) exceeding the table's top-1 % / top-10 % threshold; enrichment = Beam 1 / Beam 4 | already computed on the shown sample, so it is the safest transferable number |
| **Iterations to top-10 %** | first iteration whose Beam-1 sample median crosses the top-10 % threshold | parent's Table 1 secondary |
| **AUC over iterations** | area under the percentile trajectory | aide2 addition; lower variance than the endpoint (sigma 3.3 / 8.2 / 3.2 vs 6.4 / 15.9 / 6.9) |
| **No-match rate** | share of iterations whose constraints matched nothing | first-class, per arm — in MOF-land it ranged 2.3-34.9 % across backends and silently consumed iterations in DB mode |
| **Memorisation share** | (NF - 50) / (V0 - 50) on the final percentile, from the zero-feedback arm | the gate on every claim |
| **Attribution fidelity** | T1 tag-vs-GC Spearman rho and sign agreement; T2 composition-slope agreement over the 378-id set; T3 counterfactual hit rate over >= 50 edits | the contribution |
| **Novelty / validity** (discovery only) | novelty against the trimer-key union of both tables; validity = RDKit parse with exactly two `*`; SA score reported; template membership as the synthesizability claim | standard polymer generative practice |

**Thresholds, concretely.** HOMO-Tg has 7,733 Tg values spanning 138-768 K with median 410 K, p1 195 K and p99 657 K. So a maximise-Tg task's top-1 % threshold sits near 657 K with roughly 77 polymers above it, and top-10 % near the 90th percentile with roughly 773. A minimise-Tg task's top-1 % is near 195 K. **Enrichment ratios must be reported with their counts**: the parent's headline 162x on CH4 rests on a baseline of 1 hit in 500, and quoting such a ratio to two significant figures is exactly the statistical framing a reviewer will attack. COPO-Tg's own distribution (18,142 CSV Tg rows, median 52.55 C = 325.7 K, p99 338 C = 611 K, max 455 C = 728 K) gives the copolymer task its own thresholds; they must be computed on the **group-median, binding-resolved, deduplicated** table, not on raw rows, or replicate outliers set the top-1 % line.

### 9.2 Baselines, all under the same evaluator and the same realised budget

| Arm | Implementation | Expected outcome and why it matters |
|---|---|---|
| **Random** | Beam 4 | floor |
| **GA** | GA over (monomer A, monomer B, composition, architecture) with a surrogate retrained each iteration; 40 random valid candidates at iteration 1, population 200, 20 generations, mutation 0.2, top 80 surrogate-ranked submitted, up to 40 completed per iteration — the parent's protocol | **This is where the port is most likely to fail to reproduce the parent's headline, and that is a feature.** LLM4MOF's GA surrogate had held-out R2 approximately 0 and MAE 6.2-6.8 g/L — it was random search with extra steps, which the authors concede. A polymer surrogate on 7,733 Tg labels reaches R2 0.85-0.89. The polymer GA is therefore a genuinely strong baseline and may win. Say so in advance. |
| **BO** | latent-variable GP over the categorical monomer pair plus a **real-valued** composition dimension, EI acquisition, 40 random initial | stronger than the parent's, because composition is continuous and a standard GP dimension applies, where LLM4MOF had to force a 6-d latent over pure categoricals |
| **Fox** | greedy selection by Fox-predicted Tg from matched homopolymers | the interpretable copolymer baseline: published R2 0.835 / RMSE 42.57 C on PoLyInfo copolymers vs 0.921 / 24.45 for the best GNN; the audit's own linear-mixing test gives median |dTg| about 14 C when composition is bound to the correct component |
| **Group contribution** | greedy selection by van Krevelen `tg_gc` | in-sample MAE about 10 K, out-of-sample R2 0.71 measured against single-LLM 0.67, ChemCrow 0.66 and a PolyGNN agent 0.78 on a 50-polymer Tg benchmark. **No pip-installable Van Krevelen / Bicerano implementation exists** — the table must be coded from the book or from the Kaggle transcription (-CH2- 158, p-phenylene 2820, -SO2- 2150, -NHCO- 1510), which is itself unverified against the book. Budget a week and a verification pass. |
| **polyBERT-guided** | greedy selection by a polyBERT-embedding MLP | Tg RMSE 37.9-38.4 K. Weights are on HF under a GTRC academic-research licence that was not anonymously readable — **a user decision before this arm exists**, and it also needs the CUDA env. |
| **Zero-feedback (NF)** | identical campaign with the feedback string replaced by an empty stub | **non-negotiable.** MOF memorisation shares were 0.44 / 0.44 / 0.72; the 0.72 came from the band-gap task where the pretrained model already knows the chemistry, and polymer Tg is entirely that kind of task. |
| **Hint-ablation** | feedback with the four interpretation sentences stripped | separates the agent's attribution from the harness's |
| **Supervised-shortcut probe** | GBDT on Matchmaker-visible descriptor columns, OOF R2 | the ceiling statement, published first |

### 9.3 Budget matching

Nominal budget: **40 evaluations per iteration x 10 iterations = 400 per arm per replicate**, 10 replicates per task (not 5 — aide2 measured replicate sigma of 6.4 / 15.9 / 6.9 percentile points at n = 10, so 5 replicates give SEM bars of several points and the parent's "within 0.1 points" comparisons in Table 1 are well inside noise).

Report a **realised-evaluation table per arm**, because the parent's nominal-versus-realised gap is a disclosed fairness problem: GA realised 327-368 and BO 212-265 against LLM4MOF's 380 +/- 2, and the shortfall was counted against them. In DB mode there are no assembly failures, so realised should equal nominal for every arm except when a constraint matches nothing — which is why the no-match rate is a first-class metric and why the DB-mode retry fix (section 4.3) matters.

Three budget items the parent excludes that LLM4POL must disclose:
1. **T0 evaluations.** The parent spends about 190 build/relax/Zeo++ evaluations per discovery iteration that are free in its label accounting; the aide2 simulation persona priced this at 25-35 % of total compute. LLM4POL's T0 is genuinely nearly free (milliseconds), but the count is reported anyway.
2. **PolyRank training labels** (live mode only) — see section 5.3.
3. **LLM cost.** Measured parent: 2 model calls per iteration, 20 per campaign, ~0.57 M tokens, **$1.06 +/- 0.05**, per-iteration cost rising from $0.03 to $0.19 as the transcript grows. LLM4POL's tables are narrower, so budget $0.5-1.2 per DB-mode campaign. **Whole-programme estimate: 2 LLM arms x 6 tasks x 10 replicates = 120 campaigns (~$120), plus a 6-backend x 7-task x 5-replicate benchmark = 210 campaigns (~$210), total roughly $350-500.** At the parent's measured 353 s mean per 10-iteration DB campaign (median 348, range 247-492, 6 concurrent), 330 campaigns is about 32 hours of wall clock. The entire DB-mode scientific programme fits in a week and a few hundred dollars — which is the strongest practical argument for making it the primary mode.

### 9.4 Backend benchmark

Port the parent's design: several Agent-1 backends, **Agent 2 pinned**, 7 tasks x 5 replicates, scored on first attempt only. Report `no-match %` and `unparseable %` alongside the score — the parent's haiku arm had 7.1 % unparseable and completed only 23 of 35 cells, and the nano arm's 34.9 % no-match rate interacts with the un-retried DB-mode iteration bug. Also report within-arm SD next to between-arm SD (the parent measured between-arm 3.9-13.3 vs within-arm 8.3-14.8 percentile points, i.e. the backend effect is smaller than the noise), and state plainly whether any backend difference survives.

---

## 10. (i) How the audit's defects constrain this strategy

### 10.1 The four that change the design

**D1 — composition/component binding swap (S1).** `composition_i` belongs to `component_i`, never to `smiles_i`. Row classes over the 42,557 rows: aligned 15,409, swapped 2,221, half_aligned 5,309, half_swapped 881, neither 433, one_component_id 190, no_component_ids 18,114. By slot-level propagation, **5,333 of 17,842 resolvable rows (29.9 %) have at least one slot swapped**. The evidence is decisive, not statistical: on swapped rows (N = 50) the Tg linear-mixing error is **13.7 C under component-binding versus 56.8 C under SMILES-slot binding** (45 rows better versus 4); on aligned rows (N = 343) it is 14.1 versus 27.5 (201 versus 97); robust to the Fox equation and to a |dTg| >= 60 filter.

Consequences for this strategy, all binding:
- The composition axis exists only on `binding in {by_component_majority, by_position_aligned_only}`. The 5,309 half-aligned rows are excluded — the mixing test there actually favours the *reversed* binding (23.4 versus 15.4 C), so they are not merely uncertain, they are actively misleading.
- **The Fox baseline doubles as the binding validator.** If the loader's binding is right, Fox should reproduce roughly R2 0.835 / RMSE 42.6 C on the resolved rows. If it comes out much worse, the binding is wrong. This is the cheapest correctness check in the whole project and it is milestone M3's exit criterion.
- Any composition beam built on column position would produce a **sign-flipped attribution in about a third of rows** — which, given that composition-slope agreement with Fox is the headline attribution test (T2), would not merely add noise, it would invert the result.
- Constraint propagation resolves only about 1,963-1,964 of some 2,635 ids; the rest needs the original PoLyInfo component records (user decision).

**D4 — replicates and duplicates (S2).** 56.3 % of Tg rows sit in replicate groups; 6,548 rows are exact duplicates on every column except `sample_id`, of which 1,355 carry a property. Consequences: the hidden table is a **group-median table**, not a row table, or replicate outliers set the top-1 % threshold; all splits are grouped by `polymer_uid` (invariant I21); the replicate SD is printed in the feedback and next to every error metric (section 8.1).

**D5 + D6 — missing and truncated compositions (S2).** 42.6 % of rows and 3,323 of 7,385 ids have no composition at all; 1,878 of 4,578 Tg-bearing ids never have one. Separately, 4,243 rows / 548 ids (conservative; 7,389 / 1,320 liberal) are terpolymers truncated into two slots with `component3..5` empty, so their sum-below-99 is truncation, not error. Consequences: regime P4 (composition) runs on at most **6,917 rows / 1,381 ids**, further reduced by the binding filter and by excluding `truncated_flag`; everything else goes to P5 (architecture-only), where Fox is unavailable and the composition-slope test cannot run. **The number that bounds the headline contribution is therefore not 42,557 and not 13,350 — it is the binding-resolved, untruncated, composition-parsed subset of 6,917, which M1 must measure exactly.**

**Licensing (S1 for the deliverable).** MatNavi Terms Art. 9.2 licenses the data for the licensee's own research; Art. 10(1)-(3),(5) prohibit copying, derivative use, distribution and bulk acquisition; the sole carve-out is "publication of deliverables of research and development". Consequences that shape the architecture rather than merely the paperwork:
- The hidden tables cannot be published. The reproducibility artefact is therefore the **deterministic loader + the 24 validator invariants + the vocabulary + a synthetic stand-in table**, plus the SMiPoly/OMG discovery pool, which is redistributable. Publish the recipe and the metrics, ship no rows.
- Releasing weights trained on the data is not addressed by the Terms and should be treated as requiring written permission — which makes PolyRank a private artefact and is a second argument for the property-agnostic pre-ranker.
- **Sending PoLyInfo rows to a hosted LLM API may itself be "transmission" under Art. 10(1).** The feedback design in section 3.2 (tag profiles and derived descriptors, no names, no SMILES, no ids, no raw records) is what makes the loop defensible under that reading, and it is the same design that hardens against memorisation. One decision, two benefits.

### 10.2 The rest, tabulated

| Defect | Number | Effect on this strategy |
|---|---|---|
| D2 encoding | UTF-8 with 3 damaged sequences; cp949 read mangles 16 cells; P908186 lost; 2 garbage rows | loader reads `utf-8, errors=replace` and asserts exactly 9 U+FFFD; the 2 rows are flagged, never used |
| D3 electrical strings | 0 values parse as float directly; a greedy regex misreads 2,061 of 4,048 | bounds the multi-property phase only; Tg and Tm are unaffected |
| D8 unit mislabels | `Elongation_at_break_GPa` is percent; CSV Tg in degC, XLSX Tg_K in Kelvin | one offset (+273.15) and one rename; the elongation column name will mislead an LLM reading the schema, so rename it in the domain model, not just in a comment |
| D10 identity | periodic key falsely merges 5 XLSX / 2 CSV / 1 cross-file pairs | trimer ring-closed key everywhere; novelty checks and dedup depend on it |
| D11 same-monomer copolymers | 3,952 rows / 713 ids with `smiles1 == smiles2`; 4,756 rows share one key | routed to the homopolymer path; they inflate "both monomers matched" (4,680 of the 32,994 matched rows are such pairs) |
| D12 XLSX join incomplete | 2,338 rows (17 %) property-free, **including the primary pids of PE, PS, PMMA, PVC, PET, PEO, PLA, PCL** | a "the system rediscovered polyethylene" narrative will fail on the primary pid; PS, PDMS, PTFE and PVDF carry data under a *second* pid, so any named-polymer claim must state which pid |
| D13 architecture tags | 27.7 % multi-tag, 49.0 % plain `unspecified`, 4,033 alternating-tag rows lack `-alt-` in the name | architecture is a **half-trustworthy** axis: usable inside Beams 1-2, never as the Beam-3 primary axis (that is backbone class), and its attributed contribution is reported with the tag-reliability caveat |
| D15 outliers | 78 rows with Tg > Tm; 41 with Tg/Tm(K) < 0.4; density 0.024-6.194 | range warnings, not silent fixes |
| D16 corrupt zip | 15 member CSVs, all NUL | whatever wider copolymer export it held is unavailable; do not plan on it |

### 10.3 What this means for the pre-proposal's Phase 2 (PFAS)

Three plain statements:
1. **There is no public SMILES-labelled polymer-adsorbent PFAS dataset.** The two structured sets are 457 literature points over 21 PFAS species x 16 polyamide NF/RO membranes (plus 77 in-house AFFF experiments), and a resin-screening set covering 43 PFASs described by *bulk* properties, not SMILES. A 200-500 polymer set is a literature-mining project with heterogeneous conditions (pH, water matrix, PFAS species), not a dataset in hand.
2. **The pre-proposal miscites its anchor.** Dangayach et al. 2025 is described as "ML inverse design for polymeric membranes including PFAS removal, but single-surrogate and no beam attribution". It is a **review** — ACS labels the article type "Review" — covering data collection, model choice, HTVS, BO, generative inverse design and a case-study table. It is not a single-surrogate PFAS design system and cannot be the foil the Related Work section uses it as. Fix the citation.
3. **PFAS is not a "sparse regime of the Tg system"; it is a second, more MOF-shaped system.** Adsorption of PFOA in a crosslinked porous polymer network is GCMC in a Polymatic-built cell — a cheap, per-candidate physical oracle of exactly the kind Tg lacks. The design vocabulary (cationic head, H-bond donor, hydrophobic versus fluorophilic tail) is real and the chemistry is documented. But the adsorbent families are network polymers, which the two-slot PoLyInfo monomer table cannot represent at all. **Recommendation: keep PFAS, reframe it as a separate discovery-mode campaign with its own pool and its own GCMC oracle, and gate it on a dataset decision rather than scheduling it as Weeks 5-8.** One mechanism correction while re-reading the adsorbent literature: the PPN-6 study reports electrostatic and hydrogen-bonding interactions driving **short**-chain PFAS adsorption and hydrophobic/fluorophilic interactions improving **long**-chain adsorption — the pre-proposal's shorthand has this inverted.

---

## 11. (j) Component map

Verdicts: **PORT-AS-IS** (copy, rename strings), **ADAPT** (keep the shape, replace the domain content), **REPLACE** (a polymer-specific module takes its place, but the interface is kept), **DROP**, **NEW** (no parent counterpart).

| LLM4MOF component | Polymer equivalent | Action | Rationale |
|---|---|---|---|
| Agent 1 (`agent1_handler.py`, 242 l.; multi-turn, T=0.0, 8-field JSON of which 4 validated) | Same handler; hypothesis JSON fields become `target_property`, `hypothesis_mechanism`, `ideal_descriptor_profile`, `backbone_composition`, `sidegroup_composition`, `composition_and_architecture`, `novelty_justification`, `lesson_learnt` | PORT-AS-IS | The wrapper, the multi-turn history, the JSON-repair-then-halt path and the four-key validation are domain-free. Only the required-key list and the wrapper's English change. Keep `meta_cognition.reasoning` and the Exploitation/Exploration declaration — it is what makes the trace readable. |
| Agent 2 (`agent2_handler.py`, 345 l.; stateless, T=0.0, soft validation, `{DATABASE_MODE_RULES}` injection) | Same handler; the three mode-rule blocks become the five **regime** rule blocks (P1-P5) | ADAPT | The stateless-translator pattern plus soft validation is the right shape. The regime blocks are where the pre-proposal's regime idea actually lives, and injecting them at init keeps the regime deterministic instead of conversational. |
| Controlled vocabulary (124 tags, 215 aliases, 105 SMARTS, ~152 hierarchy entries) | ~95 polymer tags in 8 categories + alias map + polymer SMARTS set | REPLACE (machinery PORT-AS-IS) | `constraint_utils.canon` / `get_approved_vocab` / AND-OR-negative parsing / branch matching / categorized groups are all domain-free. Only the JSON file changes. Drop the PORMAKE coordination-tag handover; add the architecture category. Fix the parent's `UNIFIED_ONTOLOGY_PATH` vs `UNIFIED_VOCABULARY_PATH` mismatch before copying anything. |
| Matchmaker (`matchmaker.py`, 668 l., PORMAKE assembly) | Monomer / pair / composition-window search over the polymer tables | REPLACE | The body is MOF assembly logic; the interface (constraint JSON in, candidates + diagnostics + structured error out) is the stable part. Port the default-permissive rule, the no-silent-default halt and the cross-table tag portability guarantee. |
| hMOF / QMOF matchmakers (whole-record filtering, `search_mode` full / metal_only / linker_only) | `HomoMatchmaker`, `CopoMatchmaker` with `search_mode` full / backbone_only / chemistry_only | ADAPT | This, not `matchmaker.py`, is the right template: tags AND/OR/exclude + numeric ranges + a `search_mode` that builds the beams. Metals become backbone classes; topology becomes architecture; the numeric ranges become the descriptor and composition windows. |
| Building-block library (518 nodes x 156 linkers, `pormake_bb_dictionary_v7.json`) | Monomer library: 4,792 CSV monomer SMILES + 13,661 XLSX repeat units (4,782 RDKit-valid, 4,666 distinct backbones) for DB mode; SMiPoly's 1,083 monomers for discovery | ADAPT | Same role: the closed set of things the proposer may assemble. Keys are trimer keys, not `N###` / `E###`. |
| Topology library (952 single-node topologies, `sim_safe_topologies.py`) | **Architecture tags** {random, alternating, block, graft, statistical, periodic} + composition grid | DROP the module, RETARGET the role | There is no polymer topology. The combinatorial third axis is architecture x composition, and it is far smaller (6 x 9) than 952 — which is why the design space must be a rule-matched sum over monomer pairs, not a product with a topology factor. |
| hMOF (51,145) | COPO-Tg: 13,350 rows / 2,735 ids usable core; 6,917 / 1,381 composition-parsed | ADAPT | hypothetical-flavoured, whole-record, coverage-restricted, needs an explicit restriction sentence in the inquiry — same shape |
| QMOF (20,373 DFT records of synthesised MOFs) | HOMO-Tg: 13,725 rows, Tg 7,733 / Tm 3,696 / density 1,651 | ADAPT | real published materials, one aggregate value per record, aggregation rule unknown on both sides |
| PORMAKE tables (14,173 / 9,533, pre-filtered to the proposable space) | SYNTH: SMiPoly 169,347 homopolymers x composition grid x architecture | ADAPT | same "table restricted to what the proposer can reach" concept; keep the concept, drop `build_canonical_db.py` |
| CoRE-MOF | PoLyInfo public counts + PI1M (academic-only) | ADAPT | novelty reference only, never scored |
| MOF2Zeo (`filter_candidate.py` 840 l. + `mof2zeo/`; 545,107 train, R2 0.99, MAE slack, triage only) | `PolyRank` surrogate + the identical triage contract | REPLACE (contract PORT-AS-IS) | The categorical-embedding regression head does not transfer to SMILES/composition inputs. The *rules* do transfer and are the strategy's answer to the surrogate meta-loop: pre-rank only Beam 1, widen the window by the model's own per-regime MAE, never gate. Flag the label-accounting asymmetry (section 5.3). |
| Four beams (`sensitivity_analyzer.run_analysis`, `_build_beam_specs`) | Full hypothesis / chemistry-only / backbone-only / random, as the nested ladder of section 7.1 | ADAPT | The ladder is domain-free; the three axes are not. Fix the Beam-3 geometry-filter asymmetry and the Beam-1 fallback contamination rather than reproducing them. |
| Extra sensitivity sets (B..S, human-only EF / Mann-Whitney report) | Same, over polymer descriptors | PORT-AS-IS | Explicitly "Human analysis ONLY - NOT shared with Agent 1". Keep that firewall exactly. |
| Sampling strata (`sampling_strata.py`, 160 l., metal round-robin, identity only) | `backbone_class_of` round-robin, plus the aide2 `STRATA_MODE` switch | ADAPT | Identity-only stratification that never reads the target is the single most transferable trick in the parent. The stratum key is the only thing that changes. |
| Memory ledger (`memory_ledger.py`, 673 l.) | Same, with `_GEOMETRY_COLS` to descriptors and `_struct_label` to the tag profile | PORT-AS-IS | Facts-only rendering; the finding that prescriptive text hurt is a result to inherit, not re-derive. Keep the verified random-beam behaviour (C8) and decide the transcript-window question explicitly (E4). |
| Feedback generator (`feedback_generator.py`, 910 l.) | Same skeleton; every column, row-renderer and hint sentence rewritten | ADAPT | Structure domain-agnostic, content entirely MOF. Add `(N=n)`, replicate SD and `basis`; remove names and SMILES. |
| Feedback live adapter (`feedback_live_adapter.py`, 245 l.) | Oracle result to beam DataFrame | ADAPT | This is the correct seam for swapping T2 / T3 / T4 oracles behind one feedback schema. |
| Oracle: PORMAKE to LAMMPS-UFF to Zeo++ to RASPA3 GCMC (`hpc/run_mof_sim.py`, 949 l.) | T0 GC/Fox (gate), T2 table look-up (DB ground truth), T3 RadonPy density (live gate), T4 MD Tg (live target, <= 10 finalists) | REPLACE | Nothing of the MOF chemistry survives. The **result-JSON + `.DONE` sentinel contract** does survive and should be kept byte-compatible. |
| Force fields, adsorbate registry, unit conversions, PACMAN charges, `_pacman_worker.py`, physical sanity gates | GAFF2_mod / OPLS via RadonPy; Tg / Tm / density registry in K and g/cm3; sanity gates 100 <= Tg_K <= 800, 150 <= Tm_K <= 900 (invariant I17) | DROP and rebuild | Entirely domain-specific; the *pattern* of a per-property registry with units, direction and sanity bounds is what transfers. |
| HPC runner (`run_live_experiment.py` 1,988 l., `prepare_batch.py`, `aggregate_results.py`, `submit_iteration*.sh`) | dirac PBS via the `hpc-submit` skill's mandated `config/hpc.json` + `scripts/submit.py` | ADAPT | dirac is also PBS, but the skill requires its own convention and stops without it. Port the **logic** (manifest up, per-job JSON + `.DONE` down, aggregate, adapter, `SimCache` keyed by candidate_id, real-iteration accounting) into that convention — not the shell scripts. The parent's live runner is also broken at HEAD (`core.han_safe_topologies` does not exist). |
| GA baseline (Note S6) | GA over (monomer A, monomer B, composition, architecture) with a retrained surrogate | ADAPT | Same protocol, but the polymer surrogate is genuinely predictive where the parent's had held-out R2 approximately 0. Expect a much stronger baseline and pre-commit to reporting it honestly. |
| BO baseline (Note S7, LVGP + EI) | LVGP over the monomer pair + a **continuous** composition dimension | ADAPT | Composition being real-valued makes the polymer BO stronger than the parent's all-categorical version. |
| Generative baseline (EGMOF, own prior work) | polyBART / POLYT5 / PolyTAO / CharRNN-RL as published, or dropped | ADAPT | The parent's own comparison "is never compared numerically" because the halves use different GCMC codes. In DB mode LLM4POL has no such excuse — everything can be scored by the same table — so either do it properly or omit it. |
| Fox / group contribution | — | **NEW** | No MOF counterpart exists. These are simultaneously interpretable baselines and the attribution ground truth. |
| Evaluation protocol (percentile of beam median, hit rate / enrichment, 5 replicates, ablation-one-at-a-time, label accounting) | Same, plus the fixed-n primary statistic, AUC, no-match rate, and 10 replicates | ADAPT | The protocol is the most valuable thing in the parent. The changes are the three flaws its own critique exposes: unreported n, too few replicates for the observed sigma, and un-retried DB-mode no-match iterations. |
| Backend benchmark (6 backends x 7 tasks x 5 reps, Agent 2 pinned, first attempt) | Same | PORT-AS-IS | Also report within-arm SD next to between-arm SD, and wire the Anthropic branch that the parent's shipped `llm_client.py` never had despite three Table-1 arms using it. |
| Battery driver (OLD `scripts/precheck/run_battery.py`, `parse_results.py`) | Same | PORT-AS-IS | Seeded replicates, `--no-feedback`, percentile-of-hidden-table metric and AUC — this is the evaluation harness the published repo lacks and the port needs from day one. |
| `llm_client.py` (446 l., OpenAI + Gemini, usage logging, 4-strategy JSON repair) | Same + an Anthropic branch | PORT-AS-IS | Wire `agent_backend(n)` through properly; the parent defines a Claude branch in config that `llm_client.py` never references. |
| `memory_manager.py` (304 l., context / conversation / experiment logs) | Same | PORT-AS-IS | Pure audit plumbing. |
| `name_resolver.py` (125 l.) | Tag-profile renderer | REPLACE | Deliberately *not* a name resolver — names are the leakage channel (section 3.2). |
| `config.py` (840 l.) | Same skeleton | ADAPT | Keep the provider block, env toggles, experiment dir and cost logging; replace the metric/unit/adsorbate registries; drop RASPA and Zeo++ sections. Fix the `LLM2POR_*` versus `LLM4MOF_*` env-name divergence before copying. |
| `database_construction/` (Layer-1 facts + 105 SMARTS + tag hierarchy + display-only LLM enrichment) | Polymer equivalent driven by the audit's loader | ADAPT | `5_shared/smarts_library.py` and `4_vocabulary/04_build_vocab_mapping.py` are directly reusable with a polymer SMARTS set, and the two-layer philosophy is the strategy's defence against LLM-written fields leaking into filters. |
| `build_canonical_db.py` | — | DROP (keep the idea) | "restrict the hidden table to what the proposer can reach" is the concept; the parent's implementation rewrites CSVs in place. |
| — | **Loader + 24-invariant validator** (audit sections 3.4 and 4) | **NEW** | No parent counterpart and the single largest piece of net-new work. Everything downstream is wrong without it. |
| — | **`RegimeRouter`** | **NEW** | The pre-proposal's regime idea, implemented deterministically. |
| — | **Composition-slope statistic** (378-id instrument) | **NEW** | Attribution over a continuous axis; no MOF analogue. |
| — | **Attribution scorer (T1/T2/T3)** | **NEW** | The contribution. Measures what the parent asserted. |
| — | **Zero-feedback + hint-ablation arms** | **NEW** (exists in aide2, absent from the published system) | The memorisation and prompt-echo controls. Non-negotiable for polymers. |
| — | **Supervised-shortcut probe** | **NEW** (exists in aide2, absent from the published system) | The ceiling statement, published before the results. |

---

## 12. (k) Milestones and exit criteria

Parallel-safety column: **P** = can run concurrently with the milestones listed; **B** = blocking.

| # | Milestone | Measurable exit criterion | Parallel |
|---|---|---|---|
| **M0** | Repo and environment | Repo exists **outside Dropbox** (the `hpc-submit` skill warns Dropbox locks corrupt its ledger); pixi manifest + lock committed; a single `scripts/check.py` gate runs ruff, ruff-format, mypy strict, import-linter and pytest and is green in CI on windows-latest + ubuntu-latest; `config/hpc.json` and `scripts/submit.py` exist per the skill's contract; the CUDA-torch decision is recorded as an ADR | **P** with M1 |
| **M1** | Loader + 24-invariant validator | Loader reproduces, exactly: 42,557 CSV rows with 9 U+FFFD, 7,385 polymer_ids, 13,725 XLSX rows, Tg_K n = 7,733. Binding resolution reproduces aligned 15,409 / swapped 2,221 / half_aligned 5,309 / half_swapped 881 / neither 433 / one_id 190 / no_ids 18,114. Trimer key gives **0 false merges** against the stored allow-list (the periodic key gives 5 + 2 + 1). Usable core reproduces **13,350 rows / 2,735 ids** and **6,917 rows / 1,381 ids**. All 24 invariants implemented, hard ones failing the load. **New number this milestone must produce: the size of the binding-resolved, untruncated, composition-parsed subset** — the true bound on the composition contribution. | **B** for everything below |
| **M2** | Hidden tables, vocabulary, Matchmaker | Three tables built (HOMO-Tg group-median; COPO-Tg composition-eligible; COPO-arch). Vocabulary >= 90 canonical tags, each with >= 20 matches in at least one table, and >= 95 % of rows carrying at least one backbone-class tag. **Portability test: a 50-constraint fixture set returns non-empty matches from both HOMO and COPO for >= 90 % of fixtures.** Matchmaker returns the structured-error shape on empty/malformed input and never silently defaults. | **P** with M3 |
| **M3** | Descriptor layer, GC table, Fox | All 7 descriptors computed for every monomer with <= 1 % RDKit failures beyond the known 10. GC Tg reproduces in-sample MAE <= 15 K on HOMO-Tg. **Fox reproduces approximately R2 0.835 / RMSE 42.6 C on the binding-resolved copolymer rows — if it does not, M1's binding is wrong and M1 reopens.** van Krevelen table transcription verified against a second source. | **P** with M2 |
| **M4** | Loop skeleton, DB mode | A 10-iteration campaign runs end to end with 2 LLM calls per iteration; artefacts match the parent's layout (`agent1_output.json`, `agent2_output.json`, `beam_data.csv` **with n per beam**, `feedback_selected.txt`, `memory_ledger.json`, `usage_log.json`); no-match iterations are retried and not counted; cost < $2 per campaign; a grep of `feedback_selected.txt` across a full campaign finds **zero** IUPAC names, SMILES strings, pids or sample_ids | after M2 interfaces freeze; **P** with M3 |
| **M5** | Battery and pre-registered controls | 10 replicates x 6 tasks for V0 and the zero-feedback arm; measured sigma of the final percentile reported; supervised-shortcut probe OOF R2 published per table; memorisation share (NF-50)/(V0-50) reported per task. **Gate: any task with memorisation share > 0.8 is dropped from the headline and reported as memorised.** | **B** for any claim; **P** with M6's non-LLM arms |
| **M6** | Baselines and budget matching | Random, GA, BO, Fox, GC (and polyBERT if licensed) at realised budgets within 5 % of 400; a per-arm realised-evaluation table; a per-arm no-match table. The claim is whatever survives — including "GA wins", if it does. | **P** with M5 |
| **M7** | Attribution measurement | T1 reported over >= 20 tags with n >= 30 (Spearman rho + sign agreement vs van Krevelen); T2 reported over the 378-id instrument (sign-agreement fraction vs Fox, with the 67 low-rho ids broken out); T3 reported over >= 50 counterfactual hypothesis edits; hint-ablation arm complete. All three pre-registered before M5 ran. | after M5 |
| **M8** | Discovery mode (only if M5-M7 pass) | SMiPoly/OMG pool built with the design space reported as a **rule-matched sum**, not a product; RadonPy Tg preset validated against PoLyInfo on >= 20 overlapping polymers with the calibration stated; 40 pre-finalists through T3 density; <= 10 finalists through T4 Tg with >= 3 replicates, raw and calibrated values both reported; realised dirac core-hours logged | after M7 |
| **M9** | PFAS, reframed (optional) | Gated on a dataset decision. If it proceeds: a curated set with explicit condition columns, a Polymatic-built network pool, and a GCMC oracle — a second discovery-mode campaign, not a regime of the Tg system | fully independent; **P** with everything once M0 exists |

**Critical path:** M1 to M2 to M4 to M5 to M7. M0, M3 and the non-LLM half of M6 run alongside. M8 and M9 are downstream and resource-gated.

**Sequencing note against the pre-proposal.** The pre-proposal's Phase 1 (Weeks 1-4) is "compute RDKit descriptors, implement 5 Tg hypotheses x 4 beams, aggregate Tg per beam, produce a causal attribution". That skips M1 and M2 entirely — the loader, the 24 invariants, the hidden-table construction and the vocabulary — and the audit lists 16 defects, four of them S1, against the proposal's two listed data-quality actions. M1 alone is a multi-week milestone. A four-week Phase 1 that produces an attribution claim on an unvalidated table produces an attribution claim that is wrong in roughly a third of the composition rows.

---

## 13. (l) Decisions only the user can make

| # | Decision | Why it is blocking and what swings on it |
|---|---|---|
| **U1** | **May PoLyInfo-derived content be sent to a hosted LLM API?** (MatNavi Art. 10(1) "transmission") | The entire loop. If no, the options are a local model (needs a CUDA env that does not exist) or a strictly derived-metadata payload — which is what section 3.2 already proposes, so a "derived tags only" answer is compatible with this strategy, but a blanket no is not. |
| **U2** | **What is the deliverable?** Paper / internal tool / released model / released dataset | A paper is fully supported by DB mode. A released dataset is prohibited. A released model trained on the data is unaddressed by the Terms and should be treated as needing NIMS written permission — which makes PolyRank private and strengthens the case for the property-agnostic pre-ranker. |
| **U3** | **Homopolymer-only (the pre-proposal) or homopolymer + copolymer?** | Homopolymer-only is a cleaner dataset and a straightforward port — but it discards the continuous composition axis, which is the single largest source of genuine novelty versus LLM4MOF. Choosing homopolymer-only reduces this project to a transplant. |
| **U4** | **The 5,309 undetermined-binding rows: drop, or obtain the original PoLyInfo component records?** | Drop costs 12.5 % of rows and, worse, is non-random (the mixing test there favours the reversed binding). Obtaining the records requires a new export. |
| **U5** | **The 30 conflicting XLSX duplicate-structure Tg groups (max spread 169 K) and 77 conflicting duplicate-name groups (max 212 K): average, keep, or drop?** | These cap achievable RMSE and set the top-1 % threshold. Median-aggregating a 169 K conflict is a decision, not a repair. |
| **U6** | **One hypothesis per iteration (parent) or N (pre-proposal)?** | N multiplies the oracle budget by N and breaks budget matching against GA/BO. This strategy assumes 1 with `monomer_branches` carrying alternatives. |
| **U7** | **Is regime classification an LLM decision (pre-proposal) or a deterministic router (this strategy)?** | The parent's mode-blindness ("the hypothesis-generating agent receives no signal indicating which mode it is running in") is one of its cleanest controls and this strategy preserves it. Making it an LLM call is defensible only with a measured regime-classification accuracy and a control arm. |
| **U8** | **Does PFAS Phase 2 proceed given that no public dataset exists?** If yes: who mines the literature, on what schedule, and does it become a separate GCMC-oracle campaign? | Section 10.3. As written in the pre-proposal it is not schedulable. |
| **U9** | **polyBERT licence** (HF, GTRC academic-research, not anonymously readable) | Determines whether the polyBERT-guided baseline exists. |
| **U10** | **Create a CUDA 12.8+/13.x torch environment for the RTX 5050? Does dirac expose GPU nodes?** | Needed only for the polyBERT baseline and GPU LAMMPS. **M1-M7 need none of it** — a useful fact, since it means the scientific programme is not blocked on hardware. |
| **U11** | **Repo location and stack.** Outside Dropbox; adopt the CALF20 conventions (pixi, src layout, single check gate, MADR ADRs, append-only ledger, per-project GSD with OMC disabled)? | The prior project's stack is proven on this machine and its ADR-0003 ("scientific agents are API calls, never Claude Code subagents") is directly relevant to how the two agents are implemented. |
| **U12** | **API budget.** ~$350-500 covers the DB-mode programme plus a 6-backend benchmark (about 330 campaigns at roughly $1 each, about 32 hours of wall clock at 6 concurrent). | Small, but it must be approved before M5. |
| **U13** | **Which parent snapshot to fork.** The newer public clone (HEAD 2026-09-09) cannot run — `config.py` exports `UNIFIED_ONTOLOGY_PATH` while `constraint_utils` imports `UNIFIED_VOCABULARY_PATH` (DB mode dies at matchmaker init) and `live_runner` imports a module that does not ship. The older clone imports cleanly and the two git histories are unrelated. | Recommendation: fork the **older** clone for the loop and the battery harness, and take the newer one only for the multi-backend and provider-switch work. |

---

## 14. (m) Risks

| # | Risk | Evidence it is real | Mitigation built into this strategy |
|---|---|---|---|
| **R1** | **Memorisation dominates.** The agent reproduces textbook polymer knowledge and the beams merely dress it up. | MOF memorisation shares 0.44 / 0.44 / 0.72, worst on the task where the model already knew the chemistry. Polymer Tg is entirely that kind of task. | Zero-feedback arm is mandatory with a hard gate (share > 0.8 drops the task); feedback carries no names, SMILES or ids; the supervised-shortcut probe bounds the achievable enrichment and is published first. |
| **R2** | **The composition attribution is sign-flipped.** | D1: about 30 % of resolvable rows are swapped; the mixing test is 13.7 C versus 56.8 C. | Binding is a first-class field with an `undetermined` state; the composition axis runs only on resolved rows; Fox reproduction is M3's exit criterion and doubles as the binding validator. |
| **R3** | **GA and BO beat the LLM loop**, so the parent's headline does not port. | The parent's GA surrogate had held-out R2 approximately 0 (its own SI concedes neither baseline is strong for a 12.5 M categorical space at 400 labels). A polymer surrogate reaches R2 0.85-0.89, and composition being continuous makes BO stronger too. | Pre-commit to reporting it. The contribution is the measured attribution (T1-T3), not the win. A paper whose headline is "beam attribution agrees with group contribution at rho = X, and GA matches the loop on raw performance" is publishable and honest; one that buries a losing baseline is not. |
| **R4** | **Replicate noise swamps every effect.** | Within-group Tg SD median 7.0 C, p90 33.1; within-id range median 20.2 C with 588 ids over 50 C; campaign-level sigma 6.4-15.9 percentile points at n = 10; W2's 210 seeded campaigns found no variant beating the default at Holm-corrected significance. | 10 replicates not 5; AUC alongside the endpoint; replicate SD printed in the feedback and next to every metric; no claim about a configuration difference without a power statement. |
| **R5** | **Interpretability is still unmeasurable** because the beam-implied contributions are too noisy at n = 10 per beam. | The parent shows the matched set swinging 1 to 9,533 and never reports n. | Fixed-n primary statistic; tags need n >= 30 to enter T1; the 378-id composition instrument is chemistry-controlled by construction; T3 counterfactuals are independent of beam noise entirely. |
| **R6** | **The GC table is wrong.** No pip-installable van Krevelen / Bicerano implementation exists; the available transcription is unverified against the book. | Landscape open question 1. | M3 verifies the transcription against a second source before it becomes the attribution ground truth; GC in-sample MAE <= 15 K is the sanity gate. |
| **R7** | **Live mode breaks the "no property-labelled training structure" claim** because PolyRank is property-labelled. | Section 5.3. | DB mode keeps the claim intact and is primary; live mode reports loop evaluations and surrogate labels as one number; a property-agnostic MLFF pre-ranker (SimPoly-class, PolyArena-benchmarked) is spiked as the clean alternative. |
| **R8** | **MD validation is unaffordable or uninterpretable.** | 4,000-20,000 CPU-h per candidate; 0.3-1.5 candidates/day at 256 cores; +40-120 K offset; >= 10 replicas for a CI under 20 K; RadonPy's Tg preset has no published PoLyInfo validation. | MD is a top-k validator only (<= 10 finalists); calibration against PoLyInfo precedes use; raw and calibrated values both reported; T3 density (R2 0.890, about a day on 32 cores) is the cheap gate; PolyArena is the ready-made external benchmark. |
| **R9** | **PFAS Phase 2 has no data.** | No public SMILES-labelled polymer-adsorbent set; 457 membrane points and a 43-PFAS bulk-descriptor resin set are the structured alternatives; the pre-proposal's anchor citation is a review. | Reframe as a separate GCMC-oracle discovery campaign, gate on a dataset decision, do not schedule it as Weeks 5-8. |
| **R10** | **The prompt, not the data, produces the "design rules."** | The parent's prompt dictates the axis menu, the exploration trigger, the soft-count rule and a read-the-evidence procedure, several tuned empirically; the feedback hints tell the agent how to read the beams. | Hint-ablation arm; T3 counterfactuals; the attribution table is scored against GC and Fox, which the prompt does not know. |
| **R11** | **Licence exposure through the loop or the outputs.** | Art. 10(1) transmission; generated candidates could regurgitate PoLyInfo entries. | Derived-tag payload only; novelty checked against the trimer-key union of both tables plus the public PoLyInfo counts; the released artefact is the loader + validator + vocabulary + SMiPoly pool, never rows. |
| **R12** | **Schedule collapse in M1.** The pre-proposal budgets two data-quality actions; the audit found sixteen defects, four at S1. | Sections 10.1-10.2. | M1 is explicitly blocking with hard, reproducible exit numbers, and nothing downstream starts on an unvalidated table. |

---

## 15. What is genuinely new versus LLM4MOF — and what the pre-proposal oversells

### 15.1 Genuinely new and defensible

1. **A continuous design axis with a physical mixing law, and a chemistry-controlled statistic for attributing it.** MOFs have no continuous axis and no Fox equation. The within-pair composition-slope test on the 378-id instrument is a new kind of beam statistic, not a relabelled one.
2. **Measured attribution.** van Krevelen increments give a per-tag numeric ground truth that MOF-land simply does not have; T1, T2 and T3 turn "interpretable" from an adjective into three numbers. This directly answers the parent's largest reviewer wound, which its own critique corpus documents: interpretability never measured, and a supervised probe recovering 94 % of one hidden table from three columns.
3. **An oracle that is measured experimental data.** In DB mode, "the design rule is an artefact of the force field" — the critique that lands on the parent's CO2 and C2 results — cannot be made. This is a scientific upgrade purchased by accepting that live mode is expensive.
4. **Memorisation-hardened evaluation for LLM design agents.** Name-free, SMILES-free, id-free feedback plus a mandatory zero-feedback arm plus a hint-ablation arm. Motivated by a domain where the pretrained model genuinely knows the answers, and generalisable beyond polymers.
5. **A deterministic applicability-domain router with per-regime surrogate slack.** The implementable residue of the pre-proposal's regime idea, and something LLM4MOF never needed because one force field covered everything.

### 15.2 Oversold in the pre-proposal

1. **"First adaptation of diagnostic-beam attribution from MOFs to polymers"** is, on its own, a port. It becomes a contribution only with 15.1.2. Note also that the closest competitor is not acknowledged: CI-LLM / HAPPY mines chemically meaningful subgroups from about 10,000 PoLyInfo repeat units and does Integrated-Gradients subgroup-level attribution with RL design at 100 % scaffold retention. That paper must be cited and beaten on the attribution-validity axis, not ignored.
2. **"An explicit LLM surrogate meta-loop with validation and extrapolation-risk flagging"** — the mechanism already exists deterministically in the parent (`_apply_mae_slack` plus "the surrogate reorders, never decides"), and the strong novelty claim is contested by SPACIER (RadonPy + BO, synthesized polymers), a 2026 polymer-electrolyte BO + MD system, Polymer-Agent (every LLM edit re-validated by the predictor) and PolyFusionAgent (GPR filter at tau = 0.5 sigma). The only defensible framing is the measured one: does the router lower surrogate-failure rate versus a naive single surrogate, on a held-out regime. That needs a failure-rate definition, which the pre-proposal does not give.
3. **"Regime boundaries that control the abstraction level of LLM reasoning"** — as a deterministic router this is sound engineering. As "the agent's first decision is always which regime is this", it removes the parent's mode-blindness control and adds an unmeasured branch upstream of everything. And on Tg specifically the meta-loop's measurable value is near zero: the candidate surrogates differ by about 5 K RMSE while the data's replicate SD is 7.0 C at the median and 33.1 C at p90. **Selecting among those models is selecting inside the noise.**
4. **Regimes R4 and R5.** R4 (PFAS) is a different physics with a different oracle and no dataset. R5 (block copolymers, thermosets, dendrimers) includes materials the two-slot monomer table cannot represent — 4,243 rows are already terpolymers truncated into two slots with `component3..5` empty.

### 15.3 Where the pre-proposal collides with the audit

| Pre-proposal statement | Audit finding | Consequence |
|---|---|---|
| Primary dataset "13,725 homopolymers"; the copolymer CSV is never mentioned | The 42,557-row CSV holds the only continuous axis, with a usable core of **13,350 Tg rows / 2,735 ids** and a composition-parsed subset of **6,917 rows / 1,381 ids** | The proposal's own regimes R4-R5 and its composition story have no data behind them as written. Fixing this is what makes the project novel. |
| Two data-quality actions: elongation units, "~100 duplicate canonical SMILES" | 16 defects, four at S1 (binding swap, encoding, electrical string units, corrupt zip). Duplicates are 91 groups / 192 rows / 101 excess, of which **30 have conflicting Tg up to 169 K**, plus 206 duplicated names giving 77 conflicting groups up to 212 K | "Aggregate to a per-structure median" is not a repair for a 169 K conflict; it is user decision U5. M1 is a milestone, not a preamble. |
| Phase 1 in Weeks 1-4 produces a causal attribution | Requires the loader, 24 invariants, three hidden tables and the vocabulary first | Four weeks produces an attribution that is sign-flipped on about a third of composition rows. |
| "5 Tg hypotheses x 4 beams" | Parent runs 1 hypothesis per iteration, 2 LLM calls, 400 evaluations per campaign | Budget x5 and budget matching against GA/BO is destroyed. Use `monomer_branches`. |
| No replicate or uncertainty protocol | 56.3 % of Tg rows are replicates (SD p90 33.1 C); campaign sigma 6.4-15.9 percentile points | A one-shot run measures nothing. 10 replicates minimum. |
| No memorisation control | MOF memorisation share up to 0.72, worst on the pretrained-knowledge task | The single most important omission in the document. |
| "Modern polymer ML predicts Tg well (R2 about 0.85)" | 56.3 % replicate rows means random row splits leak; grouped splits are mandatory (invariant I21) | The 0.85 is partly replicate leakage; leakage-aware numbers are the only comparable ones. |
| Phase 4: "compare beam-derived claims to MD ground truth" | MD Tg carries +40 to +120 K systematic offset and needs >= 10 replicas for a CI under 20 K | MD is not ground truth for Tg. Calibrate MD **against** PoLyInfo, then use it only outside PoLyInfo. |
| Risk table: "MD too expensive for a loop; two-tier oracle" | Correct, but the tier-2 budget is 0.3-1.5 candidates/day at 256 cores | "A handful of finalists" means <= 10 per task, and one live task is a few weeks of dirac. |

### 15.4 Where the pre-proposal collides with the 2026 literature

1. **Dangayach 2025 is a review**, not a single-surrogate PFAS inverse-design system. Double-sourced; ACS labels it "Review". The Related Work foil must be replaced.
2. **RadonPy now has a Tg preset** (`sim/preset/tg.py`, `AutoMD_scripts/4_tg.py`) and random / alternating / block copolymer builders — Tg was absent only from the 2022 paper. Phase 4 is more feasible than the proposal assumes, but the preset has no published PoLyInfo validation, so validating it is a deliverable.
3. **PolyJarvis is homopolymer-only** (nine homopolymers, 18 of 25 property comparisons passing, Tg within 50 K in 7 of 9). It cannot validate copolymer candidates as written, and the "cooling-rate bias rather than agent error" phrase attributed to it is not verbatim.
4. **The PORMAKE analogue already exists** and the proposal does not mention it: SMiPoly (22 rules, 1,083 monomers to 169,347 polymers, BSD-3), OMG (17 reactions to about 12 M CRUs, GPL-3), VFS/pvfsga (over 7 M ROP polymers, three lab-validated). A discovery mode without one of these has no synthesizable design space.
5. **CI-LLM / HAPPY is the closest interpretability competitor** and is absent from the Related Work section.
6. **The PFAS mechanism shorthand is inverted** relative to the PPN-6 adsorbent study (electrostatics and H-bonding drive short-chain uptake; hydrophobic and fluorophilic interactions improve long-chain uptake).
7. **Two arithmetic traps inherited from the parent's own documentation**: never write the design space as a plain product (518 x 156 x 952 = 76,929,216 overstates the correct connectivity-matched 12,499,656 by 6.2x), and never pair an iteration-10 statistic with a pooled-over-all-iterations reference (the parent's SF6 "7.7 versus 2.8" does exactly that — 2.8 is the pooled random median while the iteration-10 value is 2.55).

---

## 16. One-paragraph summary

Take LLM4Polymer v1.0 at its word about *what* it wants — attribution, surrogate discipline, regime awareness — and take LLM4MOF at its code about *how* those are built. Regimes become a deterministic Agent-2 rule router over five polymer regimes, preserving the parent's mode-blindness control. The surrogate meta-loop splits into an offline, pre-registered bake-off and the parent's own online mechanism, `_apply_mae_slack`, made per-regime. The beams stay a nested relaxation ladder over backbone class, side-group chemistry, composition window and descriptor window, with one hypothesis per iteration and alternatives carried in `monomer_branches`. Database mode over the audit-repaired PoLyInfo tables (7,733 homopolymer Tg values; a 13,350-row copolymer core narrowing to 6,917 composition-parsed rows and further to the binding-resolved subset) is the primary mode, because the measured-data oracle removes the force-field-artefact critique that the parent cannot answer, and because MD Tg at 4,000-20,000 CPU-hours per candidate can only ever validate ten finalists. The contribution is not the port: it is that polymers, unlike MOFs, come with van Krevelen group increments and the Fox law, so for the first time a diagnostic-beam system can be *scored* against an independent physical attribution baseline instead of narrating one. Everything else in this document — the name-free feedback, the mandatory zero-feedback and hint-ablation arms, the supervised-shortcut ceiling probe, ten replicates, n printed on every beam — exists so that the score, whatever it turns out to be, is believable.
