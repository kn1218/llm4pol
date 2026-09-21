# LLM4POL PORTING MAP — LLM4MOF → 고분자 이식 논의자료

**작성** 2026-09-11 · **수신** LLM4MOF PI/lead · **성격** 논의자료(discussion material), 결정문서 아님.
**입력** `LLM4MOF-ANATOMY.md`(+ fact-check C1–C25 / E1–E11), `POLYMER-LANDSCAPE.md`(+ citation-check REF-101…153), 세 전략서 S1/S2/S3, `BOOTSTRAP-REPORT.md`(+ independent verify), `DATA-FOUNDATION-REPORT.md`, `LLM4Polymer_Research_Proposal.md` v1.0(입력물, 승인된 진실 아님), 3-lens judge panel(reviewer / engineer / scientist).
**표기** 검증 패킷에서 `confirmed`인 수치만 사용. `refuted`(C5·C8·C22, REF-105·REF-112·REF-134·REF-140)는 교정된 형태로만 인용. 추정치는 [EST]로 표시.

---

## 1. LLM4MOF 한 장 요약

1. **루프**: 고정 10 iteration, early stopping 없음. iteration 당 Agent 1 → Agent 2 → Matchmaker → beam 샘플링 → 평가 → feedback (C1).
2. **주의**: DB mode에서 zero-match iteration은 **재시도되지 않고 10회 중 1회를 소모**한다. SI는 무조건 재시도라고 쓰지만 그 규칙은 discovery mode에만 적용된다 (C1 caveat / E5).
3. **Agent 1** — stateful(multi-turn), T=0.0, 8-field strict JSON 중 4개만 코드가 검증 (C2).
4. **Agent 2** — stateless, T=0.0, `node_query` / `linker_query` / `global_requirements` / `geometry_filter` 출력, `linker_branches`는 OR-of-ANDs, 검증은 soft (C3).
5. **Vocabulary** — 124 canonical tags / 10 categories / 215-entry alias map(런타임 로더는 183개 구성) + 105 curated SMARTS (C4).
6. **Beams(4개)** — Z 전체 가설(chemistry ∩ 수치 gate) / A chemistry only / F primary identity only / R 전체 테이블 random. DB mode 정의는 코드로 확인됨 (C6).
7. **인접 비교로 귀속**: 1vs2 = 수치 window, 2vs3 = linker chemistry, 2vs4 = chemistry vs chance. **자동 귀속 통계는 루프 안에 없다** — agent가 텍스트로 읽고 저자가 그림으로 읽는다.
8. **beam 당 노출** ≤10개 → 10×4×10 = **400 labels/campaign** (C7). DB는 metal-stratified random sample, live는 `nlargest(10,'target')` (C7).
9. **plot되는 beam median은 matched set 전체**의 median이고 그 크기는 요동친다: 기록된 캠페인 iteration 10에서 Z 43 / A 257 / F 3,591 / R 9,533, iteration 1에서 Z 1 / A 1 / F 3 (C23).
10. **Ledger** — `global_best`, top-10 frontier, geometry envelope, iteration history. **random beam도 `beam_medians`·outside-promising 용도로는 ingest된다**; frontier/best/envelope만 3개 가설 beam으로 제한 (C8 교정).
11. Agent 1에게는 `render_facts_only`만 보여준다. 지시형 renderer는 rare-peak task에서 **성능을 해쳐서** 폐기됨 (C8).
12. **Transcript는 압축되지 않는다.** `multi_turn=True`가 전체 대화를 매번 재전송하며 trim/window/eviction이 없다 — ledger는 무한 transcript 위의 **추가물**이지 대체물이 아니다 (E4). Note S11 ablation은 "full history 위의 ledger"를 측정한 것.
13. **Oracle(DB mode)** — 시뮬레이션 0회, hidden table lookup.
14. **Oracle(discovery)** — PORMAKE → LAMMPS/UFF → Zeo++ → RASPA3 GCMC 5,000 init + 5,000 production, 12.8 Å cutoff, PBS job array, `.DONE` sentinel (C11, C24).
15. **Discovery 생성량** — iteration 당 100(Z) + 30×3 = 190 build/relax/Zeo++, GCMC는 beam 당 ≤10 (C12).
16. **MOF2Zeo** — 545,107/84,228 학습, 평균 R² 0.99. **Beam 1 pre-rank 전용이며 gate는 항상 재계산된 Zeo++ 값** (C10). 이것이 비순환성을 지키는 유일한 장치.
17. **DB mode는 MOF2Zeo를 전혀 쓰지 않는다** — surrogate 없는 순수 lookup.
18. **비용** — campaign 당 정확히 2 model calls/iteration, ~0.57 M tokens, **$1.06 ± 0.05**, 380 ± 2 RASPA (C12). 5개 replicate 중 2개는 22 calls(비생산 iteration 재시도, E10b).
19. **DB campaign wall-clock** — 10-iteration 평균 **353 s** (n=160, median 348, range 247–492) (C23).
20. **성과(discovery, budget-matched)** — H₂ 77 K/5 bar iteration-10 median: LLM4MOF 29.3 / GA 21.8 / BO 17.7 / random 14.3 g/L; 실현 예산은 GA 327–368, BO 212–265 vs 380±2 (C13).
21. **성과(DB, enrichment)** — 8개 task에서 4.3×–18×, CH₄에서 162×이나 그 baseline은 **500개 중 1 hit** (C16) — 비율만 인용하면 안 되는 수치.
22. **Backend 비민감성** — 6 backends × 7 tasks × 5 reps: 91.3 / 91.3 / 91.2 / 86.7 / 86.6 / 79.5, no-match 2.3–34.9% (C14).
23. **Design space(discovery)** = Σ_c n_c·t_c·L = 80,126 × 156 = **12,499,656**. 518×156×952 = 76,929,216은 **6.2× 과대**이며 SI의 수치가 아니다 (C5 refuted). 이식 시 이 공식을 그대로 베끼면 안 된다.
24. **저장소 상태** — 신규 clone(5adb33e)은 matchmaker init과 live runner import가 모두 실패하고, 구 clone(f1d731a)은 정상 import되며 battery harness(`run_battery.py` 233 l. + `parse_results.py` 213 l.)를 갖고 있다. 두 history는 무관하다 (C17, E2).
25. **미구현** — Table 1의 Claude arm 3개를 만든 provider branch가 `llm_client.py`에 **없다** (C18); env toggle 이름이 clone 간 불일치 (C19).

---

## 2. Polymer 분야 landscape 요약 — 컴포넌트별로 무엇이 이미 있는가

| LLM4MOF 컴포넌트 | 고분자 쪽에 존재하는 것 | 존재하지 않는 것(= 우리가 만들 것) |
|---|---|---|
| RASPA3 GCMC (초 단위 oracle) | 없음. Tg의 all-atom MD 등가물은 **candidate 당 4,000–20,000 CPU-h**, 계통 오차 **+40~+120 K** | 값싼 물리 oracle. density만이 유일하게 싸고(≈1일/32 core) 정량 검증됨(R² 0.890 vs PoLyInfo) |
| Zeo++ (결정적·비target descriptor) | RDKit + van Krevelen group contribution. **pip 구현 없음** | 검증된 van Krevelen/Bicerano 테이블 구현 |
| MOF2Zeo (property-agnostic pre-ranker) | polyBERT / polyGNN / PolyFusion 등 surrogate — 그러나 **전부 target을 예측**하므로 label-free 주장이 깨짐 | property-agnostic pre-ranker. SimPoly-class MLFF가 유일한 후보(미검증) |
| PORMAKE 조립 공간 | **SMiPoly**(22 rules, 1,083 monomers → 169,347 polymers, BSD-3), **OMG**(17 reactions → ~12 M CRUs, GPL-3), VFS/pvfsga(>7 M ROP) | copolymer 열거(monomer pair × composition grid × architecture) — 셋 다 homopolymer-first |
| 124-tag 통제 어휘 | **없음**. PoLyInfo ontology(CC BY 4.0), HAPPY/FORGE subgroups, PolyBench-LLM SME descriptor가 seed | 고분자 design-tag 어휘 자체가 기여물 |
| 4-beam 통제 귀속 | **없음**. 2024–26 고분자 agent 13종 중 controlled-arm attribution을 하는 시스템 0개 | 전부 |
| 해석가능성 | 전부 post-hoc SHAP / attention / Integrated Gradients | 사전 통제 arm으로 분해하는 방식 |
| 도메인 baseline | Fox 식(PoLyInfo copolymer에서 R² 0.835 / RMSE 42.6 °C), GC(in-sample MAE ≈10 K, out-of-sample R² 0.71) | LLM4MOF에는 없던 "reviewer가 반드시 요구할" baseline |
| 검증 관행 | 2025–26 Nature-portfolio 고분자 inverse-design 논문은 **전부** 합성 1종 또는 MD 검증을 포함 | 우리의 검증 채널 결정 |

**의사결정에 직접 영향을 주는 12개 reference**

| # | Ref | 무엇을 결정하는가 |
|---|---|---|
| 1 | **REF-101 RadonPy** (npj Comput. Mater. 8:222; BSD-3; LAMMPS≥3Mar20 + **Psi4≥1.5**) | 현재 릴리스에 Tg preset(`sim/preset/tg.py`)과 random/alternating/block copolymer builder가 **있음**(2022 논문엔 없었음). Psi4가 pip 불가라는 점이 최대 설치 리스크 |
| 2 | **REF-104 Afzal 2021** (315 polymers) | MD Tg 평균 **+79.1 K** 과대, slope 1.30, 보정식 Tg = 0.77·Tg_calc + 21.08 K. density R² 0.95 |
| 3 | **REF-110 Suter 2025** | **≥10 replica라야 95% CI < 20 K**. 3 replicate면 ±35–45 K [EST] — MD로 40 K 미만 차이를 주장할 수 없다 |
| 4 | **REF-106 Gudla & Zhang 2024** | MD Tg 과대추정 "평균 80–120 K" — 절대값은 못 쓰고 순위만 쓸 수 있다 |
| 5 | **REF-117 SMiPoly** (BSD-3) / **REF-116 OMG** (GPL-3) | PORMAKE 등가 설계공간. 라이선스가 릴리스 정책을 결정(OMG는 copyleft 전염) |
| 6 | **REF-113 van Krevelen 4th ed.** + **REF-146 Kaggle 전사**(−CH₂− 158, p-phenylene 2820, −SO₂− 2150, −NHCO− 1510) | 태그 단위 **수치 귀속 ground truth**. pip 구현 없음, 전사본은 책 대조 미완 → critical path 리스크 |
| 7 | **prior-art REF-26 Fox on PoLyInfo copolymers** (R² 0.835 / RMSE 42.57 °C vs 최고 GNN 0.921 / 24.45) | Fox를 경쟁자로 두면 진다. residual objective로 돌려야 null model이 된다 |
| 8 | **REF-136 CI-LLM / HAPPY** (arXiv:2512.06301) | 가장 가까운 해석가능성 경쟁자(subgroup + Integrated Gradients). pre-proposal Related Work에 **누락**되어 있음 |
| 9 | **REF-124 Zhou 2026 CEJ** (copolymer LLM 추출 1,195 entries, 생성 2,052종, **MD 8종 검증 4.17% 오차**) | copolymer inverse design + MD top-k 검증의 현재 표준선 |
| 10 | **REF-103 SPACIER** (RadonPy + BO, **합성된** 광학 고분자) | MD-in-the-loop 설계의 유일한 선례이자 BO baseline의 근거 |
| 11 | **REF-102 PolyJarvis** (Claude orchestrator + 13 workers; 9 homopolymer, Tg 50 K 이내 7/9) | LLM이 MD를 몰 수 있다는 증명이자, homopolymer 전용이라는 한계 |
| 12 | **REF-137 Dangayach 2025** | pre-proposal이 "single-surrogate PFAS 시스템"으로 인용했으나 **review 논문**이다. Related Work의 foil을 교체해야 함 |

PFAS 관련 결론: **공개된 SMILES-labelled 고분자 흡착제 PFAS 데이터셋은 존재하지 않는다.** 구조화된 대안은 457 points(21 PFAS × 16 polyamide 막)와 43-PFAS 수지 스크리닝(bulk descriptor)뿐이다.

---

## 3. 컴포넌트별 이식 맵 (3개 전략 합의표)

범례: **PORT-AS-IS**(복사 후 문자열만 교체) · **ADAPT**(형태 유지, 내용 교체) · **REPLACE**(인터페이스만 유지) · **DROP** · **NEW**.
Agreement: **unanimous**(3/3) · **majority**(2/3) · **contested**(3안 갈림).

| # | LLM4MOF component | Polymer equivalent | Action | Agreement | Note |
|---|---|---|---|---|---|
| 1 | Agent 1 handler (242 l., multi-turn, T=0) | 동일 handler, 8-field JSON 유지 | PORT-AS-IS (handler) / ADAPT (prompt) | unanimous | prompt의 axis menu·stagnation trap·COMMIT-to-REDUCE 골격은 유지. 단 prompt가 결론 절차를 지시한다는 결합(weakness #12)은 **공개**해야 |
| 2 | Agent 2 handler (345 l., stateless, soft validation) | `{DATABASE_MODE_RULES}` → HOMO/COPO(또는 P1–P5) rule block | ADAPT | unanimous | default-permissive + structured-error halt (E9a/b)는 의도적으로 구현할 것 |
| 3 | Controlled vocabulary (124 tags / 215 aliases / 105 SMARTS) | 고분자 태그셋 | REPLACE(내용) + PORT-AS-IS(machinery) | unanimous on action, contested on size | S1 ~114/10 cat · S2 85–105/10 cat · S3 ~95/8 cat. `readable_name` 부분문자열 bouncer는 **버릴 것**(LLM 생성 필드로 필터링) |
| 4 | `matchmaker.py` PORMAKE 조립 경로 (668 l.) | — (Phase 1) / 생성형 CopolymerMatchmaker | DROP (S1, Phase 1) vs REPLACE-with-generator (S2 즉시, S3 M8 gated) | contested | S1: 조립 등가물 없음 → Phase 3 템플릿으로 보관. S2: pool 선택을 버리고 생성으로 전환. S3: DB 우선, 생성은 gate 뒤 |
| 5 | `hmof_matchmaker.py` (341 l.) 레코드 필터 | `copolymer_matchmaker` / `homopolymer_matchmaker`, `search_mode ∈ {full, backbone_only, sidegroup_only}` | ADAPT | unanimous | **이것이 진짜 이식 대상**이다. `matchmaker.py`가 아니라 이쪽이 템플릿 |
| 6 | Building-block library (518 nodes × 156 linkers) | 4,792 CSV monomer SMILES(4,782 valid, 4,666 backbone) + 13,624 XLSX repeat unit | REPLACE | unanimous | key는 trimer ring-closed key(stereo 분리) — periodic key는 5+2+1쌍을 잘못 병합 |
| 7 | Topology library (952 topologies) | architecture tag 6–7종(random/alternating/block/graft/statistical/periodic) | REPLACE(역할 재배치) | unanimous | 952 → 7. 그래서 설계공간은 **rule-matched sum**이지 product가 아니다 |
| 8 | hMOF / QMOF hidden tables | COPO-Tg(13,350 rows / 2,735 ids) / HOMO-Tg(13,725 rows, Tg 7,733) | ADAPT | unanimous | QMOF↔homopolymer(합성된 실물, 집계규칙 불명), hMOF↔copolymer(대형·noisy·coverage 제한) 대응이 정확 |
| 9 | **MOF2Zeo** (geometry surrogate, triage 전용) | S1: Phase 1 DROP / S2: **PolyNet-G**가 G=(ρ,CED,FFV,C∞) 예측 / S3: **PolyRank**가 target 예측 | contested | contested | 핵심 분기점. S2만이 "gate는 target이 아니다"라는 모(母)논문의 불변식을 구조적으로 보존. S3의 PolyRank는 target을 예측하므로 label-free 주장이 깨짐(S3 스스로 인정) |
| 10 | Zeo++ 7-descriptor gate | S1: rigidity/arom_frac/ecoh_vk/ffv_proxy/hbond_density/mw_ru/sidechain_len · S3: 동일 계열 7개 중 `tg_gc`는 표시하되 **gate 제외**(6개만 gate) · S2: G=(ρ,CED,FFV,C∞)를 MD가 재계산 | REPLACE | contested | arity 7을 지키면 `geometry_filter` JSON·MAE-slack·ledger envelope·feedback 컬럼이 그대로 이동한다는 점은 합의 |
| 11 | 4 beams (Z/A/F/R) | 전체가설 / chemistry only / **backbone class only** / random(backbone-class-stratified) | ADAPT | unanimous | 축 대응(metal→backbone class, linker chem→side group+comonomer, geometry→descriptor+composition window)이 3안 동일 |
| 12 | Beam 3의 geometry_filter 잔존 (C25) | 양쪽 mode에서 제거 | FIX | unanimous | 공개된 비일관성을 재현할 이유 없음 |
| 13 | Beam 1 fallback 충전 (C25) | 채우지 않거나 별도 `Z_fallback`으로 분리 | FIX | unanimous | "Beam 1 = 전체 가설"이 거짓이 되는 것을 막음 |
| 14 | 인간 전용 sensitivity sets B..S | 동일 + composition-only / chem+composition set | PORT-AS-IS | majority (S1·S3) | firewall("Human analysis ONLY")을 그대로 유지 |
| 15 | Sampling strata (metal round-robin, identity only) | `backbone_class_of()`; copolymer track은 `polymer_id_of()` | ADAPT | unanimous on key, S1 only on polymer_id | polymer_id를 쓰지 않으면 한 고분자의 10개 조성이 "10개 후보"가 되는 pseudo-replication 발생 |
| 16 | Memory ledger (673 l.) | 동일, `_GEOMETRY_COLS`/`_struct_label`만 교체 | PORT-AS-IS | unanimous | S2는 `md_refs`(측정치 vs 예측치 구분) 추가 제안 |
| 17 | Feedback generator (910 l.) | 동일 골격, 컬럼·row describer·hint 문장 전면 교체 | ADAPT | unanimous | |
| 18 | Feedback에 이름/SMILES 노출 | **억제**(S1 D-1, S3 §3.2) vs **monomer 이름 표시**(S2 §2.4) | contested | majority for 억제 (2/3) | 억제 근거: 누출 채널 차단 + Art. 10(1) 노출 축소. 반대 근거: 모논문 대비 fidelity 이탈. 절충안=억제 + 이름 노출 arm 1개로 비용 측정 |
| 19 | `feedback_live_adapter.py` (245 l.) | 미사용 상태로 보관 → 미래 oracle의 seam | ADAPT | unanimous | 물리 채널이 열릴 때의 유일한 삽입점 |
| 20 | Oracle: PORMAKE→LAMMPS→Zeo++→RASPA3 | **측정된 PoLyInfo 값(table lookup)** | REPLACE | unanimous (DB mode) | DB mode에는 surrogate가 없다 = "oracle은 surrogate만큼만 좋다" 문제가 **모드 선택으로 해소** |
| 21 | 동 (MD 배치) | S1: gated top-k validator(≤10 finalist) · S3: gated M8 · S2: **in-loop 80×T2 + 30×T3 = 82,905 core-h/campaign** | contested | majority for top-k only (2/3) | S2의 in-loop 물리는 13.5일/캠페인(256 core), 5 replicate면 67.5일 |
| 22 | HPC job contract (manifest → per-job JSON + `.DONE` → aggregate) | 동일 계약, `config/hpc.json` + `scripts/submit.py`(hpc-submit skill 규약)로 재표현 | ADAPT | unanimous | dirac도 PBS. skill은 Dropbox file lock이 ledger를 손상시킨다고 경고 |
| 23 | GA baseline (Note S6) | 동일 프로토콜, genome = (monomer A, B, composition bin, architecture) | ADAPT | unanimous | 모논문 GA surrogate는 held-out R² ≈ 0이었다. 고분자 surrogate는 R² 0.85–0.89 → **GA가 이길 수 있다**. 3안 모두 사전 공표 권고 |
| 24 | BO baseline (LVGP + EI) | 동일 + f_A를 진짜 연속 차원으로 | ADAPT | unanimous | 연속 축 때문에 BO가 MOF 때보다 구조적으로 유리 |
| 25 | (없음) Fox / group contribution | 도메인 baseline이자 귀속 ground truth | NEW | unanimous on existence, contested on role | S1·S3: baseline + ground truth. S2: **residual δ(f)=Tg−Tg_Fox를 objective로** 만들어 null model로 강등 |
| 26 | EGMOF 생성 모델 비교 | polyBART / POLYT5 / PolyTAO 등 | DROP / defer | majority | 모논문 스스로 "수치 비교하지 않는다"고 했고 공통 evaluator가 없음 |
| 27 | 평가 프로토콜 + battery driver (OLD clone) | 동일 + n-per-beam, 10 replicate, no-match rate, AUC | PORT-AS-IS | unanimous | 공개 repo에 없는 가장 값진 자산 |
| 28 | Backend benchmark (6×7×5) | 3–6 backend × 5 task × 5 rep, Agent 2 pinned, first attempt | PORT-AS-IS | majority (S2는 descope) | **Anthropic branch를 새로 작성해야 함**(C18) |
| 29 | `config.py` (840 l.) | 동일 골격, metric/unit registry를 Tg/Tm/density로 | ADAPT | unanimous | `LLM2POR_*` vs `LLM4MOF_*` 불일치(C19)를 먼저 정리 |
| 30 | `name_resolver.py` (125 l.) | 태그 프로파일 렌더러(인간 보고서 전용) | REPLACE | unanimous | |
| 31 | `filter_candidate.py` / `mof2zeo/` / `core/simulation/**` / `_pacman_worker.py` | — | DROP | unanimous | torch 의존성이 사라지는 것이 부수 이득(이 머신에 CUDA torch 없음) |
| 32 | `database_construction/` 2-layer 파이프라인 | 동일 철학 + 고분자 SMARTS | ADAPT | unanimous | "Layer 1 결정적 사실 + Layer 2 SMARTS만 필터링, LLM 생성 필드는 표시 전용" |
| 33 | `build_canonical_db.py` (테이블을 도달가능 집합으로 사전 필터) | 개념 유지, 전/후 카운트 **공개** | ADAPT | unanimous | 모논문은 19,997/12,188 → 14,173/9,533을 조용히 수행했다 |
| 34 | (없음) loader + 24–27 invariant validator | audit §3.4/§4 구현 | NEW | unanimous | 순 신규 작업 중 최대. 이것 없이는 하류 전부가 틀림 |
| 35 | (없음) zero-feedback arm + supervised-shortcut probe | 사전등록 통제 | NEW | unanimous | aide2에 존재, 공개 시스템엔 없음 |
| 36 | (없음) 귀속 채점기 T1/T2/T3 | 태그-vs-van Krevelen ρ / composition slope-vs-Fox / counterfactual edit | NEW | contested on scope | S3: 3개 전부 headline. S1: mechanism-edit 1개(n=10 sign test). S2: I1–I4 중 I4(MD)가 headline |
| 37 | (없음) 378-id composition-slope 도구 (median \|ρ\| 0.868) | 조성 축 귀속 | NEW | unanimous on existence, contested on role | S1: 인간 전용 진단 · S2: **CI hard gate ≥0.85** · S3: **1차 추정량** |
| 38 | (없음) provenance-tier guard (T0/T1 값이 figure에 닿으면 build 실패) | — | NEW | S2 only — 3 judge 전원 graft 권고 | ~20줄로 "surrogate는 재정렬만, 결정은 안 한다"를 문화가 아닌 기계로 만듦 |
| 39 | (없음) RegimeRouter (P1–P5) | pre-proposal 기여 #3의 결정적 구현 | NEW | S3 only — 3 judge 전원 **cut 또는 ablation 1개로 강등** 권고 | S3 스스로 §15.2에서 "Tg에서 그 가치는 거의 0 — 노이즈 안에서 고르는 것"이라 씀 |
| 40 | (없음) MD-LEDGER (생성 후보에 대한 MD 결과) | 유일하게 재배포 가능한 정량 산출물 | NEW | S2 only | MatNavi가 표는 못 내보내게 하지만 생성 후보의 MD 결과는 낼 수 있다 — 전략적으로 날카로운 관찰 |

---

## 4. 세 전략 비교

### 4.1 각 전략 한 문단

**S1 — Faithful Port.** MIT 라이선스 구 clone(f1d731a)을 fork해 루프·두 에이전트·4-beam·ledger·평가 프로토콜을 그대로 두고 도메인 레이어만 교체한다. 결정적 관찰은 *LLM4MOF의 DB mode가 이미 pool 기반 레코드 필터링 시스템*이라는 점이다 — 고분자 표는 코드 변경 없이 그 seam에 꽂힌다. 강제된 이탈은 정확히 6개(이름 억제, inclusive bound, 10 replicate, replicate-median table, stratum key, 루프 밖 통제 3종)이고 각각에 원인과 비용이 붙어 있다. 캠페인 당 ~353 s / ~$1, 전체 프로그램 200 campaign ≈ 20 h ≈ $210, GPU·HPC·CUDA torch 불필요. 대가는 명확하다: Figure 2의 절반만 얻고 Figure 4–7(de novo 생성, live 시뮬, 발견 주장)을 포기하며, 모논문의 12개 reviewer 압박점을 그대로 상속한다.

**S2 — Oracle-First.** 물리 예산을 먼저 고정하고 거기에 루프 크기를 맞춘다. free tier(van Krevelen GC + Fox + surrogate)가 10 iteration 전부와 4 beam을 돌리되 **보고되는 수치는 절대 만들지 않고**, paid tier가 gate descriptor G=(ρ,CED,FFV,C∞)를 MD로 재계산하고(80 run/campaign) 사전등록된 30-candidate audit(10 Beam-1 / 10 Beam-4 / 10 max-disagreement, manifest에 해시로 커밋)이 target Tg를 측정한다. 인식론은 세 전략 중 가장 날카롭다 — "gate는 target이 아니다"라는 모논문의 유일한 비순환성 장치를 정확히 짚었고, `nlargest(10,'target')` 패턴에 대한 구조적 답을 제시하며, Fox 가역성 누출까지 잡아냈다. 그러나 산술이 살인적이다: 82,905 core-h/campaign = 256 core에서 13.5일, 5 replicate면 67.5일이고, dirac 할당량·Psi4 설치·유한크기 오차가 전부 **미확인 직렬 게이트**이며 M6 이전에 산출물이 하나도 없다.

**S3 — Proposal-Faithful Port with Measured Attribution.** pre-proposal의 세 기여 중 둘(regime, surrogate meta-loop)을 결정적 기계장치로 강등하고 — regime은 deterministic Agent-2 rule router로, meta-loop는 오프라인 bake-off + 모논문의 `_apply_mae_slack`으로 — 절약된 예산을 *LLM4MOF가 한 번도 하지 않은 것*, 즉 귀속이 참인지 측정하는 데 쓴다. 핵심 통찰: **고분자에는 MOF에 없는 태그 단위 수치 귀속 ground truth(van Krevelen 증분, Fox 법칙)가 있으므로 diagnostic beam을 서술이 아니라 채점할 수 있다.** T1(태그-vs-GC Spearman), T2(pair 내 조성 기울기 vs Fox, 378-id 도구로 화학이 구조적으로 통제됨), T3(≥50 counterfactual edit), 그리고 hint-ablation arm까지 사전등록한다. M1–M7이 GPU·HPC·CUDA 없이 돌고 총 ~$350–500 / ~32 h이다.

### 4.2 Judge score table

| Strategy | Lens | Sci. validity | Reuse | Feasibility | Novelty | Risk(inv) | Total |
|---|---|---|---|---|---|---|---|
| **S1** | reviewer | 7 | 10 | 9 | 5 | 8 | 39 |
| | engineer | 8 | 10 | 9 | 6 | 8 | 41 |
| | scientist | 8 | 10 | 10 | 5 | 9 | 42 |
| | **mean** | **7.67** | **10.00** | **9.33** | **5.33** | **8.33** | **40.67** |
| **S2** | reviewer | 8 | 6 | 3 | 9 | 3 | 29 |
| | engineer | 8 | 6 | 3 | 9 | 3 | 29 |
| | scientist | 8 | 7 | 4 | 9 | 3 | 31 |
| | **mean** | **8.00** | **6.33** | **3.33** | **9.00** | **3.00** | **29.67** |
| **S3** | reviewer | 9 | 8 | 8 | 8 | 7 | 40 |
| | engineer | 9 | 8 | 8 | 7 | 7 | 39 |
| | scientist | 9 | 9 | 9 | 8 | 8 | 43 |
| | **mean** | **9.00** | **8.33** | **8.33** | **7.67** | **7.33** | **40.67** |

**Panel 결론**: reviewer → S3(40), engineer → **S1**(41), scientist → S3(43). 평균은 **S1 = S3 = 40.67 동률**, S2는 29.67로 명확히 뒤진다. 그러나 세 judge가 독립적으로 같은 말을 덧붙였다: *S1과 S3는 구현의 ~85%를 공유하며, S3 = S1 + 귀속 채점기 − RegimeRouter이다.* 즉 이것은 두 전략 사이의 선택이 아니라 **한 경로의 두 단계**다. S2는 "최고의 인식론과 최악의 산술"로 세 judge가 동일하게 평가했고, 그 불변식들은 어느 쪽이 채택되든 이식되어야 한다.

### 4.3 제기된 치명적 결함 (judge panel)

**S1**
- **[venue, 3/3 judge 지적]** 범위대로면 Nature-portfolio급이 아니다. §0.3(4)가 Figure 4–7을 포기하고, landscape §6.4는 2025–26 Nature-portfolio 고분자 inverse-design 논문이 **전부** 합성 또는 MD 검증 물질을 최소 1종 포함한다고 보고한다. 새 물질도 새 물리도 없는 same-lab 동반 논문은 salami-slicing으로 읽힐 수 있다(§L-9 미해결).
- **[headline 붕괴, self-rated High]** 7개 descriptor slot은 표준 Tg feature set이고, S1이 인용하는 문헌 자체가 descriptor로 R² 0.895에 도달한다. 사전등록 probe가 OOF R² > 0.80을 넘길 가능성이 높으며, 그 경우 headline 귀속은 replicate SD 중앙값 7.0 K인 표 위의 chemistry contrast 3개로 축소된다. **규칙은 명시되어 있으나 그 이후의 논문이 설계되어 있지 않다.**
- **[내부 모순]** §0.1의 "byte-identical loop" 헤드라인과 §0.2의 6개 이탈 목록(특히 D-1, MOF agent가 갖던 입력을 제거)이 충돌한다. Table-1 비교가능성 논증이 자기 이탈 목록을 견디지 못한다.
- **[오염]** 7개 slot 중 2개(`ecoh_vk`, `ffv_proxy`)가 미검증 전사본에 의존한다. 전사가 틀리면 probe·window·envelope·feedback이 모두 오류를 상속하는데 검증 pass가 예산에 없다.

**S2**
- **[산술, 3/3 judge]** 82,905 core-h/campaign, 5 replicate = 67.5일(256 core). dirac 할당(D2)은 **미해결 사용자 결정**이고, Psi4≥1.5는 pip 불가(R7)이며, M2는 스스로 "task가 아니라 gate"이고 그 측정치가 "전체 캠페인 설계를 무효화할 수 있다"고 쓴다. 그리고 S1의 R-12나 S3의 M8 gate와 달리 **fallback 선언이 없다**.
- **[검정력]** headline Δ_MD는 n=10 vs 10 Mann-Whitney인데 후보 당 CI가 ±35–45 K이고 §5.2 스스로 40 K 미만 차이를 주장하지 말라고 한다. R12가 underpowering을 인정하면서 예산 내 해법을 제시하지 못한다.
- **[구조적 모순, scientist 지적]** 귀속(beam 궤적, Z–A/A–F/F–R contrast)은 T0/T1 tier에서 계산되는데 §5.6의 provenance guard는 T0/T1 값이 figure에 닿으면 build를 실패시킨다. **guard가 해석가능성 증거인 그 figure들을 금지하거나, 바로 그 figure에 대해서만 예외가 된다.** 문서가 이를 해결하지 않는다.
- **[미검증 계측기로 감사]** T3 audit oracle(RadonPy Tg preset)은 PoLyInfo 검증 이력이 공개된 바 없고 3,600 vs 10,000 atom 유한크기 오차도 미측정이다. 검증되지 않은 oracle로 agent를 검증하는 것은 이 전략이 막으려던 바로 그 비판이다.
- **[gate의 물리]** G=(ρ,CED,FFV,C∞)를 pore-size window의 정확한 유비라 하지만, pore diameter는 흡착의 기하학적 전제조건인 반면 CED와 C∞는 **Tg의 master variable 그 자체**다(S2 §4.1이 그렇게 쓴다). "gate는 target이 아니다"가 형식적으로만 참이 된다.

**S3**
- **[순환성, 2/3 judge]** `tg_gc`(van Krevelen Tg)와 `ced_proxy`(Hoftyzer-van Krevelen CED)를 agent에게 **보여주면서** T1이 그 agent를 van Krevelen 증분에 대해 채점한다. GC-gate arm은 gating 버전만 통제하고 display 버전은 아무도 통제하지 않는다. **M5 이전에 고쳐야 하며**, 수정은 싸다(feedback에서 tg_gc 제거한 arm 1개 + 태그 정체성에 대한 category-내 permutation null).
- **[ground truth가 아직 없음]** headline 수치를 떠받치는 van Krevelen 표가 **이 프로젝트가 만드는 산출물**이고 critical path 위에 있다. 전사 오류는 탐지 불가능한 방향으로 틀린다. M3의 in-sample MAE ≤15 K gate는 필요하지만 충분하지 않다.
- **[범위 초과]** 5개 regime rule block + RegimeRouter + held-out-regime 실험 + 5-family surrogate bake-off(그중 2개는 존재하지 않는 CUDA 환경 필요) — 그런데 §15.2가 직접 "Tg에서 그 가치는 거의 0, 노이즈 안에서 고르는 것"이라 쓴다.
- **[다중비교 계획 없음]** V0 + zero-feedback + hint-ablation + GC-gate + no-ledger + no-stratification × 6 task. W2의 210 seeded campaign에서 어떤 변형도 Holm 보정 후 기본 설정을 이기지 못했다(max +1.80 σ, p_holm = 1.0). §9에 보정 계획이 없다 = 가짜 유의 arm이 나온다.
- **[숫자의 부재]** 가장 novel한 주장(T2 조성 귀속)을 한정하는 수치 — binding-resolved · untruncated · composition-parsed subset 크기 — 가 M1에서야 측정된다. 명목 6,917 rows / 1,381 ids에서 수백 pair로 떨어질 수 있다.

**세 전략 공통 (cross-cutting)**
- **MatNavi Art. 10(1) "transmission" 문제가 미해결이고 모든 LLM arm을 막는다.** S1 L-2 / S2 D1 / S3 U1이 모두 지적한다. Terms는 machine learning을 **0회** 언급한다. 전면 금지라면 로컬 모델이 필요한데 이 머신 어느 환경에도 CUDA torch가 없다(Blackwell RTX 5050은 CUDA 12.8+/13.x wheel 필요). binned/anonymised/tag-only feedback은 완화책이지 답이 아니다.

### 4.4 Graft 아이디어 (어느 경로를 택하든 가져갈 것)

**S2에서 (인식론적 불변식)**
1. **Fox residual을 objective로**: δ(f) = Tg_measured(f) − Tg_Fox(f)를 최대화하는 task를 두면, 해석적 null은 자기 residual을 최적화할 수 없다. Fox는 무료이고 70년 되었고 R² 0.835 — 경쟁자로 두면 이기고, null로 두면 referee가 원하는 바로 그것이 된다. **가장 비용 대비 가치가 높은 graft. 표가 고정되는 M3 이전에 결정해야 한다.**
2. **Tg_Fox 자체는 절대 보여주지 말고 residual만**: Fox는 가역적이라, 두 조성에서 Tg_Fox를 본 agent는 Tg_A와 Tg_B를 풀어내 본 적 없는 homopolymer 값을 복원한다. MOF에는 mixing law가 없어 존재하지 않던 누출 채널이다.
3. **provenance-tier guard를 check gate 테스트로**: 모든 레코드가 `provenance.tier ∈ {TABLE,T0,T1,T2,T3}`를 갖고, 예측값 tier가 `figure_*.csv`에 닿으면 build 실패. ~20줄.
4. **보고 target을 replicate noise floor로 binning**: "Tg 372–379 K"이지 "375.4 K"가 아니다. Art. 10(1) 완화이자 정직함(세 번째 유효숫자가 7.0 K SD 아래).
5. **feedback에 noise-floor footer**: "이 표에서 ±7 K 이내는 구분되지 않음, p90에서 ±33 K". GCMC에는 run-to-run noise가 없어 모논문이 하지 않은 것.
6. **두 통화 예산 회계**(oracle call **과** core-hour), 명목이 아닌 **실현**치로 arm 간 ±5% 일치. 모논문은 명목 400에 대해 GA 327–368, BO 212–265를 실현했다.
7. **MD 채널이 열리면 top-k가 아니라 사전등록·해시된 10/10/10 draw**를 job 제출 **전에** manifest에 기록. S1 §E.3과 S3 §M8이 현재 top-k를 제안하는데, 그것이 바로 `nlargest(10,'target')` 패턴이다.

**S1에서 (엔지니어링 규율)**
8. **모든 descriptor slot에 inclusive bound**: 고분자 fraction descriptor는 0.0과 1.0에 질량점이 있어서 모논문의 strict `DI_MIN < di < DI_MAX`를 그대로 옮기면 polyolefin 계열 전체가 조용히 삭제된다. 한 글자 수정, S2·S3 모두 언급 없음 — 놓치면 출하되는 버그.
9. **결정적 mechanism-edit 테스트를 T3와 함께**: S3의 T3는 Agent 2를 재실행하므로 LLM 분산을 안고 간다. S1 버전은 constraint JSON의 한 절을 기계적으로 뒤집고 **LLM 없이** matchmaker+evaluator만 재실행한다. T3는 agent의 가설을, mechanism-edit는 constraint 언어를 측정한다.
10. **replicate-group median table**(18,142 → 10,249 groups)과 **copolymer stratum key = polymer_id**. 둘 다 S3에 없고, 후자가 없으면 한 고분자의 10개 조성이 10개 후보로 계수된다.
11. **headline arm은 10 replicate, grid cell은 5**. 측정된 σ 6.4–15.9 percentile point에서 적절하고 wall-clock을 되산다.
12. **매 커밋마다 원본 MOF 데이터로 3-iteration hMOF 캠페인을 CI smoke test로**. LLM 호출 6회. "우리가 루프를 망가뜨렸다"와 "고분자 Tg가 어렵다"를 혼동하지 않게 하는 유일한 싸구려 보험이며 S2·S3 모두 명시하지 않는다.
13. **hidden table을 reachable set으로 명시 정의하고 전/후 카운트 공개**, 항상 "top-1% of the reachable table, n = N"으로 표기. 모논문이 조용히 한 것을 의도적·공개적으로.
14. **`feedback_live_adapter.py`를 미사용 상태로 트리에 유지** — 물리 채널이 열릴 때의 올바른 단일 삽입점. 비용 0.

**S3에서 (측정 계측기)**
15. **T1/T2/T3 귀속 채점기**. S1의 novelty 결손을 메우고 "beam을 이식했다"를 "beam이 의미가 있는지 측정했다"로 바꾸는 graft.
16. **pair 내 composition-slope를 연속 축의 1차 추정량으로 승격**. monomer pair가 자기 자신의 통제이므로 raw beam median을 삼키는 pair 간 분산이 상쇄된다. 낮은 ρ 67개 id(EVA ρ 0.20, SAN ρ −0.06)는 실패가 아니라 물리적으로 흥미로운 non-Fox 계로 별도 보고.
17. **hint-ablation arm**: beam 해석 문장 4개를 제거한 동일 캠페인. 귀속 표가 그대로면 데이터의 것이고 무너지면 prompt의 것이다. arm 2개, ~$20, weakness #12에 대한 유일한 직접적 답.
18. **M5의 memorisation hard gate**: share > 0.8인 task는 headline에서 **탈락**하고 "memorised"로 보고. S1은 share를 측정하지만 탈락 규칙이 없어 숫자를 본 뒤에 결정하게 된다 — 정직하게 결정하기 가장 어려운 시점.
19. **Fox 재현을 binding validator이자 hard milestone gate로**: binding-resolved row에서 Fox가 R² ~0.835 / RMSE ~42.6 °C 근처에 착지하지 않으면 binding이 틀린 것이고 M1이 재개된다. 프로젝트에서 가장 싼 정확성 검사이며 D1을 직접 방어한다.
20. **378-id monotonicity set을 CI hard regression gate로**(median |Spearman ρ| ≥ 0.85, 측정값 0.868). D1이 해결 가능 row의 ~30%에서 조성 기울기 부호를 뒤집으므로, binding swap 재유입에 대한 가장 싼 방어.
21. **`tg_gc`는 계산·표시하되 gate에서 제외**하고 GC-gate arm으로 효과를 측정. **단 수정 필수**: feedback에서도 숨긴 arm을 함께 돌리지 않으면 T1이 "agent가 건네받은 숫자를 읽었는가"를 측정하게 된다.
22. **fixed n=10 shown-sample median을 1차 beam 통계로**, 전체 matched-set median은 모논문 Table 1과의 비교용 2차 지표로 유지.

---

## 5. 추천안 — synthesizer의 견해

> **이하는 synthesizer의 견해이며 결정이 아니다.** 3-judge panel은 S1(engineer)과 S3(reviewer, scientist)로 갈렸고 평균은 정확히 동률이다. 아래는 그 분기를 해소하는 한 가지 읽기다.

### 5.1 추천: **단일 경로 "Measured-Attribution Faithful Port" = S1 골격 + S3 계측기 + S2 불변식**

근거는 네 가지다.

**(1) S1과 S3는 경쟁 전략이 아니라 한 경로의 두 단계다.** 세 judge가 독립적으로 같은 문장에 도달했다 — S3 = S1 + 귀속 채점기 − RegimeRouter. 구현의 ~85%가 동일하다. 따라서 "무엇을 고를 것인가"가 아니라 "무엇을 먼저 커밋하고 무엇을 자를 것인가"가 실제 질문이다. **먼저 커밋할 것은 S1의 골격이고**(오늘 이 conda base에서 도는 유일한 critical path, 캠페인 당 ~353 s / ~$1, 8개 stable interface가 형태 그대로 이동), **첫 headline 캠페인 전에 접붙일 것은 S3의 채점기다.**

**(2) 결정적 기준은 "headline이 실패해도 논문이 되는가"이다.** S1의 자체 평가로 R-1(descriptor window가 supervised shortcut)은 **High**이고, S1이 인용하는 문헌 자체가 descriptor로 R² 0.895에 도달하며, MOF 쪽 등가 probe는 3개 컬럼으로 OOF R² 0.943을 기록했다. 즉 probe는 발화할 가능성이 높다. 그때 S1은 replicate SD 중앙값 7.0 K인 표 위의 chemistry contrast 3개만 남지만, **S3는 기여물이 결과(outcome)가 아니라 계측기(instrument)이기 때문에 여전히 논문이 된다** — "beam 귀속을 van Krevelen 증분과 Fox 법칙에 대해 채점했고 hint-ablation으로 harness 기여분을 분리했다"는 probe가 발화하든 말든 참인 결과다.

**(3) S2는 채택하지 말되 해체해서 가져간다.** feasibility 3.33 / risk-inverse 3.00은 세 lens가 완전히 일치한 유일한 지점이다. dirac 할당·Psi4·유한크기 오차가 직렬 게이트이고 M6 이전 산출물이 없으며 fallback 선언이 없다. 그러나 S2의 §0.2 불변식("gate는 recompute되어야 하고 target이면 안 된다"), 해시된 10/10/10 audit draw, Fox 가역성 누출, provenance guard, Fox-residual objective는 **세 judge가 전원 graft를 권고한 항목**이다. 이것들은 in-loop MD 없이도 전부 구현 가능하다.

**(4) 잘라야 할 것은 명확하다.** RegimeRouter(S3 스스로 Tg에서 가치 "거의 0"이라 서술, 3 judge 전원 cut 권고 — ablation arm 1개로 강등), 5-family surrogate bake-off(2개 계열이 존재하지 않는 CUDA 환경 필요, §15.2가 null을 예측), S2의 in-loop MD ladder 전부, PFAS Phase 2(공개 데이터셋 없음 — 별도 GCMC-oracle 캠페인으로 재구성하거나 제외).

### 5.2 선행조건 2개 (M1 착수 전)

- **P-1 (blocking):** MatNavi Art. 10(1) transmission 질문. 세 전략 전부가 여기서 막히며, 이것은 일정이 아니라 **아키텍처**를 무효화할 수 있다.
- **P-2 (framing):** LLM4MOF 저자단과의 관계 및 목표 venue. "동일 루프가 변경 없이 이전된다"가 우아함으로 읽힐지 self-repetition으로 읽힐지는 이 선언에 전적으로 달려 있다.

### 5.3 추천 경로의 첫 세 milestone과 측정 가능한 exit criteria

| | **M1 — 데이터 기반 + 하네스 스모크** (blocking) |
|---|---|
| 내용 | audit §3.4 loader + §4 validator 구현; 구 clone `f1d731a` fork(MIT 헤더 보존); 알려진 결함 4개 수정(`UNIFIED_VOCABULARY_PATH`, `core.han_safe_topologies`, env toggle 이름, Anthropic branch 부재); 원본 MOF 데이터에 대한 smoke campaign |
| Exit (전부 정확히 재현되어야) | CSV **42,557 rows / U+FFFD 정확히 9개 / 7,385 polymer_ids**; XLSX **13,725 rows / 13,624 unique CanonSMILES / Tg_K n = 7,733**; binding class가 **aligned 15,409 / swapped 2,221 / half_aligned 5,309 / half_swapped 881 / neither 433 / one_id 190 / no_ids 18,114**로 재현; trimer key가 저장된 allow-list(XLSX 5 + CSV 2 + cross-file 1)에 대해 **false merge 0**; usable core **13,350 rows / 2,735 ids**와 **6,917 rows / 1,381 ids** 재현; hard invariant 전부 통과; **binding-resolved · untruncated · composition-parsed subset의 정확한 크기를 신규 산출**(T2 헤드라인을 한정하는 수치); `pixi run check` 5/5; **원본 hMOF 데이터로 3-iteration 캠페인이 LLM 호출 6회로 완주하고 `beam_data.csv` 생성** → 이후 CI에 고정 |
| 실패 시 | 어떤 하류 작업도 시작하지 않음. M1은 preamble이 아니라 multi-week milestone이다 |

| | **M2 — 사전등록 게이트 (측정 가능성 자체를 먼저 측정)** |
|---|---|
| 내용 | 7개 descriptor + 어휘 구축; supervised-shortcut probe; van Krevelen 표 2차 출처 대조; Fox 재현; composition regression gate |
| Exit | 7개 descriptor가 13,624 XLSX + 4,792 CSV 구조에 대해 계산되고 RDKit 실패 ≤ 알려진 10건; 어휘 **≥100 canonical tags / ≥150 aliases / ≥80 SMARTS**이고 **구조의 ≥95%가 ≥3개 태그 보유**; `TAG_HIERARCHY` 전파 단위 테스트 통과; **shortcut probe의 OOF R²를 사전 선언된 fail action과 함께 공개**(>0.80이면 headline 귀속을 chemistry arm으로 제한하고 Fox-residual task를 headline으로 승격 — 이 결정을 숫자를 보기 **전에** 확정); van Krevelen 표가 2차 출처와 대조되고 **in-sample MAE ≤ 15 K**; **Fox가 binding-resolved row에서 R² 0.835 ± 0.05 / RMSE ≈ 42.6 °C 재현 — 실패 시 M1 재개**; **378-id monotonicity set의 median \|Spearman ρ\| ≥ 0.85가 CI hard gate로 배선**(측정값 0.868) |
| 왜 여기인가 | S1의 R-1, S3의 R-6, D1 부호 뒤집힘이 전부 이 게이트 하나에 모인다. 캠페인 지출 전에 결정되는 유일한 지점 |

| | **M3 — 첫 headline 배터리 + 기억화 바닥** |
|---|---|
| 내용 | polymer matchmaker + analyzer 배선 후 10-iteration homopolymer Tg-max 캠페인; 4 arm 배터리; 통제 arm 전부 |
| Exit | `search_mode` 3종 전부가 id 리스트 반환하고 **손으로 쓴 constraint JSON 20개에 대해 Z ⊆ A ⊆ F ⊆ total 포함관계 성립**; zero-match constraint가 structured error + diagnostic footer 발화; 10-iteration 캠페인이 **정확히 20 LLM calls, ≤ $1.50**로 완주하고 wall-clock을 MOF 기준(353 s)과 비교 보고; **4 arm(V0 / `--no-feedback` / hint-ablation / no-ledger) × 10 replicate**; **어떤 효과를 주장하기 전에 replicate σ를 먼저 보고**; task별 memorisation share (NF−50)/(V0−50) 보고 + **share > 0.8이면 해당 task를 headline에서 탈락**; 모든 산출물에 **beam 당 n 기록**; `feedback_selected.txt` 전체 grep에서 **IUPAC name / SMILES / pid / sample_id 0건**; 어떤 beam 분리도 p50 within-group SD(7.0 K) 미만이면 효과로 보고하지 않음 |
| 실패 시 | memorisation share가 전 task에서 0.8 초과면 headline을 "loop가 parametric memory 대비 X point를 더한다"로 재구성하고 X를 보고 |

M4 이후(요약): baseline 5종(random / GA / BO / Fox / GC) 실현 예산 ±5% 일치 → T1/T2/T3 귀속 측정 + mechanism-edit 테스트 → backend benchmark → 그리고 **MD 채널은 별도 게이트**(dirac 할당 ≥50,000 core-h 확인, RadonPy+LAMMPS+Psi4 설치, 공개 density 3종 5% 이내 재현, 후보 당 wall-clock 실측)로만 열리며, 열린다면 top-k가 아니라 **해시된 10/10/10 draw**로 실행한다.

---

## 6. 데이터 감사가 이식에 미치는 제약 — 어떤 결함이 어떤 컴포넌트를 문다

| Defect (severity) | 물어뜯는 컴포넌트 | 구속 조건 |
|---|---|---|
| **D1 조성/성분 바인딩 swap (S1)** — `composition_i`는 `component_i`에 속하고 `smiles_i`에는 결코 속하지 않음; 해결 가능 row의 **29.9%(5,333/17,842)**가 최소 한 slot swap; mixing test 13.7 °C(component binding) vs 56.8 °C(slot binding) | **composition window(Beam 1의 수치 gate), Fox baseline, T2 조성 귀속, dominant-component rule 전부** | copolymer hidden table은 `binding ∈ {by_component_majority, by_position_aligned_only}` row만 포함. **half_aligned 5,309 row는 추측하지 말고 제외** — 그 구간의 mixing test는 오히려 역방향 binding을 지지(23.4 vs 15.4 °C)하므로 무작위보다 나쁘다. 이것을 틀리면 T2는 노이즈가 아니라 **부호가 뒤집힌 결과**를 낸다 |
| **D4 replicate/중복 (S2)** — Tg row의 56.3%가 replicate group; within-group SD p50 **7.0 °C** / p90 33.1 / p99 120; 6,548 row가 `sample_id` 제외 완전 중복 | **hidden table 정의, 모든 threshold, 모든 beam 분리 주장, split 전략** | table은 **replicate-group median table**(18,142 → 10,249 groups). split은 `polymer_id` 기준. **7 K 미만 beam 분리는 보고 금지**. feedback에 SD를 인쇄하고 noise-floor footer 추가 |
| **D5 조성 결측 42.6%** — 18,116 row, 4,578개 Tg 보유 id 중 1,878개가 조성을 한 번도 안 가짐 | **Beam 4(random baseline)의 공정성** | Beam 4가 Beam 1이 도달 불가능한 row를 뽑으면 Beam 1이 구조적으로 불리해진다 → copolymer hidden table을 composition-parsed·both-monomer-matched core로 **정의**하고 4개 beam이 동일 객체를 필터 |
| **D6 terpolymer 절단 (S2)** — 4,243 row / 548 id(보수), `component3..5` 비어 있음, 4,023 row가 99 미만 합 | **composition window, Fox** | `truncated_flag` row 제외. 합이 84인 2성분 조성은 정규화할 오류가 아니라 표가 표현 못 하는 **세 번째 단량체**다 |
| **D10/D11 구조 정체성 (S3)** — periodic key가 XLSX 5 + CSV 2 + cross-file 1쌍을 잘못 병합; `smiles1 == smiles2`가 3,952 row / 713 id | **primary key, novelty 계산, dedup, MD cache key, Beam 1의 정당성** | primary key는 **trimer ring-closed key**(stereo 분리, `stereo_canon` 연결). `same_monomer_flag` row는 copolymer table에서 제외 — copolymer id를 입은 homopolymer이므로 Beam 1이 공짜로 이긴다. 단 S2의 관찰도 유효: 이것들은 Fox가 필요로 하는 **f→0 / f→1 끝점**이므로 버리지 말고 homopolymer 경로로 라우팅 |
| **D2/D3 인코딩·전기 문자열 (S1)** — UTF-8에 손상 3건, P908185가 두 레코드를 삼키고 P908186 소실; `1/(ohm*cm)`에서 greedy regex가 `2e-16`을 `2e-161`로 읽음(4,048 중 2,061) | **loader만** (Tg/Tm은 무영향) | audit §3.4 loader 규칙을 순서대로, I1/I2/I7을 hard gate로. 전기 물성을 task로 쓸 경우 두 컬럼이 아니라 한 컬럼의 log₁₀ |
| **D8/D15 단위·이상치 (S2/S4)** — `Elongation_at_break_GPa`가 실은 percent; XLSX Tg/Tm은 K, CSV는 °C; 78 row에서 Tg > Tm | **metric registry, sanity gate** | 전부 SI(K)로 저장하고 `unit_assumed` 플래그. **컬럼명 자체를 도메인 모델에서 개명**할 것 — LLM이 스키마를 읽으면 오도된다 |
| **XLSX 중복 구조 충돌** — 91 group 중 **30개가 Tg 충돌, 최대 spread 169 K**; 중복 이름 77 group, 최대 212 K | **top-1% threshold, 달성 가능한 RMSE 상한** | 이것들은 평균낼 측정 replicate가 아니라 구조/이름 충돌이다. **169 K 충돌을 median으로 뭉개는 것은 수리가 아니라 값의 날조**다 → 사용자 결정(§8-Q8) |
| **D13 architecture 태그 (S3)** — 27.7% multi-tag, 49.0%가 단일 `['unspecified']`, 4,033 row가 이름에 `-alt-` 없이 alternating 태그 | **architecture 축의 신뢰도** | architecture는 class가 아니라 **multi-label**. `unspecified`는 "unknown"이며 agent가 요구할 수 있는 값이 아니다. Beam 3의 primary 축으로 쓰지 말 것(그건 backbone class) |
| **D12 XLSX 집계 규칙 불명** — 2,338 row(17%)가 물성 없음, 여기에 **PE·PS·PMMA·PVC·PET·PEO·PLA·PCL의 primary pid가 포함** | **"시스템이 폴리에틸렌을 재발견했다"류 서사, MD calibration anchor set** | calibration anchor는 pid가 아니라 **structure key로** 구성(PS·PDMS·PTFE·PVDF는 두 번째 pid에 데이터가 있음). 명명된 고분자 주장은 어느 pid인지 명시해야 |
| **D16 `copolymer.zip`이 전부 NUL** | 범위만 | 유효한 zip 컨테이너이나 15개 member CSV가 전부 NUL로 압축 해제. 현재 어떤 경로도 이것에 의존하지 않음 |
| **Licensing (MatNavi Art. 9.2, 10(1)–(3),(5))** | **저장소 형태, feedback payload, 릴리스 가능 산출물, 그리고 어쩌면 LLM arm 자체** | hidden table은 커밋 불가 → `data/` git-ignore + `MANIFEST.sha256` + rebuild script를 **commit 1부터**(나중 개조는 history rewrite). 릴리스 가능: 코드·어휘·SMARTS·descriptor 정의·prompt·traces(이름 억제 후)·집계 통계. **루프는 아무것도 학습하지 않으므로 weights 라이선스 문제가 없다** — 모논문의 "not a single property-labeled training structure"가 그대로 이전되고 여기서는 법적 자산이기도 하다 |

---

## 7. 저장소 부트스트랩 상태

**위치** `C:/Users/molsim/Desktop/LLM4POL` (Dropbox 밖 — hpc-submit skill이 Dropbox file lock의 ledger 손상을 경고). **git init -b main, 커밋 0개, remote 없음** — 리드 엔지니어의 검토 후 커밋하도록 남겨둠.

| 항목 | 상태 |
|---|---|
| **Check gate** | `pixi run --manifest-path env/pixi.toml check` → **5/5 PASS, exit 0** (ruff check / ruff format --check(5 files) / mypy(1 source file) / import-linter(**Contracts: 0 kept, 0 broken**) / pytest **4 passed**). 검증자가 독립 재실행하여 byte-identical 출력 확인 |
| **pixi** | `env/pixi.toml` + `env/pixi.lock`(212,798 B, **win-64 + linux-64 양 플랫폼**); `pixi install` 28 s, exit 0. 해결된 스택: Python 3.13.15, pandas 3.0.5, rdkit 2026.03.6 |
| **GSD Core** | per-project 설치(`npx -y --package=@opengsd/gsd-core@latest -- gsd-core --claude --local`), **VERSION 1.13.0**(CALF20과 동일). **72개 `gsd-*.md` command**(CALF20 목록과 `diff` 결과 동일), 35 agents, 28 hooks, profile `full` |
| **데이터** | 3개 원본 파일을 `cp -p`로 `data/raw/`에 복사, sha256 재검증 일치. `polymer_final_0824.csv` `a110918…8013` (10,015,654 B), `230227_Homopolymer_CanonicalSMILES.xlsx` `06a8f05…7ab0a` (985,398 B), `copolymer.zip` `cf1c868…873e9` (8,783 B, **KNOWN-CORRUPT**: 유효한 zip 컨테이너이나 15개 member CSV가 전부 NUL) |
| **문서** | `docs/audit/`에 12개 `.md`(10 top-level + `refute_csv/` 1 + README) — **11개 전부 scratchpad 원본과 sha256 동일**; `.pkl`/`.py`/`.csv`/`.pdf`는 복사되지 않음(일부가 PoLyInfo row 포함). `docs/reference/`에 proposal 사본(본문 verbatim, 3줄 blockquote 헤더 + `---`; CRLF로 기록되어 byte-identical은 아님) |
| **정책 강제** | `.gitignore`가 `data/raw|interim|processed`, `.env`, `env/.pixi`, `.claude/settings.local.json`을 실제로 무시(각 규칙 `git check-ignore -v` 확인). `tests/test_manifest.py`가 manifest의 size+sha256을 실제로 검증(4개 테스트 모두 실행됨, skip 없음) |
| **Python scaffold** | `pyproject.toml`: `llm4pol` 0.0.1, requires-python ≥3.13, src layout, **mypy strict**, `[tool.importlinter]` root_package `llm4pol`에 **contract 0개**(아키텍처 동결 시 추가). `src/llm4pol/__init__.py`는 docstring + `__version__`뿐 |

**의도적으로 하지 않은 것**
- **커밋하지 않음**(0 commits), remote 없음, planning command 미실행.
- **`.planning/` 디렉터리는 존재하지 않음** — bootstrap 보고서의 "CALF20처럼 tracked"라는 주장은 검증에서 **refuted**(C9). README는 "created by GSD; none yet"으로 정직하게 적혀 있으나 layout 블록은 없는 디렉터리를 문서화한다.
- **OMC 비활성화 키를 복제하지 않음** — LLM4POL의 `settings.local.json`에는 `hooks`/`worktree`/`permissions`만 있고 `enabledPlugins`·`DISABLE_OMC`가 없다(CALF20에는 둘 다 있음). 헌장 시점의 소유자 결정으로 남김.
- **production code 0줄**(CLAUDE.md의 "헌장 승인 전 production code 금지"), torch·LLM SDK·agent framework·surrogate 라이브러리 미설치, `.env` 미생성(`.env.example`만, 값 전부 비어 있음).
- **데이터를 git에 넣지 않음** — 대신 manifest + 테스트로 강제.

**보고서가 과장하지 않은 점 / 주의할 점 2가지**
- README는 "동일 호출이 CI에서도 돈다"고 하나 **CI는 한 번도 실행된 적이 없다**(커밋 0, remote 없음). 동치성 자체는 `ci.yml` 검사로 참이지만 `actions/checkout@v7.0.1`·`setup-pixi@v0.10.2`·`pixi-version: v0.80.0` 핀은 미검증이므로 첫 push 전에 확인 필요.
- 게이트는 `python -m mypy`를 실행하므로 `[tool.mypy] packages=['llm4pol']`만 검사된다 — **`scripts/`와 `tests/`는 타입 검사되지 않는다**(mypy가 "1 source file"이라 보고). README의 "mypy --strict on src/"보다 관대하다.
- CALF20 무수정 확인은 **데이터 쪽만 확정적**이다. CALF20의 `git status`는 이후 14개 항목으로 변했으나, 그 커밋(8f7dc13, 16:38:27)이 bootstrap 종료(16:35) 이후이고 변경 경로가 전부 CALF20 자신의 HPC/GCMC 도메인이므로 **동시 작업**으로 판단됨. 이 세션 작업에 귀속되는 변경은 없음.
- **아키텍처가 헌장보다 먼저 굳어진 부분**: GSD 워크플로(`.claude/` 하위 770 파일이 tracked 대상), pixi + conda-forge, src layout, 패키지명 `llm4pol`, Python ≥3.13, 그리고 의존성 집합(pandas/numpy/scipy/sklearn/rdkit/pyarrow/pydantic/openpyxl/jsonschema)이 조용히 **tabular + RDKit 모델링 경로를 전제**한다. `.env.example`의 4개 provider 키는 multi-provider LLM agent 설계를 전제하는 유일한 지점이다.

---

## 8. Deep-interview 질문 목록 — 오직 사용자만 답할 수 있는 것

아키텍처를 바꾸는 정도 순. 파일에서 답할 수 있는 것은 제외했다.

**Q1. MatNavi Art. 10(1) "transmission": PoLyInfo 유래 내용을 호스팅 LLM API에 보낼 수 있는가?**
옵션 (a) 제한 없이 가능 (b) **파생 태그 + noise-floor로 binning된 값만** 가능 (c) 불가.
함의: (b)는 세 전략 전부와 호환되고 S1의 D-1(이름 억제)을 법적으로도 정당화한다. (c)는 로컬 모델을 강제하는데 **이 머신 어느 환경에도 CUDA torch가 없고** Blackwell RTX 5050은 CUDA 12.8+/13.x wheel이 필요하다 — 일정이 아니라 아키텍처가 바뀐다. (a)는 fidelity 논증을 강화하지만 누출 채널(이름이 BB id를 식별하는 문제)은 남는다. **세 전략 전부가 여기서 막혀 있다.**

**Q2. 목표 venue와 LLM4MOF 저자단과의 관계 선언.**
옵션 (a) sanctioned companion paper (b) 독립 투고 (c) 내부 도구/사내 플랫폼.
함의: 공개 repo 소유자(`kn1218`)와 이 계정이 동일 GitHub 로그인이다. 선언되지 않으면 referee는 "새 물질도 새 물리도 없는, 저자 자신의 미발표 방법을 두 번째 데이터셋에 적용한 것"으로 읽는다. (a)면 "동일 루프가 변경 없이 이전된다"가 headline이 되고 fidelity가 최우선. (b)면 novelty가 최우선이라 S3의 귀속 채점기가 **필수**가 된다. (c)면 통계 검정력 요구가 크게 낮아지고 MD 채널이 아예 불필요해진다.

**Q3. dirac 할당: 지속 core 수, job wall limit, queue 이름, 그리고 GPU node 노출 여부.**
옵션 (a) ≥50,000 core-h 확보 가능 (b) 소규모만 (c) 없음.
함의: (c)면 MD 채널이 아예 닫히고 **논문은 DB-mode only로 확정**된다(S1 R-12의 fallback). S2는 존재 자체가 불가능해진다. (a)여도 top-k validator(≤10 finalist)까지이며, S2식 in-loop 물리는 256 core에서 13.5일/campaign·5 replicate 67.5일이다. hpc-submit skill에 gpu/cuda 언급이 0회이므로 GPU 여부는 사용자만 안다. **M8이 아니라 헌장 시점에 답해야 한다** — 이 답이 논문의 형태를 정한다.

**Q4. 합성 협력자가 있는가(단 1종이라도)?**
옵션 (a) 있음 (b) 섭외 가능 (c) 없음.
함의: landscape §6.4 — 확인된 2025–26 Nature-portfolio 고분자 inverse-design 논문은 **전부** 합성 또는 MD 검증 물질을 최소 1종 포함한다(polyBART, POLYT5, Kern thiocane, Zheng vitrimer, SPACIER). (c)면 Q2의 venue 기대치를 Digital Discovery / JACS Au / npj Comput. Mater. 급으로 조정하고, 그 사실을 **미리** 받아들이고 설계해야 한다(S1·S3 모두 이 천장을 공유).

**Q5. Homopolymer 전용인가, homopolymer + copolymer인가?**
옵션 (a) homopolymer만(pre-proposal 그대로) (b) 둘 다 (c) copolymer 우선.
함의: (a)는 깨끗하고 단순한 이식이지만 **연속 조성 축을 버린다** — LLM4MOF 대비 진짜 novelty의 유일한 원천이고, 이 선택은 프로젝트를 transplant로 축소한다. (b)/(c)는 D1(부호 뒤집힘)과 6,917 rows / 1,381 ids라는 작은 표(QMOF의 1/3, hMOF의 1/20)를 떠안는다. Beam 1이 n=1–3으로 붕괴할 수 있어 median 지표가 무의미해질 위험.

**Q6. Anchor task와 방향, 그리고 objective의 형태.**
옵션 (a) homopolymer Tg-max (b) Tg-min(방향 인식 검증용) (c) copolymer Tg-max (d) **Fox residual δ(f) = Tg − Tg_Fox 최대화** (e) Tm 또는 density.
함의: 모든 threshold가 방향 인식적이고 Agent 1 prompt의 axis menu가 여기 의존한다(homopolymer Tg: median 410 / top-10% 563 / top-1% 657 K; 최소화 방향 277 / 195 K). **(d)가 전략적으로 특별하다** — Fox는 무료이고 R² 0.835라 경쟁자로 두면 이기지만, residual을 objective로 두면 해석적 null이 자기 잔차를 최적화할 수 없다. 이 선택은 **M3에서 표가 동결되기 전에** 내려져야 한다.

**Q7. pre-proposal 기여 #3(regime-aware modelling)은 살아남는가?**
옵션 (a) 5-regime RegimeRouter를 1급 기여로 유지 (b) **ablation arm 1개로 강등**(3 judge 전원 권고) (c) 모논문의 2-way mode switch로 축소.
함의: 이것은 PI 본인의 pre-proposal 기여이므로 기술적 판단만으로 결정할 수 없다. 3 judge 전원이 cut을 권고했고 S3 본인도 §15.2에서 "Tg에서 그 가치는 거의 0 — 노이즈 안에서 고르는 것"(surrogate 간 차이 ~5 K RMSE vs replicate SD 7.0 K)이라 쓴다. 유지하면 5개 rule block이 모든 matched set의 **상류**에 confound로 들어간다.

**Q8. pre-proposal 기여 #2(surrogate meta-loop)는 어떤 형태로 살아남는가?**
옵션 (a) LLM이 매 캠페인 surrogate를 선택 (b) 결정적 router + per-regime MAE slack (c) **오프라인 사전등록 bake-off 1회** + 모논문의 `_apply_mae_slack` 그대로.
함의: (a)는 세 번째 model call을 추가하고 그 효과가 Agent 1의 효과와 분리 불가능해진다 — W2의 210 seeded campaign에서 어떤 변형도 Holm 보정 후 수동 튜닝 기본값을 이기지 못했다. (c)는 DB mode에서 **surrogate가 아예 없다**는 S1/S3의 구조적 방어를 보존한다.

**Q9. 더 완전한 PoLyInfo 재export가 가능한가?**
필요 항목: 절단된 terpolymer 4,243–7,389 row의 `component3..5`; 5,309개 미확정 binding을 해결할 per-sample component 레코드; canonical component-id → SMILES 표; 손상되지 않은 `copolymer.zip`; XLSX per-pid 집계 규칙.
함의: 없으면 copolymer 표가 그만큼 줄고 그 축소가 논문에 보고되어야 한다. **떨어진 세 번째 단량체는 어떤 추론으로도 복원되지 않는다.** T2 headline을 한정하는 수치가 여기 달려 있다.

**Q10. 데이터 정책 3건(감사가 "소유자 전용"으로 분류한 것).**
(a) Tg가 충돌하는 XLSX 중복 구조 30개 group(최대 spread **169 K**)과 충돌 이름 77 group(최대 212 K): 평균/보존/제외? (b) cis-trans·tacticity 변이: 별개 단량체인가 trimer key에서 병합인가? (c) 조성 없는 42.6% row: 별도 모델링인가 제외인가?
함의: 이것들이 달성 가능한 RMSE 상한과 top-1% threshold를 정한다. **169 K 충돌을 median으로 뭉개는 것은 수리가 아니라 결정이다.**

**Q11. Feedback에서 이름/SMILES를 억제할 것인가?**
옵션 (a) 억제(S1 D-1, S3 §3.2) (b) 모논문처럼 표시(S2) (c) **억제 + 이름 표시 arm 10 replicate로 비용 측정**.
함의: 억제는 누출 채널을 닫고 memorisation 채널을 좁히며 Art. 10(1) 노출을 줄이지만, MOF agent가 갖던 입력을 제거하므로 "byte-identical" 주장과 충돌한다. (c)가 유일하게 그 비용을 **수치로** 만들고 동시에 memorisation 채널을 직접 측정한다. S1 스스로 "judgement call"이라고 적은 항목.

**Q12. LLM provider, key, 예산 승인.**
옵션 (a) GPT-5.2(모논문 Table 1 및 $1.06/campaign과 최대 비교가능성) (b) Claude (c) 둘 다 + backend benchmark.
함의: 현재 어느 scope에도 API key가 없다. **어느 쪽을 고르든 Anthropic branch는 새로 작성해야 한다**(C18: Table 1의 Claude arm 3개를 만든 client가 repo에 없음). 예산: DB-mode 전체 프로그램 + 6-backend benchmark ≈ 330 campaign ≈ **$350–500**, 6 concurrent에서 ~32 h.

**Q13. PFAS Phase 2는 진행하는가?**
옵션 (a) 별도 GCMC-oracle 발견 캠페인으로 재구성(Polymatic 망상 고분자 + 자체 pool) (b) 데이터셋 결정이 날 때까지 gate (c) 범위에서 제외.
함의: 공개 SMILES-labelled 고분자 흡착제 PFAS 데이터셋은 **없다**. pre-proposal의 anchor 인용(Dangayach 2025)은 dataset 논문이 아니라 **review**이므로 Related Work의 foil을 교체해야 한다. 흡착제 계열은 망상 고분자라 2-slot 단량체 표로 표현 불가. pre-proposal의 "Weeks 5–8" 일정은 성립하지 않는다. 또한 PPN-6 연구의 메커니즘이 pre-proposal에서 **반대로** 요약되어 있다(정전기·수소결합이 short-chain을, 소수성·친불소성이 long-chain을 구동).

**Q14. Replicate 예산과 fidelity의 교환.**
옵션 (a) 5(LLM4MOF 충실, Table 1 비교가능) (b) **10**(측정된 σ 6.4–15.9 percentile point에서 통계적으로 적절) (c) headline 10 / grid 5.
함의: 비용은 어느 쪽이든 무시할 만하다(캠페인 당 ~$1). 이것은 **어떤 주장이 방어 가능한가**의 문제다 — n=5면 SEM이 2.9–7.1 point라 Table-1식 "0.1 point 이내" 진술은 노이즈 안이다. 그리고 arm 수가 늘어나면(V0 / no-feedback / hint-ablation / GC-gate / no-ledger …) **다중비교 보정 계획**이 함께 필요하다 — S3의 현재 누락 지점.

---

### 부록 — 이 문서가 의도적으로 인용하지 않은 수치

검증 패킷이 `refuted`로 판정했거나 추정량이 혼용된 항목: 설계공간의 평문 곱(518×156×952 = 76,929,216 — 올바른 값은 connectivity-matched sum **12,499,656**); SF₆ "7.7 vs 2.8"(iteration-10 통계와 pooled reference의 혼합; iteration-10 random median은 2.55); W2 grid "14 variants × 3 tasks × 2 budgets"(실제는 42 cells × 5 reps); ledger가 random beam을 전면 배제한다는 서술(`beam_medians`용으로는 ingest됨); SI의 "transcript가 압축된다"는 서술(코드는 압축하지 않음); REF-105의 R² 0.83(MD-vs-experiment가 아니라 MD 값에 적합한 ML 모델의 R²); REF-112 저자명(Karuth, Alesadi, Xia, Rasulev); REF-134 저자명(단독 저자 Luis A. Miccio); REF-140 메커니즘(방향 반전); REF-141(인용 URL 무효).
