# LLM4POL — Prior-art, dataset-licensing and tooling landscape (as of 2026-09-11)

Auditor lane: prior-art / licensing / tooling. No project files were modified. All web evidence was retrieved on 2026-09-11 with WebSearch, WebFetch or the Exa fetch/search MCP tools; four PDFs were downloaded and text-extracted locally (copies in this directory: `MatNavi_agreement_en.pdf/.txt`, `transpolymer_2209.01307.pdf/.txt`, `kuenneth2021_2103.14174.pdf/.txt`, `aldeghi2022_2205.08619.pdf/.txt`, plus `polyinfo_I_fulltext.txt`).

Legend for `verified_by`: **fetched** = I opened the URL (WebFetch / Exa fetch / PDF download) and the quoted facts come from that page; **search-result-only** = the URL and title came from a search hit whose snippet carried the fact, but the page itself was not opened (or opening it failed with 403).

---

## 0. Executive summary (what matters for LLM4POL)

1. **PoLyInfo licensing is the project's single biggest external risk.** The MatNavi Service Terms of Use (rev. 2024-08-01) license the DATA "only for use by [Registrants] themselves" (Art. 9.2) and prohibit "copying, translation, adaption, derivative use, transmission, uploading, distribution, assignment, lending, licensing" and "selling or distributing the DATA or Processed DATA through publication, download sales or by other means" (Art. 10(1),(2)), and "obtaining data the volume of which ... is at or above a certain limit, by web scraping ... or by other means" (Art. 10(5)). The only carve-out is "publication of deliverables of research and development ... using the DATA" (Art. 10(2),(3)). Nothing in the Terms mentions machine-learning models explicitly; a trained model is arguably a "deliverable", but **the extracted 42,557-row CSV itself and any per-row Tg table are "DATA/Processed DATA" and cannot be redistributed, put in a repo, on Zenodo, HuggingFace, or Kaggle.** The PoLyInfo home page repeats: "No reproduction, republication or distribution to third parties of any content is permitted without written permission of NIMS." Whether a fine-tuned LLM that has memorised PoLyInfo rows can be released is legally unsettled; the safe reading is: publish papers/metrics, release code and pipelines, do **not** release the data or a model that can regurgitate it without written NIMS permission (contact: dice_help@nims.go.jp per Art. 9.4).
2. **There is no public PoLyInfo API for property data.** The "PoLyInfoRDF" SPARQL endpoint exists (https://materials-open-rdf.nims.go.jp/sparql) but my live query shows the public `polyinfo-rdf_v1_1` graph holds only 56,121 triples / 20,313 subjects, all ontology/taxonomy classes — zero `P######` polymer or `S######` sample IDs. The NIMS MDR hosts only the PoLyInfo *ontology* (CC BY 4.0), not the data.
3. **Closest prior art for "LLM fine-tune for Tg" already exists and is negative-leaning:** Gupta, Mahmood, Shukla & Ramprasad 2025 fine-tuned LLaMA-3-8B (LoRA) and GPT-3.5 on 11,740 thermal entries (Tg 5,253) and got **Tg RMSE 39.48 K (LLaMA-3) / 47.2 K (GPT-3.5) vs ≈28 K Polymer Genome, ≈32 K polyGNN, ≈38 K polyBERT**; multi-task LLM fine-tuning did *not* help. Jacobs et al. (2024/2026) found fine-tuned LLaMA-3 regression errors "5–10x higher" than SOTA on QM9. LLM4Mat-Bench found chat-LLMs far behind small fine-tuned encoders. The literature therefore predicts that a decoder-LLM regression head will **underperform** a fingerprint/GNN/polyBERT baseline on PoLyInfo-scale Tg data unless the contribution is elsewhere (copolymers, multimodal text conditions, low-data transfer, uncertainty, or synthesis-condition text).
4. **Copolymer modelling is the under-served niche.** The project data are ~38 % copolymer rows (composition columns present). Prior copolymer work: Kuenneth 2021 (composition-weighted PG fingerprints, 4,426 copolymer Tg points from PoLyInfo, meta-learner Tg RMSE 20.50 K), Aldeghi & Coley 2022 wD-MPNN (42,966 simulated copolymers), Huang et al. 2024 Weighted-Chained-SMILES (PoLyInfo: 3,569 unique copolymer Tg, WCS-GCN R² 0.921 / RMSE 24.45 °C), Bhati 2026 (666 points, RMSE ≈14 K). The BigSMILES-vs-SMILES ChemRxiv study reports BigSMILES "more accurately encodes chemical information and monomer connectivity for copolymers within LLM frameworks". No 2024-2026 paper fine-tunes an LLM on PoLyInfo *copolymer* Tg with composition — that is a genuine gap.
5. **Open substitutes exist but are smaller or simulated:** Kaggle NeurIPS-2025 Open Polymer (7,973 train SMILES; only **511 Tg labels**; rules Section 7 licence "Open Source – CC-BY-NC-SA 4.0" per a participant quote; MD-simulated targets; documented Tg train/test shift 102.9→179.8 °C), POINT² (Tg 7,208 points, MIT code, data "upon formal publication"), PI1M (~1 M unlabeled generated pSMILES, MIT, "academic purpose only"), OPoly26 (6.57 M DFT calcs, CC BY 4.0, no Tg), PolyBench-ACS (39 tasks, 42,169 records). Note the licence tension in Kaggle-derived work and that PI1M was *generated from* PoLyInfo.
6. **Evaluation practice:** every polymer LM paper above uses random or 5-fold CV splits; polymer-family / monomer-held-out splits (Aldeghi & Coley's monomer-A hold-out; Bhati's "unique formulations" split) and UMAP-cluster splits (Guo et al. 2024) exist and should be used. Watch for PolyNC-style leakage (split *after* SMILES augmentation).
7. **Tooling:** psmiles/canonicalize_psmiles require exactly two `[*]` atoms and are, respectively, MIT / "academic non-commercial only"; polyBERT code is under a GTRC Academic Research Use License (source on request) but the HF weights `kuelumbus/polyBERT` are downloadable (4,973 downloads/month); TransPolymer is MIT with a `ckpt` folder; polymer-chemprop (wD-MPNN) is an MIT fork of Chemprop **v1** and upstream Chemprop v2.3.1 has no polymer/weighted-edge support. RDKit 2025.09.6 parses `*` as atomic number 0 and Morgan fingerprints do distinguish `[*]CC[*]` from `CC` (Tanimoto 0.000) and are invariant to string order (`[*]CCO[*]` vs `[*]OCC[*]` = 1.000) but *not* to repeat-unit multiplicity (`[*]CCOCCO[*]` vs `[*]CCO[*]` = 0.625), so canonicalisation to the shortest unit is required before fingerprinting.

---

## 1. PoLyInfo (NIMS) terms of use, redistribution, ML use, API status

### REF-1 — MatNavi Service Terms of Use (NIMS), Established 2018-04-01, Revised 2024-08-01
- URL: https://mits.nims.go.jp/agreement/MatNavi_agreement_en.pdf — verified_by: **fetched** (PDF downloaded, 9 pages, 20,941 chars extracted with PyMuPDF; local copy `MatNavi_agreement_en.txt`).
- Header: "MatNavi Service Terms of Use National Institute for Materials Science Established on April 1, 2018 Revised on April 1, 2021 Revised on January 17, 2023 Revised on August 1, 2024".
- Definitions, Art. 1(7): "'Processed DATA' The DATA that have been processed into a table or other form of expression. The Processed DATA shall include the DATA and other data, etc., that have been processed into a table or other form of expression."
- **Article 9: Rights to Data, etc.**
  - 9.1: "Rights to use and manage the DATA that are provided through MatNavi and the Service are held by the Institute. Copyrights to MatNavi, all web pages on the Site and the relevant systems in general are also held by the Institute."
  - 9.2: "The Institute shall license Registrants to use the DATA only for use by themselves for the purpose of education, or research and development or product development and the manufacture of products so developed, and review pertaining to the foregoing."
  - 9.3: "When Registrant publishes any deliverables of research and development or product development using the DATA, Registrant shall indicate the names of the Institute and the Service as the source of data in the following manner ... (1) ... 'This research was conducted (in part) using the [database name] provided by the Materials Data Platform (MDPF) of the National Institute for Materials Science (NIMS).' (2) When the Service is referred to in a research paper, etc., the appropriate references as selected from the list posted on the DICE portal site shall be indicated as the source. ... (3) When data is cited in a research paper, etc., if a digital object identifier (DOI) is assigned to the data, the DOI shall be indicated as the source. ..."
  - 9.4: "If Registrants have any questions about the Institute's rights relevant to use or exploitation of the DATA, Registrants' obligation to display the source, etc., please contact the user consultation service (dice_help@nims.go.jp)."
- **Article 10: Prohibited Acts** — "Registrants shall not commit any of the following acts.
  - (1) All acts of using the DATA other than use licensed under paragraph 2 of the preceding Article (including copying, translation, adaption, derivative use, transmission, uploading, distribution, assignment, lending, licensing or merchandising other than use licensed under paragraph 2 of the preceding Article);
  - (2) Act of selling or distributing the DATA or Processed DATA through publication, download sales or by other means. However, publication of deliverables of research and development or product development using the DATA shall be excluded;
  - (3) Act of reprinting the DATA or Processed DATA in documents, websites, etc. However, the publication of deliverables of research and development or product development using the DATA shall be excluded;
  - (4) Use of the Service in violation of these Terms;
  - (5) Act of obtaining data the volume of which in the judgment of the Institute is at or above a certain limit, by web scraping (meaning automatic extraction of data from web pages by using a program) or by other means;"
- Art. 18: governed by the laws of Japan; Tokyo District Court / JCAA arbitration for registrants outside Japan.
- **Interpretation for LLM4POL:** (a) the words "machine learning", "model", "training" do not appear anywhere in the Terms; (b) 9.2 is a personal, non-transferable licence ("only for use by themselves"); (c) redistribution of the CSV or any Tg table = prohibited by 10(1)-(3); (d) papers/metrics = allowed under the "deliverables" carve-out with the Art. 9.3 acknowledgement; (e) releasing model weights trained on the data is not addressed — treat as requiring NIMS written permission, especially for LLMs that can reproduce training rows; (f) how the 42,557-row file was obtained matters under 10(5) ("at or above a certain limit ... by other means" covers manual bulk export too).

### REF-2 — PoLyInfo home page (NIMS DICE)
- URL: https://polymer.nims.go.jp/ — verified_by: **fetched**.
- Quotes: "Web scraping of data is prohibited! The acquisition of large amounts of data, whether by manual or mechanical means, is prohibited by the MatNavi Service Terms of Use. User accounts will be suspended when there is a possibility of data access that is deemed to be a violation."; "National Institute for Materials Science (NIMS) holds the copyright of this database system."; "No reproduction, republication or distribution to third parties of any content is permitted without written permission of NIMS."; required citation: Ishii et al. 2024 STAM-Methods 4(1) doi:10.1080/27660400.2024.2354649 or "PoLyInfo: https://polymer.nims.go.jp/ National Institute for Materials Science (NIMS), accessed {date}". Coverage claim: "About 100 types of properties ... Homopolymers, copolymers, furthermore polymer blends, composites and compounds ... are open to the public." Registration requires a DICE account with an institutional e-mail domain.

### REF-3 — Notice of Amendment to the MatNavi Service Terms of Use (effective 2024-08-01)
- URL: https://dice.nims.go.jp/news/2024/08/20240801-2-en.html — verified_by: **fetched**.
- The 2024 amendment changed only: how to indicate the data source in publications (Art. 9.3), the consultation e-mail (Art. 9.3), and "Mandatory submission of user reports (Article 18)" [sic, per notice]. No AI/ML-specific clause was added. (Earlier 2023-01-17 amendment, https://dice.nims.go.jp/news/2023/01/20230117-2.html — search-result-only — added DICE accounts and an export-control prohibition in Art. 10.)

### REF-4 — Ishii, Ito, Sado, Kuwajima (2024) "NIMS polymer database PoLyInfo (I): an overarching view of half a million data points", Sci. Technol. Adv. Mater.: Methods 4(1)
- URL: https://www.tandfonline.com/doi/full/10.1080/27660400.2024.2354649 — verified_by: **fetched** (Exa; 55,362 chars saved to `polyinfo_I_fulltext.txt`).
- Relevant quotes: "this database is now being employed in a variety of unprecedented applications, including as training data for machine learning and material exploration in unexplored areas"; "if users do not understand the data policy and structure of PoLyInfo, they may chemically misuse the data, affect the quality of secondary data, or waste time in material development by building and using inappropriate prediction models"; on copolymer IDs: "'Alternating', 'Periodic', 'Block', and 'Graft Copolymer' are managed under different COIDs ... the risk of using only CUIDs as structural descriptors in modeling, such as machine learning." The paper contains **no** licensing/API/terms text (grep for "terms of use", "license", "API", "redistribut" = 0 hits). NIMS thus *acknowledges* ML training use in its own paper but grants no rights beyond the Terms.

### REF-5 — Ishii, Ito, Sakamoto (2024) "PoLyInfo (II): machine-readable standardization of polymer knowledge expression", STAM-Methods 4(1)
- URL: https://www.tandfonline.com/doi/full/10.1080/27660400.2024.2354651 — verified_by: **fetched** (Exa, first 12 k chars). Keywords list "SPARQL, ShEx, RDF, ontology"; describes PoLyInfoRDF and a schema in ShEx; also states the DB is now used as "training data for machine learning". A search-result snippet (PoLyInfo (III), doi:10.1080/27660400.2025.2544516, **search-result-only**) says "The RDB provides users with data in various formats via GUI, application programming interface (API), and RDF" and names the SPARQL endpoint below.

### REF-6 — NIMS "materials-open-rdf" SPARQL endpoint (PoLyInfoRDF public graph) — live query 2026-09-11
- URL: https://materials-open-rdf.nims.go.jp/sparql — verified_by: **fetched** (Virtuoso query page) **and queried programmatically** (urllib, JSON results).
- Graph counts (top): supercon-rdf 2,867,439; chrip 1,011,744; **polyinfo-rdf_v1_1: 56,121 triples**; polyinfo_ontology_v1_4: 12,598; polyinfo-rdf: 5,446. Triples with "polyinfo" in the subject IRI: 811,120 (mostly ontology/taxonomy IRIs).
- Inside `https://polyinfo-rdf_v1_1.nims.go.jp/`: 20,313 distinct subjects; top rdf:type classes are taxonomy classes `PoLyInfo-ont/Schema#E_PHN_30` (8,212), `E_ETL_30` (5,021), `E_AMD_30` (3,160) ...; **0 subjects matching `/P[0-9]{6}` (polymer IDs) and 0 matching `/S[0-9]{6}` (sample IDs)**. Conclusion: the public RDF is the polymer *classification/ontology* layer, not the >500 k property data points. There is no public API for Tg values.

### REF-7 — NIMS MDR: "PoLyInfo Ontology Version 1.2" (Ishii & Sakamoto, 2025-05-03)
- URL: https://mdr.nims.go.jp/datasets/b5fb3e53-cc31-4775-8e9a-33ccc7329dca — verified_by: **fetched**. Rights: "Creative Commons BY Attribution 4.0 International"; files `polyinfoowl.ttl` (774 KB) + Readme (5.04 KB); DOI 10.48505/nims.5395. MDR also hosts the PoLyInfo (II) paper PDF (https://mdr.nims.go.jp/datasets/4d722a55-6463-4336-b8d0-e5fda13bf28e, search-result-only). MDR does **not** host the PoLyInfo property data.

### REF-8 — MatNavi "For New User" / index pages (search-result-only)
- URLs: https://mits.nims.go.jp/beginners.html , https://mits.nims.go.jp/index.html — verified_by: **search-result-only** (Exa snippets). "The use of MatNavi is free. All you need to do is register."; "Mass downloading of data is prohibited".

---

## 2. Polymer property prediction with LLMs / transformers (2023-2026)

### REF-9 — Kuenneth & Ramprasad (2023) "polyBERT: a chemical language model to enable fully machine-driven ultrafast polymer informatics", Nature Communications 14:4099
- URLs: https://pmc.ncbi.nlm.nih.gov/articles/PMC10336012/ (fetched); https://www.nature.com/articles/s41467-023-39868-6 (redirect to IdP, not opened); GitHub https://github.com/Ramprasad-Group/polyBERT (fetched); HF https://huggingface.co/kuelumbus/polyBERT (fetched). verified_by: **fetched**.
- Model: DeBERTa-v2 encoder, mean-pooled 600-dim fingerprint; pretraining on "100 million hypothetical PSMILES strings" (BRICS-enumerated).
- Fine-tuning data: 29 properties; 28,061 (≈80 %) homopolymer + 7,456 (≈20 %) copolymer data points; **Tg: 8,495 points (5,183 homopolymer, 3,312 copolymer), experimental, range [80 K, 902 K]**; provenance "produced using computational methods or obtained from literature and other public sources" (PoLyInfo not named in the PMC text).
- Metric: overall R² across 29 properties **0.80 (polyBERT) vs 0.81 (Polymer Genome handcrafted FP)**; Tg-specific RMSE is in Supplementary Table S1 (not retrieved). Speed: "215 times" faster fingerprinting on GPU. Protocol: 80/20 split, five-fold CV + meta-learner.
- Licensing: GitHub README — "distributed under an Academic Research Use License" (GTRC), "Use is restricted to non-commercial academic research and teaching", source "available upon request" (e-mail Prof. Ramprasad with institutional address, cc PI). HF weights are downloadable ("Please see the license agreement in the LICENSE file"; 4,973 downloads last month; usable via `sentence-transformers`). Depends on `canonicalize_psmiles`.
- Relevance: the de-facto polymer LM baseline; includes copolymer Tg via composition-weighted fingerprints (from Kuenneth 2021).

### REF-10 — Xu, Wang, Barati Farimani (2023) "TransPolymer: a Transformer-based language model for polymer property predictions", npj Computational Materials 9:64
- URLs: https://arxiv.org/abs/2209.01307 (fetched abstract), https://arxiv.org/pdf/2209.01307 (fetched PDF, 49 pp, text extracted), https://www.nature.com/articles/s41524-023-01016-5 (Exa snippet), GitHub https://github.com/ChangwenXu98/TransPolymer (fetched). verified_by: **fetched**.
- Model: RoBERTa + MLP head; chemistry-aware tokenizer; MLM pretraining on PI1M "approximately 5M augmented unlabeled polymers" (PI1M ~1 M × 5 SMILES enumerations). Copolymers encoded with '.' between constituents, '^' for branches, ratios/Tg/MW as descriptor tokens with `NAN_*` placeholders.
- **No Tg benchmark.** Ten downstream datasets (Table 1): PE-I conductivity 9,185; PE-II 271; Egc 3,380; Egb 561; Eea 368; Ei 370; Xc 432; EPS 382; Nc 382; OPV 1,203. Splits: 5-fold CV except PE-I (train 2018 / test 2019). Best-reported: PE-I test R² 0.69 (vs 0.32 best baseline); PE-II RMSE 0.61 / R² 0.73; "average decrease of evaluation RMSE by 7.70% and an increase of evaluation R² by 0.11" vs best baselines.
- Code: MIT; "Pretrained model can be found in `ckpt` folder"; datasets in `data` folder.
- Relevance: shows how to serialise copolymer composition and conditions as tokens; not a Tg reference.

### REF-11 — Qiu, Liu, Qiu, Dai, Ji, Sun (2024) "PolyNC: a natural and chemical language model for the prediction of unified polymer properties", Chemical Science
- URLs: https://pmc.ncbi.nlm.nih.gov/articles/PMC10763023/ (fetched), https://pubs.rsc.org/en/content/articlelanding/2024/sc/d3sc05079c (search), GitHub https://github.com/hkqiu/Unified_ML4Polymers (fetched: Apache-2.0), HF https://huggingface.co/hkqiu/PolyNC (search). verified_by: **fetched**.
- Model: T5 initialised from "Text+Chem T5"; text-to-text with natural-language prompt + SMILES. Data: 1,681 original entries (Tg 685, band gap 236, atomization energy 390, heat-resistance class 370) augmented by SMILES enumeration to 22,970; split 90/10 **after** augmentation (leakage risk). Tg R² ≈ 0.85 single-task; "5–20 °C" deviations on novel structures.
- Relevance: closest "LLM-style text-to-text" polymer regression; tiny Tg set; augmentation-then-split protocol should not be copied.

### REF-12 — Gupta, Mahmood, Shukla, Ramprasad (2025) "Benchmarking Large Language Models for Polymer Property Predictions", arXiv:2506.02129; Macromol. Rapid Commun. 2025 (doi:10.1002/marc.202500388)
- URLs: https://arxiv.org/abs/2506.02129 (fetched), https://arxiv.org/html/2506.02129v1 (fetched), https://onlinelibrary.wiley.com/doi/10.1002/marc.202500388 (search-result-only). verified_by: **fetched**.
- Data: "manually curated benchmark dataset of experimental thermal property values": **Tg 5,253, Tm 2,171, Td 4,316 (11,740 total)**. Models: LLaMA-3-8B (LoRA, 2×L40S) and GPT-3.5 fine-tunes vs Polymer Genome, polyGNN, polyBERT, single-task and multi-task.
- **Tg RMSE (single-task): LLaMA-3-8B 39.48 K; GPT-3.5 47.2 K; Polymer Genome ≈28 K; polyGNN ≈32 K; polyBERT ≈38 K** (baselines read from Fig. 3). Multi-task: "LLaMA-3 and GPT-3.5 models failed to achieve similar improvements". Conclusion quotes: "LLM-based methods approach traditional models in performance, they generally underperform in predictive accuracy and efficiency"; "Analysis of molecular embeddings reveals limitations of general purpose LLMs in representing nuanced chemo-structural information compared to handcrafted features and domain-specific embeddings."
- Relevance: **direct prior art for LLM4POL's central idea**, from the Ramprasad group, with a negative-leaning result on homopolymer thermal properties.

### REF-13 — Rubungo, Li, Hattrick-Simpers, Dieng (2024/2025) "LLM4Mat-Bench: Benchmarking Large Language Models for Materials Property Prediction", NeurIPS 2024 AI4Mat workshop; Mach. Learn.: Sci. Technol. 6 (2025)
- URLs: https://arxiv.org/abs/2411.00177 (fetched), https://github.com/vertaix/LLM4Mat-Bench (fetched), https://iopscience.iop.org/article/10.1088/2632-2153/add3bb (search). verified_by: **fetched**.
- ~1.9 M crystal structures, 10 sources, 45 properties; inputs composition/CIF/text (4.7 M / 615.5 M / 3.1 B tokens). Fine-tuned LLM-Prop-35M and MatBERT-109M "substantially outperform baseline CGCNN and Llama 2-7b-chat"; zero/few-shot Llama/Gemma/Mistral weak; "need for task-specific predictive models and task-specific instruction-tuned LLMs". Data licence: "belongs to the original creators of each dataset". Not polymer-specific.

### REF-14 — Liu, Sun, Matusik, Jiang, Chen (2024/ICLR 2025) "Multimodal Large Language Models for Inverse Molecular Design with Retrosynthetic Planning" (Llamole)
- URLs: https://arxiv.org/abs/2410.04223 (fetched), https://github.com/liugangcode/Llamole (search), https://iclr.cc/virtual/2025/poster/28198 (search). verified_by: **fetched**. LLM + Graph Diffusion Transformer + GNN + A*; "significantly outperforms 14 adapted LLMs across 12 metrics". Small molecules only — no polymers. Relevance: template for LLM-with-graph-module generative work, not for polymer regression.

### REF-15 — Savit, Sahu, Shukla, Xiong, Ramprasad (2025) "polyBART: A Chemical Linguist for Polymer Property Prediction and Generative Design", arXiv:2506.04233 (v2 2025-10-17; Findings of EMNLP 2025 per Ramprasad-group PDF listing, search-result-only)
- URLs: https://arxiv.org/abs/2506.04233 (fetched), https://arxiv.org/html/2506.04233 (fetched), https://ramprasad.mse.gatech.edu/wp-content/uploads/2025/11/2025.findings-emnlp.647.pdf (search-result-only). verified_by: **fetched**.
- BART transferred to polymers via "Pseudo-polymer SELFIES (PSELFIES)"; pretraining "Over 200 million PSELFIES strings ... including 12,473 known polymers"; thermal data "PolyInfo repository" + literature. **Tg RMSE: polyBART-small 39.92 ± 1.27 K, polyBART-large 40.32 ± 1.16 K, polyBERT 38.41 ± 1.92 K, SELFIES-TED-large 62.58 ± 1.94 K.** First LM-designed polymer synthesised and validated (Td). Code availability not stated.

### REF-16 — Kaur, Zhang, Liu (2026) "PolyFusionAgent: A Multimodal Foundation Model and Autonomous AI Assistant for Polymer Property Prediction and Inverse Design", arXiv:2605.26543 (2026-05-26)
- URLs: https://arxiv.org/abs/2605.26543 , https://arxiv.org/html/2605.26543 — verified_by: **fetched**.
- PolyFusion pretrained on 2 M and 5 M polymers "drawn from the union of PI1M ... and polyOne", aligning PSMILES, 2D graph, 3D proxies and fingerprints; downstream "PolyInfo dataset: approximately 1.8×10⁴ experimentally validated polymers". **Tg: PolyFusion_5M R² 0.907 ± 0.004, MAE 22.45 ± 0.71 K, RMSE 33.69 ± 0.64 K vs polyBERT R² 0.882, MAE 26.01, RMSE 37.94 K.** No code/weights statement. Relevance: current (2026) SOTA claim for a polymer foundation model on PoLyInfo-derived Tg; note it uses PoLyInfo data downstream despite the Terms.

### REF-17 — Vuong, Van, Verma, Zhao, Wu (2025) "Fine-Tuning Vision-Language Models for Multimodal Polymer Property Prediction", arXiv:2511.05577
- URLs: https://arxiv.org/abs/2511.05577 , https://arxiv.org/html/2511.05577 — verified_by: **fetched**. LoRA (r=16) fine-tunes of Llama-3.2-11B-Vision, Llama-3.1-8B, Qwen2.5-VL-7B, Qwen2.5-7B on the Kaggle 2025 set (7,973 P-SMILES → 8,963 after merging; 90/10 split). Tg MAE (scaled ×10⁻²): LVision 58.0 ± 2.7, LText 60.0 ± 3.5 vs **MLP+RDKit 46.5 ± 3.7** (fingerprint baseline better on Tg); the VLM wins on overall wMAE 0.045. Relevance: another LLM-vs-baseline data point — LLMs lose on Tg specifically.

### REF-18 — Zhang & Yang (2025) "Multimodal machine learning with large language embedding model for polymer property prediction" (PolyLLMem), Chem. Mater. 37, 7002–7013; arXiv:2503.22962
- URL: https://arxiv.org/abs/2503.22962 — verified_by: **fetched**. Llama-3 text embeddings + Uni-Mol 3D embeddings; "comparable to, and in some cases exceeds, that of graph-based models"; Tg numbers not in abstract. Relevance: LLM-as-frozen-embedder route (cheap on an 8 GB GPU) rather than LLM-as-regressor.

### REF-19 — Wang, Guo, Cheng, Yuan, Xu, Gao (2024) "MMPolymer: A Multimodal Multitask Pretraining Framework for Polymer Property Prediction", CIKM 2024; arXiv:2406.04727
- URL: https://arxiv.org/abs/2406.04727 — verified_by: **fetched**. 1D sequence + 3D structure pretraining, "Star Substitution" to build 3D from pSMILES. Evaluated on TransPolymer-style benchmarks (no Tg reported in abstract).

### REF-20 — Nigam, Chandrasekhar, Barati Farimani (2026) "Polymer-Agent: Large Language Model Agent for Polymer Design", arXiv:2601.16376
- URL: https://arxiv.org/abs/2601.16376 — verified_by: **fetched**. Terminal-based LLM agent (property prediction, property-guided generation, structure modification with SA scoring). No Tg metric in abstract.

### REF-21 — Mohanty, Hasan, Monsur, Zheng, Hsiao, Balasubramanian (2026) "Teaching and Evaluating LLMs to Reason About Polymer Design Related Tasks" (PolyBench-LLM), arXiv:2601.16312
- URLs: https://arxiv.org/abs/2601.16312 (fetched), https://arxiv.org/html/2601.16312v3 (Exa search highlight). verified_by: **fetched** (abstract); the licensing sentence is from the HTML highlight. 125 K+ tasks from a 13 M-point open knowledge base; SLMs 7B–32B trained on it rival frontier LLMs. The HTML text states: "using polymer-specific resources, like PolyInfo ... is restricted due to licensing issues" — independent confirmation that the community treats PoLyInfo as non-redistributable.

### REF-22 — (authors not captured by the fetch) "TransTg: a new transformer model for predicting glass transition temperature of polymers from monomers' molecular structures", Neural Computing and Applications 37:2733–2746 (published 2024-12-09)
- URL: https://link.springer.com/article/10.1007/s00521-024-10532-4 — verified_by: **fetched** (Exa). SMILES-to-Tg transformer; "MAE of 22.55 and R² of 0.849 on a held-out test set". Authors not captured by the fetch (listed on page). Homopolymer monomer input only.

### REF-23 — Gurnani, Kuenneth, Toland, Ramprasad (2023) "Polymer Informatics at Scale with Multitask Graph Neural Networks" (polyGNN), Chem. Mater. 35, 1560–1567
- URLs: https://doi.org/10.1021/acs.chemmater.2c02991 , https://pmc.ncbi.nlm.nih.gov/articles/PMC9979603/ , https://arxiv.org/abs/2209.13557 — verified_by: **search-result-only** (Exa highlights include the results table). 13,388 polymers, 36 properties, >21,000 points (DFT + literature + handbooks + "online databases"). **Tg RMSE: MT polyGNN 31.7 ± 1.5 K; MT PG-MLP 34.0 ± 0.9 K; ST polyGNN 36.6 ± 1.0 K; ST PG-MLP 35.5 ± 1.6 K.** Periodic repeat-unit graph (bonds across `*`), augmentation for translation invariance.

---

## 3. Copolymer-specific modelling

### REF-24 — Kuenneth, Schertzer, Ramprasad (2021) "Copolymer Informatics with Multitask Deep Neural Networks", Macromolecules 54(13):5957 (arXiv:2103.14174)
- URLs: https://arxiv.org/abs/2103.14174 (fetched), https://arxiv.org/pdf/2103.14174 (fetched, text extracted), https://pubs.acs.org/doi/10.1021/acs.macromol.1c00728 (search). verified_by: **fetched**. (Note: venue is Macromolecules, not J. Chem. Phys.)
- Data: 18,445 points; **Tg 5,072 homopolymer + 4,426 copolymer = 9,498; Tm 2,079 + 1,988; Td 3,520 + 1,360**; "7,774 (≈40 %) data points pertain to copolymers (collected from the PolyInfo repository) that encompass 1,569 distinct copolymer chemistries"; only DSC Tg/Tm and TGA Td kept; "All copolymers are furthermore assumed to be random copolymers because information about the copolymer types was not uniformly available."
- Representation: composition-weighted sum of PG fingerprints, F = Σᵢ cᵢ Fᵢ. Model: concatenation-conditioned multitask DNN; 80 % → five CV models, 20 % → meta-learner. Result: meta-learner parity (on the 80 % CV portion) **Tg RMSE 20.50 K, R² 0.96 (n=7,598)**; Tm 24.32 K / 0.94; Td 36.17 K / 0.90; "overall R² of 0.94". Deployed at polymergenome.org.
- Relevance: the canonical copolymer baseline for exactly LLM4POL's data type (PoLyInfo binary copolymers with composition). Its linear-mixing fingerprint cannot encode sequence type; the project's `copolymer_type` column is an opportunity.

### REF-25 — Aldeghi & Coley (2022) "A graph representation of molecular ensembles for polymer property prediction", Chem. Sci. 13, 10486–10498 (arXiv:2205.08619)
- URLs: https://arxiv.org/abs/2205.08619 (fetched), https://arxiv.org/pdf/2205.08619 (fetched, text extracted), https://github.com/coleygroup/polymer-chemprop (fetched), https://github.com/coleygroup/polymer-chemprop-data (search). verified_by: **fetched**.
- Data: 42,966 simulated copolymers (random/alternating/block; ratios 1:1, 1:3, 3:1), EA/IP from IPEA-xTB on octamers with DFT (B3LYP/DZP) linear calibration, Boltzmann-averaged over 8 conformers × up to 32 sequences. Model: weighted directed MPNN (wD-MPNN) — edge weights encode stoichiometry and connectivity probabilities, optional degree of polymerization. Result: "random 10-fold cross validation ... average R² of 1.00 and RMSE of 0.03 eV" for EA and IP; **monomer-A held-out 9-fold: RMSE 0.10 ± 0.01 (EA) and 0.09 ± 0.02 eV (IP)**; RF-fingerprint baseline better below ~859–1,000 training instances, wD-MPNN better above. Code "v1.4.0-polymer", MIT.
- Input string format (from repo): monomer SMILES joined by '.', `|fracA|fracB|`, numbered `[*:1]` wildcards, edge list `<1-3:0.25:0.25 ...`, optional `~DP`. Relevance: the graph-native way to encode composition + copolymer type; easy to adapt to the project's (smiles1, smiles2, composition1, composition2, copolymer_type) columns.

### REF-26 — Huang, Chen, Lin, Li, Yu, Zhu (2024) "Enhancing Copolymer Property Prediction through the Weighted-Chained-SMILES Machine Learning Framework", ACS Appl. Polym. Mater. 6(7):3666–3675 (CC-BY-NC-ND 4.0)
- URLs: https://pubs.acs.org/doi/10.1021/acsapm.3c02715 (fetched via Exa), https://pubs.acs.org/doi/full/10.1021/acsapm.3c02715 (Exa highlights). verified_by: **fetched**.
- Data **from PoLyInfo**: "20,236 homopolymer samples and 8873 binary copolymer samples, each with recorded experimental Tg values ... for Td ... 7628 homopolymer and 1205 copolymer samples"; after averaging duplicates: Data set-ho 5,650 Tg / 4,281 Td; Data set-co **3,569 Tg** / 1,585 Td; missing copolymer types "treated as random copolymers". 5-fold CV.
- Results: homopolymer Tg GCN R² 0.892 / RMSE 36.01 °C; Morgan 0.874 / 38.14; Mordred 0.885 / 37.7. **Copolymer Tg: WCS-GCN R² 0.921 ± 0.006, RMSE 24.45 ± 0.7 °C, MAE 13.24; WCS-Morgan 0.916 / 25.42; WSF (weighted-sum-of-features) GCN 0.86 / 34.52; Fox equation R² 0.835 / RMSE 42.57 °C.**
- Relevance: the most directly comparable published numbers for PoLyInfo copolymer Tg; the Fox-equation baseline (R² 0.835) is a must-have sanity baseline for LLM4POL.

### REF-27 — Bhati, Afzal, Chew, Browning, Halls (2026) "Glass Transition Prediction of Binary Copolymers Across Large Chemical Spaces Using Machine Learning and Physics-Based Modeling", Polymers 18(14):1727
- URLs: https://pmc.ncbi.nlm.nih.gov/articles/PMC13417439/ (fetched), https://doi.org/10.3390/polym18141727 (Exa). verified_by: **fetched**. 666 experimental points (315 homopolymers from Bicerano, 351 binary copolymers from Penzel); composition-weighted descriptor aggregation (mean/min/max/std/median of cᵢ·zᵢ); merged-model test RMSE 14.26 K, R² ≈0.98; copolymer-only RMSE 5.11 K vs 19.64 K for concatenated-SMILES; 90/10 split with "unique formulations" held out; data on Zenodo (records/19242815). Small but open.

### REF-28 — Qiu et al. (2025) "Is BigSMILES the Friend of Polymer Machine Learning?", ChemRxiv 10.26434/chemrxiv-2024-bxxhh-v5
- URL: https://chemrxiv.org/doi/full/10.26434/chemrxiv-2024-bxxhh-v5 — verified_by: **fetched** (abstract). 12 tasks, CNNs and LLMs; "BigSMILES enables faster training times due to its reduced token complexity, and achieves comparable or superior performance to SMILES in certain predictive tasks. Moreover, BigSMILES more accurately encodes chemical information and monomer connectivity for copolymers within LLM frameworks." Code+data linked.

### REF-29 — Lin, Coley, ... Olsen (2019) "BigSMILES: A Structurally-Based Line Notation for Describing Macromolecules", ACS Cent. Sci. 5:1523
- URLs: https://pmc.ncbi.nlm.nih.gov/articles/PMC6764162 (fetched), https://pubs.acs.org/doi/10.1021/acscentsci.9b00476 (search). verified_by: **fetched**. Stochastic objects `{ ... }` with bonding descriptors `$`, `<`, `>`; no composition probabilities in the base notation (composition must be carried separately or via later extensions).

### REF-30 — Shukla, Kuenneth, Ramprasad (2023) "Polymer informatics beyond homopolymers", MRS Bulletin (arXiv:2303.12938)
- URL: https://arxiv.org/abs/2303.12938 — verified_by: **fetched**. Universal fingerprint + multitask DNN for homopolymers, copolymers and blends on Tg/Tm/Td.

### REF-31 — Tao, Byrnes, Varshney, Li (2022) "Machine learning strategies for the structure-property relationship of copolymers", iScience
- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC9249671/ — verified_by: **search-result-only** (Exa highlight). Compares FFNN/CNN/RNN/Fusion on monomer *sequences* for alternating/random/block/gradient copolymers; bidirectional RNN generalises best. Relevance: sequence-level copolymer encoding (relevant if `copolymer_type` is to be modelled).

*No 2024-2026 paper was found that fine-tunes a decoder LLM on experimental PoLyInfo copolymer Tg with composition as input; TransPolymer (2023) tokenises composition ratios but only for electrolyte conductivity; the BigSMILES ChemRxiv study is the closest LLM+copolymer work.*

---

## 4. Public / open polymer datasets

| Dataset | Size / properties | Licence | URL | verified_by |
|---|---|---|---|---|
| **REF-32 PI1M** (Ma & Luo 2020, JCIM 60:4684) | ~1 M generated pSMILES (RNN trained on ~12 k PoLyInfo polymers); unlabeled; v2 adds SA scores | MIT (repo) but README: "Data for academic purpose only" | https://github.com/RUIMINMA1996/PI1M ; https://pubs.acs.org/doi/10.1021/acs.jcim.0c00726 | fetched |
| **REF-33 Kaggle NeurIPS Open Polymer Prediction 2025** (host: Univ. Notre Dame) | train 7,973 unique SMILES; 5 MD-simulated targets Tg/FFV/Tc/Density/Rg; Tg train labels **511**, FFV 7,030, Tc 737, Rg 614, Density 613; private LB 1,354 structures; 2,240 teams, 51,013 submissions; metric wMAE | Rules §7 "DATA ACCESS AND USE: Open Source – CC-BY-NC-SA 4.0" (quoted by a participant in the host thread; the rules page itself did not render) — i.e. **non-commercial, share-alike** | https://www.kaggle.com/competitions/neurips-open-polymer-prediction-2025/overview ; https://www.kaggle.com/competitions/neurips-open-polymer-prediction-2025/discussion/609070 | fetched |
| **REF-34 Open Polymer Challenge post-competition report** (Liu, Alosious, ..., Luo, Jiang; arXiv:2512.08896) | 11,475 polymers, 9,625 labeled; Tg train/test mean shift 102.9 → 179.8 °C; top-10 all used Morgan FP + GBDTs; 1st place = polyBERT + AutoGluon + Uni-Mol ensemble; GNNs "not commonly used"; leakage from previously public data | paper CC BY 4.0 | https://arxiv.org/abs/2512.08896 ; https://arxiv.org/html/2512.08896 | fetched |
| **REF-35 POINT²** (Xu, Liu, Guo, Jiang, Luo 2025; arXiv:2503.23491) | Tg 7,208 (5,766/1,442), Tm 3,671, TC 1,580, FFV 8,046, density 1,710, gas permeabilities 509–805; random 4:1 split; best Tg RMSE 37.32 °C (GREA) | code MIT; paper CC BY 4.0; repo: "more info regarding data&model availability will be available upon formal publication" | https://arxiv.org/abs/2503.23491 ; https://github.com/Jiaxin-Xu/POINT2 | fetched |
| **REF-36 OPoly26** (Levine et al. 2025/26; arXiv:2512.23117) | 6.57 M DFT calculations, ≤360-atom clusters, 1.2 B atoms; monomer composition / DP / architecture / solvation variation; no Tg | CC BY 4.0 | https://arxiv.org/abs/2512.23117 | fetched |
| **REF-37 Khazana** (Ramprasad group) | index of DFT/ML datasets incl. "Polymer Properties — Polymer Informatics with Multi-Task Learning, Patterns 2021", "A polymer dataset for accelerated property prediction and design, Sci. Data 2016" (1,073 polymers) | no licence text on index page | https://khazana.gatech.edu/dataset/ | fetched |
| **REF-38 Polymer Genome** (Kim et al. 2018 JPCC 122:17575; Tran et al. 2020 JAP 128:171104) | prediction *service* (homopolymer + copolymer models), not a downloadable dataset | n/a | https://www.polymergenome.org/reference ; https://pubs.aip.org/aip/jap/article/128/17/171104/1062836/ | fetched |
| **REF-39 PolyBench (ACS)** (Feng, Liu et al. 2026, Polymer Sci. & Technol.; figshare 10.6084/m9.figshare.30917717) | 39 literature-derived tasks, 42,169 property records; fixed splits + leaderboards | not captured (ACS page timed out) | https://doi.org/10.1021/polymscitech.6c00094 ; https://doi.org/10.6084/m9.figshare.30917717 | search-result-only |
| **REF-40 polymer-chemprop-data** (Aldeghi & Coley) | 42,966 copolymers with xTB EA/IP, fracA/fracB, chain_arch | MIT repo (paper's data availability) | https://github.com/coleygroup/polymer-chemprop-data | search-result-only (repo), numbers from fetched paper |
| **REF-41 Bhati 2026 Zenodo** | 666 experimental homo/copolymer Tg | Zenodo (licence not captured) | https://zenodo.org/records/19242815 | search-result-only (cited in fetched PMC article) |

Practical reading: the only *experimental* open Tg sets of PoLyInfo scale are POINT² (7,208, pending release) and the Kaggle/OPC set (511 Tg, MD-simulated, NC-SA). None has copolymer composition columns. PI1M is unlabeled and itself derived from PoLyInfo.

---

## 5. Tooling

### REF-42 — psmiles (Ramprasad-Group)
- URLs: https://github.com/Ramprasad-Group/psmiles (fetched), https://psmiles.readthedocs.io/en/stable/api/canonicalize/ (fetched). verified_by: **fetched**. MIT licence; canonicalize = "unify" (connect the two neighbour atoms, remove attachment points) + "reduce" (remove repeated substructures), iterated; **requires exactly two `[*]` atoms**; raises `UserWarning("Canonicalization failed.")` when no breakable bond is found; provides polyBERT, Morgan, Mordred, RDKit fingerprints. Not on PyPI (`pip install psmiles` → "No matching distribution"); install is `pip install git+https://github.com/Ramprasad-Group/psmiles.git` — in this sandbox both `git+` (clone error) and the archive zip (HTTP 404) failed, so it was **not** executed here.
### REF-43 — canonicalize_psmiles (Ramprasad-Group)
- URL: https://github.com/Ramprasad-Group/canonicalize_psmiles — verified_by: **fetched**. Licence: "Available for academic non-commercial use only". Four steps: shortest repeat unit (`[*]CCOCCO[*]` → `[*]CCO[*]`), cyclise, RDKit canonicalise, re-open ring. Two-star only.
### REF-44 — RDKit 2025.09.6 `*` handling — **computed locally** (script output in this audit)
- `[*]CC[*]`, `*CC*`, `C(*)C*` all canonicalise to `*CC*`; dummy atoms have atomic number 0, count as heavy atoms (`[*]CC[*]` heavy=2, MW 28.05 — MW includes no mass for `*`); 3-star `[*]C(*)C[*]` parses fine (`*CC(*)*`).
- Morgan (r=2, 2048): Tanimoto(`[*]CC[*]`, `CC`) = **0.000** (dummies enter the invariants); (`[*]CCO[*]`, `[*]OCC[*]`) = **1.000**; (`[*]CCOCCO[*]`, `[*]CCO[*]`) = **0.625**; (`[*]CCO[*]`, `[*]COC[*]`) = 0.267; (`[*]CC[*]`, `[*]CCCC[*]`) = 0.500. ⇒ multiplicity/translation of the repeat unit is *not* normalised by RDKit alone; canonicalise first (psmiles) or build periodic graphs (polyGNN/wD-MPNN).
- RDKit Book (https://www.rdkit.org/docs/RDKit_Book.html, fetched): dummy atoms in SMILES-derived queries match any atom; no statement on fingerprints.
### REF-45 — Chemprop
- polymer-chemprop (Coley group) https://github.com/coleygroup/polymer-chemprop — fetched: MIT, fork of **Chemprop v1** (`--polymer` flag; string format above), tag v1.4.0-polymer.
- Upstream Chemprop https://github.com/chemprop/chemprop (fetched: MIT; v2 paper doi:10.1021/acs.jcim.5c02332) and docs https://chemprop.readthedocs.io/ (fetched: **v2.3.1**; no mention of polymers, wD-MPNN, or stoichiometry weights). ChemRxiv v2 paper page returned 403 (search-result-only). ⇒ wD-MPNN must be run on the v1 fork (torch ≤ v1 era) or re-implemented on v2's featurizer API.
### REF-46 — HuggingFace / weights availability
- polyBERT `kuelumbus/polyBERT` (fetched): DebertaV2 + mean pooling, 600-d, license file, 4,973 downloads/month, works with `sentence-transformers`.
- PolyNC `hkqiu/PolyNC` (search) + GitHub Apache-2.0 (fetched).
- TransPolymer: weights in repo `ckpt` folder, MIT (fetched). No HF card found.
- polyBART, PolyFusion: no public weights statement found (fetched abstracts/HTML).
### REF-47 — Evaluation-split evidence
- Dablander, OPIG blog 2021-06-15 https://www.blopig.com/blog/2021/06/out-of-distribution-generalisation-and-scaffold-splitting-in-molecular-property-prediction/ (fetched): random splits inflate estimates; scaffold split imperfect but better.
- Guo, Hernandez-Hernandez, Ballester (2024) "Scaffold Splits Overestimate Virtual Screening Performance", arXiv:2406.00873 (fetched): 2,100 models on 60 NCI-60 sets; "model performance is much worse with UMAP splits"; recommend UMAP-cluster splits.
- Polymer-specific: Aldeghi & Coley's monomer-identity hold-out (R² drop; RMSE 0.10 eV vs 0.03 eV random) and Bhati's unique-formulation hold-out are the polymer analogues; every polymer LM paper surveyed (polyBERT, TransPolymer, PolyNC, Gupta 2025, POINT², polyBART, PolyFusion) reports random / k-fold splits only. The Kaggle OPC report documents a real Tg distribution shift (mean 102.9 → 179.8 °C) that broke leaderboard models. For LLM4POL: split by polymer_id (never by sample_id), plus a monomer-held-out and a copolymer-family-held-out split.

---

## 6. Can LLMs do numeric regression? Evidence

### REF-48 — Jablonka, Schwaller, Ortega-Guerrero, Smit (2024) "Leveraging large language models for predictive chemistry", Nat. Mach. Intell. 6:161–169
- URL: https://www.nature.com/articles/s42256-023-00788-1 — verified_by: **fetched** (Exa). Fine-tuned GPT-3 "can perform comparably to or even outperform conventional machine learning techniques, in particular in the low-data limit"; e.g. high-entropy-alloy phase classification with ~50 points matches an RF trained on ~1,126 points. Mostly classification/binned tasks; regression handled via text completion.
### REF-49 — Jacobs, Polak, Schultz, Mahdavi, Honavar, Morgan (2024; rev. 2026-04-21) "Regression with Large Language Models for Materials and Molecular Property Prediction", arXiv:2409.06080
- URL: https://arxiv.org/abs/2409.06080 — verified_by: **fetched**. Fine-tuned LLaMA-3 on SMILES "can rival standard materials property prediction models like random forest or fully connected neural networks on the QM9 dataset" but "LLaMA 3 errors are 5-10x higher than those of the state-of-the-art models"; on 28 materials properties "comparable, although slightly worse, accuracy relative to random forest"; LLaMA-3 > GPT-3.5 / GPT-4o.
### REF-50 — Rubungo, Arnold, Rand, Dieng (2023) "LLM-Prop: Predicting Physical and Electronic Properties of Crystalline Solids from Their Text Descriptions", arXiv:2310.14029 (npj Comput. Mater. 2025 version: https://www.nature.com/articles/s41524-025-01536-2, search-result-only)
- URL: https://arxiv.org/abs/2310.14029 — verified_by: **fetched**. T5-encoder (35 M params) on text descriptions: band gap ~4 % and unit-cell volume 66 % better than GNN baselines; beats fine-tuned MatBERT with 3× fewer parameters. Positive case — but a *small encoder* fine-tuned end-to-end, not a chat LLM.
### REF-51 — LLM4Mat-Bench (REF-13) and Gupta et al. 2025 (REF-12) — see above: small fine-tuned encoders ≫ chat LLMs; on polymer thermal properties fine-tuned LLaMA-3-8B/GPT-3.5 underperform PG/polyGNN/polyBERT and fail at multitask.
### REF-52 — Vuong et al. 2025 (REF-17): fine-tuned Llama-3.x/Qwen2.5 lose to MLP+RDKit on Tg MAE (58.0 vs 46.5 ×10⁻²) though they win the multi-property wMAE.

**Synthesis:** (i) LLM fine-tunes help in the *low-data* regime (tens–hundreds of points) and for multi-property text conditioning; (ii) at 5–10 k experimental Tg points, fingerprint/GNN/polyBERT baselines are 20–40 % lower RMSE than decoder-LLM fine-tunes; (iii) small encoders (T5/BERT-class) trained end-to-end are the LLM variants that actually win benchmarks (LLM-Prop, MatBERT, polyBERT). For an 8 GB RTX 5050 without torch installed, a polyBERT-embedding + GBDT/MLP baseline and a wD-MPNN copolymer model are feasible; an 8B LoRA fine-tune is marginal (Gupta used 2×L40S 48 GB).

---

## 7. Gaps / open questions
1. Written NIMS permission status for (a) the way the CSV was exported and (b) publishing any model trained on it — unknown; Terms give no ML clause.
2. polyBERT's Tg-specific RMSE (Supplementary Table S1) not retrieved; polyBART reports polyBERT Tg RMSE 38.41 K and PolyFusion 37.94 K on PoLyInfo-derived sets, consistent with Gupta's ≈38 K.
3. Kaggle rules page did not render; the "CC-BY-NC-SA 4.0" clause is a participant quote in the host's thread.
4. POINT² data release timing; PolyBench-ACS licence; Khazana per-dataset licences.
5. psmiles could not be installed in this sandbox (network/git); behaviour on 3+ star strings therefore inferred from docs (two-star requirement) not run.
