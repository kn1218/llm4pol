# DB-experimental.md — Experimental / Measured Polymer Property Databases & Their Licensing

**Scope:** LLM4POL survey of curated EXPERIMENTAL polymer property databases — the search for a polymer analogue of CoRE-MOF, and for legally redistributable alternatives to PoLyInfo.
**Compiled:** 2026-09-11
**Evidence rule:** every claim below carries a URL that was actually fetched (`verified_by: fetched`) or a search result whose title matched (`verified_by: search-result-only`). Numbers and licence wording are never invented. Licence text is quoted verbatim where visible.

---

## 0. TL;DR — the decision-relevant findings

1. **PoLyInfo is confirmed closed for redistribution**, and the exact prohibition text is now in hand verbatim (§1). The background brief was correct on the numbers and substantially correct on the terms — with **three corrections** (§1.4).
2. **The single strongest verified precedent**: a 260-researcher, 48-institution Japanese industry–academia consortium (the RadonPy/PolyOmics project, which works alongside NIMS) states in print that they **could not redistribute PoLyInfo experimental data**. If they could not, a smaller group will not (§1.5).
3. ⚠️ **BIGGEST TRAP — PoLyInfo laundering.** The most attractive-looking "clean" option, the **PolyMetriX `CuratedGlassTempDataset`** (Zenodo, **CC BY 4.0**, 7,367 experimental Tg), is **97.3% PoLyInfo-derived** via an intermediate dataset (GREA). A CC-BY label applied downstream does **not** cure the upstream restriction. **Do not use this as the hidden table without remediation** (§3.1). This same contamination silently affects several other popular "open" Tg sets.
4. **Recommended legally-clean composite** (§6): **polyVERSE** (Georgia Tech, redistributable, 5,212 experimental gas-transport points + ~10 other experimental property sets) as the spine, plus **OpenPoly** (MIT), **Bhati** (CC BY), **Brierley-Croft** (CC BY), **rhnet** (MIT).
5. **The Kaggle NeurIPS 2025 Open Polymer set is MD-simulated, not experimental** — verbatim: *"All properties are obtained through MD simulations."* It does not qualify (§3.2).
6. **Every classic database is closed.** CAMPUS, ATHAS, CROW, MatWeb, Wiley/Polymer Handbook and Van Krevelen are all free-or-cheap to *view* and **none** grants redistribution; MatWeb bans it by name in seven separate clauses (§4.4). "Free to view" ≠ "free to redistribute" is the single most useful lens in this survey.
7. **The scalable long-term answer is your own extraction pipeline** (§5). Tooling is free (ChemDataExtractor MIT; MaterialsBERT/polyNLP copyleft) and proven at ~300,000 records / 60 h. The real bottleneck is **publisher TDM agreements**, not NLP — check what KAIST's library already holds.
8. ⭐ **There is a proven legal template, and an open niche.** The Cole group has deposited **720,308 literature-mined property records under CC BY 4.0** on figshare with a *Scientific Data* descriptor paper, and four similar sets besides (§5.1b). Elsevier states verbatim: *"We do not claim copyright over your TDM output"* and *"There are no restrictions on where and how you can publish your TDM output."* **No polymer-specific ChemDataExtractor database has ever been published** — that is exactly the gap LLM4POL could fill.
9. **PoLyInfo's legal protection is contract-only.** The EU database right does not reach it (Directive 96/9/EC Art. 11 limits beneficiaries to EU entities; NIMS is Japanese), Japan has no equivalent right, and *Feist* denies US copyright in facts. **The click-through terms are the entire barrier** — which is why never bulk-acquiring under them is the whole game (§5.3).

> **One-line answer to the brief's core question:** there is **no polymer CoRE-MOF today**, and PoLyInfo cannot become one. The best available substitute is a **composite of six permissively-licensed sets totalling 39,222 measured points across ~38 properties** (§6.1), with **polyVERSE** and **rhnet** load-bearing — and the credible route *past* that ceiling is a ChemDataExtractor-style extraction published under CC BY, following the Cole group's template.

---

## 1. PoLyInfo (NIMS MatNavi) — confirmed, with corrections

### 1.1 Size — CONFIRMED against the live site

Fetched <https://polymer.nims.go.jp/> — statistics stated **as of 29 May 2025**:

| Quantity | Value |
|---|---|
| Homopolymers | 19,227 |
| Copolymers | 8,321 |
| Polymer blends | 2,788 |
| Composites | 3,209 |
| Polymer samples | 174,968 |
| Physical property data points | 552,427 |
| Literature records (references) | 21,793 |

`verified_by: fetched` — every figure in the project's background brief matches exactly. **No correction needed.**

**Prior snapshot — the authoritative baseline.** Ishii, Ito, Sado & Kuwajima, *"NIMS polymer database PoLyInfo (I): an overarching view of half a million data points"*, **STAM: Methods 4(1), 2354649 (20 May 2024), CC BY 4.0** — obtained as the full CC-BY PDF from the NIMS Materials Data Repository mirror (tandfonline 403s) and parsed locally. Verbatim, p. 2:

> "A statistical summary of PoLyInfo shows the following data counts **as of January 2024**.
> Homopolymers: 18,697 · Copolymers: 7,737 · Polymer blends: 2,572 · Composites: 3,069 · Polymer samples: 161,464 · Property points: 494,820 · Literature: 20,445"

And by material type (p. 6): *"Neat resin: 109,810 samples / Compound: 31,170 samples / Composite: 25,041 samples"*. `verified_by: fetched`

> ⚠️ **Two corrections to secondary sources:**
> - *Polymer Data Challenges in the AI Era* (arXiv 2505.13494) attributes the figures 18,697 / 7,737 / 494,820 / 161,464 to **"October 2023"**. They are in fact the **January 2024** figures, quoted from PoLyInfo (I) above. **Cite the primary paper, not 2505.13494.**
> - The same paper says PoLyInfo covers *"approximately 1,000 distinct material properties"*. PoLyInfo's own help page says **"about 100 types"**, and PolyOmics Table S1 independently says **"~100 distinct properties"**. **Treat ~100 as correct**; the 1,000 is an error.
>
> **Growth rate (Jan 2024 → May 2025, 16 months):** +530 homopolymers, +584 copolymers, +13,504 samples, **+57,607 property points**, +1,348 references — i.e. ~11.6% growth in data points per year. Useful for judging how stale any derived snapshot is.

**Note — PoLyInfo (I) contains no data-availability statement.** A full-text grep confirms the paper ends *Acknowledgements → Disclosure statement → ORCID → References*. The only ownership-adjacent sentence is: *"The polymer database PoLyInfo is managed and operated by National Institute for Materials Science (NIMS) and is promoted as a project of NIMS using its own financial resources."* `verified_by: fetched`

### 1.2 The terms of use — VERBATIM

Source: `https://mits.nims.go.jp/agreement/MatNavi_agreement_en.pdf` — "MatNavi Service Terms of Use", National Institute for Materials Science, *Established April 1 2018; Revised April 1 2021; Revised January 17 2023; **Revised August 1 2024***. PDF fetched and text-extracted locally. `verified_by: fetched`

**Article 1 — Definitions (verbatim):**
> (6) "DATA"  Data, content (including, without limitation, text, illustrations, pictures and tables) and data sheets that are provided through MatNavi and the Service;
> (7) "Processed DATA"  The DATA that have been processed into a table or other form of expression. The Processed DATA shall include the DATA and other data, etc., that have been processed into a table or other form of expression.

> **Note the breadth**: "Processed DATA" explicitly covers *a table you built from the DATA*. A "hidden table" benchmark derived from PoLyInfo is squarely Processed DATA.

**Article 9 — Rights to Data, etc. (verbatim):**
> 1. Rights to use and manage the DATA that are provided through MatNavi and the Service are held by the Institute. Copyrights to MatNavi, all web pages on the Site and the relevant systems in general are also held by the Institute.
> 2. The Institute shall license Registrants to use the DATA **only for use by themselves** for the purpose of education, or research and development or product development and the manufacture of products so developed, and review pertaining to the foregoing.
> 3. When Registrant publishes any deliverables of research and development or product development using the DATA, Registrant shall indicate the names of the Institute and the Service as the source of data in the following manner. […]
> (1) The following statement or other similar descriptions shall be clearly included as an acknowledgment. "This research was conducted (in part) using the [database name] provided by the Materials Data Platform (MDPF) of the National Institute for Materials Science (NIMS)."

**Article 10 — Prohibited Acts (verbatim, the operative items):**
> (1) All acts of using the DATA other than use licensed under paragraph 2 of the preceding Article (including copying, translation, adaption, derivative use, transmission, uploading, distribution, assignment, lending, licensing or merchandising other than use licensed under paragraph 2 of the preceding Article);
> (2) Act of selling or distributing the DATA or Processed DATA through publication, download sales or by other means. **However, publication of deliverables of research and development or product development using the DATA shall be excluded;**
> (3) Act of reprinting the DATA or Processed DATA in documents, websites, etc. **However, the publication of deliverables of research and development or product development using the DATA shall be excluded;**
> (5) Act of obtaining data the volume of which in the judgment of the Institute is at or above a certain limit, by web scraping (meaning automatic extraction of data from web pages by using a program) or by other means;
> (6) Resales of the Service, provision or sublicensing of use of the Service to a third party;

**Article 13.2 (termination consequence, verbatim):**
> If Registrant has violated these Terms, Registrant shall delete all DATA and Processed DATA and their duplicate data, and shall dispose of materials recording the DATA and Processed DATA. After implementing the procedures for the deletion or disposal thereof, Registrant shall, at the request of the Institute, submit to the Institute a certificate showing that those procedures have been implemented.

**On-site restatement** (fetched, <https://polymer.nims.go.jp/>): *"Data scraping is prohibited! Whether manual or automated, obtaining large quantities of data is forbidden under the MatNavi service terms."* Violations → account suspension.

### 1.3 Access route and cost

- **Registration:** individual, free. Requires DICE Account registration + e-mail **domain** registration + MatNavi usage application. Fetched <https://dice.nims.go.jp/usage.html>: *"Users are, in principle, individuals belonging to an organization"* — an organisational e-mail address is required. `verified_by: fetched`
- **Cost:** Article 1(1) defines the Service as *"Services provided **free of charge** to Registrants"*. There is **no paid tier defined anywhere in the Terms**. `verified_by: fetched`
- **Registrants are individuals.** There is **no institutional/site account** construct in the Terms; Article 10(7) forbids *"making the functions of the Service available to any person other than Registrants"*, and Article 11 forbids transferring rights. So "an institutional account" in the ordinary sense **does not exist**. `verified_by: fetched`

### 1.4 CORRECTIONS to the project's background brief

| Brief said | Correction | Evidence |
|---|---|---|
| "Art. 9.2 / 10(1)-(3),(5) forbid … with a carve-out only for 'publication of deliverables of research and development'" | **Substantially right, but the carve-out is narrower than it reads.** The carve-out is attached **only to 10(2) and 10(3)**. It is **not** attached to **10(1)** (which bans copying/derivative use/distribution outright) nor to **10(5)** (bulk acquisition). So the carve-out lets you *print values inside a paper*; it does **not** authorise bulk acquisition in the first place, nor publishing a standalone redistributable dataset. | Verbatim Art. 10 above, `fetched` |
| "There is no public API for property data" | **Needs refining.** A machine-readable **SPARQL/RDF interface does exist** — PoLyInfoRDF, **24,593,403 triples** — but it is served from an **authentication-gated endpoint**. Only the *ontology* is open (CC BY 4.0). So: no *public* API — correct in effect; but a *contract-gated* machine-readable route exists. | §1.6 below |
| (implicit) no licensed bulk route | **A contract route is documented to exist** (§1.6), though its terms are not public. | §1.6 |

### 1.5 ⭐ Documented precedent — the decisive data point

The **PolyOmics / RadonPy** paper (*Omics-scale polymer computational database transferable to real-world artificial intelligence applications*, arXiv 2511.11626 — PDF fetched, 65 pp, text-extracted) is produced by *"an industry–academia consortium of more than 260 researchers from 3 national research institutes, 8 universities, and 37 companies"*, working on Fugaku, and it uses PoLyInfo extensively (61 PoLyInfo property datasets; 15,323 PoLyInfo polymers used for chemical-space comparison).

Its **Data availability** section states verbatim:

> "Owing to licensing restrictions, the experimental datasets from the PoLyInfo database **could not be redistributed**. Access to the PoLyInfo database requires contacting the designated office of the National Institute for Materials Science via the PoLyInfo website (https://polymer.nims.go.jp)."

`verified_by: fetched`

**Interpretation for LLM4POL:** this is the best-resourced, most NIMS-adjacent polymer-data consortium in the world. They published their own 130k-polymer MD database openly on HuggingFace, and still could not redistribute PoLyInfo values. **There is no realistic path to a public PoLyInfo-based hidden table.** Treat this as settled.

I found **no documented precedent of any group being granted redistribution permission.**

### 1.6 The contract-gated machine-readable route (PoLyInfoRDF)

- **PoLyInfo Ontology v1.0** is openly published on the NIMS Materials Data Repository — licence displayed verbatim: **"Creative Commons BY Attribution 4.0 International"**; downloadable as `polyinfoowl.ttl` (769 KB). Fetched <https://mdr.nims.go.jp/concern/datasets/kw52jg498?locale=en>. `verified_by: fetched`
- **But the data itself is not there.** That record states PoLyInfoRDF is *"published in an authentication endpoint"*. The open endpoint <https://materials-open-rdf.nims.go.jp/sparql> serves the ontology/open items only.
- **PoLyInfo (II)** — Ishii, Ito & Sakamoto, *"machine-readable standardization of polymer knowledge expression"*, STAM: Methods, doi 10.1080/27660400.2024.2354651 (6 Jun 2024), CC BY. Obtained as the CC-BY PDF and parsed locally after tandfonline 403'd. **Verbatim:**

> "The latest version of PoLyInfoRDF has **24,593,403 triples**. **There are two types of triple stores: open-access and authenticated. The open-access type contains ontologies and other highly public items that can be freely used to extend data linkages. On the other hand, the authenticated type contains data that NIMS has capitalized and can be used under a certain contract.** Currently, PoLyInfoRDF data are available for access only from these endpoints, and not for GUI services based on fixed stories."

`verified_by: **fetched**` *(upgraded from search-result-only)*

- Only the **ShEx schemas** are openly deposited — *"All ShEx schemas that can reproduce PoLyInfoRDF are published in an open data repository (Materials Data Repository, MDR)"* (MDR, doi 10.48505/nims.4415). **Schemas, not data.** Together with the CC-BY ontology (§1.6 above), NIMS has open-sourced the *structure* of PoLyInfo while keeping the *values* closed. ⇒ **You can legally adopt PoLyInfo's data model for your own database** — a genuinely useful, licence-free asset.
- Supporting earlier paper, also fetched: Ishii, Takemura & Tanifuji, *"PoLyInfo RDF: A Semantically Reinforced Polymer Database for Materials Informatics"*, CEUR-WS Vol-2456 paper 18 (**CC BY 4.0**) — 2019 prototype at 227,482 triples; PoLyInfo holds **17,825 monomers**; a SPARQL crossover query returned 39,907 polymers. `verified_by: fetched`

**Practical read:** a contract route plausibly exists for *use*, but (a) its terms are not public, (b) nothing suggests it grants *redistribution*, and (c) §1.5 shows a vastly better-resourced consortium did not obtain redistribution rights. **Worth one e-mail to `dice_help@nims.go.jp`, but do not architect the project around it.**

### 1.7 Verdict

| Field | Value |
|---|---|
| Name | **PoLyInfo** (NIMS MatNavi) |
| Maintainer | National Institute for Materials Science (NIMS), Japan |
| Entries | 19,227 homopolymers / 8,321 copolymers / 2,788 blends / 3,209 composites / 174,968 samples / **552,427 data points** / 21,793 refs (29 May 2025) |
| Properties | ~100 types — thermal, mechanical, electrical, optical, transport + processing & measurement conditions |
| Experimental? | **Experimental**, literature-curated (plus values calculated from measured data; excludes cited data and commercial catalogue data) |
| Machine-readable | HTML search UI only for the public. RDF/SPARQL exists but **authentication/contract-gated**. No public API. |
| Licence | Proprietary; NIMS retains all rights. Art. 9.2 self-use only; Art. 10(1)(2)(3)(5) as quoted. |
| Cost | Free (registration required); no paid tier in the Terms |
| URL | <https://polymer.nims.go.jp/>, <https://mits.nims.go.jp/agreement/MatNavi_agreement_en.pdf>, <https://dice.nims.go.jp/usage.html> |
| verified_by | **fetched** |
| **Verdict** | ⛔ **Cannot be used as a public hidden table.** You may publish a *paper* containing derived models and cite/acknowledge NIMS (Art. 10(2)/(3) carve-out + Art. 9.3 attribution). You may **not** bulk-acquire it (Art. 10(5)) nor republish a derived table as a standalone dataset (Art. 10(1)). |

---

## 2. ⚠️ The contamination problem — PoLyInfo laundering

**This is the most important operational finding in this report.**

Several widely-used, permissively-licensed "open experimental polymer datasets" are in fact **downstream copies of PoLyInfo**, relabelled with a permissive licence by an intermediate author who had no right to grant it. Applying CC-BY to someone else's restricted data does not make it CC-BY.

### 2.1 The documented chain

```
PoLyInfo (NIMS, all rights reserved)
   └─> GREA "GlassTemp" (7,174 polymers)   [KDD 2022, repo MIT-licensed]
          └─> PolyMetriX CuratedGlassTempDataset (7,170 of 7,367 rows = 97.3%)
                 └─> Zenodo 15210035, relabelled CC BY 4.0
```

**Link 1 — verbatim, from the GREA paper's own Appendix A "DATASET DETAILS"** (arXiv 2206.02886, PDF fetched and text-extracted):

> "The four datasets GlassTemp, MeltingTemp, PolyDensity, and O2Perm are used to predict different properties of polymers such as glass transition temperature (°C), polymer density g/cm3, melting temperature (°C), and oxygen permeability (Barrer). **GlassTemp, MeltingTemp, and PolyDensity are collected from PolyInfo, which is the largest web-based polymer database [20].** The O2Perm dataset is created from the Membrane Society of Australasia portal…"

(reference [20] = Otsuka, Kuwajima, Hosoya, Xu, Yamazaki, *PoLyInfo: Polymer database for polymeric materials design*, 2011.) `verified_by: fetched`

GREA Table 1, verbatim: `GlassTemp 7,174` graphs. `verified_by: fetched`

**Link 2 — PolyMetriX's own documentation** lists `GREA` as one of nine sources, linking directly to `github.com/liugangcode/GREA/blob/main/data/tg_prop/raw/tg_raw.csv`. Fetched <https://raw.githubusercontent.com/lamalab-org/PolyMetriX/main/docs/datasets.md>. `verified_by: fetched`

**Link 3 — I downloaded the Zenodo CSV and counted the source column myself:**

```
ROWS 7367 ; NCOLS 112 ; labels.Exp_Tg(K) populated 7367/7367 ; range 134.15 – 768.15 K
meta.source  = {GREA: 7170, Qiu: 152, Xie: 21, Schrodinger: 15, Nguyen: 7, Uchicago: 2}
meta.reliability = {black: 7088, gold: 143, yellow: 132, red: 4}
```
`verified_by: fetched` (file downloaded from `https://zenodo.org/records/15210035/files/LAMALAB_CURATED_Tg_structured_polymerclass.csv`)

The Tg range 134.15–768.15 K matches the GREA-derived "7,174 polymers, 134 K to 768 K" figure reported in the literature exactly.

### 2.2 Consequences

- **97.3% of the PolyMetriX curated Tg benchmark is PoLyInfo data.** Its CC BY 4.0 label is not a valid grant for that portion.
- **Data-quality corollary (independent of licensing):** `meta.reliability` is **black for 7,088 of 7,367 rows (96.2%)** — PolyMetriX's own documentation defines black as *"the reliability of the data is uncertain because the polymers are unique, and there is limited information available."* Only **143 rows are 'gold'** (≥3 concordant independent sources). So the multi-source cross-validation that makes this look like a CoRE-MOF-grade curated set actually covers **~275 polymers**, not 7,367. **The set is neither as clean nor as independent as it presents.**
- **Presumed to affect other sets too.** Any polymer Tg/Tm/density set of roughly 7,174 / 3,651 / 1,694 entries should be assumed GREA/PoLyInfo-derived until proven otherwise. Likewise, `polyVERSE/Other/Conductivity_electrical` states in its README: *"The data were collected from the PolyInfo website"* (398 rows) — see §4.1.

### 2.3 Required action for LLM4POL

> 🚩 **How easy this trap is to fall into:** an independent research lane in this very survey, working only from the licence metadata (Zenodo API `metadata.license.id = cc-by-4.0`, repo MIT), concluded that this dataset was *"the only CoRE-MOF-analogue-grade licence in this entire study"* and recommended it as the benchmark backbone. That recommendation is **overridden here** on the strength of the GREA→PoLyInfo chain documented above. Licence metadata alone is not provenance.

**Before adopting ANY third-party "open" experimental polymer dataset, trace provenance to the primary literature.** A permissive licence file in a GitHub repo is *not* evidence of the right to relicense the data inside it. Specifically:
- Reject or quarantine anything whose chain reaches PoLyInfo.
- Prefer datasets with **per-row source DOIs** (rhnet, Brierley-Croft) — these are auditable and are facts extracted from primary literature, which is the legally cleanest basis (see §5).

---

## 3. Open / derived sets containing EXPERIMENTAL values

### 3.1 PolyMetriX — CuratedGlassTempDataset ⚠️

| Field | Value |
|---|---|
| Name | PolyMetriX `CuratedGlassTempDataset` ("Curated Glass Transition Temperature for Polymers") |
| Maintainer | Sreekanth Kunchapu & Kevin Maik Jablonka, Friedrich Schiller University Jena (LAMAlab) |
| Entries | **7,367** unique PSMILES–Tg pairs (verified by download); curated from ~9,000 entries / 9 sources; 22 polymer classes; 112 columns incl. precomputed featurisation |
| Properties | Experimental glass transition temperature `labels.Exp_Tg(K)`, 134.15–768.15 K, + reliability, stdev, Tg range, source, polymer class |
| Experimental? | Labels are experimental measurements — **but see §2, 97.3% are PoLyInfo-derived** |
| Machine-readable | ✅ Bulk CSV (5.3 MB) direct from Zenodo; Python API via `polymetrix` (MIT) |
| Licence | Zenodo record displays **"Creative Commons Attribution 4.0 International"**; code repo `lamalab-org/PolyMetriX` is **MIT** (GitHub API) |
| Cost | Free |
| URL | <https://zenodo.org/records/15210035> (DOI 10.5281/zenodo.15210035, 14 Apr 2025); <https://lamalab-org.github.io/PolyMetriX/datasets/>; <https://github.com/lamalab-org/PolyMetriX>; paper npj Comput. Mater. **11**, 312 (2025), doi 10.1038/s41524-025-01823-y |
| verified_by | **fetched** (Zenodo record, docs, GitHub API, and the CSV itself downloaded and counted) |
| **Verdict** | ⚠️ **DO NOT use as the public hidden table as-is.** The CC-BY grant is not valid for the 97.3% PoLyInfo-derived portion, and 96.2% of rows are self-rated "uncertain" reliability. **Usable subset:** the 197 non-GREA rows (Qiu 152, Xie 21, Schrodinger 15, Nguyen 7, Uchicago 2) — but verify each of those upstream licences too. Excellent as a *featurisation/splitting toolkit* (MIT) regardless. |

> **Fairness note:** PolyMetriX documents its GREA source openly and links to it; the contamination is inherited, not concealed. The authors' `meta.reliability` column is exactly the honest signal that exposes the problem.

### 3.2 Kaggle / NeurIPS 2025 "Open Polymer Prediction" — MD-SIMULATED, disqualified

| Field | Value |
|---|---|
| Name | NeurIPS 2025 Open Polymer Prediction (Kaggle competition) |
| Maintainer | Liu, Luo, Jiang et al. (Notre Dame / UConn) + Kaggle |
| Entries | **7,973** train structures; per-property Tg **511**, FFV **7,030**, Tc **737**, Rg **614**, Density **613**; ~1,500 hidden test |
| Properties | Tg, fractional free volume, thermal conductivity, density, radius of gyration |
| Experimental? | ❌ **MD-SIMULATED.** Organisers' post-competition report, verbatim: *"All properties are obtained through MD simulations."* (LAMMPS + GAFF2/Gasteiger for density/Rg/Tc; Materials Studio + PCFF for FFV/Tg) |
| Machine-readable | CSV; train behind Kaggle login |
| Licence | **Not verifiable** — Kaggle rules/data pages are reCAPTCHA-gated to automated fetch. The CC BY 4.0 that surfaces belongs to the *arXiv report*, not the dataset. A third-party test-set mirror self-tags MIT (re-uploader's declaration, not authoritative). |
| Cost | Free |
| URL | <https://arxiv.org/html/2512.08896v1>; <https://github.com/sobinalosious/ADEPT> |
| verified_by | **fetched** |
| **Verdict** | ⛔ **Disqualified on the merits** — it is simulated, so it cannot serve as an experimental benchmark, regardless of licence. **This directly answers the brief's open question.** |

### 3.3 Bhati 2026 — experimental copolymer Tg ✅

| Field | Value |
|---|---|
| Name | Experimental dataset accompanying *Glass Transition Prediction of Binary Copolymers Across Large Chemical Spaces Using Machine Learning and Physics-Based Modeling* |
| Maintainer | Manav Bhati, M. A. F. Afzal, Alex Chew, Andrea Browning, Mathew Halls — **Schrödinger Inc.** |
| Entries | **666** rows (verified by download: 666 rows, cols `ID, Poly1, Poly2, SMILES_0, SMILES_1, comp_0, comp_1, Tg(K), x1`). Paper composition: 315 homopolymers + 351 binary copolymers; provenance **301 points from Bicerano + 365 from Penzel** |
| Properties | Tg (K) vs. copolymer composition, with both comonomer SMILES |
| Experimental? | ✅ **Experimental** (the repo's other files — `enumerated_*`, `md_*` — are ML-predicted / MD and must be kept separate) |
| Machine-readable | ✅ `experimental_dataset.csv`, 64.1 kB, direct download, no login |
| Licence | **"Creative Commons Attribution 4.0 International"** (displayed on the Zenodo record) |
| Cost | Free |
| URL | <https://zenodo.org/records/19242815> (DOI 10.5281/zenodo.19242815); paper doi 10.3390/polym18141727 |
| verified_by | **fetched** (record + file downloaded and counted) |
| **Verdict** | ✅ **YES — republishable.** Clean CC BY, corporate-curated, not PoLyInfo-derived. **Also the answer to the Bicerano question (§4.6): this is the Bicerano tabulated set in machine-readable, CC-BY form.** |

### 3.4 Brierley-Croft 2025 — PAEK set ✅

| Field | Value |
|---|---|
| Name | Dataset for *Polymer Informatics Method for Fast and Accurate Prediction of the Glass Transition Temperature from Chemical Structure* (PAEK) |
| Maintainer | University of Leeds + **Victrex PLC** |
| Entries | **146** data rows (verified by download); 77 homopolymers + 69 copolymers |
| Properties | Tg (375–550 K), SMILES, fragment-count matrices, QSPR descriptors; per-point references in `Data_references.pdf` |
| Experimental? | ✅ **Experimental** — *"collected from the literature and from Victrex R&D"* |
| Machine-readable | ✅ XLSX (3 MB), open, no login |
| Licence | Verbatim: *"Copyright 2025 University of Leeds. Unless otherwise stated, this dataset is licensed under a Creative Commons Attribution 4.0 International Licence"* |
| Cost | Free |
| URL | <https://archive.researchdata.leeds.ac.uk/1431/> (DOI 10.5518/1596); paper doi 10.1021/acs.macromol.5c00178 |
| verified_by | **fetched** (record + file downloaded and counted) |
| **Verdict** | ✅ **YES — republishable.** Small and chemically narrow (PAEK only), but impeccable provenance including proprietary industrial R&D data released under CC BY. Gold-standard quality per point. |

### 3.5 Jeong 2024 — PFAS membrane rejection ⛔ (licence trap)

| Field | Value |
|---|---|
| Name | PFAS rejection dataset (Jeong et al., *Nat. Commun.*) |
| Maintainer | Georgia Tech / Colorado State / ASU / UW-Madison |
| Entries | **457** literature data points (+77 authors' own NF experiments) |
| Properties | PFAS rejection (%) across 21 PFAS × 16 polyamide NF/RO membranes |
| Experimental? | ✅ Experimental (rejection measurements digitised from literature) |
| Machine-readable | Supplementary Data 1 + Source Data XLSX on the article page |
| Licence | ⚠️ **CC BY-NC-ND 4.0** — verbatim: *"You do not have permission under this licence to share adapted material derived from this article or parts of it."* (Companion code Zenodo 13978801 is CC BY 4.0; MD files Zenodo 13924418 are MIT) |
| Cost | Free to read |
| URL | <https://www.nature.com/articles/s41467-024-55320-9>; <https://zenodo.org/records/13978801> |
| verified_by | **fetched** (licence string read from page HTML) |
| **Verdict** | ⛔ **NO — cannot republish.** The **ND** term forbids distributing a reformatted/derived table; **NC** blocks commercial reuse. Training a model on it is legally grey; **redistributing the table is clearly not permitted.** Only the code is safely reusable. |

### 3.6 Zhou 2026 copolymer Tg (LLM-extracted) — not obtainable

| Field | Value |
|---|---|
| Name | Zhou et al., copolymer Tg extracted by LLM |
| Entries | **1,195 entries from 393 papers — UNVERIFIED** (paywalled; figures could not be confirmed from any accessible source) |
| Experimental? | Presumably experimental (literature-extracted) — unconfirmed |
| Machine-readable | No repository found |
| Licence | **Not open access** (`isOpenAccess: false`); Elsevier subscription, *Chem. Eng. J.* 529, 172634 |
| URL | <https://api.semanticscholar.org/graph/v1/paper/DOI:10.1016/j.cej.2026.172634> |
| verified_by | **fetched (metadata only)**; the counts remain **search-result-only / unverified** |
| **Verdict** | ⛔ **No usable data deposit.** Cannot be used. |

### 3.7 PolyLM — never released

| Field | Value |
|---|---|
| Name | PolyLM (polymer literature corpus — *not* the DAMO multilingual LLM of the same name) |
| Maintainer | Liu, Zhu, Xiong, Tang (arXiv 2605.08255, May 2026) |
| Entries | **276,400** unique polymer samples mined from ~185,000 papers; 68,283 held-out test observations |
| Properties | 22 properties (Tg, Tm, Tc, Td, tensile/flexural strength, Young's modulus, conductivity, dielectric constant, density, crystallinity, viscosity…) with synthesis/processing context |
| Experimental? | Experimental in principle (measured values mined from full text) |
| Machine-readable | ❌ **No GitHub / HuggingFace / Zenodo link given in the paper** |
| Licence | Paper CC BY-SA 4.0; **dataset licence undefined — dataset not released** |
| URL | <https://arxiv.org/html/2605.08255> |
| verified_by | **fetched** |
| **Verdict** | ⛔ **Not possible to use** — the dataset was never published. Valuable only as evidence that literature-scale extraction (§5) is feasible at ~276k samples. |

### 3.8 OpenPoly ⭐ — a genuine small CoRE-MOF analogue ✅

| Field | Value |
|---|---|
| Name | **OpenPoly: A Polymer Database Empowering Benchmarking and Multi-property Predictions** |
| Maintainer | Wang Group, Fudan University |
| Entries | **741 unique polymers × 3,985 experimental structure–property pairs** (I downloaded and counted: 741 rows, 28 property columns, exactly **3,985** non-null values — this reproduces the paper's headline "3,985" figure *exactly*, confirming 3,985 = *pairs*, not polymers) |
| Properties | **26–28**: Tg, Tm, Td, crystallization temp, bandgap, CO₂/H₂/O₂/methanol permeability, tensile/flexural/compressive strength, Young's modulus, elongation at break, impact strength, hardness, LOI, LCST/UCST, refractive index, thermal conductivity, water contact angle, water uptake, swelling degree, ion exchange capacity, dielectric constant (electronic/ionic/total) |
| Experimental? | ✅ **Experimental** — *"literature-derived"*, *"annotated with up to 26 experimentally measured properties"*, manually validated |
| Machine-readable | ✅ CSV in git, direct raw download (`data/final_polymer_properties_fromliterature.csv`, 179 kB) |
| Licence | **MIT License, Copyright (c) 2025 WangGroupFDU** (GitHub API: `spdx_id: MIT`) |
| Cost | Free |
| URL | <https://github.com/WangGroupFDU/Openpoly_benchmark>; paper doi 10.1007/s10118-025-3402-y, *Chinese J. Polym. Sci.* (2025) |
| verified_by | **fetched** (repo tree, LICENSE via API, CSV downloaded and counted cell-by-cell) |
| **Verdict** | ✅ **YES — the cleanest true multi-property experimental benchmark found.** MIT is maximally permissive; the paper also states *"All data supporting this study are openly available under the Creative Commons Attribution 4.0 International (CC BY 4.0) license."* Small (741 polymers) but genuinely CoRE-MOF-shaped: curated, multi-property, benchmark-framed, with baseline models and results shipped alongside. **Two caveats below.** |

> ⚠️ **Caveat 1 — no per-row DOIs.** The released CSV carries no per-row source citation, so provenance is aggregate-level only. Spot-audit a sample against the primary literature before trusting it as a hidden table.
>
> ⚠️ **Caveat 2 — partial upstream contamination.** OpenPoly's live web database shows a `Reference` column that for many rows points at `nature.com/articles/s43246-024-00708-9` — i.e. rows sourced from **Gupta et al.'s LLM extraction**, whose article is **CC BY-NC-ND** and whose upstream repo is Georgia Tech academic-non-commercial, while OpenPoly asserts MIT/CC BY 4.0 over everything. This is the **same relabelling pattern as §2**, though milder: the upstream is itself literature-extracted facts (not a contract-bound database like PoLyInfo), so the *Feist*/thin-compilation argument (§5.3) applies cleanly and practical risk is low. **For a bulletproof benchmark, prefer non-Ramprasad-derived rows**, and note the ~⅔ F1 accuracy ceiling on LLM-extracted Tg (§5.1c). `verified_by: fetched`

> Note on a counting discrepancy: a parallel count reported "5,467 non-empty pairs / 30 columns". That figure incorrectly includes the two structural columns `PSMILES_2` and `PSMILES_4` (741 + 741 = 1,482; 3,985 + 1,482 = 5,467). **3,985 over 28 genuine property columns is correct** and matches the publication.

### 3.8b PolymerSolarCellsML ✅ — cleanest MIT literature-extracted experimental set

| Field | Value |
|---|---|
| Name | PolymerSolarCellsML (Shetty et al., *Chem. Mater.* **36**, 7676, 2024) |
| Maintainer | **Pranav Shetty — personal repo, NOT under the Georgia Tech GTRC licence** |
| Entries | **3,910 rows × 14 columns** (DOI, year, donor, donor_smiles, acceptor, acceptor_smiles, PCE, Voc, Jsc, FF, …) |
| Properties | Organic photovoltaic device metrics: PCE, Voc, Jsc, fill factor |
| Experimental? | ✅ **Experimental** — MaterialsBERT NER over ~3,300 OPV papers **plus manual curation** |
| Machine-readable | ✅ CSV + XLSX in git |
| Licence | `LICENSE`: *"MIT License / Copyright (c) 2024 Pranav Shetty"* |
| Cost | Free |
| URL | <https://github.com/pranav-s/PolymerSolarCellsML> |
| verified_by | **fetched** |
| **Verdict** | ✅ **YES — republishable.** The cleanest permissively-licensed, literature-extracted **experimental** polymer numbers found, **with per-row DOIs**. Narrow (OPV only), and note it overlaps polyVERSE's 422-row `Organic_solar_cell` set — this one is ~9× larger and MIT rather than copyleft, so **prefer this over the polyVERSE OSC set**. |

### 3.8c PolyIE — the extraction-accuracy benchmark

| Field | Value |
|---|---|
| Name | PolyIE (Cheung et al., NAACL 2024, with the Ramprasad Group) |
| Entries | **146 articles, 4,443 annotated relations**; `all.txt` 6.2 MB |
| Properties | Expert NER + n-ary relation annotation of full-text polymer papers |
| Experimental? | Experimental *mentions* — it is an **annotation corpus**, not a property table |
| Machine-readable | ✅ JSONL / Doccano format |
| Licence | **Apache-2.0** |
| URL | <https://github.com/jerry3027/PolyIE> |
| verified_by | **fetched** |
| **Verdict** | ✅ Use as the **extraction-accuracy benchmark** for a DIY pipeline (§5). ⚠️ It embeds PDF-parsed publisher text — the Apache grant is the *authors'*, not the *publishers'*, so do not redistribute the text spans onward. |

### 3.9 rhnet gas-solubility dataset ✅

| Field | Value |
|---|---|
| Name | rhnet experimental gas-solubility dataset |
| Maintainer | Shorku (GitHub) |
| Entries | **16,004** rows (independently downloaded and counted); **107 unique polymers × 81 unique solvents/gases**, traced to **276 unique source DOIs**. Columns: `expno, polymer, solvent, mn, mw, cryst, tg, dens, pressure, temperature, wa, doi, notes` |
| Properties | Gas/solvent uptake `wa` (wt%) vs. pressure and temperature; per-polymer Mn, Mw, crystallinity, Tg, density; **every row carries a source DOI** |
| Experimental? | ✅ **Experimental**, with per-point literature DOIs |
| Machine-readable | ✅ `data/experimental_dataset.csv` (3.2 MB) in git (+ optimised repeat-unit geometries in `geometries.tar.xz`) |
| Licence | **MIT** (GitHub API: `spdx_id: MIT`) |
| Cost | Free |
| URL | <https://github.com/Shorku/rhnet/tree/main/data> |
| verified_by | **fetched** (repo tree + LICENSE via GitHub API; CSV downloaded and counted myself) |
| **Verdict** | ✅ **YES — republishable, and the best provenance of any set found.** Per-row DOIs make it fully auditable and put it on the strongest legal footing (facts traced to primary literature). Excellent transport-property pillar. |

### 3.10 Contrast cases — simulated, not experimental

| Name | Entries | Type | Licence | Verdict |
|---|---|---|---|---|
| **PolyOmics** (RadonPy consortium) | ~130k polymers, 43 properties | **MD-simulated** | Hosted on HuggingFace `yhayashi1986/PolyOmics`; paper CC BY 4.0; dataset licence not explicitly stated on the record | Redistributable in practice, but **simulated** — use for Sim2Real pretraining, not as the experimental benchmark. `fetched` |
| **RadonPy** | `data/PI1070.csv` ≈ 1,070 polymers, 15 properties | **MD-simulated** | Code **BSD-3-Clause** | Contrast case, as expected. `fetched` |
| **Khazana / Polymer Genome** | 6,265 rows, 8 properties | **DFT-simulated** — README verbatim: *"This folder contains the dataset (export.csv) for **DFT properties**"* | ⚠️ **NO LICENCE ANYWHERE** — only *"Copyright © 2023"* in the footer ⇒ all rights reserved by default | ⛔ Not redistributable **and** not experimental. Would need written permission. `fetched` |
| **PI1M** | ~1,000,000 p-SMILES | **Generated** (RNN trained on ~12,000 PoLyInfo polymers) — no experimental labels | ⚠️ Contradictory: MIT LICENSE file vs README *"Data for academic purpose only."* Also PoLyInfo-seeded. | ⚠️ Wrong shape (structures only) + ambiguous licence. `fetched` |
| **PolyOne** | ~100M hypothetical polymers, 29 ML-predicted properties | ML-predicted | Zenodo 7766806 | Not experimental. `fetched` (via PolyOmics Table S1) |
| **OPoly26** | 6.57M DFT calcs, 2,444 monomers | **DFT** | CC-BY-4.0 | Redistributable but DFT. `search-result-only` |
| **OMG / SMiPoly** | ~12M / ~180k generated polymers | Structures only, no properties | Zenodo / GitHub | Not property data. `fetched` (via PolyOmics Table S1) |

---

## 4. Classic / commercial experimental databases

### 4.1 ⭐ polyVERSE (Ramprasad Group, Georgia Tech) — the best-kept secret

**This resource was not in the original brief and is arguably the most valuable find for LLM4POL.** It is the only large, genuinely redistributable, multi-property collection of *experimental* polymer data I located.

| Field | Value |
|---|---|
| Name | **polyVERSE** — "Informatics-Ready Polymer Datasets" |
| Maintainer | Ramprasad Group, Georgia Institute of Technology |
| Entries | See per-dataset table below — **~5,212 experimental gas-transport points alone**, plus ~10 further experimental property sets |
| Experimental? | **Mixed, and explicitly labelled per row** in most sets (`source` / `category` / `property` columns distinguish `exp` vs `sim`/`dft`) |
| Machine-readable | ✅ Plain CSV in git; also archived on Zenodo (DOI 10.5281/zenodo.13352644, v1.0.0, 21 Aug 2024) |
| Licence | **GTRC "General Public Use License Agreement"** (GitHub reports `NOASSERTION` — it is a custom, GPL-like copyleft). **"Program" is defined to include data**: *"GEORGIA TECH RESEARCH CORPORATION ("GTRC"), owner of all code, **data** and accompanying documentation (hereinafter "Program")"* |
| Cost | Free |
| URL | <https://github.com/Ramprasad-Group/polyVERSE>; <https://zenodo.org/records/13352644> |
| verified_by | **fetched** (repo tree + LICENSE via GitHub API, Zenodo record, and **every CSV below downloaded and row-counted**) |

**Licence — key verbatim clauses:**
> "1. In accordance with the terms and conditions set forth herein, this License allows you to: (a) **make copies and distribute copies** of the Program's source code provide that any such copy clearly displays any and all appropriate copyright notices and disclaimer of warranty as set forth in Article 5 and 6 of this License. All notices that refer to this License, the developers of this Program, and to the absence of any warranty must be kept intact at all times. A copy of this License must accompany any and all copies of the Program distributed to third parties."
> "At no time shall the program be **sold for commercial gain** either alone or incorporated with other program(s) without entering into a separate agreement with GTRC."
> "ii) any work that you distribute, publish, or make available, that in whole or in part contains portions of the Program or derivative work thereof, **must be licensed at no charge to all third parties under the terms of this License.**"

⇒ **Redistribution is expressly permitted.** It is **copyleft**: a republished benchmark containing polyVERSE data must itself carry this GTRC licence (it cannot be relabelled CC-BY or MIT), and it cannot be sold.

**Verified contents of `Other/` (I downloaded and counted every file):**

| Dataset | Rows | Properties | Exp vs sim |
|---|---|---|---|
| `Gas_permeability_solubility_diffusivity/master_transport_2025_08_13.csv` | **7,826** (⭐ **5,212 experimental** / 2,614 simulated; **1,184 unique polymers, 851 with experimental data**) | Permeability, diffusivity, solubility for He, H₂, O₂, N₂, CO₂, CH₄, H₂O — **34 property channels, 21 of them experimental** | Labelled per row (`p_exp_O2`, `s_sim_CH4`, …) |
| `Solvent_Diffusivity_Sorption_MTL_NCM/master_solvent_diffusivity_dataset.csv` | 3,044 | Solvent diffusivity vs. T and weight fraction | Has explicit `Experimental Selector` / `Simulated Selector` columns |
| `Solvent_Diffusivity_Sorption_MTL_NCM/master_uptake_sorption_dataset.csv` | 2,277 | Solvent uptake/sorption | — |
| `AM_hardness/only_exp_data.csv` | **2,480** | Hardness (with measurement load) | **100% experimental** (`category=exp`, `type=only_exp`) |
| `Conductivity_anionic_aging/aem_aging.csv` | 2,150 | AEM hydroxide conductivity vs. alkaline-ageing time, T, RH, IEC, additives | Experimental |
| `Melt_Viscosity/melt_viscosity_dataset.csv` | **1,959** | Melt viscosity vs. Mn/Mw/PDI/T/shear rate; 1,380 homopolymers, 446 copolymers, 133 blends; per-row literature `Source` | Experimental ⚠️ **3 rows cite "Polymer Database: PoLyInfo (nims.go.jp)"** — trivially removable |
| `chi_parameter/chi_parameter.csv` | **1,586** | Flory-Huggins χ for polymer–solvent pairs + temperature + **per-row reference DOI** | Experimental |
| `Conductivity_anionic_water_uptake_swelling/…csv` | 1,018 | AEM conductivity, water uptake, swelling | Experimental |
| `ROP_enthalpy/ROP-enthalpy-data-long.csv` | 459 | Ring-opening polymerisation enthalpy | Labelled: **109 `expt`** / 350 `dft` |
| `Organic_solar_cell/OSC_data.csv` | 422 | PCE, Jsc, Voc, FF + full processing metadata | Experimental (LLM-extracted from corpus) |
| `Conductivity_electrical/dataset.csv` | 398 | Electrical conductivity of doped polymers | ⛔ **PoLyInfo-derived** — README verbatim: *"The data were collected from the PolyInfo website"*. **EXCLUDE.** |
| `bandgap_chain` / `bandgap_crystal` / `Atomization_enthalpy` / `Electron_Affinity` / `Ionization_energy` / `charge_injection_barrier` / `Cohesive_energy_density` | 4,209 / 236 / 390 / 368 / 370 / 1,826 / 294 | — | **DFT/simulated** — exclude from an experimental benchmark |

**⚠️ OPEN DILIGENCE ITEM — must be closed before publication.** I could **not** fully verify the upstream provenance of the polyVERSE gas-transport experimental points (my #1 recommendation). The dataset README attributes them to *"Gas permeability, diffusivity, and solubility in polymers: Simulation-experiment data fusion and multi-task machine learning"* (npj Comput. Mater., 2024, doi 10.1038/s41524-024-01373-9) and to polyBERT, plus newly collected data. That paper is **403-gated at nature.com and not indexed in PMC or Europe PMC**, so I could not read its data-availability statement. *Indirect evidence that it is NOT PoLyInfo-derived:* (a) gas-permeability data in this field conventionally traces to the **Membrane Society of Australasia / Robeson** compilations, which is exactly what GREA states for its own `O2Perm` set; (b) the Ramprasad group **does disclose PoLyInfo provenance when it applies** — `Conductivity_electrical` says so explicitly — and the gas README does not. **Action: obtain the npj paper and read its data-availability statement before publishing a benchmark built on this set.** `verified_by: not verified — flagged`

**Verdict:** ✅ **YES — redistributable, subject to copyleft** (pending the diligence item above). The **χ-parameter set (1,586 rows with per-row DOIs)** is ~2.5× larger than PPPDB's and actually downloadable. The **gas-transport set (5,212 experimental points, 851 polymers, 21 experimental channels)** is the single best experimental multi-property table found anywhere in this survey. ⚠️ **Two required actions:** (1) drop `Conductivity_electrical` entirely; (2) drop the 3 PoLyInfo-sourced rows in `Melt_Viscosity`.

### 4.2 PPPDB (Polymer Property Predictor and Database, U. Chicago / CHiMaD)

| Field | Value |
|---|---|
| Name | PPPDB / 3PDB |
| Maintainer | Center for Hierarchical Materials Design (CHiMaD) — U. Chicago, Northwestern, Argonne; with NIST and AFRL. NIST project lead: Debra Audus |
| Entries | χ entry IDs run to **632**, but only **~263 χ rows and ~212 Tg rows are actually served** in the HTML tables (the rest appear retired/paginated); plus a Cloud Points database. Both carry source DOIs. Built with **ChemDataExtractor** — extraction paper: Tchoua, Chard, **Audus (NIST)**, Ward, Lequieu, de Pablo & Foster, *"Towards a Hybrid Human-Computer Scientific Information Extraction Pipeline"*, IEEE e-Science 2017 |
| Properties | χ (polymer–polymer and polymer–solvent), Tg, cloud points |
| Experimental? | Experimental values extracted from literature. ⚠️ The Tg page states verbatim: *"This data was automatically extracted as detailed in DOI: 10.1109/eScience.2017.23 and **still requires final verification**."* Built by a mix of **crowdsourcing** (χ) and **ChemDataExtractor NLP** (Tg). |
| Machine-readable | ❌ **HTML only.** No CSV export, no API. I probed `/api/chi`, `/chi/download`, `/chi.csv` → all **HTTP 404**. Individual entries at `/chi/entry/{n}`. |
| Licence | ⚠️ **No licence or terms-of-use statement anywhere on the site** (`/terms` → HTTP 404). US-government-adjacent funding does not itself confer a licence. |
| Cost | Free to view |
| URL | <https://pppdb.uchicago.edu/>, <https://pppdb.uchicago.edu/chi>, <https://pppdb.uchicago.edu/tg>, <https://www.nist.gov/programs-projects/polymer-property-predictor-and-database> |
| verified_by | **fetched** (all four pages + endpoint probes) |
| **Verdict** | ⚠️ **Free to view ≠ free to redistribute.** With no licence grant and no bulk download, scraping 632 rows and republishing them is legally unclear, and the Tg subset is self-declared unverified. **Better route: use polyVERSE's χ set (1,586 rows, explicit licence, per-row DOIs) instead — it supersedes PPPDB on every axis.** Worth an e-mail to Debra Audus (NIST) if PPPDB specifically is wanted; a NIST-affiliated resource may well be placeable in the public domain on request. |

### 4.3 Membrane Society of Australasia (MSA) polymer gas-separation database

| Field | Value |
|---|---|
| Name | MSA Polymer Gas Separation Membrane Database |
| Maintainer | Membrane Society of Australasia; built by **Aaron Thornton (CSIRO)** with Lloyd Robeson and Benny Freeman |
| Entries | ~**1,500** polymers, published 1950–2018 (`search-result-only`) |
| Properties | Experimental permeability for N₂, O₂, H₂, CH₄, CO₂ |
| Experimental? | ✅ Experimental |
| Machine-readable | ⚠️ Reported downloadable from the MSA portal, **but the database page now returns HTTP 404** (I probed `https://membrane-australasia.org/polymer-gas-separation-membrane-database/` → 404; site root → 200). The CSIRO landing page is live but lists no download link or licence. |
| Licence | **None visible anywhere.** |
| Cost | Free |
| URL | <https://research.csiro.au/virtualscreening/membrane-database-polymer-gas-separation-membranes/> (200); <https://membrane-australasia.org/> (200) |
| verified_by | **fetched** (CSIRO page + HTTP status probes); size figure `search-result-only` |
| **Verdict** | ⚠️ Historically important — it is the upstream source of GREA's `O2Perm` and feeds the polyVERSE gas set — but **the portal appears defunct and no licence is stated**. **Use polyVERSE's gas-transport set instead**, which contains this lineage under an explicit licence. |

### 4.4 CAMPUS, ATHAS, CROW, MatWeb, Polymer Handbook, Van Krevelen

**Headline: all six are "free (or cheap) to view" and NONE grants redistribution.** This is the cleanest demonstration in the whole survey that absence of a paywall is not a licence.

| Name | Maintainer | Entries | Properties | Exp vs derived | Machine-readable? | Licence (verbatim) | Cost | URL opened | verified_by | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **CAMPUS** | CWFG mbH (Chemie Wirtschaftsförderungs-Gesellschaft), Frankfurt; platform by M-Base | **4,862 unique datasheets** (counted from the live English sitemap, lastmod 2026-02-26); ~27 producers | ISO 10350 single-point (MFR, tensile, impact, Tm, Tg, permittivity, resistivity, water absorption, flammability) + ISO 11403 multipoint (stress–strain, viscosity, temperature curves) | **Experimental**, measured by the producer to binding ISO methods — but on **commercial filled/compounded grades**, not pure polymers | ❌ **HTML only; anti-scraping enforced.** *"CAMPUS does not offer any machine interfaces."* / *"If there is any indication of mass downloads or automatic access trials, the requester will be blocked from the system without further warning."* / *"The use of CAMPUS is restricted to personal consultation by qualified visitors."* | *"Contents of CAMPUS Content © Copyright CWFG, Frankfurt, 2020"*. No open licence. | Free to view | campusplastics.com sitemap + robots.txt + /campus/about + /campushome/coc; en.wikipedia.org/wiki/CAMPUS_(database) | **fetched** (sitemap count, robots.txt, Wikipedia); **search-result-only** (the three quoted restriction sentences + copyright line — site is a JS SPA that returns only a shell to non-browser fetches) | ⛔ **NO.** Explicit no-machine-interface + block-on-bulk policy; proprietary; per-producer rights. Also **wrong granularity** — commercial grades, not polymers. |
| **ATHAS Data Bank** | Founded B. Wunderlich (Univ. Tennessee Knoxville); chief editor now Marek Pyda (Rzeszów). **Now published by Springer Nature** | *"over 200 macromolecules and small molecules"*; the 1980 bank had *"almost 100 polymers"*; SpringerMaterials doc IDs run `athas_0008`…`athas_0152` | Cp(solid/liquid) 0–1000 K at 10 K intervals, enthalpy, entropy, Gibbs energy, **Tg, Tm**, ΔHf, ΔCp, vibrational spectra | ⚠️ **Mixed.** Critically reviewed *experimental* Cp, but solid/liquid Cp is also **computed** from vibrational spectra (Tarasov/Debye treatment) | ❌ No bulk download, no API; per-entry HTML behind a paywall | No open licence. Paywall: *"Don't have a subscription? … Request access"* | Institutional subscription; **no price published** ("request a quote") | materials.springer.com/polymerthermodynamics/docs/athas_0020; springernature.com librarian page; web.utk.edu/~athas via Wayback; www.prz.rzeszow.pl/athas | **fetched** | ⛔ **NO** for the compilation. See **Note B** — both free homes are dead; only the paywalled Springer copy survives. |
| **CROW Polymer Properties Database** | "Chemical Retrieval on the Web" (polymerdatabase.com) — **now defunct/parked** | Third-party GitHub mirror: **221 polymers × 57 columns** (raw TSV); 218 in the "tidy" CSV | Molar volume, density, solubility parameter, cohesive energy, **Tg**, molar Cp, entanglement Mw, refractive index | ⚠️ **Both, mixed per-cell.** Site states properties *"have been estimated by using similarity analysis and (linear) relationships … or have been predicted by using QSPR's"*. Populated **experimental** cells in the mirror: Tg 209, density 196, Vm 192, δ 119, Cp 73, Me 54, n 98 | Original HTML only → **now 404/parked**. Unofficial mirror: TSV + CSV on GitHub | *"Copyright © 2018 polymerdatabase.com"*; *"CROW (polymerdatabase.com) accepts no liability for use or misuse of the information contained herein."* **GitHub mirror `license: null`**; mirror README: *"I am not the owner of the data and have not changed any values."* | Was free to view | polymerdatabase.com (→ parking page); Wayback /about.html and /disclaimer.html; github.com/iszlobin/PolymerDataBase | **fetched** | ⛔ **NO.** No licence grant ever existed, rights-holder unreachable (**orphan work**), and data is silently part-predicted. Unsafe legally **and** scientifically — see **Note E**. |
| **MatWeb** | MatWeb, LLC (Blacksburg, VA) | *"Data sheets for **over 180,000** metals, plastics, ceramics, and composites"*; polymer subset not separately verified | Mechanical, thermal, electrical, optical, processing — vendor datasheet values | **Experimental**, vendor-reported, heterogeneous methods | Export exists (CSV, IQY/Excel, ANSYS/SolidWorks) but **hard-capped at 500 materials** | **The most explicit prohibition found anywhere.** Verbatim: *"You may not: … (b) **sell or redistribute the MatWeb™ materials database or its content**; (c) collect, organize or catalog … provided that such personal database shall **never be resold or released for public use and shall not contain more than 500 materials**; (d) sublicense, rent, lend, transfer, post, transmit, or otherwise make [it] available to anyone else; … (f) **mass export** the MatWeb™ materials database content; (g) **collect or download more than five hundred (500) materials**"* | Free tier; Premium **$99.95/yr**; enterprise custom quote | Wayback copies of matweb.com/reference/terms.aspx and /services/databaselicense.aspx (live site Cloudflare-gated, 403) | **fetched** (licence verbatim, 180k figure); **search-result-only** ($99.95) | ⛔ **NO — categorically.** Redistribution, public release, mass export, and any collection >500 materials are each separately banned **by name**. |
| **Polymer Handbook → Wiley Database of Polymer Properties** | Wiley (Brandrup / Immergut / Grulke) | *"over 2,500 polymers"*; *"initial content is derived from the Polymer Handbook"* | Full Polymer Handbook constant set: solution properties, thermodynamic, solid-state, transition data | **Experimental / critically selected literature** | A real database (DOI 10.1002/0471532053); custom tables *"may be viewed, printed, downloaded into other programs, or saved"* — **personal, subscriber-only** export | Proprietary Wiley, all rights reserved; no open licence | Institutional subscription (Wiley Online Library); Handbook also on Knovel | onlinelibrary.wiley.com/doi/book/10.1002/0471532053; wiley.com/WileyCDA/Section/id-301566.html — **both HTTP 403** | **search-result-only** | ⛔ **NO.** The closest thing to a digitized Polymer Handbook, but a commercial Wiley product with no redistribution right. |
| **Van Krevelen, *Properties of Polymers*** | D. W. van Krevelen & K. te Nijenhuis / Elsevier | Group-contribution increment tables + polymer tables (count not verified) | Group increments for Vw, Vm, Tg, Tm, δ, Cp, n, permeability, etc. | ⚠️ Mostly **derived/correlative** (group contributions), anchored to experimental values | ❌ **No machine-readable release found** (searched GitHub topics, HuggingFace, CRAN). Book only | Proprietary Elsevier, all rights reserved | Book / ScienceDirect subscription | sciencedirect.com/book/9780080548197 | **search-result-only** (negative result — absence could not be proven, only not found) | ⛔ **NO.** Nothing to redistribute, and the tables are copyrighted Elsevier content. Also largely *derived*, so a poor fit for an experimental benchmark regardless. |

**Note A — CAMPUS methodology caveat.** `campusplastics.com` is a JavaScript SPA; a non-browser fetch of `/campus/about` returns only a ~7.7 kB shell. The sitemap **was** fetched directly: 9,724 `<loc>` entries, each datasheet appearing twice (`/datasheet/…` and `/en/datasheet/…`) ⇒ **4,862 unique 16-hex datasheet IDs**. Worth flagging in any methods section: CAMPUS's `robots.txt` says `Allow: /` while its stated policy blocks bulk access — **robots permission is not a copyright licence**, and here the two directly contradict each other.

**Note B — ATHAS is an abandoned public resource that was privatized.** The archived UTK page states verbatim: *"Page has been moved to new address: http://www.prz.rzeszow.pl/athas"*. That address now returns **HTTP 000 / connection refused / 0 bytes**. Both free homes are gone; the surviving copy is the paywalled SpringerMaterials "Polymer Thermodynamics Database (ATHAS)". ⚠️ **`athas.org` is NOT the polymer database** — it is a Dark Sun / D&D fan site, and has been since at least 2000. **Do not cite it.** The only legitimate route to ATHAS numbers for a public benchmark is re-extraction from the primary literature (Wunderlich's JPCRD *"Heat capacity and other thermodynamic properties of linear macromolecules"* series; Pure Appl. Chem. **67**, 1019–1026, 1995) with citation — laborious, but the individual measured values in those papers are facts (§5).

**Note E — CROW is an active contamination hazard.** The widely-circulated GitHub mirror's `PolymerDataBase_tidy.csv` (218 rows) contains **only the calculated "preferred" values, not experimental ones**. Anyone grabbing that tidy CSV assuming it is experimental will be **benchmarking models against other models**. The raw TSV does separate them (cols 16–32 experimental, 35–55 calculated), with the sparse experimental coverage listed above (Cp only 73, Me only 54).

### 4.4b Afzal/Bicerano 315 — machine-readable, but a licence trap ⚠️

| Field | Value |
|---|---|
| Name | High-throughput MD polymer properties set (Afzal, Browning, Goldberg, Halls et al., **Schrödinger**), *ACS Appl. Polym. Mater.* **3**, 620–630 (2021) — the machine-readable Bicerano set |
| Entries | **315 rows.** Verified by download: **315/315 carry `Experiment Tg (K)`**; 117/315 carry `Experiment density at 300K (g/cc)` |
| Properties | Experimental Tg + experimental density; **plus** MD-calculated Tg, density, glass CTE, rubber CTE with std devs — **cleanly separated into distinct columns**; SMILES included (`[Ce]`/`[Th]` head/tail placeholders) |
| Experimental? | ✅ Experimental Tg (Bicerano's compiled values) alongside clearly-labelled MD companions. **The only resource in this survey where exp and calc are unambiguously column-separated.** |
| Machine-readable | ✅ `HT_MD_polymer_properties.csv` — on HuggingFace and in the ACS SI |
| Licence | ⚠️ **Upstream (authoritative) = ACS AuthorChoice CC BY-**NC-ND** 4.0** (Crossref licence URL for doi 10.1021/acsapm.0c00524). Downstream mirrors **contradict this**: `AdrianM0/bicerano_polymers` declares `license: mit`; `jablonkagroup/bicerano_dataset` says "CC BY 4.0" |
| Cost | Free |
| URL | <https://api.crossref.org/works/10.1021/acsapm.0c00524>; <https://huggingface.co/datasets/AdrianM0/bicerano_polymers>; <https://huggingface.co/datasets/jablonkagroup/bicerano_dataset> |
| verified_by | **fetched** |
| **Verdict** | ⚠️ **Qualified.** Neither mirror can grant rights the upstream author did not — **do not rely on the MIT / CC BY 4.0 relabels** (same failure mode as §2). **Prefer the Bhati route (§3.3), which is natively CC BY 4.0 and covers the same Bicerano lineage.** If this specific file is needed: publishing derived models is unproblematic; republishing the table rests on the facts/thin-compilation argument (§5) plus attribution to both Bicerano and Afzal et al. |

> **Note C — the recurring pattern.** Three separate times in this survey, a restricted upstream dataset was relabelled with a permissive licence downstream: PoLyInfo→GREA→PolyMetriX (§2), ACS-NC-ND→HuggingFace MIT/CC-BY (here), and CROW→unlicensed GitHub mirror (§4.4). **Treat any licence label on a re-upload as unverified until the upstream grant is confirmed.**

### 4.5 Bicerano's tabulated ~315-polymer set — **SOLVED**

The brief asked whether Bicerano's tabulated ~315-polymer set exists in machine-readable form. **Yes — in three places, of which one is cleanly licensed. Recommendation: use route 1.**

1. **Bhati 2026 Zenodo (§3.3)** — CC BY 4.0, 666 rows, of which **301 points originate from Bicerano** and the set comprises **315 homopolymers** + 351 binary copolymers. Direct CSV download. ✅ **This is the cleanest machine-readable Bicerano route.** `verified_by: fetched`
2. **Afzal et al. 2021 / Schrödinger `HT_MD_polymer_properties.csv`** — **315 rows, all 315 carrying `Experiment Tg (K)`**, plus clearly separated MD columns. This is the most complete and best-structured machine-readable Bicerano set, **but its upstream licence is ACS CC BY-NC-ND 4.0** and the HuggingFace mirrors relabel it inconsistently. See **§4.4b** and Note C. `verified_by: fetched`
3. **PolyMetriX documentation** states that four of its nine Tg sources — `Schrodinger`, `Liu`, `Mattioni`, `Wu` (labelled B1–B4) — *"all of which originated from the Bicerano handbook"*, and that the authors *"first corrected these sources"*. Useful as a cross-check, though in the final curated file these four contribute only 15 + 0 + 0 + 0 rows after deduplication. `verified_by: fetched`

> **Why route 1 (Bhati) wins:** it is natively **CC BY 4.0** on Zenodo with no upstream NC-ND encumbrance, it covers the same Bicerano lineage (301 of its 666 points), and it adds 351 binary copolymers that the homopolymer-only Bicerano table lacks.

### 4.6 Polymer Scholar (Ramprasad Group) — large, experimental, but no bulk download

| Field | Value |
|---|---|
| Name | Polymer Scholar 2.0 |
| Maintainer | Ramprasad Research Group, Georgia Tech (Gupta, Mahmood, Shetty, Adeboye, Ramprasad, 2024) |
| Entries | **24 properties of ~100,000 polymers**, extracted from published literature by LLM/NER (per PolyOmics Table S1) |
| Experimental? | ✅ **Experimental** (literature-extracted) |
| Machine-readable | ❌ **Bulk download: ABSENT** (PolyOmics Table S1 marks it `A`). Web search/visualisation UI only; no API advertised. |
| Licence | A `/usage-policy` page exists; content not captured. Site states *"If you use Polymer Scholar for your work, please cite the above papers"*; © Ramprasad Research Group 2024. |
| Cost | Free to view |
| URL | <https://polymerscholar.org/>; PolyOmics Table S1 (arXiv 2511.11626) |
| verified_by | **fetched** |
| **Verdict** | ⚠️ Largest experimental literature-extracted resource that actually exists as a service, but **no bulk access** ⇒ unusable as a hidden table today. **However**, its underlying pipeline is open (§5) — a group can regenerate equivalent data itself. |

---

## 5. Literature-extraction pipelines — the DIY route to a clean dataset

**This is the only route that scales to PoLyInfo size while remaining publishable.** Below, the tooling is verified; §5.2 gives the legal basis.

### 5.1 Available tooling

| Name | Maintainer | What it does | Released dataset | Machine-readable | Licence (verbatim/SPDX) | Cost | URL | verified_by |
|---|---|---|---|---|---|---|---|---|
| **MaterialsBERT / polyNLP pipeline** (Shetty & Ramprasad et al., *npj Comput. Mater.* **9**, 52, 2023) | Ramprasad Group, Georgia Tech | End-to-end NER pipeline: MaterialsBERT (trained on **2.4 million** materials-science abstracts) + property extraction. Verbatim: *"we obtained **~300,000 material property records from ~130,000 abstracts in 60 hours**"* | ⚠️ **The 300k records are NOT released as a file** — only explorable at polymerscholar.org. The annotated training set `PolymerAbstracts` **is** released | Model on HuggingFace (`pranav-s/MaterialsBERT`); code + `PolymerAbstracts` on GitHub | Code repo: **GTRC "General Public Use License Agreement"** (same copyleft as polyVERSE — redistribution permitted with notices, no commercial sale). Paper itself **CC BY 4.0** (Crossref, vor + tdm) | Free | <https://github.com/Ramprasad-Group/polymer_information_extraction>; PMC10073792; api.crossref.org/works/10.1038/s41524-023-01003-w | **fetched** (PMC full text + GitHub API + Crossref) |
| **ChemDataExtractor v2** | Cole group, Cambridge (Mavračić, Court, Isazawa, Cole) | General chemistry NER/toolkit; the standard literature-extraction engine. It is the tool **PPPDB used** to build its Tg set (§4.2) | Tool only | ✅ pip-installable | **MIT** — verbatim: *"ChemDataExtractor v2 is released under the MIT license… Permission is hereby granted, free of charge, to any person obtaining a copy… to deal in the Software without restriction"* | Free | <https://github.com/CambridgeMolecularEngineering/chemdataextractor2> | **fetched** (LICENSE via GitHub API) |
| **Polymer Scholar** | Ramprasad Group | Serving layer over the above — ~100k polymers × 24 properties | ❌ No bulk download (§4.6) | Web UI only | © Ramprasad Research Group 2024 | Free to view | <https://polymerscholar.org/> | **fetched** |
| **PolyLM** | Liu, Zhu, Xiong, Tang (2026) | LLM extraction at 276,400 samples / ~185,000 papers, 22 properties | ❌ Never released (§3.7) | — | Paper CC BY-SA 4.0 | — | <https://arxiv.org/html/2605.08255> | **fetched** |
| **NIMS / Ishii STAM-Methods series** | NIMS | PoLyInfo (I) overview, (II) machine-readable standardisation, (III) ShEx schemas for PoLyInfoRDF. Describe NIMS's own curation and RDF modelling — useful as a **schema blueprint** for your own database | PoLyInfo Ontology **CC BY 4.0** (§1.6); the data itself is not open | Ontology `.ttl` downloadable | Ontology: **CC BY 4.0**. Related earlier paper (CEUR Vol-2456 paper 18) also **CC BY 4.0** | Free | <https://mdr.nims.go.jp/concern/datasets/kw52jg498?locale=en>; <https://ceur-ws.org/Vol-2456/paper18.pdf> | **fetched** (ontology record + CEUR PDF); STAM (I)/(II)/(III) full texts **403-gated** |

### 5.1b ⭐ The Cole group precedent — the template to copy

**This is the single most actionable finding in §5.** The Cole group (Cambridge, authors of ChemDataExtractor) has for five years **openly redistributed literature-mined numbers at scale under CC BY 4.0 / MIT**, in peer-reviewed *Scientific Data* descriptor papers with figshare deposits. Licences verified via the figshare API.

| Database | Records | Licence | Size / DOI |
|---|---|---|---|
| **Stress–strain properties** (2024) — *most polymer-relevant* | **720,308 records from 382,227 articles** (UTS 294,277 · yield 215,958 · Young's modulus 157,287 · ductility 36,183 · fracture 16,579). PLA and ABS appear among the compounds | **CC BY 4.0** | `AllRecords.csv` 246 MB / `AllRecords.json` 552 MB; DOI 10.6084/m9.figshare.25881025 |
| Battery materials | 292,313 | **CC BY 4.0** | 569 MB |
| Refractive index + dielectric constants | 49,076 + 60,804 | **CC BY 4.0** | 146 MB |
| Semiconductor band gaps | 100,236 | **MIT** | — |
| Thermoelectric materials | 22,805 | **MIT** | 16 MB |

`verified_by: fetched` (figshare API for every licence; PMC11585639 for the stress–strain paper)

**Their stated legal basis is input-side only**, verbatim: Elsevier and Springer Nature *"have text and data-mining policies that allow for the mass scraping of scholarly articles"* through their APIs; *"Elsevier papers were downloaded via the ScienceDirect Search API V2, which is the … API provided by Elsevier for text and data mining purposes"*; *"2,733 papers were retrieved under copyright permission."*

> 🎯 **Two conclusions for LLM4POL:**
> 1. **The precedent is established and unchallenged.** A well-resourced group has deposited 720k literature-mined property records under CC BY 4.0 in a Springer Nature journal and nothing bad happened. That is the strongest practical evidence available that this route works.
> 2. **No polymer-specific ChemDataExtractor database has ever been published.** The stress–strain set touches polymers only incidentally. **This is an open, publishable niche that maps exactly onto what LLM4POL needs** — and it is the one path that reaches PoLyInfo-scale legitimately.

### 5.1c ⚠️ Quality reality-check on LLM extraction

The Ramprasad group's own benchmark (Gupta et al., *Commun. Mater.* **5**, 269, 2024 — >1,000,000 records, 24 properties, >106,000 unique polymers from 681,000 articles) reports verbatim: ***"GPT-3.5 achieved the highest F1 score of 0.67 for Tg"*** (MaterialsBERT 0.63, LlaMa-2 0.64; bandgap reached 0.85–0.87). `verified_by: fetched`

**Tg extraction is only ~⅔ precise-and-complete.** Auto-extraction alone is **not benchmark-grade** — budget for manual verification of any hidden table built this way. (That dataset is itself unusable regardless: browse-only, article CC BY-**NC-ND**, code under the GT academic-non-commercial notice.)

### 5.2 ⚠️ The practical blocker nobody mentions: publisher TDM licences

The polyNLP **Data availability** statement, verbatim:

> "The journal articles used to train MaterialsBERT and to extract material property data were **downloaded through licensing arrangements that Georgia Tech has with Elsevier, Wiley, Royal Society of Chemistry, American Chemical Society, Springer Nature, Taylor & Francis, and the American Institute of Physics.**"

`verified_by: fetched` (Europe PMC full text, PMC10073792)

**Implication for LLM4POL:** the bottleneck on the DIY route is **not** the NLP — the tooling is free and MIT/copyleft — it is **institutional text-and-data-mining agreements with the seven major publishers**. Before planning a large extraction effort, confirm what TDM rights the host institution's library already holds. Two mitigations if it does not:
- Restrict extraction to **open-access corpora** (PubMed Central OA subset, arXiv, ChemRxiv, MDPI, Nature Communications, RSC Gold OA) — smaller, but needs no negotiation and the outputs are unambiguously publishable.
- Note that **extracted facts are publishable even when the source article is not** (§5.3) — the TDM licence governs your right to *download and process* the articles, not your right to state the numbers you learned.

**What each publisher says about the OUTPUT (all `verified_by: fetched`):**

| Publisher | Position on publishing TDM output | Impact |
|---|---|---|
| **Elsevier** | ⭐ The most favourable statement found anywhere. Verbatim: *"**Who owns the copyright of my TDM output?** — **You do. We do not claim copyright over your TDM output (i.e., your extracted results).**"* and *"**Can I publish my findings in a journal?** — Yes. **There are no restrictions on where and how you can publish your TDM output.**"* ⚠️ But externally shared output carries *"© Some rights reserved. This work permits academic research purposes only…"* and corpus deletion is required at project end | ✅ Green light, with an academic-use rider |
| **Cambridge University Press** | *"Yes, you are welcome to share or publish any new information or knowledge generated by text and data mining of Cambridge Core content, **provided that you do so on a non-commercial basis**…"* | ⚠️ NC only |
| **Springer Nature** | "TDM Output" excludes *"any full-text duplication in whole or in part"*; output shareable *"for noncommercial use only"*; **has exercised the DSM Art. 4(3) opt-out** for non-OA content | ⚠️ NC only + opt-out |
| **ACS** | No self-service TDM — *"project by project… Principal Investigators should contact ACS"*. A Cranfield library guide records flatly *"NO. TDM is not permitted (March 2023)."* | ⛔ Highest friction |
| **Crossref** | Sets **no** terms on output (metadata relay only) | ✅ Free |
| **Wiley** | ❌ **Terms could not be retrieved.** Get the actual click-through licence before relying on anything about Wiley | ❓ Unknown |

> ⚠️ **The sharpest residual risk: "non-commercial only" vs CC BY.** Springer Nature and Cambridge both restrict output to non-commercial use, while **CC BY permits commercial reuse — and you cannot grant what your access licence forbids.** Either release the benchmark as **CC BY-NC**, or rely on the argument that those clauses bind the *corpus and verbatim snippets* but not the *uncopyrightable facts* (a good argument, but untested). Note the tension with §6.3: polyVERSE's copyleft and a CC-BY-NC release are mutually awkward — decide the target licence early.

### 5.3 Feasibility and legal basis

- **Feasibility is proven at scale.** Polymer Scholar reaches ~100k polymers × 24 properties; PolyLM reports 276,400 samples from ~185,000 papers; polyNLP produced ~300,000 records in **60 hours** of compute. All three are literature-extraction products, and all three exceed what any open experimental compilation offers.
- **Legal basis is the strongest available.** Individual measured property values are *facts*, and facts are not copyrightable in the US (*Feist v. Rural Telephone*). A database assembled by extracting facts from primary literature — rather than copying someone else's compilation — carries no inherited restriction. This is precisely why per-row-DOI datasets (rhnet, Brierley-Croft, polyVERSE χ) are the safest to republish.
- **The contrast with PoLyInfo is the whole point**: PoLyInfo's restriction is *contractual* (terms of use), not copyright in the underlying numbers. Extracting the same facts independently from the same primary papers does not breach that contract — **provided you never bulk-acquire them from MatNavi** (Art. 10(5)).

**The legal argument, stated precisely (not legal advice — have counsel confirm before publishing):**

| Layer | Protected? | Consequence for LLM4POL |
|---|---|---|
| An individual measured value ("Tg of PMMA = 378 K") | ❌ No — a fact. *Feist Publications v. Rural Telephone Service*, 499 U.S. 340 (1991): facts are never original to an author and cannot be copyrighted. | Values can be re-stated freely |
| A compilation of such values | ⚠️ Only the **selection/arrangement**, and only if original ("thin" copyright). Sweat-of-the-brow effort earns no protection in the US. | **Re-structure into your own schema**; never copy someone else's table layout, ordering, or curation choices wholesale |
| The *paper* the value was published in | ✅ Yes | Cite it; don't reproduce its text/figures |
| **A contract you agreed to in order to get the data** | ✅ **Binding regardless of copyright** | ⚠️ **This is the PoLyInfo trap.** Art. 10 binds you *because you clicked agree*, not because NIMS owns the numbers |

**Three practical rules that follow:**
1. **Never acquire from MatNavi in bulk.** The Art. 10(5) breach happens at *acquisition*, before you ever publish. This is the step that cannot be undone or cured by re-structuring.
2. **Independent re-derivation is clean.** If a value is extracted from the primary paper by your own pipeline, PoLyInfo's contract is simply not in play — you never obtained it from them. Same number, entirely different legal provenance.
3. **Per-row DOIs are the proof.** A dataset where every row cites its primary source is *self-evidencing*: it demonstrates independent derivation, enables third-party audit, and satisfies attribution. This is why **rhnet (276 DOIs)**, **Brierley-Croft** and **polyVERSE's χ set** are the strongest-footed resources in this report, and why the project should adopt per-row DOI provenance as a **hard requirement** for its own hidden table.

**Primary sources, verbatim (all `verified_by: fetched`):**

- ***Feist Publications v. Rural Telephone***, 499 U.S. 340 (1991): *"That there can be no valid copyright in facts is universally understood."* · *"the copyright in a factual compilation is thin. Notwithstanding a valid copyright, a subsequent compiler remains free to use the facts contained in another's publication to aid in preparing a competing work, so long as the competing work does not feature the same selection and arrangement."* ⇒ **A Tg, a modulus, a permeability is a measured fact. The numbers are not copyrightable in the US.**
- ***Authors Guild v. Google***, 804 F.3d 202 (2d Cir. 2015) — covers the *copying* step: *"the creation of a full-text searchable database is a quintessentially transformative use"* · *"The search engine also makes possible new forms of research, known as 'text mining' and 'data mining.'"*
- **EU DSM Directive 2019/790**: Art. 3(1) research-TDM exception for *"reproductions and extractions … by research organisations … to which they have lawful access"*; Art. 4(1) general TDM subject to the Art. 4(3) machine-readable opt-out; **Art. 7(1)** *"Any contractual provision contrary to the exceptions provided for in Articles 3, 5 and 6 shall be unenforceable"* — **protects Art. 3 from contract override, but not Art. 4.** ⚠️ Arts. 3/4 authorise only *"reproductions and extractions"* — the **input** side. The basis for publishing the *numbers* is **Recital 9**: *"Text and data mining can also be carried out in relation to mere facts or data that are not protected by copyright, and in such instances no authorisation is required under copyright law."*
- **Japan Copyright Act Art. 30-4(ii)**: permits exploitation *"in any way and to the extent considered necessary"* for *"data analysis (meaning the extraction, comparison, classification, or other statistical analysis of the constituent language, sounds, images, or other elemental data from a large number of works)"* — no opt-out, no research-institution limit. **Japan has the most permissive TDM regime of the three.**

🎯 **Key finding on PoLyInfo specifically — the EU database right does not help NIMS.** Directive 96/9/EC Art. 7(1) protects against *"extraction and/or re-utilization of the whole or of a substantial part"* of a database, **but Art. 11 limits beneficiaries to EU nationals/companies. NIMS, being Japanese, is not a beneficiary — and Japan has no equivalent *sui generis* right.** Combined with *Feist* (no US copyright in facts) and Japan's Art. 30-4, this means **PoLyInfo's numbers carry essentially no database-right or copyright protection anywhere relevant. Its protection is purely the click-through contract (§1.2).** That is precisely why the contract matters so much — and why *never agreeing to it, or never bulk-acquiring under it*, is the entire game.

⚠️ **Jurisdictional caveat for the project's own release:** *Feist* is US law; the EU *sui generis* right would apply to an EU-originated compilation; **Japan** protects databases original by selection or systematic construction (Art. 12-2). **Route 2 (independent extraction with per-row DOIs) is robust in every jurisdiction; route 1 (re-structuring someone else's compilation) is not.**

**Residual risks, stated honestly:**
1. **"Non-commercial only" clauses vs CC BY** (§5.2) — the likeliest thing to bite.
2. **Volume and shape.** One value is a fact; 10⁵ values in the same fields and scope as a commercial database starts to look like a "substantial part" in the EU, or like Elsevier's prohibition on output that would *"compete with or … substitute"* for its products.
3. **Contract survives *Feist*.** Click-through TDM licences and MatNavi's terms are contract law; copyright answers do not reach them (except DSM Art. 7(1), and only for Art. 3).
4. **Nobody has litigated the output side.** The field's *practice* is confident (§5.1b); its *stated reasoning* is thin — across four Cole-group *Scientific Data* papers the justification is entirely input-side, with *Feist* assumed and never argued.
5. **Zenodo pushes risk to you**, verbatim: *"The uploader is exclusively responsible for the content that they upload… and shall indemnify and hold CERN free and harmless."*

> *Not legal advice.* Run this past KAIST's library / scholarly-communications office — **they hold the actual subscription and TDM contracts that bind you**, and those contracts, not copyright, are the operative constraint.

---

## 6. Recommendation: what LLM4POL should actually do

### 6.1 The legally-publishable set — options that carry NO licensing problem

| Rank | Resource | Size (experimental) | Licence | Redistribute? |
|---|---|---|---|---|
| 1 | **polyVERSE** (gas transport + χ + hardness + melt viscosity + AEM + ROP + OSC) | **14,933** clearly-experimental points (breakdown below) + up to 5,321 more in mixed exp/sim solvent sets | GTRC General Public Use License (copyleft, non-commercial-sale) | ✅ yes, with copyleft |
| 2 | **rhnet** gas solubility | **16,004** pts; 107 polymers × 81 solvents/gases; **276 source DOIs** | MIT | ✅ yes |
| 3 | **OpenPoly** | **3,985** pts over 741 polymers, 26–28 properties | MIT | ✅ yes |
| 4 | **Bhati** copolymer Tg | **666** pts (incl. the Bicerano 315 lineage) | CC BY 4.0 | ✅ yes |
| 5 | **PolymerSolarCellsML** | **3,910** rows (OPV: PCE, Voc, Jsc, FF), **per-row DOIs** | **MIT** | ✅ yes |
| 6 | **Brierley-Croft** PAEK Tg | **146** pts | CC BY 4.0 | ✅ yes |

**polyVERSE experimental subtotal (each figure counted by me):** gas transport 5,212 + hardness 2,480 + AEM ageing 2,150 + melt viscosity 1,956 *(1,959 − 3 PoLyInfo rows)* + χ 1,586 + AEM uptake/swelling 1,018 + OSC 422 + ROP 109 = **14,933**. *Excluded:* `Conductivity_electrical` (398, PoLyInfo) and all DFT sets. *Partly usable:* solvent diffusivity 3,044 + uptake/sorption 2,277 = 5,321, which carry explicit `Experimental Selector` / `Simulated Selector` columns and need filtering.

> **Total cleanly-redistributable experimental inventory: 39,222 measured data points**, across **~38 distinct properties**:
>
> | Component | Points |
> |---|---|
> | polyVERSE (14,933 − 422 OSC rows superseded by PolymerSolarCellsML) | 14,511 |
> | rhnet | 16,004 |
> | OpenPoly | 3,985 |
> | PolymerSolarCellsML | 3,910 |
> | Bhati | 666 |
> | Brierley-Croft | 146 |
> | **Total** | **39,222** |
>
> Rising toward **~44,500** if polyVERSE's mixed exp/sim solvent sets (5,321 rows) are filtered and the experimental portion included.
>
> That is **~7.1% of PoLyInfo's 552,427 data points** — but it is **100% publishable**, which PoLyInfo's is not. For a benchmark, breadth of *properties* (~38) matters more than raw row count, and on that axis this composite is already comparable to PoLyInfo's ~100. **With a DIY extraction pipeline (§5) the ceiling is far higher** — the Cole group's single stress–strain deposit holds 720,308 records under CC BY 4.0.

### 6.2 Explicitly flagged as NOT publishable

⛔ PoLyInfo · ⛔ PolyMetriX curated Tg (97.3% PoLyInfo) · ⛔ polyVERSE `Conductivity_electrical` (PoLyInfo) · ⛔ GREA GlassTemp/MeltingTemp/PolyDensity (PoLyInfo) · ⛔ PI1M as a labelled set (PoLyInfo-seeded + contradictory licence) · ⛔ Jeong PFAS (CC BY-**NC-ND**) · ⛔ Khazana (no licence) · ⛔ PPPDB (no licence, no bulk download) · ⛔ Zhou 2026 & PolyLM (never released) · ⚠️ Kaggle NeurIPS 2025 (MD-simulated + unverifiable licence)

### 6.3 Suggested architecture for the hidden table

1. **Spine:** polyVERSE gas-transport (851 polymers × 21 experimental channels) — the closest thing to CoRE-MOF's structure: many materials × many measured properties, per-row exp/sim labelling.
2. **Breadth:** OpenPoly (26 properties) for multi-property coverage; rhnet for solubility depth.
3. **Tg task:** Bhati + Brierley-Croft (812 clean points) — **deliberately excluding** the tempting 7,367-row PolyMetriX set.
4. **Licence of the published benchmark:** must be the **GTRC copyleft** if polyVERSE is included. If a CC-BY benchmark is required, **drop polyVERSE** and build on rhnet + OpenPoly + Bhati + Brierley-Croft (MIT + CC BY are compatible with CC BY-SA-style release).
5. **Growth path — follow the Cole template exactly** (§5.1b). This is the only route to PoLyInfo-scale that remains publishable:
   - **Tool:** ChemDataExtractor v2 (MIT) and/or an LLM pipeline. Benchmark extraction accuracy against **PolyIE** (Apache-2.0).
   - **Input:** publisher TDM APIs where KAIST holds agreements; otherwise OA corpora (PMC OA, arXiv, ChemRxiv, MDPI, Nature Communications, RSC Gold OA).
   - **Schema:** copy **rhnet's** — polymer name + PSMILES, property, value, unit, measurement conditions, **`doi`** — plus a reliability grade in the style of PolyMetriX's black/yellow/gold/red. **Ship values and DOIs only: no sentences, no snippets, no figures.** That preserves the clean *Feist* argument and keeps you clear of every publisher's full-text-duplication prohibition.
   - **Output:** figshare or Zenodo deposit under CC BY 4.0 (or CC BY-NC if Springer Nature / Cambridge content is in the corpus — see §5.2), with a *Scientific Data*-style descriptor paper.
   - **Budget for manual verification.** LLM Tg extraction tops out near **F1 = 0.67** (§5.1c); auto-extraction alone is not benchmark-grade.
   - **Record per-row provenance and access route** so a subset can be withdrawn surgically if a publisher ever objects.
6. **Reuse PoLyInfo's *schema*, not its data.** The PoLyInfo Ontology (CC BY 4.0) and the ShEx schemas (MDR, open) are freely usable (§1.6) — NIMS open-sourced the structure while keeping the values closed. Adopting their data model costs nothing legally and buys interoperability.

---

## 7. Known gaps and open items

All sections are complete. Remaining uncertainties, stated plainly:

| # | Open item | Why it matters | How to close it |
|---|---|---|---|
| 1 | **polyVERSE gas-transport upstream provenance not verified** (§4.1) | This is the #1 recommended resource. If it turned out to be PoLyInfo-derived, the spine of the recommendation would move to rhnet. Indirect evidence says it is not. | Read the data-availability statement of npj Comput. Mater. doi **10.1038/s41524-024-01373-9** (403-gated to me; an institutional login will open it) |
| 2 | ✅ **CLOSED** — STAM-Methods PoLyInfo (I) and (II) were obtained as CC-BY PDFs via the NIMS MDR mirror and parsed. The "open-access vs authenticated / under a certain contract" wording is now **verbatim and `fetched`** (§1.6) | — | Done |
| 2b | **Wiley TDM terms could not be retrieved at all** (§5.2) | Wiley is one of the seven publishers in the polyNLP corpus; its output-side position is unknown | Obtain the actual Wiley click-through TDM licence before relying on anything about it |
| 3 | **NIMS contract terms unknown** (§1.6) | A contract route for *use* appears to exist; whether it ever permits redistribution is unknown (§1.5 suggests not) | One e-mail to `dice_help@nims.go.jp` — cheap to try, low expected value |
| 4 | **CAMPUS restriction sentences are `search-result-only`** (§4.4 Note A) | The site is a JS SPA that returns only a shell to non-browser fetches | Open in a real browser if CAMPUS is ever seriously considered (it should not be — wrong granularity) |
| 5 | **Zhou 2026 counts unverified** (§3.6) | Paywalled; no data deposit found | Institutional Elsevier access — but with no data deposit, the dataset is unusable regardless |
| 6 | **OpenPoly has no per-row source DOIs** (§3.8) | Weakens auditability of an otherwise ideal resource | Spot-audit a sample against the primary literature before adopting |
| 7 | **Van Krevelen machine-readable absence is a negative result** (§4.4) | Could not prove absence, only failed to find | Low priority — the tables are derived/correlative anyway |

**Methodological note.** Three independent research lanes ran in parallel. Where they disagreed, this document reports the **independently re-verified** figure and says so: the PolyMetriX recommendation was **overridden** on provenance grounds (§2.3), and the OpenPoly count discrepancy was **resolved by direct cell-counting** (§3.8). Row counts for polyVERSE, OpenPoly, PolyMetriX, rhnet and Bhati were obtained by downloading the files and counting, not by trusting stated figures.

---

## Appendix A — Evidence index

| Claim | URL | verified_by |
|---|---|---|
| PoLyInfo size, 29 May 2025 | <https://polymer.nims.go.jp/> | fetched |
| MatNavi Terms Art. 1/9/10/13 verbatim | <https://mits.nims.go.jp/agreement/MatNavi_agreement_en.pdf> | fetched (PDF text-extracted) |
| 2024-08-01 amendment scope | <https://dice.nims.go.jp/news/2024/08/20240801-2-en.html> | fetched |
| Registration rules, individuals only | <https://dice.nims.go.jp/usage.html> | fetched |
| "could not be redistributed" precedent | arXiv 2511.11626 (PolyOmics) | fetched (PDF) |
| PolyOmics Table S1 database survey | arXiv 2511.11626 | fetched |
| PoLyInfo Oct-2023 snapshot | arXiv 2505.13494 | fetched (PDF) |
| PoLyInfo Ontology CC BY 4.0 | <https://mdr.nims.go.jp/concern/datasets/kw52jg498?locale=en> | fetched |
| PoLyInfoRDF authenticated / "certain contract" / 24,593,403 triples | STAM-Methods PoLyInfo (II), doi 10.1080/27660400.2024.2354651 | search-result-only (403 on direct fetch) |
| GREA → PoLyInfo, verbatim | arXiv 2206.02886 Appendix A | fetched (PDF) |
| PolyMetriX sources incl. GREA | <https://raw.githubusercontent.com/lamalab-org/PolyMetriX/main/docs/datasets.md> | fetched |
| PolyMetriX Zenodo CC BY 4.0 | <https://zenodo.org/records/15210035> | fetched |
| PolyMetriX 7,367 rows / source & reliability counts | CSV downloaded from Zenodo | fetched (counted) |
| polyVERSE licence (data included in "Program") | GitHub API `/repos/Ramprasad-Group/polyVERSE/license` | fetched |
| polyVERSE per-dataset row counts | raw.githubusercontent.com CSVs | fetched (counted) |
| polyVERSE Zenodo record | <https://zenodo.org/records/13352644> | fetched |
| OpenPoly MIT + 741×3,985 | GitHub API + CSV counted | fetched |
| Bhati CC BY 4.0 + 666 rows | <https://zenodo.org/records/19242815> + CSV counted | fetched |
| Brierley-Croft CC BY 4.0 + 146 rows | <https://archive.researchdata.leeds.ac.uk/1431/> | fetched |
| Jeong CC BY-NC-ND | <https://www.nature.com/articles/s41467-024-55320-9> | fetched |
| Kaggle "All properties are obtained through MD simulations" | <https://arxiv.org/html/2512.08896v1> | fetched |
| PPPDB 632 χ entries; no download/terms (404s) | <https://pppdb.uchicago.edu/chi>, `/tg`, `/terms` | fetched |
| Khazana no licence, DFT | <https://khazana.gatech.edu/dataset/> | fetched |
| MSA database page 404 | <https://membrane-australasia.org/polymer-gas-separation-membrane-database/> | fetched (HTTP probe) |
