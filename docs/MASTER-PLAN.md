# MASTER-PLAN — LLM4POL charter

- **Status:** Approved
- **Version:** 1.0
- **Date:** 2026-09-21
- **Approved by:** owner, on `PROJECT-FOUNDATION-PROPOSAL.md` v0.1 (ADR-0005)
- **Precedence:** highest source of truth (ADR-0002). GSD artifacts are derived from this file
  and may not redefine the project's purpose. Frozen sections change only through
  `governance/AMENDMENTS.md`.

본문은 한국어, 식별자·계약·명령은 영어. 이 파일에서 **Frozen**으로 표시된 절은 소유자 결정과
amendment 없이는 바뀌지 않는다. 그 외는 ADR(charter-owned) 또는 GSD 계획(plan-owned)으로 바뀐다.

---

## 1. 문제 정의와 성공 기준 — Frozen

**연구 질문.** 가설을 세우고 근거로 수정하는 LLM 루프가, 같은 평가 예산의 무작위·GA·BO
탐색보다 "열전도율은 높고 유전율은 낮으며 Tg는 충분한" 반복단위를 더 잘 찾는가. 그리고 그
이득이 어느 설계 축(사슬 치수·자유부피·응집에너지 창 / 작용기 화학 / 골격 클래스)에서
오는지를 통제 비교로 귀속시킬 수 있는가.

**설계 문제** (ADR-0004). 열전도율 최대화, 유전율 낮게, Tg 충분히 — 전자 패키징용 열전도성
전기절연체. 목적함수의 *형태*와 임계값은 게이트 파라미터(§13, ADR-0005). 개발 기본값은 제약
단일목적: `max thermal_conductivity s.t. dielectric_const_dc ≤ table Q25, tg ≥ 400 K`.

**성공 기준.** 층위별로 다르며 섞어 쓰지 않는다.

| 층위 | 주장 | 증거 | 마일스톤 |
|---|---|---|---|
| L1 | 프로그램이 실행된다 | 결정적 선택기로 10 iteration 완주, 같은 seed 재실행 동일 | M4 |
| L2 | 평가·예산·기록이 올바르다 | evaluator·ledger 계약 테스트, resume/replay byte-identical | M2–M3 |
| L3 | LLM이 관측으로 다음 선택을 바꾼다 | feedback 유·무 두 run의 질의 diff | M5 |
| L4 | 비교 방법보다 효과적이다 | 측정된 σ 위에서 사전등록된 비교 | M7 |
| L5 | 물리·실험 타당성 | 실험 TC와의 순위 상관; live 값과의 차이 | M8/M9 |

테스트 통과는 연구 성과가 아니다. LLM arm이 비교 방법에 지더라도 L1–L3와 L4의 *보고*는
그대로 성립한다.

## 2. 범위와 명시적 비목표 — Frozen

**최소 범위 (첫 논문).** PolyOmics `general_polymers`를 hidden table로 하는 database mode
전체 루프; 무작위·GA·BO와의 예산 일치 비교; 실험 TC 출처와의 sim-to-real 점검.

**비목표 (첫 논문).** 분자량·분산도 설계(데이터에 없음, ADR-0004); 공중합 조성 축; 루프 안의
실시간 MD oracle(D-06); 합성 검증; 7월 제안서의 regime 개념; 대리모델 학습.

## 3. 행위자와 사용자

| 행위자 | 역할 |
|---|---|
| 소유자 | 과학 결정, 게이트 파라미터 확정, 리뷰 승인 |
| 코딩 에이전트 (Claude Code, GSD) | 구현·검증. 자기 작업을 자기 컨텍스트에서 승인하지 않음 |
| 과학 에이전트 (hypothesis / translator) | **API 호출**이지 서브에이전트·별도 서비스가 아님. 상태 유무와 프롬프트로 역할 분리 |
| 결과의 사용자 | 귀속된 이득 수치, 후보 목록과 근거, sim-to-real 점검 결과를 읽는 독자 |

## 4. 불변식과 제약

강제 가능한 부분집합은 `governance/INVARIANTS.md`에 있고 guard를 가진다. 헌장이 추가하는 것:

| ID | 불변식 | Guard |
|---|---|---|
| A-1 | evaluator는 인터페이스. `table`과 `radonpy`는 같은 계약을 공유하되 정확도가 같다고 가정하는 코드는 없다 (`provenance_tier`) | schema + import-linter (M2) |
| A-2 | 루프 패키지는 시뮬레이션 backend를 import하지 않는다 (ADR-0003) | import-linter (M2) |
| A-3 | 예산은 `evals`와 `cpu_hours` 두 통화를 분리 집계한다 | ledger schema (M3) |
| A-4 | 호스팅 LLM으로 나가는 payload에 행 id·테이블 크기·percentile·임계값·전역 통계가 없다 (D-19). PoLyInfo 내용은 D-04 | payload 테스트 (M5) |
| A-5 | 결과가 보고된 프롬프트·스키마는 제자리 수정하지 않고 버전을 올린다 | `protocol/` 규칙; 테스트 (M5) |
| A-6 | run 디렉터리는 append-only. 재실행은 새 id | ledger 테스트 (M3) |
| A-7 | `static_dielectric_const`는 registry에 존재하지 않는다; `dielectric_const_dc`만 (ADR-0004) | registry schema + validator (M1) |
| R-5' | production code는 이 헌장이 `Status: Approved`를 선언하는 동안만 존재한다 | `tests/test_governance.py` |

## 5. 핵심 아키텍처와 근거

LLM4MOF에서 가져온 것은 **구조**다: 고정 예산의 닫힌 루프, 상태 있는 가설 에이전트 + 상태
없는 번역기, 전체 가설/수치 창 제거/1차 축만/무작위의 4-beam 귀속, 목표 blind feedback,
사실만 담는 bounded memory, 싸구려 lookup에서 먼저 개발. 축의 *내용*, 후보 표현, vocabulary,
oracle, 인터페이스는 고분자 문제(ADR-0004)에서 도출하며 LLM4MOF와의 byte 호환은 유지하지
않는다.

```
problem spec ─► selector (deterministic | LLM agents) ─► query ─► table lookup ─► 4 beams
                     ▲                                                              │
                     └──────────── feedback (blind) + memory ◄── evaluator ◄─────────┘
                                                                 │
                                                        ledger (append-only) ─► reduce ─► results.csv
```

**기각한 대안.**

| 대안 | 기각 이유 |
|---|---|
| LLM4MOF 인터페이스 byte 호환 이식 | CLAUDE.md의 프레이밍 결정. MOF 전용 필드(topology, node, metals)가 계약을 오염 |
| 3목적 Pareto를 처음부터 | hit가 스칼라가 아니라 percentile·enrichment·GA/BO가 복잡해짐; ledger가 세 값을 다 기록하므로 사후 재분석 가능 |
| 공개/비공개 DB 물리 분리로 blind 보장 | 불필요. blind는 API로 나가는 payload를 테스트해서 보장 (A-4) |
| 에이전트를 서브에이전트/서비스로 | 역할 분리는 프롬프트와 상태로 충분; 재현성과 비용 추적이 어려워짐 |
| 대리모델을 개발 oracle로 | 대리모델 오차를 물리로 학습하게 됨 (ADR-0003) |

## 6. 도메인 모델과 컴포넌트 경계

**후보.** `candidate_id = sha256(canonical_psmiles + "|" + tacticity)[:16]`. canonical_psmiles는
두 `*` 중합점을 가진 반복단위의 RDKit canonical SMILES, 입체 유지 (D-6). 같은 후보의 여러
행은 replicate로 취급하고 median·개수·spread를 보존한다 (D-7, D-9, D-10). 행이 replicate인지
다른 tacticity인지는 M1이 밝힌다.

**Property registry** (`protocol/schemas/property-registry.json`). 단위·조건은 M1에서 HF 데이터
카드·arXiv:2511.11626과 대조 후 확정; 그 전까지 unverified.

| key | column | unit | 역할 |
|---|---|---|---|
| `thermal_conductivity` | `thermal_conductivity` | W/(m·K) | 목표 |
| `dielectric_const_dc` | `dielectric_const_dc` | – | 제약 |
| `tg` | `tg`, `tg_rmse` 필터, 100–900 K | K | 제약 |
| `rg`, `r2`, `ffv`, `sp_ced`, `density`, `refractive_index` | 동명 | 각각 | 중간 변수 / validator |

**패키지 경계** (`src/llm4pol/`).

| 패키지 | 책임 | import 금지 |
|---|---|---|
| `data` | fetch(pinned revision), load → parquet, identity, validate → report | `loop`, `llm` |
| `evaluate` | 계약, registry, cache, budget, `backends/table` (M9: `backends/radonpy`) | `loop`, `llm` |
| `run` | run id, JSONL ledger, config snapshot, resume, replay/reduce | `loop`, `llm` |
| `loop` | problem spec, tags, beams, `select/deterministic`, (M5) `agents`, feedback, memory | `evaluate.backends.radonpy` |
| `llm` | provider adapter 1개 | 모든 것; `loop.agents`만 import 가능 |

## 7. 주요 인터페이스와 동결 시점

| 인터페이스 | 위치 | 동결 마일스톤 |
|---|---|---|
| 후보 정의, property registry, 스냅샷 식별자 `polyomics:general_polymers@<hf_revision>` | §6, `protocol/schemas/property-registry.json` | M1 |
| Evaluator 요청/응답 | `protocol/schemas/eval-request.json`, `eval-response.json` | M2 |
| Import 경계 | `pyproject.toml [tool.importlinter]` | M2 |
| Run 기록 형식, problem spec | `protocol/schemas/{ledger-event,problem-spec}.json` | M3 |
| 가설·질의·tag vocabulary | `protocol/schemas/{hypothesis,query,tag-vocabulary}.json` | M4 |
| 프롬프트 v1, feedback 형식 | `protocol/prompts/*_v1.md`, `protocol/schemas/feedback.json` | M5 |
| 목적함수 형태·임계값·지표·replicate 수 | `experiments/PREREG-<date>.md` (sha256 커밋) | M6 |

**Evaluator 계약** (M2에서 스키마로 동결).

```json
// request
{"run_id": "...", "iteration": 3, "batch": [
  {"candidate_id": "...", "properties": ["thermal_conductivity", "dielectric_const_dc", "tg"]}]}
// response, one entry per (candidate, property)
{"candidate_id": "...", "property": "thermal_conductivity",
 "status": "ok | unsupported | missing | error",
 "value": 0.31, "unit": "W/(m·K)", "n_replicates": 2, "spread": 0.02,
 "backend": "table", "source": "polyomics:general_polymers@<hf_revision>",
 "provenance_tier": "md_simulated", "cached": false, "cost": {"evals": 1, "cpu_hours": 0.0}}
```

`unsupported`(registry에 없음)·`missing`(행은 있으나 값 없음)은 예산을 소비하지 않고, `error`는
재시도 대상. 캐시 키 `(candidate_id, property, backend, source)`; 적중은 `evals` 불변.

**Problem spec.**

```json
{"objective": {"property": "thermal_conductivity", "direction": "max"},
 "constraints": [{"property": "dielectric_const_dc", "op": "<=", "value": 2.6},
                 {"property": "tg", "op": ">=", "value": 400.0}],
 "form": "constrained_single",
 "budget": {"iterations": 10, "candidates_per_beam": 10, "beams": 4},
 "table": "polyomics:general_polymers@<hf_revision>", "seed": 0}
```

**가설 → 질의.** 세 축, ADR-0004 §5에서 도출.

| 축 | 내용 | 질의 |
|---|---|---|
| A1 창 | 중간 변수 수치 창 (`rg`, `ffv`, `sp_ced`, `density`) | `{property: [min, max]}` |
| A2 화학 | 작용기·헤테로원자·고리 태그, RDKit SMARTS로 결정적 계산. LLM이 쓴 필드는 필터에 쓰지 않음 | include AND / any-of OR / exclude |
| A3 골격 | 1차 축: 주쇄 클래스 | 단일 태그 |

4 beam = `full`(A1+A2+A3) / `chem`(A2+A3) / `primary`(A3) / `random`. 모든 beam은 같은 샘플링
규칙(seed 고정, 목표값을 읽지 않는 층화). 0-match iteration은 예산을 소비하지 않고 `no_match`
이벤트로 기록.

**Run 기록** (`experiments/<run-id>/`, run-id = `<UTC timestamp>-<8 hex>`).

```
meta.json     problem spec, code git sha, prompt versions, provider/model, seed, snapshot hash
ledger.jsonl  append-only events: selection / evaluation / feedback / iteration-close
usage.json    tokens, USD, evals, cpu_hours
results.csv   iteration, beam, n, median_tc, feasible_frac, pct_of_table, hits_top10, hits_top1
```

`resume`는 마지막 완결 iteration 다음부터; 같은 `(run_id, iteration, beam)` 이벤트는 두 번
기록되지 않는다. `replay`는 ledger만으로 `results.csv`를 byte-identical 재생성한다.

## 8. 의존성 우선 빌드 순서 (런타임 흐름과 다름)

런타임은 selector → query → evaluate → feedback 순으로 돌지만, 빌드는 다른 것이 의존하는
것부터: **M0 기반 → M1 데이터·registry → M2 evaluator 계약 → M3 run 기록 → M4 결정적 e2e →
M5 LLM → M6 분산·사전등록 → M7 비교 → M8 sim-to-real → M9 live.** 병렬 가능: M1 안의
fetch/identity ∥ validate; M2 ∥ M3 (M3는 응답 형식만 필요); M7 ∥ M8.

## 9. 테스트·검증 전략

- 게이트: `pixi run --manifest-path env/pixi.toml check` = ruff, format, mypy strict,
  import-linter, pytest. 커밋 전 통과, CI 두 플랫폼.
- 모든 경계 payload는 `protocol/schemas/`의 JSON Schema로 검증되고 테스트가 스키마를 로드한다.
- 불변식은 코드가 생기는 마일스톤에서 테스트로 승격 (`INVARIANTS.md` 승격 정책).
- 마일스톤 완료 = §13 종료 기준의 **재현**. 각 GSD phase의 `VERIFICATION.md`는 종료 기준
  번호를 인용한다.
- 저작과 리뷰는 별도 패스 (`REVIEW-CHECKLIST.md`).
- 분할 프로토콜: DB mode에 train/test 분할은 없다. 막는 것은 (a) LLM의 파라메트릭 기억 →
  zero-feedback arm의 memorisation share (M6) + A-4; (b) replicate 누출 → 후보 단위 dedup 후
  샘플링; (c) noise 이하 효과 → M1 noise floor를 모든 plot에, M6 σ 아래 차이는 효과로 보고하지
  않음. sim-to-real(M8)은 겹치는 반복단위의 순위 상관으로 답하며 분할과 무관. 대리모델이
  루프에 들어오는 순간 scaffold-grouped split을 ADR로 추가.

## 10. 데이터·상태 소유권

| 것 | 소유자 | 위치 | 재배포 |
|---|---|---|---|
| PolyOmics 스냅샷 (CC BY 4.0) | `data.fetch`, pinned HF revision | `data/raw/polyomics/<rev>/`, `data/processed/polyomics-<rev>.parquet`; `data/MANIFEST-open.sha256`에 해시 | 허용(귀속 필요), 크기 때문에 미커밋 |
| PoLyInfo 파일 | ADR-0001 | `data/raw/`, `data/MANIFEST.sha256` | **금지** |
| Validator report | `data.validate` | `docs/audit/polyomics-<rev>-validation.md` (숫자의 권위 문서) | 집계치만 |
| Run 출력 | `run` | `experiments/<run-id>/` git-ignored | PoLyInfo 유래가 섞이는 M8 전까지는 법적 제약 없음; 정책은 그대로 미커밋 |
| 프롬프트·스키마 | `protocol/` | 버전 파일 | 커밋 |
| 사전등록 | 소유자 | `experiments/PREREG-<date>.md` + 커밋된 sha256 | 커밋 |

저장 형식: 단일 parquet + JSON manifest; append-only JSONL ledger. DB·서비스·공개/비공개 분리
없음. SQLite는 필요해질 때 ledger에서 재구성 가능한 파생물로만.

## 11. 외부 서비스·API 경계

| 경계 | 방향 | 계약 |
|---|---|---|
| Hugging Face (`yhayashi1986/PolyOmics`) | 읽기, M1 | pinned revision, sha256 manifest |
| LLM provider (D-14, M5) | 요청/응답 | `llm.provider` adapter 1개, `config/llm.json` + schema, 키는 `.env`만. payload는 A-4 |
| dirac PBS (D-18, M9) | job manifest / result JSON | `config/hpc.json` + `scripts/submit.py`, hpc-submit skill 규약 |
| OpenPoly / PoLyInfo (D-17, M8) | 읽기 | 같은 evaluator 계약, `source`만 다름 |

## 12. 보안·프라이버시·재현성 경계

- 비밀값은 `.env`에만; 출력·로그·커밋 금지 (R-3). 존재 여부는 시작 시 검사하되 값은 읽지 않음.
- 재현성: `meta.json`에 code git sha, 스냅샷 해시, 프롬프트 버전, seed, provider/model.
  `replay`가 byte-identical. LLM 비결정성은 replicate와 σ로 다루며 숨기지 않는다.
- PoLyInfo 층은 M8까지 코드 경로에 없다; 들어올 때 D-1..D-6을 테스트로 승격.

## 13. 마일스톤, 종료 기준, 결정 게이트

| ID | 이름 | 의존 | 산출 | 종료 기준 (재현 가능한 검사) | 동결 |
|---|---|---|---|---|---|
| **M0** | 재현 가능한 개발 기반 | 헌장 | 초기 커밋; `env/pixi.toml`에 `huggingface_hub`; `.env.example`; 게이트 유지 | `pixi run check` 두 플랫폼 green; 첫 커밋 존재; `.env` 미추적 | 없음 (명시) |
| **M1** | 데이터 기반 | M0 | `data/{fetch,load,identity,validate,schema}.py`; `data/MANIFEST-open.sha256`; parquet; validator report | (1) pinned revision 파일 sha256 = manifest (2) 행 수, unique units, 필터 후 43,561, `static_dielectric_const` Maxwell 위반 88.9 %, `dielectric_const_dc` 위반 0 이 재현되거나 차이 문서화 (3) 95,335 vs 73,045 해소 (4) replicate 구조와 TC·ε·Tg noise floor 기록 (5) 개발 기본 임계값의 feasible 집합 크기 보고 (6) D-7..D-10, A-7 테스트 승격 | 후보 정의, registry, 스냅샷 id |
| **M2** | Evaluator (table) | M1 | `evaluate/{contract,registry,cache,budget,backends/table}.py`; `eval-*.json`; import-linter 첫 계약 | ok/unsupported/missing/error 각각 테스트; 캐시 적중 시 `evals` 불변; 배치 100건 순서·개수; 모든 응답에 source·backend·provenance_tier; 스키마 검증이 게이트에 포함 | evaluator 계약, A-1, A-2 |
| **M3** | 실행 관리 | M2 | `run/{ids,ledger,config,resume,reduce}.py`; `experiments/README.md` 갱신 | 중단→resume 후 중복 이벤트 0; replay byte-identical; `usage.json` 두 통화 = ledger 합 | run 기록, problem spec, A-3, A-6 |
| **M4** | 최소 e2e (결정적) | M3 | `loop/{problem,beams,tags,select/deterministic}.py`; hypothesis/query/tag-vocabulary 스키마; CLI `llm4pol run --selector deterministic` | 같은 seed 두 run 출력 동일; 4 beam n ≥ 1 기록; 10 iteration < 5 min; no_match 예산 불소비 | 가설·질의·vocabulary |
| **M5** | LLM 루프 | M4, **D-14** | `llm/provider.py`; `loop/agents/{hypothesis,translator}.py`; feedback, memory; 프롬프트 v1; `config/llm.json`+schema | 10 iteration 완주; 스키마 통과율 기록; feedback 유·무 두 run의 질의 diff 제시(L3); 토큰·USD 기록; A-4 payload 테스트가 게이트에 | 프롬프트 v1, feedback |
| **M6** | 분산·통제·사전등록 | M5, D-15 | replicate 배터리; zero-feedback arm; `PREREG-<date>.md` | 10 replicate × (결정적, LLM, zero-feedback); σ 수치; memorisation share; **D-16 형태·임계값·지표·replicate 수를 담은 사전등록 sha256 커밋** | **D-16** |
| **M7** | 비교 arm | M6 | random / GA / BO, 같은 evaluator | 실현 evals가 LLM arm ±5 %; 두 통화; 결과 표에 모집단·n | 없음 |
| **M8** | sim-to-real | M6, **D-17** | 실험 TC backend(`source`만 다름); PoLyInfo loader 첫 등장 | 겹치는 반복단위 수; 순위 상관과 CI | D-17 |
| **M9** | live mode (게이트) | M8, **D-18** | `backends/radonpy`, `config/hpc.json`, `scripts/submit.py` | finalist ≤ 할당; 첫 round-trip; table vs radonpy 차이 보고 | D-18 |

**게이트 파라미터** (ADR-0005). 값이 개발 기본값과 다르게 확정되면 `AMENDMENTS.md`에 기록.

| 파라미터 | 개발 기본값 | 확정 시점 |
|---|---|---|
| D-16 목적함수 형태·임계값 | constrained single; ε ≤ Q25; Tg ≥ 400 K | M6 사전등록 |
| D-17 실험 TC 출처 | OpenPoly; PoLyInfo 재수출 병행 요청 | M8 진입 |
| D-18 live 범위 | 첫 논문 밖 | M9 진입 |
| D-14 provider | 미정 | M5 진입 |
| D-15 replicate·보정 | M6에서 측정 후 MDE로 결정; Holm | M6 |

**첫 e2e (M4) 입력과 예상 출력.** 입력: 위 problem spec(seed 0), M1 스냅샷, 결정적 선택기
(iteration 1 = seed로 뽑은 골격 태그 1 + 작용기 태그 2, A1 창 없음; i > 1 = 이전 full beam
feasible 상위 5의 rg/ffv 중앙값 ±20 %를 A1 창으로), 최대 400 evals. 출력: `meta.json`,
≈10×(1+1+4+≤40+1) 이벤트의 `ledger.jsonl`, `usage.json {evals ≤ 400, cpu_hours 0, tokens 0}`,
`results.csv`. random beam median이 테이블 median 근처에 평평하고 full이 위로 움직이면 파이프
라인이 살아 있는 것이며, **이 곡선은 연구 결과가 아니다.**

**전이 조건.** M4→M5: M4 종료 기준 + D-14 키 + `config/llm.json` 스키마 통과. M5→M6: L3 검사와
A-4 테스트. M6→M7: σ·memorisation share 보고 + 사전등록 sha256 커밋 — **그 전에는 어떤 비교
수치도 주장하지 않는다.** M6→M8: D-17. M8→M9: D-18 + `config/hpc.json`.

## 14. GSD와의 관계

`.planning/ROADMAP.md`는 §13을 **참조**하고 복제하지 않는다. `STATE.md`가 실행 상태,
phase별 `VERIFICATION.md`가 종료 기준 번호를 인용한 증거. GSD가 생성한 산출물은 이 헌장과
drift 대조 후 구현 시작 (ADR-0002). 게이트 파라미터를 GSD 산출물이 조용히 확정하면 drift다.
