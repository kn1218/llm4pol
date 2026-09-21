# Adversarial fact-check of `LLM4MOF-ANATOMY.md`

Date 2026-09-11. Every claim below was re-derived from the primary source myself (`grep -n` in the
manuscript/SI text dumps, or reading/executing the code), not from the anatomy report's own citations.
Code paths: NEW = `C:/Users/molsim/Dropbox/Antigravity/LLM2POR_20260115_v2home/LLM2POR_Automation_v2.5_20260205/LLM4MOF`,
OLD = `C:/Users/molsim/Dropbox/Work to do/Paper review/projects/aide2-llm4mof/LLM4MOF`.

**Headline: 22 of 25 claims confirmed, 3 refuted (C5, C8, C22).** All three are definitional/arithmetic
slips rather than invented facts; the report's substance survives. Eleven additional findings follow.

---

## 1. Verdicts

| id | verdict | what I checked |
|---|---|---|
| C1 | confirmed (mode-qualified) | `SI.txt:62-66` verbatim: "fixed ten iterations with no early-stopping criterion... it is retried, and the plotted iteration index counts the iterations that produced candidates." `run_live_experiment.py:1539-1557`: `real_iterations` counts only iterations with R2 RASPA results, `_MAX_TOTAL_ATTEMPTS = max_iter * 3`. **Caveat:** true only in discovery mode. In DB mode (`run_experiment.py:512-537`) a zero-match iteration is *not* retried - it prints, auto-continues with empty result sets, and the loop counter still advances, so it consumes one of the ten. The SI states the rule unconditionally; the anatomy 2.1 records the DB-mode exception, the condensed claim does not. |
| C2 | confirmed | JSON block at `prompts/agent1_v3.0_production.md:112-124` contains exactly the eight fields listed (`meta_cognition.reasoning`, `target_application`, `hypothesis_mechanism`, `ideal_pore_geometry`, `node_composition`, `linker_composition`, `novelty_justification`, `lesson_learnt`). `core/agent1_handler.py:131-133`: `required = ['target_application','hypothesis_mechanism','node_composition','linker_composition']` - four. |
| C3 | confirmed | `core/agent2_handler.py:91` `LLMClient(self.system_prompt, multi_turn=False, ...)`. `config.py:420-421` `AGENT1_TEMPERATURE = 0.0` / `AGENT2_TEMPERATURE = 0.0` (the claim's 421-422 is off by one). Schema at `SI.txt:1221-1273` has the four top keys incl. `linker_branches: [{description, required_tags}]`, and `SI.txt:131` calls it "an OR of ANDs". `_validate_constraints` (139-213) hard-requires only `node_query`, `linker_query`, `geometry_filter` + `metals_include`; everything else prints WARNING and returns True. |
| C4 | confirmed | Table S4 (`SI.txt:1986-2012`) category counts 5+16+35+39+4+6+6+6+3+4 = **124** over **10** categories; caption says "215-entry alias map". I ran the loader's own algorithm over `data/unified_vocabulary.json`: 124 canonical tags, **215** alias strings listed in the file, **183** entries in the map the code actually builds (aliases that normalise onto their canonical form collapse, and each canonical self-maps). OLD clone prints `124 canonical tags, 183 alias mappings` at load. |
| C5 | **refuted** | The three counts are right (`core/mof2zeo/data/{topology,node,edge}.txt` = 952 / 518 / 156 non-empty lines) and the whitelist really is those files (`config.py:96-104` "SINGLE source of truth"; `core/matchmaker.py:29-33` `_NODE_WHITELIST`/`_EDGE_WHITELIST`). But **518 x 156 x 952 = 76,929,216, not 12,499,656**. `SI.txt:112-116` defines the space as the connectivity-matched sum \|D\| = sum_c n_c t_c L; Table S5's per-class rows give sum_c n_c t_c = 80,126, x 156 = 12,499,656. The anatomy writes the product with an `=` in 2.5 and repeats it in the section-6 numbers table. A port that copies the formula would overstate its own design space by 6.2x. |
| C6 | confirmed | `sensitivity_analyzer.py`: `df_total = self.df_master.copy()` (l. 573, "Baseline: The Full Master DB"); `set_a` = chemistry-only (`filter_h2_db`, l. 661); `set_f = df_total[df_total.apply(filter_node_only)]` where `valid_nodes = self._get_node_list(node_q)` (l. 527, 559-563) and `_get_node_list` (l. 147+) filters on metals + connectivity + ligand_chemistry only, no linker constraint; `set_z = set_d[sa/vf/density/dif/cv inclusive]` where `set_d = set_a[(di > DI_MIN) & (di < DI_MAX) & (df > DF_MIN) & (df < DF_MAX)]` - strict on Di/Df, inclusive on the other five, exactly as claimed. |
| C7 | confirmed | `config.py:409` `FEEDBACK_SAMPLE_SIZE = 10  # Per-beam sample count (10 x 4 beams x 10 iters = 400)`. `feedback_generator.py:449-462`: live -> `df.nlargest(min(n,len(df)),'target')`; DB -> `sampling_strata.stratified_reduce(df,n)` then `df.sample(..., random_state=...)`. `sampling_strata.py:76-100` is metal round-robin, identity only, `target` never read. |
| C8 | **refuted** (one sub-clause) | Everything except "ingests only the three hypothesis beams" checks out: `_HYPOTHESIS_BEAMS = ["z","a","f"]`, `_GEOMETRY_COLS`, `frontier_k = 10`, `render_facts_only` at 544-584 with the verbatim rationale "that exploit guidance HURT the PORMAKE rare-peak apps"; `feedback_generator._prepend_memory_block` (679-710) passes only `self._ledger_beam_samples` (the <=10 rows shown). **But** the keymap there includes `"Beam 4" -> "total"`, and `MemoryLedger.ingest` (172-254) iterates `_ALL_BEAMS = ["z","a","f","total"]` to store `beam_medians` in `history[]` and feeds the random beam into `_detect_outside_promising`. The random beam *is* ingested; what excludes it is only `global_best` / `frontier` / `geometry_envelope` - which is also precisely what `SI.txt:209-211` says ("random candidates are never permitted to populate the ledger's top-K frontier or geometry envelopes"). The anatomy's own 2.8 lists `beam_medians{z,a,f,total}`, so the report contradicts this condensed claim. No leak reaches Agent 1: `render_facts_only` prints neither `beam_medians` nor `outside_promising`. |
| C9 | confirmed | `SI.txt:1392-1409`: nine DB applications x five replicates = 90 runs; "positive or neutral effect across all nine"; largest gains "delta = +41.7 mol/kg" (grav H2 100 bar) and "delta = +9.3" (Xe/Kr); under the peak metric "the ledger is net-neutral to slightly negative on the rare-peak PORMAKE applications"; "metal-stratified sampling algorithm serves as the primary mechanism for raising the absolute performance ceiling". Table S6 rows match the anatomy's table. |
| C10 | confirmed | `SI.txt:269-293`: MOF-NET architecture, 128-d embeddings, seven descriptor heads, 545,107 train / 84,228 valid, average R2 0.99, "used only for simulation triage... The recomputed geometry is the value used for downstream geometry gating". `core/mof2zeo/config.yaml`: `latent_dim 128, hid_dim1 64, hid_dim2 32, desc_dim 7, topo_size 952, node_size 518, edge_size 156, seed 1, batch 256, lr 0.001, max_epochs 500`. `live_runner.py:114-121` `_MOF2ZEO_PRED_ERR = {Di 0.746, Df 0.751, Dif 0.828, sa 50.7, vf 0.0098, density 0.0152}`; `_margin_table()` defaults to `"mae"`; `_expand_geometry_filter` widens only the preranking copy, "The original filter (agent1 output) is kept intact and applied to real Zeo++ geometry later." |
| C11 | confirmed | `SI.txt:1416-1432` (UFF, harmonic bonds, 12.8 A cutoff, cg, 1e-4/1e-6/1000/10000, two outer aniso loops, final atomic minimisation, Zeo++ 1.2 A probe, 5,000+5,000 cycles, Lorentz-Berthelot, no tail corrections, box >= 2x cutoff). Code: `hpc/run_mof_sim.py:274-289` emits exactly `min_style cg` / `variable llm2por_i loop 2` / three `minimize 1.0e-4 1.0e-6 1000 10000` / `fix ... box/relax aniso 0.0 vmax 0.001`; `stage_zeo` (357+) runs `-sa 1.2 1.2 5000`, `-vol 1.2 1.2 50000`, `-res`; `build_sim_json` (498+) with `cutoff=12.8`; `_write_result` (938-945) writes `<filename>.json` plus a `<filename>.DONE` sentinel. `config.py:588-589` 5000/5000; `757-758` LAMMPS 900 s / RASPA 7200 s; `767-777` `HPC_HOST="hpc"`, `HPC_BASE_DIR="~/llm2por"`, node property `ac`, poll 300 s, 24 h ceiling, 3 SSH retries. |
| C12 | confirmed | `Manuscript.txt:454-458` "100 candidates are generated for Beam 1 and 30 for each remaining beam; all are assembled with PORMAKE, relaxed with LAMMPS/UFF, and characterized with Zeo++ ... up to ten structures per beam are evaluated by RASPA3". Code: `config.py:577-579` `LIVE_SIM_Z_POOL_SIZE=100`, `LIVE_SIM_AF_POOL_SIZE=30`, `LIVE_SIM_Z_RASPA_TOP=10`; `LIVE_SIM_N_PER_BEAM=10` (l. 569). `SI.txt:422-424` "380 +/- 2 independent RASPA3 simulations and consumed 0.57 million GPT-5.2 tokens, resulting in a total LLM inference cost of $1.06 +/- 0.05 (mean +/- SEM over five replicates)". Recomputed from `source_data/figure6_token_usage_and_cost.csv`: GCMC per replicate 376/381/379/386/378 (mean 380.0, SEM 1.70), cost 0.877/1.087/1.123/1.140/1.088 (mean 1.063, SEM 0.048), total tokens per replicate 0.556-0.584 M (mean 0.570 M), `model_calls` == 2 in every row. |
| C13 | confirmed | `Manuscript.txt:549-552` 29.3 / 21.8 / 17.7 / 14.3 g/L. `SI.txt:1473-1474` "327 to 368 per replicate for the genetic algorithm and 212 to 265 for the Bayesian optimizer, against at most 400 for this work." `SI.txt:327-329` "held-out R2 values close to zero and MAE values of approximately 6.2-6.8 g L-1". |
| C14 | confirmed | `Manuscript.txt:419-433` Table 1 reproduces all six triples exactly, incl. haiku 23/35 and 7.1% unparseable and the 2.3-34.9% no-match span. `source_data/table1_backend_summary.csv` is identical in content. `SI.txt:1451-1453` "the same prompts, the same constraint-translation model" (Agent 2 pinned), "seven tasks in five replicates, and every cell is scored on its first attempt". |
| C15 | confirmed | `Manuscript.txt:529-537` "median selectivity of 1.93 against 1.47 and a median SF6 uptake of 7.7 mol kg-1 against 2.8"; `Manuscript.txt:516` "five of five replicates in both tasks (one-sided sign test, p = 0.031)". `SI.txt:1433-1438` "The task is ethane-selective by design: in a charge-free united-atom description ethane is strictly the stronger adsorbate, ethylene selectivity in real materials arising largely from pi-complexation that classical force fields do not represent." `config.py:692-718`: the `"c2"` entry, `selectivity_pair: ("C2H6","C2H4")`, 298.0 K, 100000.0 Pa, `charge_method "None"`, with the same argument spelled out in the comment. |
| C16 | confirmed | `SI.txt:1861-1887` caption ("Both beams supply up to ten candidates per iteration under the same sampling rule ... pooled across all five independent replicates and all 10 iterations ... 500 per task ... between 155 and 473 per task"). `source_data/tableS2_hit_rates.csv`: `beam1_n` 155-473, `beam4_n` 500 everywhere, CH4 `beam4_hits` = 1, enrichments 4.8/4.3/5.6/5.5/162/7.1/9.1/18/9.0 - the eight non-CH4 values span 4.3x-18x. |
| C17 | confirmed | `config.py:113` `UNIFIED_ONTOLOGY_PATH = .../unified_ontology.json` (absent on disk; `unified_vocabulary.json` present); `core/constraint_utils.py:60` `from config import UNIFIED_VOCABULARY_PATH`; `core/live_runner.py:24` `from core.han_safe_topologies import ...` with only `core/sim_safe_topologies.py` shipped. Reproduced: `import core.live_runner` -> `ModuleNotFoundError: No module named 'core.han_safe_topologies'`; `get_approved_vocab()` -> `ImportError: cannot import name 'UNIFIED_VOCABULARY_PATH' from 'config'`. Git: NEW HEAD `5adb33e` 2026-09-09 15:05 +0900, 29 commits; OLD HEAD `f1d731a` 2026-07-18 10:39 +0900, 23 commits; `git cat-file -t 5adb33e` in OLD -> "fatal: Not a valid object name" (unrelated histories). OLD loads the vocabulary cleanly and `SIM_SAFE_TOPOS` reports 952 eligible topologies. See finding E2 for a correction to the report's Appendix-A reproduction. |
| C18 | confirmed | `config.py:40-72`: `CLAUDE_API_KEY`, `CLAUDE_MODEL`, `agent_backend(n)` with a `provider == "claude"` branch. `grep -rni "claude\|anthropic" core/*.py` -> **zero hits**. `core/llm_client.py:69` `self.provider = LLM_PROVIDER` (the global, never `agent_backend`); `128-131` dispatches `openai` else `gemini`; no third branch. |
| C19 | confirmed | NEW `config.py:448,456,463,464,477` read `LLM2POR_STRATIFIED_SAMPLING`, `LLM2POR_STRATIFY_RANDOM_BEAM`, `LLM2POR_SHUFFLE_METAL_ORDER`, `LLM2POR_USE_MEMORY_LEDGER`, `LLM2POR_GEOM_MARGIN_MODE`; NEW `README.md:183-184` and `.env.example:19-21` document `LLM4MOF_*`; OLD `config.py:367,368,374,379,393` read `LLM4MOF_*`. |
| C20 | confirmed | `2026-07-17_w1_analysis.md` arm table: V0 final 94.8 +/- 6.3 / 82.2 +/- 15.9 / 89.5 +/- 6.9, NF final 69.5 +/- 19.2 / 64.3 +/- 13.4 / 78.4 +/- 5.6, n = 10/arm. Memory-share table: T1 **0.435**, T2 **0.443**, T3 **0.719** (the claim's 0.44/0.44/0.72 is that rounded). sigma_final in the MDE table: 6.4 / 15.9 / 6.9. |
| C21 | confirmed | `2026-07-17_obvious-filter_probe-interpretation.md`: T1 PorMake H2-vol 100 bar n = 9,533, OOF R2 **0.943**, dominant features vf-up / sa-up / density-down; T2 hMOF Xe/Kr OOF Spearman **0.829** with "pld-down (argmax 4.9 A)"; CO2 "OMS contribution ~ 0 (imp 0.027)" and "OMS median 4.49 < non-OMS 5.14 (6.30 < 6.67 even after vf 0.6-0.8 control)", explicitly a property of the label/oracle. `Manuscript.txt:293-297` is the OMS -> micropore "feedback-driven correction" the probe recovers. |
| C22 | **refuted** (grid description) | Substance confirmed by `2026-07-18_w2_verdict.md`: 210/210 campaigns, K1 FAIL 0/3 tasks with max effect "T4 B3_H +1.80 sigma (p_holm=1.0)", K2 FAIL (25 nominal reversals, all inside noise, interaction p 0.2-0.7), and CRN "paired_sd ~ naive_sd ... LLM non-determinism dominates the campaign trajectory". **But the grid is not 14 x 3 x 2.** From `2026-07-18_w2_summary.csv`: the 210 W2 campaigns are 42 cells x 5 reps, over 8 distinct variant labels (V0-V4, M1, B2, B3) x 2 budgets (H carries all 8, L only 6) x 3 tasks (T1/T2/T4). "14" is arms *per task* with the budget already folded in (8 H + 6 L). 14 x 3 x 2 would be 84 cells / 420 campaigns. |
| C23 | confirmed | `experiments/exp_20260717_0810_V0_T1_h2vol__r01/iteration_10/beam_data.csv`: Z 43 / A 257 / F 3,591 / R 9,533 (medians 563.76 / 515.19 / 506.33 / 501.88); `iteration_1/beam_data.csv`: Z 1 / A 1 / F 3 / R 9,533. `experiments/_battery_logs/manifest_*.csv` (status ok): 10-iteration campaigns n = 160, mean 353.4 s, median 348.5, min 246.7, max 491.6. |
| C24 | confirmed | `core/hpc/prepare_batch.py:65-83` emits `{version:1, experiment_id, iteration, created_at, n_jobs, config{raspa_cycles, raspa_init_cycles, temperature, pressure, skip_lammps, lammps_timeout, raspa_timeout, geometry_filter}, jobs[...]}`; job dicts carry `job_idx, beam_id, filename, topology, node, edge, predicted_geometry, match_score`, and the R2 writer (224-238) adds `pipeline:"stage2_only", cif_path, real_geometry`. `hpc/run_mof_sim.py:743-759` builds the per-job result dict; `_write_result` (938-945) writes `<filename>.json` + `.DONE`. `hpc/aggregate_results.py:66-76` builds `{experiment_id, iteration, n_jobs, n_success, n_fail, n_missing, total_wall_seconds, aggregated_at, results[]}`. Note `pipeline`/`cif_path`/`real_geometry` are R2-only and `created_at` is omitted from the claim; the anatomy 3.2 marks them correctly. |
| C25 | confirmed | `core/live_runner.py:1155-1174`: when `n_strict < LIVE_SIM_Z_RASPA_TOP`, non-passing stage-1 results are sorted by `compute_geometry_match_score` and promoted, with `geo_filter_fail_reason` recorded - these then go to RASPA and into Beam 1. `feedback_generator.py:520-527` adds the `GeoFilter` column rendering `PASS` / `fallback (reason)`. `_build_beam_specs` (842-871) for `"F"` pops only `linker_query.{functional_groups, linker_branches, abstract_features}` and `global_requirements`; its own comment says "keep metals and geometry", so `geometry_filter` survives in the metal-only beam. |

---

## 2. Extra findings (disagreements with, or omissions from, the anatomy report)

**E1 - section 2.5 and section 6: the design-space formula is arithmetically wrong.** (= C5.)
518 x 156 x 952 = 76,929,216. The SI's 12,499,656 is sum_c n_c t_c L over nine connectivity classes
(`SI.txt:112-116`, Table S5 `SI.txt:2021-2031`). Fix before the polymer analogue is sized the same way.

**E2 - Appendix A reproduces the wrong failure mode for the vocabulary bug.** The report states
`from core.constraint_utils import get_approved_vocab` -> `ImportError`. It does not: the offending
`from config import UNIFIED_VOCABULARY_PATH` sits *inside* `_load_vocabulary()` (`constraint_utils.py:60`),
so the module imports fine and even `from core.matchmaker import Matchmaker` succeeds. The `ImportError`
fires on the first **call**, which is `Matchmaker.__init__` line 78 (`self.approved_vocab = get_approved_vocab()`).
The conclusion ("DB mode crashes at component init") is right; the reproduction recipe is not - and a
reader who tries the stated command will see it pass and conclude the report is wrong. Also,
"OLD imports cleanly" is only partly reproducible here: OLD's `core/live_runner` raises
`ModuleNotFoundError: No module named 'torch'` in this environment (missing optional dependency, not a
code defect); OLD's `constraint_utils` and `sim_safe_topologies` do load.

**E3 - section 0 item 3 cites `.env.example:520-522`.** The file has ~22 lines; the `LLM4MOF_*` entries
are at lines 19-21, and the README entries at 183-184 (not 184-185). Cosmetic, but the report's value is
the precision of its citations.

**E4 - Note S1 contradicts the shipped code on context management, and the report does not flag it.**
`SI.txt:76-78`: "Agent 1 receives the complete, verbose feedback report **only for the immediately preceding
iteration**, while older empirical observations are compressed into a fixed-size Memory Ledger." The code
does no such compression: `LLMClient` with `multi_turn=True` appends every user message and every assistant
reply to `self.conversation_history` and re-sends the whole list (`llm_client.py:85-88`, and the two
`if self.multi_turn: self.conversation_history.append(...)` sites inside `_send_openai`); there is no trim,
window or eviction anywhere in the file. Every prior iteration's full four-beam report stays in the
transcript. The SI's own cost note confirms this ("the conversational context that must be re-sent grows
monotonically as empirical feedback accumulates", `SI.txt:429`), as does the measured token growth
($0.03 -> $0.19 per iteration). The anatomy states both halves separately (2.2 "keeps its full conversation
history across all ten iterations"; 2.8 the ledger) but never says they are in conflict. **For LLM4POL this
is load-bearing**: the ledger is an *addition* on top of an unbounded transcript, not a replacement for it,
so Note S11's ablation measures "ledger on top of full history", not "ledger instead of history", and a
polymer port that implements the SI's described design will not reproduce the ablation.

**E5 - DB-mode no-match iterations are not retried, which changes how Table 1 should be read.**
(= the C1 caveat.) `run_experiment.py:512-537` continues with empty beams and the counter advances. With
gpt-5.4-nano at 34.9% no-match, roughly a third of its ten iterations produced no candidates at all and
were still charged to the budget; that, not reasoning quality, may account for much of its 79.5 vs 91.3
gap, and similarly for gpt-5.6-sol at 24.6%. The anatomy has the code fact in 2.1 but never connects it
to the backend table in 1.2 / 2.15.

**E6 - Note S12 omission: a post-hoc pore-accessibility screen on the C2 structures.** `SI.txt:1442-1444`:
"Individually cited C2H6/C2H4 structures additionally satisfy a pore-accessibility criterion, a pore-limiting
diameter of at least 4.44 A, the kinetic diameter of ethane; distribution-level statistics are essentially
unchanged by this criterion; the full-hypothesis median moves from **1.883 to 1.860**." Neither the criterion
nor the 1.883/1.860 pair appears in the anatomy, although 1.3 otherwise summarises Note S12 carefully.

**E7 - the headline "X vs random Y" pairs mix two estimators.** Recomputed from `source_data/figure5_*.csv`:
C2 Beam 1 iteration-10 **replicate-averaged** median = 1.930 (pooled over all iterations = 1.883, i.e. Note
S12's number); the C2 random beam is 1.461 (iter-10) / 1.469 (pooled) - indistinguishable, so the C2 pair is
safe. SF6 Beam 1 iter-10 replicate-averaged = 7.689 ~ 7.7, but SF6 random at iteration 10 is **2.55**, while
the quoted 2.8 is the pooled-over-all-iterations random median (2.777 pooled / 2.816 replicate-averaged). So
"7.7 vs 2.8" compares a final-iteration statistic against an all-iteration reference. This is disclosed in
principle (`Manuscript.txt:480-482` defines the discovery reference distribution as the pooled Beam-4
structures) and the anatomy records that sentence in 1.3, but the anatomy repeats the headline pairs in 1.2,
1.3 and section 6 without noting that the two sides are not the same estimator.

**E8 - Note S14 omission that weakens the label-accounting figure.** `SI.txt:1491-1494`: "Published
training-set sizes are upper bounds; the model's own ablation reaches, at 1,000 labeled structures, within
four percentage points of its full-training-set performance, and minimum training-set sizes for the other
compared models are not reported." The anatomy quotes Fig. 7b's "400 spent vs generative training sets
1,000-289,000" without this self-issued caveat. A polymer port reusing the label-accounting framing should
carry the caveat with it, since the caveat is what a reviewer will quote back.

**E9 - Note S2 omissions that a port must implement deliberately.** Three sentences that 2.5 does not carry:
(a) `SI.txt:150-151` "Any constraint left unset by Agent 2 simply defaults to a 'pass' condition" - the whole
constraint language is default-permissive, which is what makes Agent 2's "OPTIONAL != EXCLUDE" rule safe; the
anatomy shows this only piecemeal (length defaults 0..999, unknown abstract features "benefit of doubt").
(b) `SI.txt:136-137` "An empty or malformed constraint query is rejected with a structured error,
automatically halting the iteration rather than silently substituting default values" - the *no-silent-default*
guarantee, distinct from the JSON-parse halt in Note S1.
(c) `SI.txt:141-145` the generic-tag propagation hierarchy is applied to hMOF/QMOF as well as PORMAKE "so that
an identical Agent 2 constraint maps consistently across all three databases" - cross-database constraint
portability is an explicit design requirement, and it is exactly the guarantee LLM4POL needs between its
homopolymer and copolymer tables.

**E10 - two smaller code/text mismatches the anatomy did not catch.**
(a) The Beam-1 interpretation hint actually sent to Agent 1 says fallback structures were "promoted to fill
the **15-candidate quota**" (`feedback_generator.py:737`) while `config.LIVE_SIM_Z_RASPA_TOP = 10`. Stale
number in live feedback text the agent reads.
(b) `source_data/figure6_token_usage_and_cost.csv` has 11 rows for replicates 2 and 5 (22 `model_calls`), so
the anatomy's section-6 line "2 per iteration; **20 per campaign**" is not universal - two of five replicates
spent 22 calls because an unproductive iteration was retried (that is what `iteration_raw` records). The
"exactly 2 per iteration" half is exact.

**E11 - minor attribution slip in 2.5.** `SI.txt:148-150` assigns the open-metal-site flag to the *QMOF*
matchmaker ("the QMOF Matchmaker processes electronic filters, including oxidation state, coordination
geometry, and open-metal-site flags"); the anatomy lists OMS in the shared hMOF/QMOF filter list and gives
QMOF only "connectivity, oxidation state, coordination geometry".

---

## 3. Section 3 code-module map - spot-checks

I checked line counts for all 29 mapped files plus the six OLD/HPC scripts, and the named
functions/classes for eleven rows. **No row misdescribes its file.** Line counts are exact in every case
(config 840, run_experiment 675, run_live_experiment 1988, agent1_handler 242, agent2_handler 345,
llm_client 446, matchmaker 668, hmof_matchmaker 341, qmof_matchmaker 225, constraint_utils 686,
sensitivity_analyzer 956, feedback_generator 910, feedback_live_adapter 245, memory_ledger 673,
memory_manager 304, sampling_strata 160, name_resolver 125, sim_safe_topologies 96, filter_candidate 840,
live_runner 1513, run_simulation 226, prepare_batch 287, collect_results 138, run_mof_sim 949,
aggregate_results 87, build_canonical_db 61, _pacman_worker 63, agent1 prompt 124, agent2 prompt 336;
OLD run_battery 233, parse_results 213; submit_iteration.sh 114, submit_iteration_packed.sh 148,
check_complete.sh 34, run_prepare_step 186, run_collect_step 197).

| Row spot-checked | Verdict |
|---|---|
| `core/llm_client.py` - "PORT-AS-IS but the Claude branch is not wired" | **Accurate.** Only `_send_openai` / `_send_gemini`; `self.provider = LLM_PROVIDER`; zero `claude`/`anthropic` occurrences under `core/`. |
| `core/sampling_strata.py` - "metal round-robin, identity only, fail-safe" | **Accurate.** `metal_of`, `stratified_reduce`, `stratified_select_dicts`, `stratified_rank_select` all present; `target` never referenced; every path wrapped in `try/except -> return df`. |
| `core/name_resolver.py` - "Singleton BB id -> readable name; parses topo+N+E" | **Accurate.** `NameResolver.resolve`, `.translate_mof_filename`, module-level `get_name_resolver()` singleton. |
| `core/sim_safe_topologies.py` - "MOF2Zeo vocab and single-node and not blacklisted; DROP" | **Accurate.** `_compute_sim_safe_topos()` intersects the three loaders; `SIM_SAFE_TOPOS`, `is_sim_safe`, `filter_matchmaker_result` exported; importing it prints `952 eligible topologies (mof2zeo=952, single-node=1618, bblist=952, blacklisted=0)`. |
| `core/feedback_live_adapter.py` - "LiveResults -> filter_sets, unit conversion, selectivity passthrough" | **Accurate.** `_mol_kg_to_volumetric`, `_resolve_target`, `_sim_results_to_dataframe`, `live_results_to_filter_sets`, `_is_selectivity`. |
| `scripts/build_canonical_db.py` - "pre-filter markscheme CSVs to the whitelist (backs up originals); DROP" | **Accurate.** Filters the six PORMAKE H2 CSVs to `core/mof2zeo/data/{node,edge,topology}.txt`, backs up to `data/_full_backup/`; docstring states the single-node single-edge keep rule. |
| `core/hpc/prepare_batch.py` + `collect_results.py` - "manifest writers and results -> LiveResults (computes `geo_filter_passed` from Zeo++ vs filter)" | **Accurate.** `collect_results.py:76-77` literally recomputes `geo_filter_passed` from the real Zeo++ geometry against the strict LLM range. |
| `core/filter_candidate.py` - "MOF2Zeo inference + combination generation + geometry-match ranking ('Agent 3')" | **Accurate.** `GeometryPredictor`, `ComponentGenerator`, `MOFRanker`, `Agent3Handler`, `_apply_mae_slack` all present in the stated roles. |
| `core/matchmaker.py` - "`smart_matchmaker_single_node`" at 378-539 | **Accurate** (a method, not a module function; defined at 378). |
| `requirements.txt` / `requirements-live.txt` pins | **Accurate**, verbatim, including the "NOT pip-installable: RASPA3, LAMMPS" footnote. |
| OLD `scripts/precheck/*` - "battery driver / parser; PORT-AS-IS" | **Accurate.** `expand_runs`, `build_command`, `execute_run`, `write_manifest`; `load_db_values`, `percentile_of`, `parse_campaign`, `summarize`. |

One presentational nit: `submit_iteration_packed.sh` appears in the `core/hpc/` row and again in the `hpc/`
row. Both copies exist on disk (`core/hpc/submit_iteration_packed.sh` and `hpc/submit_iteration_packed.sh`);
only the latter has the 148-line count the table quotes.
