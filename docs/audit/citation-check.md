# LLM4POL — Adversarial citation check of `prior-art.md` (2026-09-11)

Checker lane: every REF-n claim in prior-art.md was re-opened independently (WebFetch, Exa fetch/search, GitHub REST API, live SPARQL, local PDF text extraction with PyMuPDF, local RDKit 2025.09.6). Working files are in `audit/citecheck/` (fresh downloads: `gupta2506.02129.pdf`, `kuenneth.pdf`, `polyfusion2605.26543.html`, `vipea_dataset.csv`, `gupta_fig3_zoom.png`). No project files were touched.

Verdict key: **confirmed** = page exists, title/author/year match, and every stated fact was found; **refuted** = at least one stated fact is contradicted or absent from the source (details in the note); **unverifiable** = site unreachable from here.

## Summary

| Status | Count | IDs |
|---|---|---|
| confirmed | 44 | 1-10, 13-15, 17-38, 40, 42-49 |
| refuted (in part) | 4 | REF-11, REF-12, REF-16, REF-41 |
| unverifiable | 1 | REF-39 |

The four refutations matter for the project narrative:

1. **REF-12 (Gupta et al. 2025) baseline Tg numbers are misread.** Figure 3 of arXiv:2506.02129 (rendered at 300 dpi, `citecheck/gupta_fig3_zoom.png`) shows single-task Tg RMSE of roughly **PG ≈35 K, polyGNN ≈40 K (MT ≈35 K), polyBERT ≈41 K**, not "≈28 / ≈32 / ≈38 K". The text gives only LLaMA-3 39.48 K and GPT-3.5 47.2 K (both confirmed) and no numeric baseline values. Consequently the prior-art executive-summary statement that fingerprint/GNN/polyBERT baselines are "20–40 % lower RMSE" than the LLM fine-tune is not supported by this paper: LLaMA-3 ST (39.5 K) is within ~4 K of Polymer Genome and on par with polyGNN-ST/polyBERT-ST. The qualitative conclusion of the paper ("generally underperform", multitask fails for LLMs) is confirmed verbatim.
2. **REF-16 (PolyFusionAgent) "no code/weights statement" is false.** The arXiv HTML carries a *Data availability* section ("Pretrained model weights ... are available at https://huggingface.co/kaurm43/polyfusionagent-weights") and a *Code availability* section ("https://github.com/mk1426/PolyFusionAgent"). All quoted Tg metrics (0.907 ± 0.004 / 22.45 / 33.69 K vs polyBERT 0.882 / 26.01 / 37.94 K), the 2 M / 5 M PI1M+polyOne pretraining and the ≈1.8×10⁴ PolyInfo downstream set are confirmed.
3. **REF-11 (PolyNC) "split applied after augmentation" is not what the paper says.** PMC10763023 states: "We initially divided the dataset for each task into training and test sets using a ratio of 0.9/0.1. During data augmentation, we followed an equal mixing strategy ..." i.e. the split is described as preceding augmentation (the 20,673/2,297 numbers are the augmented-corpus sizes). The leakage criticism in prior-art.md is therefore unsupported. No numeric Tg R² (≈0.85) appears in the text (figure only). Title/authors/Text+Chem-T5 init/1,681 entries/Tg 685/22,970/Apache-2.0 are confirmed.
4. **REF-41 (psmiles) GitHub URL is dead.** `GET https://api.github.com/repos/Ramprasad-Group/psmiles` → 404 and WebFetch → 404 on 2026-09-11; a GitHub repo search for "psmiles" returns no Ramprasad-Group/psmiles entry. `psmiles.readthedocs.io` still exists and `pip download psmiles` → "No matching distribution" (confirmed). The readthedocs canonicalize page does not explicitly state an "exactly two [*]" requirement (it is only implied by the unify() special cases) and the `UserWarning("Canonicalization failed.")` is confirmed. The MIT licence could not be re-verified because the repo is gone.

## Per-claim notes (facts actually re-computed or re-fetched)

- **REF-1** confirmed. Fresh PDF fetched (131.7 KB): 9 pages, 20,933 chars extracted; header "Established on April 1, 2018 / Revised ... August 1, 2024"; Art. 9.2 and Art. 10(1)-(5) text identical to quotes; regex counts: "machine learning" 0, "model" 0, "training" 0.
- **REF-2** confirmed. https://polymer.nims.go.jp/ serves Japanese text; the English sentences quoted are on https://polymer.nims.go.jp/en/ ("Web scraping of data is prohibited! ..."; "No reproduction, republication or distribution to third parties ... without written permission of NIMS").
- **REF-3** confirmed. Notice lists exactly 3 items (Art. 9 para 3 citation rules; consultation e-mail; mandatory user reports Art. 18); no AI/ML mention.
- **REF-4** confirmed. Exa fetch of tandfonline (WebFetch 403): sentence "now being employed ... including as training data for machine learning" present; authors Ishii, Ito, Sado, Kuwajima per PoLyInfo citation block; local `polyinfo_I_fulltext.txt` (55,620 chars): "machine learning" 4, "terms of use" 0, "license" 0, "API" 0 (case-sensitive), "redistribut" 0.
- **REF-5** confirmed. Authors Masashi Ishii, Takuro Ito, Koichi Sakamoto (MDR/SAMURAI/PDF header); keywords SPARQL, ShEx, RDF; "training data for machine learning" sentence present.
- **REF-6** confirmed by live SPARQL on 2026-09-11: graph `https://polyinfo-rdf_v1_1.nims.go.jp/` 56,121 triples; 20,313 distinct subjects; top types E_PHN_30 8,212, E_ETL_30 5,021, E_AMD_30 3,160; subjects matching /P[0-9]{6}: 0; /S[0-9]{6}: 0.
- **REF-7** confirmed (Ishii & Sakamoto, 2025-05-03, CC BY 4.0, polyinfoowl.ttl 774 KB, DOI 10.48505/nims.5395).
- **REF-8** confirmed with caveat: the quoted English sentence is on https://mits.nims.go.jp/en/beginners.html; the claimed URL (no /en/) shows the Japanese equivalent "ご利用は無料ですが、ユーザ登録が必要です".
- **REF-9** confirmed (PMC: 100 M PSMILES; 28,061/7,456; Tg 8,495 = 5,183 + 3,312, [8e+01, 9e+02] K; R² 0.80 vs 0.81; 215×; GitHub "GTRC Academic Research Use License", "available upon request"; HF DebertaV2, 600-d, 4,973 downloads last month).
- **REF-10** confirmed (local PDF text: Table 1 sizes match exactly; "approximately 5M augmented"; "7.70%" and "R2 by 0.11"; PE-I test R² 0.69; no Tg dataset; GitHub MIT via API; ckpt/pretrain.pt).
- **REF-13** confirmed (arXiv 2411.00177; ~1.9 M structures, 45 properties; README: LLM-Prop/MatBERT ≫ Llama-2-7b-chat, CGCNN baseline).
- **REF-14** confirmed (quote verbatim; no polymers).
- **REF-15** confirmed (Tg RMSE 39.92 ± 1.27 / 40.32 ± 1.16 / polyBERT 38.41 ± 1.92; >200 M PSELFIES incl. 12,473 known; PolyInfo thermal data).
- **REF-17** confirmed (7,973 → 8,963; 7,950/1,013; Tg MAE 58.0 ± 2.7 vs 46.5 ± 3.7; wMAE 0.045).
- **REF-18/19/20** confirmed from arXiv abstracts (Chem. Mater. 37, 7002–7013; CIKM 2024; Polymer-Agent terminal agent).
- **REF-21** confirmed; v3 HTML sentence verbatim: "using polymer-specific resources, like PolyInfo [Ishii et al. (2024)] is restricted due to licensing issues".
- **REF-22** confirmed (Springer via Exa: published 09 Dec 2024, vol 37 pp 2733–2746 (2025); MAE 22.55, R² 0.849).
- **REF-23** confirmed via PMC9979603 (Chem. Mater. 35(4) 1560–1567; Table 1 Tg RMSE 31.7 ± 1.5 / 34.0 ± 0.9 / 36.6 ± 1.0 / 35.5 ± 1.6; 13,388 polymers, 36 properties, >21,000 points).
- **REF-24** confirmed (fresh arXiv PDF: Table 1 "Tg 5,072 4,426 9,498 ... Total 10,671 7,774 18,445"; "7,774 (≈40 %) ... PolyInfo repository ... 1,569 distinct copolymer chemistries"; "assumed to be random copolymers"; Fig. "Tg RMSE 20.50 R2 0.96 Ct. 7598"; journal ACS Macromolecules DOI 10.1021/acs.macromol.1c00728).
- **REF-25** confirmed (text: "R2 of 1.00 and ... RMSE of 0.03 eV"; "RMSEs of 0.10 ± 0.01 and 0.09 ± 0.02 eV" for monomer-A hold-out; cross-over "2% (859)" and "~1000 data instances"; repo tag v1.4.0-polymer exists per GitHub API; MIT).
- **REF-26** confirmed from ACS full text (60,196 chars): 20,236 / 8873; 5650 / 3569; WCS-GCN 0.921(0.006) / 24.45(0.7) / MAE 13.24; Fox 0.8352 / 42.57; homopolymer GCN 0.892(0.004) / 36.01(0.72); 5-fold CV; CC-BY-NC-ND 4.0; ACS Appl. Polym. Mater. 2024, 6, 7, 3666–3675.
- **REF-27** confirmed (PMC13417439; Polymers 18(14) 2026; 666 = 315 + 351; RMSE 14.26 K, R² ≈0.98; Zenodo 19242815).
- **REF-28** confirmed (ChemRxiv v5 abstract verbatim).
- **REF-29** confirmed (ACS Cent. Sci. 2019, 5(9), 1523–1531; Lin ... Olsen; `{}` stochastic objects; `$`, `<`, `>`).
- **REF-30/31/32** confirmed (arXiv 2303.12938 / MRS Bull. DOI; iScience 2022 bidirectional RNN; PI1M MIT via API + README "Data for academic purpose only", ~12,000 PolyInfo polymers).
- **REF-33** confirmed (Exa: overview Jun 16–Sep 15 2025, five MD targets, wMAE formula; sidebar "2,240 Teams", "51,013 Submissions", 10,336 entrants; discussion 609070 quotes "7. DATA ACCESS AND USE Open Source - CC-BY-NC-SA 4.0").
- **REF-34** confirmed (11,475; 9,625; 7,973; Tg 511 / FFV 7,030 / TC 737 / Rg 614 / Density 613; 1,354; μ 102.9 → 179.8; Morgan+GBDT top-10; first place polyBERT+AutoGluon+Uni-Mol; CC BY 4.0).
- **REF-35** confirmed (5,766 / 1,442 = 7,208; 4:1 random; GREA 37.32 °C; MIT repo; "upon formal publication").
- **REF-36** confirmed (6.57 M DFT, ≤360-atom clusters, >1.2 B atoms, CC BY 4.0, no Tg mention).
- **REF-37** confirmed (index lists "Polymer Properties — Patterns 2, 100238, 2021" and "A polymer dataset ... Sci. Data 3, 160012 (2016)"; no licence text).
- **REF-38** confirmed (polymergenome.org/reference lists Tran 2020 JAP and Kim 2018 JPCC; homopolymer + copolymer prediction sections; JAP 128, 171104 (2020), first author Huan Doan Tran, doi 10.1063/5.0023759).
- **REF-39** unverifiable: pubs.acs.org timed out in both WebFetch and Exa; doi.org resolves (302) to `.../polymscitech.6c00094/5383048/PolyBench-A-Reproducible-Open-Benchmark-Platform`; a WebSearch snippet gives "39 literature-derived tasks with 42,169 property records", authors Wenzhuo Feng, Lunyang Liu et al., published 2026-08-31. The figshare record 30917717 carries a different title ("PolyBench: A Standardized Benchmark Platform for Artificial Intelligence in Polymer Science", Wenzhuo Feng).
- **REF-40** confirmed with a naming correction: `datasets/vipea/dataset.csv` has 42,966 rows and columns `poly_id, poly_type, comp, fracA, fracB, EA (eV), IP (eV), EA vs SHE (eV), IP vs SHE (eV), monoA, monoB` — the architecture column is `poly_type` (block 18,414 / random 18,414 / alternating 6,138), not `chain_arch`; repo MIT.
- **REF-42** confirmed ("available for academic non-commercial use only"; 4 steps as claimed).
- **REF-43** confirmed by re-running: `[*]CC[*]`, `*CC*`, `C(*)C*` → `*CC*` (Z=0, heavy=2); Tanimoto 0.0 / 1.0 / 0.625 / 0.267 / 0.5; RDKit Book: unspecified query properties are not matched, so SMILES dummy matches any atom.
- **REF-44** confirmed (polymer-chemprop MIT fork of chemprop, tag v1.4.0-polymer, input format with `|0.25|0.75|<1-3:0.25:0.25 ... ~DP`; chemprop.readthedocs.io v2.3.1, no polymer/wD-MPNN/stoichiometry mention; v2 DOI 10.1021/acs.jcim.5c02332).
- **REF-45/46** confirmed (2,100 models, 60 NCI-60 sets, "much worse with UMAP splits"; OPIG blog Dablander 2021-06-15).
- **REF-47** confirmed (Nature article text: "with only around 50 data points, we get a similar performance to the model of ref. 24, which was trained on more than 1,000 data points"; RF on 1,252 points, 10-fold → ~1,126 training points).
- **REF-48/49** confirmed (arXiv 2409.06080 v2 2026-04-21 quotes; LLM-Prop ~4 % band gap, 66 % volume, MatBERT with ~1/3 parameters).

## Important prior art / licence facts MISSING from prior-art.md

1. **PolySea** — Qiu, Zhao, Jing, Hu, Lv, Li, Sun, "Introducing PolySea: An LLM-Based Polymer Smart Evolution Agent", ChemRxiv 2025-04-17, https://doi.org/10.26434/chemrxiv-2025-zw65g (CC BY-NC 4.0). A LoRA-fine-tuned domain LLM whose training set "integrat[es] high-fidelity polymer property data from PolyInfo" — a direct precedent for "LLM fine-tuned on PoLyInfo", and a data-licensing precedent (a released LLM trained on PoLyInfo rows).
2. **POLYT5** — Sahu, Xiong, Savit, Shukla, Ramprasad, "POLYT5: an encoder-decoder foundation chemical language model for generative polymer design", npj Artificial Intelligence, 2026-03-03, https://doi.org/10.1038/s44387-026-00087-1. Tg fine-tuning set of 5,130 polymers (80–873 K); says it "can be extended beyond homopolymers by fine-tuning on curated datasets for copolymers".
3. **Zhou ... Gao (HKUST), "Large language models for automated data extraction and inverse design of copolymers with targeted glass transition temperatures"**, Chemical Engineering Journal 529, 172634 (2026), https://doi.org/10.1016/j.cej.2026.172634. LLM-extracted copolymer Tg/Tm dataset (1,195 entries from 393 papers), forward Tg R² 0.791, inverse design of 2,052 copolymers. This is 2026 LLM + copolymer + Tg work and weakens the "no LLM copolymer-Tg paper" gap claim (though it is extraction/inverse design, not PoLyInfo fine-tuning).
4. **PolyLM** — Liu, Zhu, Xiong, Tang, "Can LLMs Predict Polymer Physics Just by Reading Synthesis and Processing Prose?", arXiv:2605.08255 (2026). Qwen3.5-9B LoRA on 185,000 papers / 276,400 samples / 22 properties, Tg test n = 5,391; shows the "synthesis-condition text" direction the prior-art file suggests is already being pursued.
5. **PolyTrace** — Wu & Zhou, ChemRxiv 2026-06-16, https://doi.org/10.26434/chemrxiv.15004805/v1. Evidence-grounded LLM reasoning for Tg: MAE 8.7 K on 77 PAEKs; MAE 28.4 K / R² 0.874 on a 7,637-polymer homopolymer benchmark (1,084 test) — a tie with the best fingerprint baseline; uses scaffold-grouped CV.
6. **Roy, Bazgir, Santos, Zhang, "Autonomous Multi-Agent AI for High-Throughput Polymer Informatics ..."**, arXiv:2602.00103 (2026): PolyGNN agent Tg R² 0.89 on 1,251 held-out polymers; single-LLM prediction R² 0.67 vs agent 0.78 on a Tg benchmark.
7. **Park & Vital Brazil (IBM), "Understanding Structural Representation in Foundation Models for Polymers"**, arXiv:2512.11881: SMI-TED-POLYMER on 28 benchmarks incl. copolymer EA/IP; finds even chemically invalid SMILES variants reach near-SOTA — relevant to representation choices; explicitly notes polymer data are "restrictively licensed".
8. **HHT** — Huang & Liu, "HHT: A Polymer Property Prediction Framework Leveraging Natural Language", ChemRxiv 2026-02-22, https://doi.org/10.26434/chemrxiv.15000246/v2.
9. **PoLyInfo public size page** https://polymer.nims.go.jp/datapoint.html (as of 29 May 2025): 19,227 homopolymers, 8,321 copolymers, 2,788 blends, 3,209 composites, 174,968 samples, 552,427 data points, 21,793 references — useful denominator for the project's 7,385 polymer_id / 42,557 rows.
10. **PolyBench-LLM v3 wording** also states "polymer-specific datasets, such as PolyInfo (Ishii et al., 2024) are available only under license, restricting their use by broader research community".
11. **PolyFusionAgent weights/code** are public (HF `kaurm43/polyfusionagent-weights`, GitHub `mk1426/PolyFusionAgent`) — a second example (with PolySea) of released models trained on PoLyInfo-derived data, relevant to the licensing discussion in §1 of prior-art.md.
12. **polyBERT HF LICENSE** file is not anonymously readable (`/raw/main/LICENSE` → "Invalid username or password"); the licence text must be read after HF login before relying on HF weights being usable.
