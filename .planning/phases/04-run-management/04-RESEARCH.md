# Phase 4: Run Management - Research

**Researched:** 2026-09-29
**Domain:** append-only run records (JSONL ledger with a header line), resume, byte-identical replay, two-currency usage accounting, problem spec schema (charter M3)
**Confidence:** HIGH for what was read or probed on this machine; MEDIUM for cross-platform byte identity (no Linux host was available, so it rests on documentation until the two-platform CI run)

**How facts were obtained.** Every in-repo and precedent file named below was opened in full this
session with line numbers (`cat -n` through the shell, which is how this session routes reads).
Every number was produced by a read-only probe in the pixi environment (`PYTHONPATH=src`), with
scripts kept in the session scratchpad. Nothing was written under `src/`, `tests/`, another phase's
directory, LLM4MO or LLM2POR.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Copied verbatim from `04-CONTEXT.md` `<decisions>` ("Implementation Decisions (proposed; each cites its source)").

#### D-01 Run identity and meta (charter §7)
`run_id = <UTC YYYYMMDDTHHMMSSZ>-<8 hex>`. `experiments/<run_id>/` is created with `mkdir(exist_ok=
False)`; an existing directory is refused with the twin's message shape ("run exists; use replay").
`meta.json` is written once and holds the charter's fields — problem spec, `code_git_sha` (+`dirty`),
`prompt_versions` ({} until Phase 6), `provider`/`model` (null until Phase 6), `seed`, `snapshot`
(`polyomics:general_polymers@041e5834`), `registry_version`, `created_at` — and, from LLM4MOF, any
secret-shaped config value is written as `***REDACTED***`, asserted by a test.

#### D-02 Ledger events (`ledger.jsonl`, `protocol/schemas/ledger-event.json`)
One canonical JSON object per line (`sort_keys`, `separators=(",",":")`, `allow_nan=False`, LF).
**The first line is a header** (`{schema_version, run_id, problem, provenance{seed, snapshot,
registry_version, selector, code_git_sha}}`); `resume` and `replay` read the problem from it rather
than from CLI arguments, so a resumed run cannot silently change its own problem (D-21, taken from
LLM4MO; the text format is kept so the record stays readable and diffable).
Every later line is an event with the envelope
`{seq, ts, run_id, iteration, event, payload}`. Event kinds for M3: `run_opened`,
`iteration_opened`, `selection`, `evaluation`, `no_match`, `iteration_closed`, `run_closed`.
Phases 5–6 add `hypothesis`, `query`, `feedback`, `llm_call` without changing the envelope.
**No hash chain** — neither reference uses one (see D-03 for what replaces it).

#### D-03 Integrity by replay, not by chaining (from LLM4MO)
Append-only is enforced three ways, all proven in the sibling project:
1. `run` refuses an existing run directory; a rerun gets a new id (A-6 as a precondition).
2. A byte-prefix test: after every append, the previous file content is a prefix of the new content.
3. **Replay-sequence match**: `resume` replays the ledger and asserts the deterministic selector's
   expected prefix equals what was recorded, refusing to continue on mismatch. This catches a doctored
   or truncated ledger at the only moment it matters — when the run is continued or a result is
   re-derived — without making a repaired ledger unusable.
`replay` ends by printing `result_sha256` over the canonical reduced result, so a published number
has a hash anyone can recompute from the committed record.

#### D-04 Usage, metrics and replay output
`usage.json = {evals, cpu_hours, tokens, usd}` — `evals`/`cpu_hours` summed from `evaluation` event
costs, never combined (A-3); `tokens`/`usd` 0 until Phase 6. From LLM4MOF, **every per-iteration
metric row carries its population**: `results.csv` columns `iteration, beam, n, n_population,
median_tc, feasible_frac, pct_of_population, hits_top10, hits_top1`, and `run_summary.json` carries
`percentile_trend[]` and `candidate_count_trend[]`. `replay` regenerates `results.csv` from
`ledger.jsonl` alone, byte-identical.

#### D-05 Problem spec (`protocol/schemas/problem-spec.json`)
Charter §7 exactly, with the twin's strictness: `extra` forbidden, `schema_version` pinned,
`budget > 0`, constraints referencing registry keys only, `form` enum `["constrained_single"]` with
`"pareto"` reserved (D-16 gated). A committed example goes in the `schema-inventory` gate step.

#### D-06 Package boundary
`llm4pol.run` may import `llm4pol.evaluate` and `llm4pol.data`; forbidden from `llm4pol.loop` and
`llm4pol.llm`. Contract added with the package.

#### D-07 CLI
`python -m llm4pol.run {run|resume|replay|usage} …` — the twin's verb set. Exit 0 / 2 (schema, IO) /
4 (sequence mismatch or duplicate event). Errors print one generic message (twin's convention) with
detail on stderr only.

#### Owner decisions (answered 2026-09-23 / 2026-09-24, verbatim from `<open_for_owner>`)

| # | Question | LLM4MO (twin) | **Decision for LLM4POL** |
|---|---|---|---|
| A | Ledger storage | SQLite, header row + events | **JSONL with a header line** — the twin's resume-safety property, text format kept (D-21) |
| B | Data partitions | `development / validation / test` | **None**; charter §8 stands — DB mode trains nothing, so there is no model to overfit. A scaffold-grouped split enters by ADR when a surrogate first joins the loop (D-22) |
| C | Contract types | pydantic `BaseModel` (frozen, extra=forbid, strict) | **Keep frozen dataclasses + JSON Schema** — built and green in Phase 3; the schemas check the contract from outside the language and ride the `schema-inventory` gate step (D-23) |
| D | Public/private data split | `public/` and `priv*/` jsonl directories | **No physical split** — blindness is guaranteed by testing the payload that leaves for the provider (A-4), not by storage layout; revisit if the Phase 6 payload test proves insufficient (D-24) |

| # | Question | **Decision** |
|---|---|---|
| E | `experiments/` git policy | **Commit the summaries, ignore the ledger** — `meta.json`, `usage.json` and `results.csv` are tracked so a published number can be cited from inside the repository; `ledger.jsonl` stays ignored for size. ADR-0001's wording is corrected in the same change, since its licence reason no longer covers the PolyOmics layer (D-27) |

Phase boundary (verbatim): "Not in scope: selector, beams, tags, feedback text, agents (Phases 5–6).
Phase 4's tests drive the ledger with a stub selection (a plain list of candidate ids) and exercise
the reducer on recorded events only."

`CALF20_DiscoveryLoop` is **not** a source for this phase.

### Claude's Discretion

`04-CONTEXT.md` has no section with this name. The points the context leaves unspecified, and which
this research therefore treats as discretion or as owner questions, are listed in
`## Open Questions` with the status of each.

### Deferred Ideas (OUT OF SCOPE)

Copied verbatim from `<deferred>`:

- Selector, beams, tag vocabulary, feedback, memory → Phases 5–6.
- `evidence_class` / `reference` provenance fields (twin) → revisit at M8 when a second source exists.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (REQUIREMENTS.md) | Research support |
|----|-------------------------------|------------------|
| RUN-01 | A run has id `<UTC timestamp>-<8 hex>`; `experiments/<run-id>/meta.json` records problem spec, code git sha, prompt versions, provider/model, seed and snapshot hash | F-51 (id shape probe), F-52 (git sha and the `dirty` trap), F-24 (parquet metadata carries `llm4pol.source_sha256`), F-46..F-49 (redaction), Pattern 1, Pitfalls 9 and 10 |
| RUN-02 | `ledger.jsonl` is append-only; one event per selection, evaluation, feedback and iteration-close; a rerun gets a new id | F-33..F-40 (JSONL probes), F-05 (twin's existing-ledger guard), F-56 (self-contained schema probe), Pattern 2, Pitfalls 1, 2, 3 |
| RUN-03 | `resume` continues from the last closed iteration and never records the same `(run_id, iteration, beam)` event twice | F-01..F-08 (twin), F-57..F-59 (spike: 13 crash points, 0 duplicates; naive resume diverges), Pattern 3, Pitfalls 4, 5 |
| RUN-04 | `replay` regenerates `results.csv` from the ledger alone, byte-identical to the original | F-26..F-32 (CSV probes), F-11..F-17 (parent metric definitions), F-18..F-23 (population), Pattern 4, Pitfalls 6, 7, 8 |
| RUN-05 | `usage.json` totals for `evals` and `cpu_hours` equal the ledger sums; tokens and USD are reported separately | F-42 (charging rule), F-58 (sum by result equals sum by response cost), F-56 (schema refuses a merged cost field), Pattern 5 |
| RUN-06 | Problem specs validate against `protocol/schemas/problem-spec.json` | F-55 (draft schema probe, 7 of 8 cases), F-54 (NaN passes `type: number`), F-53 (cross-file `$ref` fails in the gate step), Pattern 6 |
</phase_requirements>

## Summary

Phase 4 adds one package, `llm4pol.run`, and installs nothing: every mechanism it needs is in the
standard library (`json`, `csv`, `hashlib`, `secrets`, `bisect`, `statistics`, `os.fsync`) or already
locked (`jsonschema` 4.26.0). The sibling port LLM4MO proves the design the context adopted: a header
that binds the run to its problem, a ledger that is the only source of budget state, and a policy
sequence that is checked rather than assumed. What LLM4MO gets from SQLite for free — atomic appends,
a primary-key sequence, a read-only open — has a plain JSONL equivalent, and each equivalent was
probed here.

A scratch spike drove the real `Evaluator` over the synthetic table with a stub selection, crashed
it at each of 13 event boundaries and resumed. With the cache and the meter **rebuilt from the
ledger**, all 13 resumed ledgers and all 13 `results.csv` files were byte-identical to the
uninterrupted run with zero duplicate keys. With a fresh cache and meter (the naive resume), 6 of 13
diverged and charged 6 evals instead of 5. That is the central design rule of this phase.

Four findings change what the plan must contain, and each is raised to the owner rather than
resolved here:

1. **The population number in D-26 is a row count.** `42,733` is rows (`all source rows`); the
   candidate-level population under the same filter is **39,454**, against **40,212** for the README
   triple. `n_population` in `results.csv` will print 39,454.
2. **"From the ledger alone" and "percentile of a population" pull against each other.** A percentile
   needs the population's distribution, which lives in the parquet. The ledger must therefore carry
   the population reference. Three ways to do it are laid out in Open Question OQ-1.
3. **Three of the six metric columns have no definition anywhere.** `feasible_frac`, `hits_top10`
   and `hits_top1` appear only as column names in the charter; LLM4MOF computes none of them.
4. **`results.csv` column names differ between the charter and the context.** Charter §7 and
   LOOP-06 say `pct_of_table`; CONTEXT D-04 says `pct_of_population` and adds `n_population`.

**Primary recommendation:** build `llm4pol.run` so that the ledger is the single source of state —
header on line 1 written with `open("xb")`, one fsynced binary append per event, cache and meter
reconstructed from `evaluation` events on every resume, `results.csv` produced by a pure function of
the parsed events and written as bytes — and settle OQ-1 to OQ-4 with the owner before the run
record format freezes.

## Project Constraints (from CLAUDE.md)

Directives extracted from `CLAUDE.md` and `.claude/CLAUDE.md`. The plan must honour each.

| # | Directive | Consequence for Phase 4 |
|---|-----------|-------------------------|
| C-1 | Precedence: charter > REQUIREMENTS.md > `CLAUDE.md` > generated blocks. A conflict is flagged to the owner, never resolved silently | OQ-2, OQ-3 and OQ-5 are conflicts of this kind and are flagged, not resolved |
| C-2 | Never act on a reopened decision; read `DECISIONS-LOG.md`, `INVARIANTS.md`, `ENGINEERING-OPERATING-MODEL.md` first | No reopened decision touches this phase. D-21, D-22, D-27 are Accepted; D-26 is Recorded |
| C-3 | A decision in the log is not binding architecture until it appears in the charter or an accepted ADR | D-27 changes charter §10; it needs an ADR and a charter edit (OQ-5) |
| C-4 | Production code exists only while the charter declares `Status: Approved` | Holds: charter is `Approved`, v1.0 |
| C-5 | No data file of either layer is committed; `data/raw/`, `data/interim/`, `data/processed/` stay ignored | Tests run on the synthetic root; real-file tests skip |
| C-6 | Content sent to a hosted LLM never carries row ids, table size, percentiles, thresholds or global statistics (A-4, D-19) | The ledger will hold percentiles and population sizes. Nothing in Phase 4 sends anything; Phase 6's payload test is the guard. See Pitfall 12 |
| C-7 | Never print or log `.env` contents or a secret value | `meta.json` redaction; CLI errors are generic |
| C-8 | `protocol/schemas/`: a payload with no schema has no guard; a schema that produced a reported result is never edited in place | `ledger-event.json` and `problem-spec.json` land with committed examples in `[tool.llm4polcheck]` |
| C-9 | `config/`: every file has a sibling `*.schema.json`; no secrets | Phase 4 adds no file under `config/` |
| C-10 | `experiments/`: append-only; a rerun gets a new identifier | A-6 guard lands as a ledger test |
| C-11 | `docs/governance/ADR/`: `NNNN-kebab-case.md`, contiguous numbering, Status and Date lines | A new ADR is `0007-…` |
| C-12 | `pixi run --manifest-path env/pixi.toml check` passes before anything is committed; CI runs it on Windows and Linux | Baseline today: 7/7 steps, 189 tests (F-60) |
| C-13 | Authoring and review are separate passes (`REVIEW-CHECKLIST.md`) | Verification is a separate pass |
| C-14 | A rule that matters becomes a test, a schema or a CI check | A-3 (ledger guard) and A-6 become tests here; `INVARIANTS.md` gains rows |
| C-15 | A number is published in one place; an unverified transcription is labelled unverified | Every number below carries its population and source |
| C-16 | A milestone is done when its exit criterion is reproduced. Placeholder notes, skipped tests, stubs and unimplemented branches are blockers | The "stub selection" must not be a stub in production code (OQ-7) |
| C-17 | Conventional commits, scoped by GSD plan id | `feat(04-01): …` |
| C-18 | Coding style (global rules): immutable data, files under 800 lines, functions under 50 lines, explicit error handling, validation at boundaries | Frozen dataclasses as in Phase 3; `BudgetMeter`-style replace-not-mutate |
| C-19 | TDD: test first (RED), then implementation (GREEN) | Plans order tests before code, as Phases 2 and 3 did |

## Facts the plan may cite

Status is `verified` (read or probed this session) or `unverified` (reasoned, documented elsewhere,
or not reproducible on this host). Line ranges are from this session's read.

### LLM4MO — run, resume, replay (Question 1)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-01 | The header is built in the evaluator constructor, verbatim: `self._header = {"schema_version": 1, "problem": problem.model_dump(mode="json"), "oracle_sha256": self._artifact, "provenance": provenance, "max_attempts": 4 * problem.budget}`. It is stored as canonical JSON in table `metadata`, row `id=1` (`CHECK(id=1)`) | verified | `[VERIFIED: LLM4MO/src/llm4mo/database_evaluator.py:44-54]` |
| F-02 | On every open the header is recomputed from the current environment and compared byte for byte: `elif row[0] != canonical(self._header): raise EvaluationError("Run configuration or source changed")`. `provenance` carries `python` and `code_sha256` for six modules, so a resumed run refuses to continue after any change to those modules | verified | `[VERIFIED: database_evaluator.py:55-56; database_run.py:45-50]` |
| F-03 | `_replay()` reads events ordered by id and checks three things: the sequence (`if event_id != index or index > self._header["max_attempts"]: raise EvaluationError("Invalid ledger sequence")`), the shape (strict pydantic parse of request and response), and the **content** — it recomputes `expected = decide(request, self._records, cache, self._problem.budget, self._artifact)` and raises `"Ledger replay mismatch"` when `response != expected`. Every `ValueError` is re-raised as `"Ledger integrity check failed"`. The cache is rebuilt inside the loop: `if response.charged: cache[request.candidate_id] = response` | verified | `[VERIFIED: database_evaluator.py:67-84]` |
| F-04 | The policy-sequence check runs for all three verbs, before anything is appended: `previous = evaluator.replay()`, `expected = random_requests(eligible, problem.budget, seed)`, `if tuple(request for request, _ in previous) != expected[:len(previous)]: raise EvaluationError("Random policy sequence mismatch")`. The policy is a pure function of `(eligible ids, budget, seed)`, so the full expected sequence is known up front | verified | `[VERIFIED: database_run.py:95-98; random_policy.py:8-11]` |
| F-05 | The existing-ledger guard applies to the verb `run` only: `if args.ledger.exists(): raise EvaluationError("Run ledger already exists; use replay")`. `resume` and `replay` take `problem`, `partition` and `seed` from the header (`read_header`), opened read-only so a typo cannot create a database: `sqlite3.connect(ledger.resolve().as_uri() + "?mode=ro", uri=True)` | verified | `[VERIFIED: database_run.py:54-57, 76-88]` |
| F-06 | `decide()` order: unknown candidate → `invalid`; candidate in cache → copy with `{"cached": True, "charged": False, "spent": spent}`; `spent >= budget` → `budget_exhausted`; otherwise charged, `spent + 1`. `spent = len(cache)`: the budget counter is **derived from the ledger**, never stored on its own. Every attempt, including `invalid`, `budget_exhausted` and cached, is recorded as an event; `max_attempts` bounds the ledger | verified | `[VERIFIED: database_evaluator.py:19-32]` |
| F-07 | LLM4MO **charges a `missing` bundle** (`status="missing" if missing else "ok"` with `charged=True`). LLM4POL does not: `unsupported`, `missing`, `error` and cache hits cost nothing (EVAL-02, F-42). The twin's accounting cannot be copied | verified | `[VERIFIED: database_evaluator.py:29-32; llm4pol/evaluate/evaluator.py:21-26]` |
| F-08 | `resume` continues by index: `run_random(eligible, evaluator, problem.budget, seed, completed=len(previous))`, which evaluates `requests[completed:]`. The result ends with `result["result_sha256"] = hashlib.sha256(canonical(result).encode()).hexdigest()`. Errors print one JSON message on **stdout** and return **1** | verified | `[VERIFIED: database_run.py:99-114; random_policy.py:14-19]` |
| F-09 | The twin's tests for this behaviour: `run` on an existing ledger returns 1; `replay` and `resume` on a complete ledger return the same result as the first `run`; a ledger holding one event resumes to `attempts == 3` with `duplicates == 0`; editing one stored response makes reopening raise `"integrity"`; a failed insert rolls back and leaves `replay() == ()` | verified | `[VERIFIED: LLM4MO/tests/test_database_run.py:31-53; test_database_evaluator.py:83-97, 134-145]` |
| F-10 | What is SQLite-specific in the twin and needs re-expression: (a) `BEGIN IMMEDIATE` … `commit()` / `rollback()` — atomic append; (b) `events.id INTEGER PRIMARY KEY` — the sequence; (c) `metadata` with `CHECK(id=1)` — exactly one header; (d) `?mode=ro` — an open that cannot create; (e) `timeout=30` — writer exclusion; (f) journal rollback — a torn write is invisible | verified | `[VERIFIED: database_evaluator.py:47-62, 89-103]` |

### LLM4MOF — metric definitions (Question 2)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-11 | `percentile_of_candidate_median`: `cand_target = candidates[target_col].dropna()`, `full_target = full_db[target_col].dropna()`, `cand_median = float(cand_target.median())`, `percentile = float((full_target < cand_median).mean() * 100)`, stored as `round(percentile, 1)`. Strict less-than; the denominator is the number of **non-null** targets in the full table | verified | `[VERIFIED: LLM2POR_Core_20260319/core/metrics.py:46-66]` |
| F-12 | `n_total = len(full_db)` counts rows including those with a null target, so the recorded `n_total` is **not** the percentile's denominator whenever the target has nulls. `reduction_ratio = round(len(candidates) / n_total, 4)` | verified | `[VERIFIED: core/metrics.py:34, 60-65]` |
| F-13 | `candidate_stats` and `full_db_stats` are the same function `_stats(series)`: `mean`, `median`, `std` (pandas default, ddof=1), `min`, `max`, `p90` (`quantile(0.90)`), `p95` (`quantile(0.95)`), each `round(float(…), 2)`; an empty series gives `{}` | verified | `[VERIFIED: core/metrics.py:72-84]` |
| F-14 | `percentile_trend` is the list of `m.get("percentile_of_candidate_median", 0.0)`; `candidate_count_trend` the list of `m.get("n_candidates", 0)`; `improving = percentiles[-1] > percentiles[0]` when there are at least two; `best_iteration = best_idx + 1` where `best_idx` is the first argmax. `query`, `mode`, `target_metric`, `completed_iterations` are added by the pipeline | verified | `[VERIFIED: core/metrics.py:97-125; core/pipeline.py:253-258]` |
| F-15 | **An empty iteration is recorded as percentile `0.0`**, indistinguishable from the worst possible result. The read run shows it: `percentile_trend [62.9, 0.0, 63.4, 41.8, 47.6]`, `candidate_count_trend [3, 0, 99, 14, 2]`, `worst_iteration 2`, `worst_percentile 0.0` | verified | `[VERIFIED: core/metrics.py:36-44; experiments/exp_p3_v0_pormake_123/run_summary.json]` |
| F-16 | A failed iteration is skipped from `metrics_list` (`continue`), so `best_iteration` is a position in the list of **successful** iterations, not an iteration number | verified | `[VERIFIED: core/pipeline.py:236-244, 253]` |
| F-17 | `feasible_frac`, `hits_top10` and `hits_top1` are **defined nowhere**. In this repository they occur only as column names (`docs/MASTER-PLAN.md:183`, `REQUIREMENTS.md:55`, `ROADMAP.md:163`). LLM4MOF has no hit count: its `top_1_target` / `sample_top1` is the best value in a set (`round(float(s_target.max()), 4)`), and `first_hit_iteration` in `analysis/compare_runs.py` is "first iteration that reaches >= 50th percentile" | verified (absence confirmed by grep over both trees) | `[VERIFIED: grep this session; core/feedback.py:157; analysis/compare_runs.py:165-169]` |
| F-18 | LLM4MOF's run record is **not** append-only: `os.makedirs(self.run_dir, exist_ok=True)` and every file is opened with `"w"`. It has no resume and no replay. The "one immutable file per iteration" of the context is a convention of use, not something the code enforces | verified | `[VERIFIED: core/logger.py:57-61, 71, 91, 104]` |

### The population (Question 5)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-19 | The candidate parquet has **no** `check_tc` column; the rows parquet has. `build_candidates` aggregates only `PROPERTY_COLUMNS` plus `n_rows`, `canonical_psmiles`, `tacticity` | verified | `[VERIFIED: src/llm4pol/data/load.py:110-126; probe: pq.read_schema]` |
| F-20 | Measured now, after plan 02-06, on the in-scope rows (95,332): README triple **43,560** rows; triple ∧ `check_tc` **42,732** rows. D-26's `42,733` is the same filter on **all source rows** (`triple_check_tc_all_rows`), i.e. a row count | verified | `[VERIFIED: probe_population.py; src/llm4pol/data/expectations.py:108; docs/audit/polyomics-041e5834-validation.md:181]` |
| F-21 | **Candidate-level populations** (filter rows, then one row per candidate): README triple **40,212** candidates; triple ∧ `check_tc` **39,454** candidates. Both ids sets are subsets of the served candidate table (78,375 candidates, 68,792 with a TC median). Building both takes 0.29 s | verified | `[VERIFIED: probe_population.py, probe_synth_pop.py]` |
| F-22 | The population is obtained without re-implementing a filter: `filters.readme_triple_mask(rows, registry)`, `filters.check_tc_mask(rows, registry)` and `load.build_candidates(rows[mask])` (or `filters.candidate_level_triple(rows, registry)` for the README triple). Reading the 13 needed columns of the rows parquet takes 0.07 s | verified | `[VERIFIED: src/llm4pol/data/filters.py:74-86, 125-137, 150-167; probe]` |
| F-23 | **The evaluator serves unfiltered medians** ("No population filter of any kind is applied: a candidate outside the README triple or with `check_tc` False still gets its values"). On the 39,454 population the served TC median differs from the filtered median for **5,119** candidates (more than 5 % for 928, more than 20 % for 43; maximum relative difference 4.83). Served `dielectric_const_dc` differs for 6,599 (max absolute 19.9); served `tg` for 629 (max absolute 53,881 K). Served TC reaches 1.284 W/(m K) on two members, where the filtered maximum is 0.910 | verified | `[VERIFIED: src/llm4pol/evaluate/backends/table.py:10-14; probe_population2.py]` |
| F-24 | Both parquets carry these metadata keys, verbatim: `b"llm4pol.snapshot"`, `b"llm4pol.revision"`, `b"llm4pol.source_rows"`, `b"llm4pol.source_columns"`, `b"llm4pol.excluded_second_monomer"`, `b"llm4pol.excluded_parse_failure"`, `b"llm4pol.source_sha256"`. The last is the sha256 of the pinned CSV: the "snapshot hash" RUN-01 asks for | verified | `[VERIFIED: src/llm4pol/data/load.py:155-163]` |
| F-25 | Reference values on served medians: check_tc population — TC at 0.25 has 24,497 below (62.0900 %); the 3,945th largest value is 0.298965899; the 395th largest is 0.452962627. README triple — 24,589 below 0.25 (61.1484 %). 39,446 of 39,454 TC values are distinct, so `<` and `<=` differ on at most 8 ties. Feasible under the charter example's thresholds (`dielectric_const_dc <= 2.6`, `tg >= 400.0`) on served values: 5,533 of 39,454 and 5,620 of 40,212. Under the development default (Q25 of filtered medians): Q25 = 2.65038754225 and 6,645 feasible on the check_tc population; 2.6524122727500004 and 6,793 on the README triple | verified | `[VERIFIED: probe_population.py, probe_refsize.py]` |

### Byte-identical `results.csv` (Question 3)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-26 | Host facts: Python 3.13.15, `sys.float_repr_style == "short"`, `os.linesep == "\r\n"`, preferred encoding `cp949` | verified | probe_csv.py |
| F-27 | `open(path, "w")` + `csv.writer(fh)` writes **`\r\r\n`** on Windows (6 CR for 3 rows). `newline=""` + default writer writes `\r\n` on every platform (the `excel` dialect's terminator). `newline=""` + `lineterminator="\n"` writes LF only: 0 CR, 3 LF. `newline="\n"` + `lineterminator="\n"` gives the same bytes (same sha256) | verified on win32 | probe_csv.py; `[CITED: github.com/python/cpython/blob/v3.13.9/Doc/library/csv.rst]` |
| F-28 | pandas 3.0.5 `to_csv` writes CRLF on Windows by default, **including into a `StringIO`**; `lineterminator="\n"` fixes it. It renders NaN and None as the empty field | verified on win32 | probe_csv.py |
| F-29 | `repr(float)`, `str(float)` and `json.dumps(float)` give the same text (shortest round-trip), e.g. `0.30000000000000004`, `1e-07`, `1e+16`, `1.0`. Fixed formats round: `f"{2/3:.4f}" == "0.6667"`. `csv.writer` renders `None` as the empty field and `float("nan")` as `nan` | verified | probe_csv.py |
| F-30 | Locale does not reach `repr`, `str`, `json.dumps` or `format(x, ".4f")`: under `de_DE.UTF-8`, `German_Germany.1252` and `fr_FR.UTF-8` (decimal point `,`) all four still print `1234567.891` / `1234567.8910`. Only the `n` format type follows the locale (`1,23457e+06`) | verified | probe_csv.py |
| F-31 | `statistics.median`, `numpy.median` and `pandas.Series.median` return the identical double on an even-length list (`0.271868171375`). `json.loads(json.dumps(v))` is bit-equal for all **742,085** served median and std values of the real candidate table; none is non-finite | verified | probe_csv.py, probe_misc.py |
| F-32 | `.gitattributes` holds `* text=auto eol=lf`. A committed LF `results.csv` has identical worktree and blob sha256; a CRLF file does not (git warns "CRLF will be replaced by LF"), so a CRLF summary would stop matching its own replay after a checkout | verified in a scratch repository | gitignore_probe |
| F-33 | **Not verified: Linux.** No Linux host, WSL or Docker is available here. That the recipe gives the same bytes on ubuntu-latest rests on the csv and `open` documentation. The proof is a test that pins the sha256 of a `results.csv` reduced from a committed fixture ledger and runs on both CI legs | unverified | `[ASSUMED]` until the CI run |

### JSONL append and partial writes (Question 4)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-34 | Binary append (`open("ab")`, one `write` of a line ending in `b"\n"`) produces 0 CR and keeps non-ASCII as UTF-8. `open("xb")` on an existing ledger raises `FileExistsError` | verified on win32 | probe_jsonl.py |
| F-35 | Truncating the last line at each of its 168 byte positions: 1 leaves a clean file (nothing of the line written), 165 leave a tail that is invalid JSON, 1 leaves a torn UTF-8 character (`UnicodeDecodeError` on a text read), and **1 leaves complete, valid JSON with only the final LF missing**. No proper prefix of a JSON object parses, so the rule "the file ends with LF and every LF-terminated line parses" catches all 167 torn states | verified | probe_jsonl.py |
| F-36 | Text-mode iteration **hides** the missing-LF case: it yields the unterminated line and `json.loads` accepts it. `JsonlCache._replay` reads this way (`open("r", …)` with `enumerate(fh)`), which is acceptable for a derived cache and not for the ledger | verified | probe_jsonl.py; `[VERIFIED: src/llm4pol/evaluate/cache.py:86-98]` |
| F-37 | Cost on this machine: open-append-flush-close 0.185 ms per event; with `os.fsync` 0.601 ms; keeping the handle open with fsync 0.330 ms. A campaign of about 470 events costs about 0.28 s in fsync. Reading and parsing 4,701 lines (710 KiB) takes 0.019 s | verified | probe_jsonl.py (Phase 3 measured 2.1 ms per fsync, F-36 there; the order of magnitude agrees) |
| F-38 | `os.fsync` calls `fsync` on Unix and `_commit` on Windows; a buffered Python file needs `f.flush()` first | cited | `[CITED: github.com/python/cpython/blob/v3.13.9/Doc/library/os.rst]` |
| F-39 | `json.loads` accepts `NaN` and `Infinity` by default and collapses duplicate keys (`{"seq":1,"seq":2}` → `{"seq": 2}`). `parse_constant` and `object_pairs_hook` refuse both | verified | probe |
| F-40 | Byte-prefix pattern that worked in the probe and the spike: `before = path.read_bytes()`; append; `after = path.read_bytes()`; `assert after.startswith(before) and len(after) > len(before)` | verified | probe_jsonl.py, spike_run.py |

### Evaluator facts the ledger depends on

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-41 | `EvalResult.to_json()` has twelve fields plus `reason` when set: `candidate_id`, `property`, `status`, `value`, `unit`, `n_replicates`, `spread`, `backend`, `source`, `provenance_tier`, `cached`, `cost`. Status values, verbatim: `Status = Literal["ok", "unsupported", "missing", "error"]`. `EvalResult.from_json` type-checks every field and raises `ValueError` | verified | `[VERIFIED: src/llm4pol/evaluate/contract.py:30, 124-207]` |
| F-42 | Charging: `evals = 1 if lookup.status == "ok" and entry.candidate_id not in charged else 0` — one eval per candidate per request on its first non-cached `ok` property. A cache hit is returned as `dataclasses.replace(hit, cached=True, cost=Cost(0, 0.0))`. `_CACHEABLE = frozenset({"ok", "missing"})` | verified | `[VERIFIED: src/llm4pol/evaluate/evaluator.py:45, 93-105]` |
| F-43 | `BudgetExceeded` is raised **before** anything is committed and is "never a per-result status"; the CLI maps it to exit 3 (`EXIT_OK = 0`, `EXIT_INPUT = 2`, `EXIT_BUDGET = 3`). CONTEXT D-07 lists exits 0 / 2 / 4 and does not mention 3 | verified | `[VERIFIED: src/llm4pol/evaluate/budget.py:46-53; src/llm4pol/evaluate/evaluator.py:111-116; src/llm4pol/evaluate/__main__.py:44-46]` |
| F-44 | `JsonlCache(path=None)` is memory-only; `put_many` is its only way to add records and it also appends to `path` when one is set. `Evaluator(backend, properties, *, cache=None, meter=None, evals_limit=None)` accepts both a prepared cache and a prepared meter | verified | `[VERIFIED: src/llm4pol/evaluate/cache.py:51-83; src/llm4pol/evaluate/evaluator.py:63-76]` |
| F-45 | `eval-request.json`: `run_id` is `{"type": "string", "minLength": 1}` (no pattern); `iteration` is `{"type": "integer", "minimum": 0}`; `batch` has `"minItems": 1, "maxItems": 1000`; `candidate_id` pattern `^[0-9a-f]{16}$`; `properties` has `"uniqueItems": true` | verified | `[VERIFIED: protocol/schemas/eval-request.json:10-27]` |

### Secret redaction (Question 7)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-46 | LLM4MOF's rule is a key-name rule with an exact, lowercased match: `_REDACTED_FIELDS = {"openai_api_key", "api_key", "secret", "token", "password"}` and `"***REDACTED***" if str(k).lower() in _REDACTED_FIELDS`. It misses `CLAUDE_API_KEY`, `GEMINI_API_KEY` and `hf_token` | verified | `[VERIFIED: LLM2POR_Core_20260319/core/logger.py:24, 36-47; probe_misc.py]` |
| F-47 | The names this project can meet, from `.env.example`: `LLM_PROVIDER`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`. No key of `meta.json` as D-01 defines it is secret-shaped. **`usage.json` has the key `tokens`**: a substring rule on the scanner's words (`_CRED_WORDS = ("KEY", "SECRET", "TOKEN", "PASSWORD", "PASSWD", "CREDENTIAL", "APIKEY")`, applied case-insensitively) would redact it, and also `max_tokens` and `token_budget` | verified | `[VERIFIED: .env.example:2-5; scripts/history_secret_scan.py:90; probe_misc.py]` |
| F-48 | A suffix rule on the singular word separates the two groups correctly in the probe: `(?:^|_)(?:api_?key|secret|token|password|passwd|credential)$`, case-insensitive, matches `openai_api_key`, `OPENAI_API_KEY`, `api_key`, `CLAUDE_API_KEY`, `GEMINI_API_KEY`, `hf_token`, `password`, `secret` and does not match `tokens`, `max_tokens`, `token_budget`, `key`, `candidate_id`, `code_git_sha` | verified | probe_misc.py |
| F-49 | `scripts/history_secret_scan.py` exports `PATTERNS` (ten value-shape classes) and is importable from tests through `tests/conftest.py`'s `sys.path` insertion. It is **not** importable from `src/llm4pol` without making production code depend on `scripts/`. On a redacted `meta.json` text the patterns give no hit; on an unredacted provider key they give `openai_secret_key`. The tracked summaries are also covered by the gate's `history-secret-scan` step once committed | verified | `[VERIFIED: scripts/history_secret_scan.py:140-203; tests/conftest.py:34-38; probe_misc.py]` |
| F-50 | LLM4MO never writes a key at all: its summary reports `"api_key_configured": bool(...)`. This matches charter §12 ("존재 여부는 시작 시 검사하되 값은 읽지 않음") better than writing a redacted placeholder | verified | `[VERIFIED: LLM4MO/src/llm4mo/settings.py:24-32; docs/MASTER-PLAN.md:236]` |

### Run identity

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-51 | `f"{now:%Y%m%dT%H%M%SZ}-{secrets.token_hex(4)}"` gives e.g. `20260929T010203Z-3edf27ad`: 25 characters, matches `^\d{8}T\d{6}Z-[0-9a-f]{8}$`, and contains none of the characters Windows forbids in a file name | verified | probe_misc.py |
| F-52 | `git rev-parse HEAD` returns the 40-hex sha (exit 0). **`git status --porcelain` reports the tree dirty today** because of one untracked planning directory. A `dirty` flag computed that way is true on almost every run; writing `experiments/<run-id>/meta.json` would itself make the next run dirty | verified | probe_misc.py |

### Schemas (Questions 6 and 9 support)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-53 | A relative cross-file `$ref` (`{"$ref": "eval-response.json"}`) fails under plain `jsonschema.validate` with `_WrappedReferencingError: Unresolvable: eval-response.json`. It resolves only with an explicit `referencing.Registry`. `scripts/check.py::validate_inventory` calls `jsonschema.validate(instance=instance, schema=schema)` with no registry, so `ledger-event.json` must be **self-contained** | verified | probe_schema.py; `[VERIFIED: scripts/check.py:151-154]` |
| F-54 | `{"type": "number"}` accepts a Python `nan`. Combined with F-39, a problem spec file holding `NaN` as a threshold parses and validates unless the reader passes `parse_constant` | verified | probe_schema.py |
| F-55 | A draft `problem-spec.json` (closed objects, `schema_version` const 1, `form` enum `["constrained_single"]`, property enum read from the registry schema, positive integer budget fields, `table` pattern `^polyomics:general_polymers@[0-9a-f]{8}$`) behaved as intended on 7 of 8 cases; the eighth is F-54. **The charter's example as printed is rejected** because it has no `schema_version` | verified | probe_schema.py |
| F-56 | A draft self-contained `ledger-event.json` (`oneOf` header / event; `if`/`then` payload rules per event kind; `cost` and `result` copied into `$defs`) accepted a header, `selection`, `evaluation` and `no_match`, and refused: an unknown event kind, a selection without `beam`, a cost with a third field, a cost without `cpu_hours`, a cached result with `evals: 1`, an extra envelope key, `seq` given as a boolean, a header with an extra key. 12 of 12 | verified | probe_schema.py |
| F-57 | `validate_inventory` loads each matched instance as **one JSON document** (`json.load`). A `.jsonl` file cannot be an inventory instance; the committed examples must be single-object `.json` files. `instances` is a glob, so several example files can share one schema | verified | `[VERIFIED: scripts/check.py:137-154]` |
| F-58 | The registry schema's key list, verbatim: `"thermal_conductivity", "dielectric_const_dc", "tg", "rg", "r2", "ffv", "sp_ced", "density", "refractive_index"` | verified | `[VERIFIED: protocol/schemas/property-registry.json:28-39]` |

### Spike: stub selection through the real evaluator

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-59 | On the synthetic table, a stub selection of four `(iteration, beam)` entries produced 13 events in this order: `run_opened, iteration_opened, selection, evaluation, selection, evaluation, iteration_closed, iteration_opened, selection, evaluation, no_match, iteration_closed, run_closed`. The ledger is 8,640 bytes with 0 CR | verified | spike_run.py |
| F-60 | Ledger evals summed over results (5) equal the sum of response costs (5). In iteration 1, beam `random`, `evals` is 2 while only 1 candidate has an `ok` objective: a candidate whose TC is missing is still charged for its first `ok` property. **`evals` is not the number of candidates with an objective value** | verified | spike_run.py |
| F-61 | Crashing before each of the 13 appends and resuming **with the cache and meter rebuilt from the ledger**: 13 of 13 ledgers byte-identical to the uninterrupted one, 13 of 13 `results.csv` byte-identical, 0 duplicate `(iteration, beam, event)` keys. The clock and run id were injected constants | verified | spike_run.py |
| F-62 | The same with a fresh cache and meter: 7 of 13 identical; evals per crash point `[5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 5, 5, 5]` against a reference of 5. A resume that does not rebuild state overcharges and changes `cached` flags | verified | spike_run.py |

### Git policy (Question 6)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-63 | Today's rules, verbatim: line 37 `# run outputs: derived from PoLyInfo data (redistribution) and large/numerous.`, line 39 `experiments/*`, line 40 `!experiments/README.md` | verified | `[VERIFIED: .gitignore:37-40]` |
| F-64 | Adding `!experiments/*/meta.json` (and the other two) after `experiments/*` does **nothing**: `git check-ignore -v` attributes all three files to `.gitignore:1:experiments/*`, and `git status` lists only the README. The run directory itself is excluded, and "It is not possible to re-include a file if a parent directory of that file is excluded" | verified | gitignore_probe (git 2.53.0); `[CITED: git-scm.com/docs/gitignore]` |
| F-65 | The pattern that works (see Code Examples): re-include the directory (`!experiments/*/`), ignore its contents (`experiments/*/*`), re-include the three files. Result: `meta.json`, `usage.json`, `results.csv` untracked-and-visible; `ledger.jsonl`, `run_summary.json`, `cache.jsonl` and `nested/meta.json` ignored; `experiments/PREREG-2026-10-01.md` and a stray file at the top level ignored. The same holds for paths that do not exist yet | verified | gitignore_probe |
| F-66 | `git check-ignore -v` exits **0 for a re-included file** and prints the negated pattern (`.gitignore:5:!experiments/*/meta.json`). Only the form without `-v` separates the cases by exit code: 1 for `meta.json`, 0 for `ledger.jsonl` | verified | gitignore_probe |
| F-67 | The governance test asserts two substrings and one file: `assert "experiments/*" in gitignore, "run outputs must be git-ignored (ADR-0001)"`, `assert "!experiments/README.md" in gitignore, …`, `assert (ROOT / "experiments" / "README.md").is_file()`. **It still passes unchanged under the new pattern**, so it would stop stating the policy without failing | verified | `[VERIFIED: tests/test_governance.py:91-95]`; gitignore_probe |
| F-68 | **ADR-0001 contains no sentence about `experiments/`.** Its decision is "No data file is ever committed." and its guard names only `data/raw/`, `data/interim/`, `data/processed/`. The PoLyInfo rationale for ignoring run outputs lives in: `.gitignore:37`, `tests/test_governance.py:93`, `experiments/README.md`, `README.md:47` (`experiments/ run outputs; git-ignored except the README`), the `CLAUDE.md` table row, and charter §10 (`Run 출력 … git-ignored … 정책은 그대로 미커밋`) | verified | `[VERIFIED: docs/governance/ADR/0001-repository-location-and-data-handling.md:25-46; docs/MASTER-PLAN.md:218]` |
| F-69 | `CHANGE-POLICY.md` classes "Architecture, component boundaries, major interfaces" as charter-owned, changed by "An ADR that supersedes the relevant one, plus a charter edit". `DECISIONS-LOG.md` states a decision "is **not** binding architecture until it appears in `MASTER-PLAN.md` or an accepted ADR" | verified | `[VERIFIED: docs/governance/CHANGE-POLICY.md:5-10; docs/governance/DECISIONS-LOG.md:3-4]` |
| F-70 | The pre-registration file of Phase 7 (`experiments/PREREG-<date>.md`, charter §10 "커밋") is ignored by both the current and the new pattern. It needs its own re-include when Phase 7 arrives | verified | gitignore_probe |

### Import boundary (Question 8)

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-71 | Four contracts exist. The ones that already name `run`: the data contract forbids `"llm4pol.evaluate", "llm4pol.run", "llm4pol.loop", "llm4pol.llm", "sklearn"`; A-1 forbids `"llm4pol.loop", "llm4pol.llm", "llm4pol.run"` from `llm4pol.evaluate` | verified | `[VERIFIED: pyproject.toml:62-75]` |
| F-72 | A `forbidden` contract with `source_modules = ["llm4pol.run"]` **fails while the package is absent**: output `Module 'llm4pol.run' does not exist.`, exit 1. The contract and `run/__init__.py` must land in the same commit | verified | il_probe (import-linter 2.15); `[CITED: github.com/seddonym/import-linter/blob/main/src/importlinter/contracts/forbidden.py]` |
| F-73 | With the package present and importing `llm4pol.data.snapshot`, `llm4pol.evaluate.Evaluator` and `llm4pol.evaluate.backends.table.TableBackend`: `Contracts: 5 kept, 0 broken.` | verified | il_probe |
| F-74 | `run → loop` breaks the new contract with the chain `llm4pol.run.resume -> llm4pol.loop (l.1)`. `run → llm` breaks **two** contracts: the new one and the existing EVAL-06 rule (`source_modules = ["llm4pol.*"]`), which already covers `llm4pol.run` without being edited | verified | il_probe |
| F-75 | `evaluate → run` breaks A-1 today (`llm4pol.evaluate.budget -> llm4pol.run`). Neither the A-2 layers contract nor the EVAL-06 rule needs a change for Phase 4 | verified | il_probe |
| F-76 | Three existing assertions fail as soon as the package and its contract exist: `assert len(section["contracts"]) == 4`; `assert "Contracts: 4 kept, 0 broken." in output` with `assert output.count(" KEPT") == 4`; and `for name in ("loop", "llm", "run"): assert not (PACKAGE / name).exists(), name`. The comment in `scripts/check.py:201` says "declares four contracts" | verified | `[VERIFIED: tests/test_import_boundary.py:122, 154-155, 236-237; scripts/check.py:201]` |

### Environment and baseline

| # | Fact | Status | Source |
|---|------|--------|--------|
| F-77 | Gate baseline on this machine, this session: `SUMMARY: 7/7 steps passed`, `Contracts: 4 kept, 0 broken.`, `llm4polcheck inventory: 3 entries, 3 instances processed`, `189 passed in 61.36s`, wall clock 72 s | verified | gate run |
| F-78 | Versions in the pixi environment: Python 3.13.15, pandas 3.0.5, numpy 2.5.3, pyarrow 25.0.0, jsonschema 4.26.0, pytest 9.1.1, ruff 0.16.6, mypy 2.3.1, import-linter 2.15, pyyaml 6.0.3; pixi 0.80.0, git 2.53.0, gh 2.96.0 | verified | probe |
| F-79 | On the synthetic root **both populations are the same four candidates** (`7ec8cb49ff317efc`, `b3a635a55e1a6645`, `c3da5668f5a82772`, `d751b16095852737`; served TC `[0.155, 0.18, 0.2, 0.315]`). The only `check_tc == False` row of the fixture is already outside the triple. No test can show that the two populations are kept apart without an added row | verified | probe_synth_pop.py; `[VERIFIED: tests/conftest.py:64-79]` |
| F-80 | Charter §13 M4 expects "≈10×(1+1+4+≤40+1) 이벤트": four selections and up to **forty evaluation events** per iteration, i.e. one evaluation event per candidate (4 beams × 10 candidates), not one per beam | verified (the reading of the arithmetic is an inference) | `[VERIFIED: docs/MASTER-PLAN.md:269]` |

## Answers by question

### 1. LLM4MO's run / resume / replay — adopt and re-express

**Adopt as designed** (F-01..F-09):

| Property | LLM4MO | LLM4POL |
|---|---|---|
| The run is bound to its problem | header row, compared on every open | header line; `resume` / `replay` take the problem from it and never from CLI arguments (D-02) |
| Budget state has one source | `spent = len(cache)`, cache rebuilt by replay | meter and cache rebuilt from `evaluation` events on every resume (F-61, F-62) |
| Determinism is checked | policy prefix compared with the recorded requests | selector's recomputed selection compared with each recorded `selection` event, in order |
| `run` cannot touch an existing record | `args.ledger.exists()` | `mkdir(exist_ok=False)` on the run directory and `open("xb")` on the ledger |
| A response is released only after it is durable | commit before return | the append is flushed and fsynced before the next step; a failed append ends the process |
| The result carries its own hash | `result_sha256` over the canonical result | the same, over the canonical reduced result |

**Re-express for JSONL** (F-10, F-34..F-40):

| SQLite mechanism | JSONL equivalent |
|---|---|
| Transaction commit / rollback | One binary `write` of a complete line ending in LF, `flush`, `os.fsync`. A line counts only if it is LF-terminated |
| `events.id` primary key, `event_id == index` | Envelope field `seq`, contiguous from 1, equal to the line number minus one; checked on every read |
| `metadata` with `CHECK(id=1)` | Line 1 is the header and no later line may validate as a header |
| `?mode=ro` | `open("rb")` never creates a file; the run id is matched against its pattern before any path is built |
| Journal rollback hides a torn write | The reader detects the torn tail (F-35) and refuses; see OQ-6 |
| `timeout=30` writer exclusion | No equivalent. Single writer is an assumption (A5) |

**Do not copy:**

- The twin's content re-derivation (`response != expected`) needs the oracle. It fits `resume`, which
  has the table, and cannot be part of `replay`, which by RUN-04 reads the ledger alone.
- The twin's header comparison includes code hashes, so any code change blocks resume (F-02). Whether
  LLM4POL's `resume` refuses when `HEAD` differs from the header's `code_git_sha` is not stated in the
  context (OQ-8).
- The twin's accounting (a charged `missing`, a `budget_exhausted` status) contradicts EVAL-02 (F-07).
  Here `BudgetExceeded` is an exception raised before commit (F-43).
- The twin's full-sequence-up-front check works because its policy ignores observations. Phase 5's
  deterministic selector reads the previous `full` beam, so the expected selection can only be
  recomputed step by step from the ledger prefix.

### 2. LLM4MOF's metrics — what is defined and what is not

| `results.csv` column | Parent definition | Status for LLM4POL | Depends on the objective form (D-16)? |
|---|---|---|---|
| `n` | `n_candidates = len(candidates)`: the matched set, including members with a null target | Needs a statement: selected candidates, or candidates with an `ok` objective (F-60 shows they differ) | No |
| `n_population` | `n_total = len(full_db)`, which is not the percentile denominator (F-12) | Define as the denominator actually used: population members with a non-null objective | No; depends on the population (D-26) |
| `median_tc` | `float(cand_target.median())` after `dropna()` | Adoptable as is, over `ok` objective values | Column name assumes the objective is TC (fixed by ADR-0004); the reducer should read `problem.objective.property` |
| `pct_of_population` | `(full_target < cand_median).mean() * 100`, strict, rounded to 1 decimal | Adoptable. For `direction: "min"` the comparison reverses | **Yes**: direction; undefined as one scalar under `pareto` |
| `feasible_frac` | none | **Undefined** (F-17). Denominator and the treatment of a missing constraint value are open | **Yes**: thresholds and constraint list |
| `hits_top10`, `hits_top1` | none | **Undefined** (F-17). "top 10" as top decile or top ten candidates; among all members or among feasible ones | **Yes**: form and thresholds |
| `percentile_trend`, `candidate_count_trend` | F-14 | Adoptable per beam. Carry the iteration number with each entry (F-16) and render an empty beam as null, not `0.0` (F-15) | Inherits from `pct_of_population` |

Everything marked "Yes" must be computed by a function that takes the problem spec as an argument.
Nothing about thresholds or direction may be a literal in the reducer.

### 3. Byte-identical `results.csv` — the recipe

1. Reduce to rows of Python `int`, `float`, `str`, `None` by a pure function of the parsed events.
2. Render into `io.StringIO(newline="")` with `csv.writer(buffer, lineterminator="\n")`
   (`QUOTE_MINIMAL`).
3. Floats as `repr(x)`; integers as `str(i)`; a missing value as the empty field. Never `nan`,
   `None` or `0.0` for "no value".
4. Header and column order from one module-level tuple. Row order is ledger order.
5. `path.write_bytes(text.encode("utf-8"))` — no BOM, no text-mode file.
6. No pandas in the reducer (F-28), no `n` format type (F-30), `statistics.median` and `math.fsum`
   for the two aggregations.
7. Proof: one test reduces a committed fixture ledger and compares the sha256 with a constant, on
   both CI legs (F-33).

Verified on Windows (F-26..F-32); Linux is unverified until CI.

### 4. JSONL append and partial writes

See F-34..F-40 and Pattern 2. A crash mid-line leaves an unterminated tail; the reader must work on
bytes and require a final LF. `resume` refuses a torn tail by default (OQ-6 covers the repair path).
Fsync every event: 0.6 ms each.

### 5. The population

See F-19..F-25 and Code Example 5. The population comes from `llm4pol.data.filters` and
`llm4pol.data.load.build_candidates` on the rows parquet; the reducer never sees a filter. Both
populations are captured at run time and written into the ledger. The number to print is 39,454
candidates (check_tc) beside 40,212 (README triple).

### 6. Tracking summaries

See F-63..F-70 and Code Example 6.

### 7. Redaction

A key-name rule inside `llm4pol.run` (F-48), plus a test that runs the scanner's `PATTERNS` over the
written file (F-49). Prefer not writing a key at all and recording only whether it is configured
(F-50).

### 8. import-linter

One new `forbidden` contract; no change to A-2 or to the EVAL-06 rule; three test assertions and one
comment to update (F-71..F-76, Code Example 7).

### 9. Validation

See `## Validation Architecture`.

## Architectural Responsibility Map

The project has no browser, server or database tier. The tiers are the charter §6 packages.

| Capability | Primary tier | Secondary tier | Rationale |
|------------|-------------|----------------|-----------|
| Run id, run directory creation, `meta.json` | `llm4pol.run` (`ids`, `config`) | — | Charter §6 row `run`: "run id, JSONL ledger, config snapshot, resume, replay/reduce" |
| Problem spec parsing and validation | `llm4pol.run` (`config`) | `protocol/schemas/problem-spec.json` | The schema freezes at M3. `run` may not import `loop`, so the parsed type must live where Phase 5's `loop/problem.py` can import it |
| Ledger write, read, integrity checks | `llm4pol.run` (`ledger`) | `protocol/schemas/ledger-event.json` | The schema checks each line from outside the language (D-23) |
| Deciding what is charged | `llm4pol.evaluate` | — | Frozen at M2. `run` records costs; it never computes one |
| Rebuilding cache and meter on resume | `llm4pol.run` (`resume`) | `llm4pol.evaluate` (`JsonlCache`, `BudgetMeter`) | The ledger is the durable record; "The cache is a derived artifact" (`cache.py:12`) |
| Choosing candidates | caller of `llm4pol.run` (Phase 5 `loop`, tests in Phase 4) | — | Out of scope here; `run` defines only the protocol the selector satisfies |
| Population membership and values | `llm4pol.data` (`filters`, `load`) | `llm4pol.run` captures the result at run time | The reducer must not re-implement a filter |
| Metrics, `results.csv`, `usage.json` | `llm4pol.run` (`reduce`) | — | Pure function of ledger events |
| What is tracked in git | `.gitignore`, `tests/test_governance.py` | ADR, charter §10 | D-27 |

## Standard Stack

### Core

No new dependency. Everything is in the locked environment (F-78).

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| Python standard library | 3.13.15 | `json`, `csv`, `io`, `hashlib`, `secrets`, `datetime`, `os.fsync`, `bisect`, `statistics`, `math.fsum`, `subprocess`, `argparse`, `dataclasses` | Deterministic text and bytes; nothing to lock |
| jsonschema | 4.26.0 | `Draft202012Validator` for `problem-spec.json` and `ledger-event.json` | Already the validator of Phases 2 and 3 |
| pyarrow | 25.0.0 | Reading the rows and candidate parquets for the population | Already used by `TableBackend` |
| pandas | 3.0.5 | Only inside `llm4pol.data` calls (masks, `build_candidates`) | Not in the ledger or the reducer (F-28) |

### Supporting

| Library | Version | Purpose | When |
|---------|---------|---------|------|
| pytest | 9.1.1 | Tests | All plans |
| import-linter | 2.15 | The new contract | Plan that creates the package |
| mypy | 2.3.1 (strict) | Type checking of `llm4pol.run` | Gate step |

### Alternatives considered

| Instead of | Could use | Why not |
|------------|-----------|---------|
| JSONL + fsync | SQLite, as LLM4MO | Decided: D-21, charter §10 |
| Frozen dataclasses + JSON Schema | pydantic models | Decided: D-23 |
| `csv` module | `pandas.DataFrame.to_csv` | CRLF by default on Windows, even into a `StringIO` (F-28) |
| `repr(float)` | fixed precision (`.4f`) | Also deterministic, but it introduces a precision choice and a second rounding when the number is cited |
| `statistics.median` | `numpy.median` | Identical result (F-31); the standard library keeps the reducer free of array types |

**Installation:** none.

## Package Legitimacy Audit

This phase installs no external package. `gsd-tools query package-legitimacy check` was not run
because there is no candidate to check.

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| — | — | — | No install in this phase |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System architecture

```
 problem spec (JSON) ──validate──► ProblemSpec ─┐
                                                │
 run id + clock (injectable) ───────────────────┤
 git sha, snapshot id + source sha256,          │
 registry version ──────────────────────────────┤
                                                ▼
                                  create experiments/<run-id>/   (mkdir exist_ok=False)
                                  write meta.json once, ledger line 1 = header (open "xb")
                                                │
        ┌───────────────────────────────────────┘
        ▼
   read ledger bytes ──► LF rule, per-line schema, seq contiguity, no duplicate key
        │                        │ any failure ──► refuse (exit 4 / 2)
        ▼
   rebuild state from events:  done keys, JsonlCache (memory), BudgetMeter
        │
        ▼
   for each (iteration, beam) not yet recorded:
        selector(problem, seed, history) ──► candidate ids
             │  recorded selection exists? ──► recomputed == recorded, else refuse (exit 4)
             ▼
        ids empty ──► append no_match
        ids       ──► append selection ──► Evaluator.evaluate ──► append evaluation
                                              │ BudgetExceeded ──► append run_closed(budget_exhausted)
        ▼
   append iteration_closed … run_closed
        │
        ▼
   reduce(events)  ──► rows ──► results.csv bytes ──► write, sha256
                   ──► usage {evals, cpu_hours, tokens, usd}
                   ──► result_sha256

 replay  = read ledger ──► reduce ──► write/compare results.csv     (no table, no selector)
 usage   = read ledger ──► sums
 population reference: llm4pol.data (rows parquet) ──► captured once at run_opened, recorded in the ledger
```

### Recommended structure

Charter §13 M3 names the five modules `run/{ids,ledger,config,resume,reduce}.py`.

```
src/llm4pol/run/
├── __init__.py      # exports; no eager import of evaluate backends
├── __main__.py      # CLI: run | resume | replay | usage
├── ids.py           # run id, pattern, injectable clock and token source
├── config.py        # ProblemSpec (frozen dataclass), parse + schema, meta.json, redaction, git sha
├── ledger.py        # canonical line, header, append, read, integrity checks
├── resume.py        # state from events, selector protocol, campaign driver
├── reduce.py        # events -> rows -> csv bytes; usage; result hash
└── population.py    # population reference through llm4pol.data (not in the charter's list; implementation detail)
protocol/schemas/
├── problem-spec.json
└── ledger-event.json
protocol/examples/
├── problem-spec.example.json
├── ledger-header.example.json
└── ledger-event.<kind>.example.json     # one per event kind, matched by a glob
tests/
├── test_run_config.py      # RUN-01, RUN-06
├── test_run_ledger.py      # RUN-02, A-3, A-6
├── test_run_resume.py      # RUN-03
├── test_run_reduce.py      # RUN-04, RUN-05
├── test_run_cli.py         # D-07
└── test_run_real_file.py   # population sizes; skips without the parquet
```

### Pattern 1: Identity and clock are injected

**What:** `new_run_id(now, token)` takes the time and the random token as arguments; production
passes `datetime.now(timezone.utc)` and `secrets.token_hex(4)`. Every event's `ts` comes from the same
injected clock.

**Why:** `ts` and `run_id` are in every line. Two runs with the same seed cannot have identical
ledgers unless both are fixed, and LOOP-05 requires "identical `ledger.jsonl`". The spike's
byte-identity result (F-61) was obtained with both injected.

### Pattern 2: One complete line per append, read as bytes

**What:** serialise to canonical JSON, encode, append `b"\n"`, write once in binary mode, flush,
fsync. Read with `read_bytes()`, require the final LF, split on LF, decode and parse each line with
`parse_constant` and `object_pairs_hook` guards, validate each against the schema, check `seq`.

**When:** every ledger access. The canonical form is the one `cache.canonical_line` already uses
(`sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False`).

### Pattern 3: The ledger is the only state

**What:** `resume` derives from the events (a) the set of recorded keys, (b) a memory-only
`JsonlCache` seeded with every recorded result that has `cached == False` and status `ok` or
`missing`, (c) `BudgetMeter(evals=<sum>, cpu_hours=<fsum>)`, and passes (b) and (c) to `Evaluator`.
`run` is the same code path starting from a ledger that holds only the header.

**Why:** F-61 against F-62.

**Key for "the same event twice":** `(iteration, event)` for iteration-scoped kinds,
`(iteration, beam, event)` for `selection` and `no_match`, and `(iteration, beam, event)` or
`(iteration, beam, candidate_id, event)` for `evaluation` depending on OQ-9.

### Pattern 4: The reducer is a pure function with no I/O

**What:** `reduce(header, events) -> Reduced` returns rows, usage and summary as plain values.
Writing bytes is a separate two-line function. `replay` is `read → reduce → render → compare`.

**Why:** byte identity is then a property of one function that a test can call twice and hash.

### Pattern 5: Two currencies are summed separately

**What:** `evals = sum(int)`, `cpu_hours = math.fsum(float)`, over the `cost` of every result of
every `evaluation` event. `usage.json` is `{"evals", "cpu_hours", "tokens", "usd"}` with no fifth
field; the schema of the `cost` object has `additionalProperties: false` (F-56).

### Pattern 6: The problem spec is validated before it is typed

**What:** same order as `parse_request` in Phase 3: read text with `parse_constant` refusing
non-finite constants, validate against `problem-spec.json`, then build the frozen dataclass.
Registry keys come from the schema's enum, which a test compares with the registry schema's enum
(F-58) so the list is not published twice.

### Anti-patterns

- **A persistent evaluator cache beside the ledger.** If the process dies after the cache file is
  appended and before the ledger is, the next resume sees a hit the ledger never recorded and charges
  0 where the uninterrupted run charged 1.
- **Reading the ledger in text mode line by line** (F-36).
- **Continuing after a failed append.** The evaluator has already charged in memory; the only
  consistent state is the file.
- **A `0.0` for "no candidates"** (F-15).
- **A threshold, a direction or a property name as a literal in `reduce.py`.**
- **`pandas` in the reducer or the ledger** (F-28).
- **A cross-file `$ref` in a schema** (F-53).

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Population filters | a second triple or `check_tc` mask | `filters.readme_triple_mask`, `filters.check_tc_mask`, `load.build_candidates` | One definition; the validator report is the number authority |
| Charging | any cost arithmetic in `run` | `Evaluator.evaluate` and the recorded `cost` | Frozen at M2 |
| Result parsing | a new reader of result dictionaries | `EvalResult.from_json` | Type-checks every field (F-41) |
| Canonical JSON | a custom serialiser | `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` | Already proven byte-stable in Phase 3 |
| CSV quoting | string joins with commas | `csv.writer(..., lineterminator="\n")` | Quoting rules |
| Schema validation | hand-written field checks | `jsonschema.Draft202012Validator` | Same as Phases 2 and 3 |
| Secret value shapes | new regular expressions | `history_secret_scan.PATTERNS`, in tests | Ten classes with self-tests |
| Snapshot id and paths | string literals | `llm4pol.data.snapshot`, `PropertyTable.snapshot` | One place |
| Median, exact float sum | loops | `statistics.median`, `math.fsum` | Correct and order-independent |

**Key insight:** the two things this phase must get right — what was charged and which candidates
form the population — are already decided by code that exists. `llm4pol.run` records and tabulates;
it decides neither.

## Existing guards and documents that change

This is a greenfield package, so there is no runtime state to migrate. These existing items encode
the pre-Phase-4 state and must change in the same commits as the code:

| Item | Today | Change |
|------|-------|--------|
| `tests/test_import_boundary.py:122` | `assert len(section["contracts"]) == 4` | 5 |
| `tests/test_import_boundary.py:154-155` | `"Contracts: 4 kept, 0 broken."`, `output.count(" KEPT") == 4` | 5 |
| `tests/test_import_boundary.py:236-237` | `for name in ("loop", "llm", "run"): assert not (PACKAGE / name).exists(), name` | drop `"run"` |
| `tests/test_import_boundary.py` | no negative probe for `run` | add one on a scratch copy, as for A-2 (F-74) |
| `scripts/check.py:201` | comment "declares four contracts" | five |
| `pyproject.toml [tool.llm4polcheck]` | 3 entries | add the problem spec and ledger examples |
| `tests/test_governance.py:91-95` | substring test citing ADR-0001 | behavioural test of D-27 (F-66, F-67) |
| `.gitignore:37-40` | comment and two patterns | new comment and pattern block (Code Example 6) |
| `experiments/README.md` | "Git-ignored except for this file"; layout lists `<per-iteration>/`; "The run directory itself is not a citable artifact" | rewrite for D-27; charter §13 M3 lists this file as a deliverable |
| `README.md:47`, `CLAUDE.md` table row `experiments/` | "git-ignored except the README" | owner-approved edit (OQ-5) |
| `docs/MASTER-PLAN.md` §10 row "Run 출력" | git-ignored, "정책은 그대로 미커밋" | charter edit through an ADR (OQ-5) |
| `docs/governance/INVARIANTS.md` | A-3 row says "The ledger-schema guard the charter names lands at M3 (Phase 4)"; no A-6 row | extend A-3, add A-6 |
| `env/pixi.toml` | task `evaluate` | a task for the run CLI (name: A6) |
| `.claude/CLAUDE.md` "Data" constraint | "no data file of either layer is committed" | generated block; record in `GENERATED-DOC-CORRECTIONS.md` if it needs to change |

## Common Pitfalls

### Pitfall 1: CRLF or `\r\r\n` on Windows
**What goes wrong:** the ledger or the CSV differs between platforms.
**Why:** text mode translates `\n`; the `excel` dialect adds `\r\n` (F-27).
**Avoid:** write bytes. **Warning sign:** `b"\r" in path.read_bytes()`.

### Pitfall 2: A torn tail that looks fine
**What goes wrong:** the last event is complete JSON without its LF; a text reader accepts it; the
next append glues a second object onto the same line.
**Avoid:** the LF rule on bytes (F-35, F-36). **Test:** truncate a fixture at every byte of its
last line and assert every truncated file is refused.

### Pitfall 3: Duplicate keys and non-finite numbers in a line
**What goes wrong:** `{"seq":1,"seq":2}` reads as `seq 2`; `NaN` reads as a float and passes
`type: number` (F-39, F-54).
**Avoid:** `object_pairs_hook` and `parse_constant` on every `json.loads` of a ledger line or a
problem spec.

### Pitfall 4: Resume with a fresh evaluator
**What goes wrong:** 6 of 13 resumed ledgers differ and overcharge (F-62).
**Avoid:** Pattern 3. **Test:** crash at every event boundary, resume, compare bytes.

### Pitfall 5: Resuming "from the last closed iteration" by discarding the open one
**What goes wrong:** the ledger is append-only, so the events of the interrupted iteration stay.
Restarting that iteration records `(iteration, beam)` twice, which RUN-03 forbids.
**Avoid:** resume at the first key not yet recorded, inside the open iteration.

### Pitfall 6: A percentile without its population in the ledger
**What goes wrong:** `replay` cannot reproduce `pct_of_population` without the parquet, and CI has
no parquet.
**Avoid:** OQ-1.

### Pitfall 7: Ranking a served value in a distribution of filtered values
**What goes wrong:** the evaluator serves the median over all rows of a candidate; the population
built from filtered rows holds a different median for 5,119 members (F-23). A candidate can rank
above or below itself.
**Avoid:** take membership from the filter and values from the served table (Code Example 5), and
state the choice (OQ-4).

### Pitfall 8: `evals` read as "candidates with a value"
**What goes wrong:** `n` or a denominator is taken from `cost.evals`. A candidate with a missing
objective and an `ok` constraint is charged (F-60).
**Avoid:** count from statuses of the objective property.

### Pitfall 9: `dirty` that is always true
**What goes wrong:** `git status --porcelain` counts untracked files; planning files and the
tracked summaries of earlier runs make every run dirty (F-52).
**Avoid:** restrict the check to the paths that define behaviour (A3).

### Pitfall 10: Redacting `tokens`
**What goes wrong:** a substring rule on "token" replaces the token count in `usage.json` with
`***REDACTED***` (F-47).
**Avoid:** the suffix rule on singular words (F-48), with `tokens` in the test.

### Pitfall 11: The re-include that does nothing
**What goes wrong:** `!experiments/*/meta.json` after `experiments/*` leaves the file ignored, and
the old governance test stays green (F-64, F-67).
**Avoid:** Code Example 6 and a test that asks git.

### Pitfall 12: Population statistics sitting next to the facts the feedback builder reads
**What goes wrong:** Phase 6 builds feedback from ledger facts. If ranks or population sizes sit in
the same payloads as the values, a careless builder forwards them, which A-4 forbids.
**Avoid:** keep the population reference in one event kind the feedback builder never reads; Phase
6's payload test remains the guard.

### Pitfall 13: PoLyInfo-derived summaries tracked at M8
**What goes wrong:** the D-27 pattern tracks the summaries of **every** run directory. From M8 a run
can be PoLyInfo-derived, and those may not be committed (`experiments/README.md` reason 3).
**Avoid:** a governance test that every tracked `experiments/*/meta.json` has a `snapshot` beginning
with `polyomics:`.

### Pitfall 14: A contract that lands before its package
**What goes wrong:** the gate fails with `Module 'llm4pol.run' does not exist.` (F-72).
**Avoid:** package, contract and test updates in one commit.

### Pitfall 15: A console encoding that cannot print
**What goes wrong:** this session hit `UnicodeEncodeError: 'cp949' codec can't encode character
'–'` when printing a parent record.
**Avoid:** `stream.reconfigure(encoding="utf-8", errors="replace")` in `main`, as
`llm4pol.evaluate.__main__` does (`__main__.py:86-88`).

## Code Examples

Examples 1 to 5 ran in this session on win32 in the pixi environment. Names are illustrative.

### 1. Canonical line and durable append

```python
# Source: probe_jsonl.py / spike_run.py (this session); canonical form from src/llm4pol/evaluate/cache.py:40-48
def canonical_line(record: Mapping[str, object]) -> bytes:
    text = json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return (text + "\n").encode("utf-8")


def create(path: Path, header: Mapping[str, object]) -> None:
    with path.open("xb") as fh:          # FileExistsError on an existing ledger (A-6)
        fh.write(canonical_line(header))
        fh.flush()
        os.fsync(fh.fileno())


def append(path: Path, event: Mapping[str, object]) -> None:
    with path.open("ab") as fh:
        fh.write(canonical_line(event))  # one write, one complete line
        fh.flush()
        os.fsync(fh.fileno())
```

### 2. Reading with the LF rule

```python
# Source: probe_jsonl.py (this session)
def _refuse_constant(name: str) -> float:
    raise ValueError(f"non-finite JSON constant {name}")


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate key")
    return dict(pairs)


def read_lines(path: Path) -> list[dict[str, object]]:
    raw = path.read_bytes()
    if not raw.endswith(b"\n"):
        raise LedgerError(f"{path}: the final line is not terminated")
    return [
        json.loads(line.decode("utf-8"), parse_constant=_refuse_constant,
                   object_pairs_hook=_no_duplicates)
        for line in raw.split(b"\n")[:-1]
    ]
```

### 3. State rebuilt from the ledger

```python
# Source: spike_run.py (this session); 13 of 13 crash points byte-identical.
# The spike nested the results under payload["response"]; the payload layout is the plan's to fix.
def rebuilt_evaluator(events, backend, properties, evals_limit):
    cache, evals, hours = JsonlCache(), 0, []
    for event in events:
        if event["event"] != "evaluation":
            continue
        for item in event["payload"]["results"]:
            result = EvalResult.from_json(item)
            evals += result.cost.evals
            hours.append(result.cost.cpu_hours)
            if not result.cached and result.status in ("ok", "missing"):
                cache.put_many(
                    [(key_for(result.candidate_id, result.property, backend), result)]
                )
    meter = BudgetMeter(evals, math.fsum(hours))
    return Evaluator(backend, properties, cache=cache, meter=meter, evals_limit=evals_limit)
```

### 4. CSV bytes

```python
# Source: probe_csv.py / spike_run.py (this session). What ran is the rendering; the spike's own
# columns were iteration, beam, n, median_tc, evals. The tuple below is CONTEXT D-04's list.
COLUMNS = ("iteration", "beam", "n", "n_population", "median_tc", "feasible_frac",
           "pct_of_population", "hits_top10", "hits_top1")     # names per CONTEXT D-04; see OQ-2


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def render_csv(rows: Sequence[Sequence[object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow([_cell(value) for value in row])
    return buffer.getvalue().encode("utf-8")
```

### 5. Both populations through `llm4pol.data`

```python
# Source: probe_synth_pop.py (this session); 0.29 s on the real table
def populations(root: Path) -> dict[str, tuple[list[str], list[float]]]:
    registry = load_registry()
    processed = snapshot.processed_dir(root)
    objective = registry.by_role("objective")[0]
    columns = [*registry.columns(), "candidate_id", "canonical_psmiles", "tacticity", "check_tc"]
    rows = pq.read_table(snapshot.rows_parquet(processed), columns=columns).to_pandas()
    triple = filters.readme_triple_mask(rows, registry)
    check = filters.check_tc_mask(rows, registry)
    served = pq.read_table(snapshot.candidates_parquet(processed)).to_pandas().set_index("candidate_id")
    column = objective.column + filters.MEDIAN_SUFFIX
    out = {}
    for name, mask in (("check_tc", triple & check), ("readme_triple", triple)):
        members = build_candidates(rows[mask])["candidate_id"].tolist()      # membership: the filter
        values = sorted(float(v) for v in served.loc[members, column].tolist())  # values: as served
        out[name] = (members, values)
    return out

# rank of a value, LLM4MOF's strict definition (F-11):
#   n_below = bisect.bisect_left(values, median);  pct = 100 * n_below / len(values)
```

### 6. `.gitignore` for D-27

```gitignore
# Source: gitignore_probe (this session, git 2.53.0)
# run outputs: the ledger and everything else in a run directory stay untracked (size);
# meta.json, usage.json and results.csv of each run are tracked (D-27).
experiments/*
!experiments/README.md
!experiments/*/
experiments/*/*
!experiments/*/meta.json
!experiments/*/usage.json
!experiments/*/results.csv
```

A behavioural test asks git, without `-v` (F-66):

```python
def _ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", path], cwd=ROOT, check=False
    )
    return result.returncode == 0
# tracked:  experiments/<id>/meta.json, usage.json, results.csv, experiments/README.md
# ignored:  experiments/<id>/ledger.jsonl, experiments/<id>/anything-else, experiments/<id>/sub/meta.json
```

### 7. The import contract

```toml
# Source: il_probe (this session, import-linter 2.15): 5 kept; BROKEN on run -> loop and on run -> llm
[[tool.importlinter.contracts]]
name = "llm4pol.run never imports llm4pol.loop or llm4pol.llm (charter section 6, CONTEXT D-06)"
type = "forbidden"
source_modules = ["llm4pol.run"]
forbidden_modules = ["llm4pol.loop", "llm4pol.llm"]
```

## State of the Art

| Parent or twin approach | Approach here | Why |
|-------------------------|---------------|-----|
| LLM4MOF: one JSON file per iteration, overwritable, no resume (F-18) | one append-only JSONL with a header, resume and replay | charter A-6, D-21 |
| LLM4MOF: metrics stored as computed, empty iteration as `0.0` (F-15) | metrics re-derived by the reducer; empty beam as `no_match` and an empty field | RUN-04, LOOP-04 |
| LLM4MOF: redaction by exact key name (F-46) | suffix rule plus value-shape test; preferably no key written (F-50) | R-3 |
| LLM4MO: SQLite transactions (F-10) | fsynced complete lines and the LF rule | D-21 |
| LLM4MO: header re-derived and compared, code hashes included (F-02) | header read; comparison scope in OQ-8 | not stated in the context |

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | The recipe of Question 3 gives the same bytes on ubuntu-latest | Answers 3, F-33 | RUN-04 fails on one CI leg; found by the pinned-hash test on the first push |
| A2 | Identical IEEE-754 doubles result from `statistics.median`, `100 * n / m` and `math.fsum` on both CI platforms (64-bit CPython, no extended precision) | Answers 3 | A last-digit difference in `repr`; found by the same test |
| A3 | `dirty` should be computed over the paths that define behaviour (`src`, `protocol`, `config`, `pyproject.toml`, `env/pixi.toml`, `env/pixi.lock`), untracked files in those paths included | Pitfall 9 | `dirty` means something else than the owner expects; low |
| A4 | Run-scoped events (`run_opened`, `run_closed`) use `iteration: 0`, iterations are numbered from 1 | Pattern 3 | Off-by-one against Phase 5's numbering; the request schema allows 0 (F-45) |
| A5 | One writer per run directory; no lock | Answers 1 | Two `resume` processes interleave lines; the `seq` check then refuses the ledger |
| A6 | A pixi task named `run` would be confusing (`pixi run … run replay …`); another name such as `campaign` is safer | Existing guards | Cosmetic; not probed |
| A7 | Charter §13 M4's "≤40" means one evaluation event per candidate | F-80, OQ-9 | The event count of Phase 5 differs from the charter's estimate, which is marked "≈" |
| A8 | `selector` in the header is a name and version string for deterministic selectors; an LLM selector declares itself non-replayable so the sequence check is skipped for it | Answers 1 | Phase 6 cannot resume; design revisited then |

## Open Questions

Each is either resolved by a CONTEXT decision, left to the planner within a CONTEXT decision, or
stated as needing the owner.

| # | Question | Status |
|---|----------|--------|
| OQ-1 | How does the ledger carry the population so that `replay` needs no parquet? | **Needs the owner** (it fixes part of the frozen run record) |
| OQ-2 | `pct_of_table` (charter §7, LOOP-06) or `pct_of_population` + `n_population` (CONTEXT D-04)? | **Needs the owner** (charter against context) |
| OQ-3 | Definitions of `n`, `feasible_frac`, `hits_top10`, `hits_top1` | **Needs the owner** |
| OQ-4 | D-26 cites 42,733 (rows). Is 39,454 candidates the number to print, and are percentiles taken over served or filtered medians? | **Needs the owner** |
| OQ-5 | What form does "ADR-0001's wording is corrected" take, given F-68 and F-69? | **Needs the owner** |
| OQ-6 | Torn tail on `resume`: refuse, or repair? | Resolved in direction by D-03; the repair path is planner discretion |
| OQ-7 | Where does the stub selection live, and what does the verb `run` do in Phase 4? | Planner discretion within D-07 and the phase boundary |
| OQ-8 | Does `resume` refuse when `HEAD` differs from the header's `code_git_sha`? | **Needs the owner** |
| OQ-9 | One `evaluation` event per beam or per candidate? | Planner discretion within D-02 |
| OQ-10 | Is `run_summary.json` tracked, and where is `result_sha256` committed? | **Needs the owner** |
| OQ-11 | Exit code for a budget refusal | Planner discretion within D-07 |
| OQ-12 | Ledger storage | Resolved: D-21 |
| OQ-13 | Partitions | Resolved: D-22 |
| OQ-14 | Hash chain | Resolved: D-02, D-03 (none) |
| OQ-15 | Contract types | Resolved: D-23 |

### OQ-1 Population in the ledger

- **Known:** RUN-04 says "from the ledger alone"; D-04 puts `n_population` and `pct_of_population`
  in `results.csv`; CI has no real parquet; the reference sizes are measured (F-25 and below).
- **Options:**

| Option | What the ledger holds | Size per run | Exact parent definition (F-11) | Survives a metric redefinition at the D-16 gate |
|---|---|---|---|---|
| A | per evaluated candidate, its rank in each population; per beam, the rank of the median | a few bytes per event | yes, if the median's rank is recorded at close | no |
| B | once, in `run_opened`: the sorted objective values of each population (and of its feasible subset) | 1,089 KiB measured for both populations; parses in 0.01 s | yes | yes for objective-based metrics |
| C | per beam, the metrics as computed at run time; `replay` tabulates | small | yes | no; `replay` formats instead of re-deriving |

- **Recommendation:** B. The reducer stays a pure function, any definition the owner settles in OQ-3
  can be computed from the same ledger, and the population block is confined to one event kind
  (Pitfall 12). The cost is one long line per ledger, which is untracked.

### OQ-2 Column names

- **Known:** charter §7, verbatim: `results.csv   iteration, beam, n, median_tc, feasible_frac, pct_of_table, hits_top10, hits_top1`.
  CONTEXT D-04, verbatim: `iteration, beam, n, n_population, median_tc, feasible_frac, pct_of_population, hits_top10, hits_top1`.
  The charter outranks the context; the run record freezes at the exit of this phase.
- **Recommendation:** the owner chooses. If D-04's names are kept, the charter's §7 line and LOOP-06
  are updated in the same change. How the second population is shown "side by side" (D-26) is part of
  the same choice: keeping `results.csv` to one population and printing the second in `replay`'s
  output and the summary leaves the column list as D-04 wrote it.

### OQ-3 Undefined metrics

- **Known:** F-17, F-60.
- **Recommendation to put to the owner:** `n` = candidates in the recorded selection; `median_tc`
  over those whose objective is `ok`; `feasible_frac` = candidates whose constraint values are all
  `ok` and satisfy every constraint, divided by `n` (a missing constraint value is not feasible);
  `hits_top10` / `hits_top1` = candidates whose objective is at or above the value of the
  `round(0.10 n_population)`-th / `round(0.01 n_population)`-th largest member. Whether a hit must
  also be feasible is the part that depends on D-16.

### OQ-4 Population number and value basis

- **Known:** F-20, F-21, F-23.
- **Unclear:** whether D-26's intent ("leaving them in would let the search optimise unconverged NEMD
  runs") is met when the evaluator still serves medians that include `check_tc == False` rows of
  multi-row members. Two members of the 39,454 have a served TC above the filtered maximum.
- **Recommendation:** membership by the D-26 filter, values as served, so that a candidate is ranked
  in the distribution of what the loop can actually observe. The evaluator's value semantics were
  frozen at M2; changing them is outside this phase and would need an ADR.

### OQ-5 The form of the D-27 correction

- **Known:** F-68, F-69. D-27 changes charter §10. ADR numbering must be contiguous; the next number
  is 0007.
- **Recommendation:** a new ADR-0007 that narrows ADR-0001 for PolyOmics-derived run summaries, the
  charter §10 row edited in the same change, and the hand-written `CLAUDE.md` and `README.md` lines
  updated with the owner's approval.

### OQ-6 Torn tail

- **Known:** D-03: the check exists "without making a repaired ledger unusable". Removing a torn
  tail shortens the file, which the byte-prefix property forbids for ordinary operation.
- **Recommendation:** `resume` refuses and reports the offset of the last LF and the number of
  trailing bytes on stderr. Repair is a separate, explicit action that a person takes.

### OQ-7 The stub selection

- **Known:** C-16 forbids stubs in production code; D-07 lists `run` as a verb; Phase 5 owns
  `--selector deterministic`.
- **Recommendation:** `llm4pol.run` defines the selector protocol. A selector that replays a fixed
  plan read from a file is a complete feature, not a stub, and gives the verb `run` something to do
  in Phase 4. If the planner prefers to keep the plan-reading selector in `tests/`, the CLI verb
  `run` must still do something complete.

### OQ-8 Code identity on resume

- **Known:** F-02: the twin refuses. The header has `code_git_sha`.
- **Recommendation:** `resume` refuses on a different snapshot or registry version and on a
  different `code_git_sha`; `replay` and `usage` do not compare the code sha.

### OQ-9 Evaluation event granularity

- **Known:** F-80 (charter arithmetic suggests per candidate); RUN-03's key is per beam; the spike
  used per beam and works.
- **Recommendation:** per candidate. It matches the charter's count and a crash inside a beam loses
  at most one candidate. `selection` stays one event per beam with `uniqueItems`.

### OQ-10 `run_summary.json` and the result hash

- **Known:** D-04 names `run_summary.json`; D-27 tracks three files and does not name it; charter §7
  lists four files and does not name it. D-03 says the hash can be recomputed "from the committed
  record", but the ledger is not committed.
- **Recommendation:** the owner decides whether `run_summary.json` exists as a fifth file and is
  tracked. Whatever is decided, the sha256 of `ledger.jsonl` and of `results.csv` should be written
  into a tracked file, so that a person holding the ledger can check it against the repository.

### OQ-11 Budget exit code

- **Known:** F-43.
- **Recommendation:** 3, as in `llm4pol.evaluate`, and a `run_closed` event whose payload states the
  reason.

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| pixi environment | everything | yes | pixi 0.80.0, Python 3.13.15 | — |
| git | `code_git_sha`, ignore test, gate | yes | 2.53.0.windows.2 | — |
| gh | CI evidence | yes | 2.96.0 | — |
| Real rows and candidate parquets | population sizes, real-file test | yes on this machine | `data/processed/*-041e5834.parquet` | tests skip; CI has neither |
| Linux host (WSL, Docker) | local check of cross-platform bytes | **no** | — | the ubuntu-latest CI leg |
| LLM provider key | — | not needed | — | — |

**Missing with no fallback:** none.
**Missing with fallback:** a Linux host; CI is the evidence.

## Validation Architecture

`workflow.nyquist_validation` is `true` in `.planning/config.json`.

### Test framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 |
| Config | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `addopts = "-q"`) |
| Quick run | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_ledger.py -q` |
| Full suite | `pixi run --manifest-path env/pixi.toml check` (7 steps; 72 s today) |

### What runs where

| Layer | Runs in CI (both platforms) | Needs the real parquet (skips in CI) |
|-------|-----------------------------|--------------------------------------|
| Schemas and examples | `schema-inventory` step, schema tests | — |
| Ledger write, read, truncation, prefix | yes, on `tmp_path` | — |
| Campaign with a stub selection, crash and resume | yes, on `synthetic_candidates` | — |
| Reducer and byte identity | yes; pinned sha256 of a fixture ledger's `results.csv` | — |
| Usage equals ledger sums | yes | — |
| Population sizes 39,454 and 40,212, and that the two differ | — | `real_candidates`-style fixture, skips with a stated reason |
| Ignore policy | yes (`git check-ignore`; CI checks out with full history) | — |
| Import contract and its negative probe | yes | — |

**How a stub selection drives the ledger without Phase 5:** a mapping
`(iteration, beam) -> candidate ids` over the ids of `tests/conftest.py` (F-59). The spike's plan
covers four cases in 13 events: two `ok` candidates; a beam mixing a missing objective, a missing
constraint and an unknown id; a cache hit in a later iteration; and an empty beam (`no_match`).

### Requirements → test map

| Req | Behaviour | Type | Command | Exists |
|-----|-----------|------|---------|--------|
| RUN-01 | id matches `^\d{8}T\d{6}Z-[0-9a-f]{8}$`; an existing directory is refused | unit | `pytest tests/test_run_config.py -q` | no, Wave 0 |
| RUN-01 | `meta.json` has the D-01 fields; a secret-shaped key is `***REDACTED***`; `tokens` is not; scanner `PATTERNS` give no hit | unit | same file | no |
| RUN-02 | every line validates; `seq` contiguous; bytes have no CR; prefix holds after each append | unit | `pytest tests/test_run_ledger.py -q` | no |
| RUN-02 / A-6 | `open("xb")` refuses; truncation at every byte of the last line is refused | unit | same file | no |
| RUN-02 / A-3 | schema refuses a cost with a third field or without `cpu_hours` | unit | same file | no |
| RUN-03 | crash at every event boundary, resume: ledger bytes equal, zero duplicate keys | integration | `pytest tests/test_run_resume.py -q` | no |
| RUN-03 | a recorded selection that differs from the selector's is refused with exit 4 | integration | same file | no |
| RUN-04 | `replay` output equals the original bytes; sha256 equals a pinned constant | integration | `pytest tests/test_run_reduce.py -q` | no |
| RUN-04 | the reducer never opens a parquet (run with no data directory) | unit | same file | no |
| RUN-05 | `usage.json` `evals` and `cpu_hours` equal the ledger sums; `tokens` and `usd` are 0 and separate | unit | same file | no |
| RUN-06 | example validates; charter example without `schema_version`, `pareto`, a barred key, zero budget, extra key, `NaN` are refused | unit | `pytest tests/test_run_config.py -q` | no |
| D-06 | five contracts kept; `run → loop` breaks | integration | `pytest tests/test_import_boundary.py -q` | yes, to edit |
| D-07 | verbs and exit codes, in-process `main([...])` | integration | `pytest tests/test_run_cli.py -q` | no |
| D-27 | git tracks the three summaries and ignores the ledger | unit | `pytest tests/test_governance.py -q` | yes, to edit |
| D-26 | 39,454 and 40,212 on the real table | real-file | `pytest tests/test_run_real_file.py -q` | no |

### Sampling rate

- **Per task commit:** the quick run of the file the task touches (1 to 2 s each).
- **Per wave merge:** `pixi run --manifest-path env/pixi.toml check`.
- **Phase gate:** the full gate green locally and on both CI legs, with the run id recorded, as in
  Phases 2 and 3.

### Wave 0 gaps

- [ ] `tests/test_run_config.py`, `test_run_ledger.py`, `test_run_resume.py`, `test_run_reduce.py`,
      `test_run_cli.py`, `test_run_real_file.py` — none exists.
- [ ] A fixture ledger and the pinned sha256 of its `results.csv`.
- [ ] A synthetic row that is inside the triple and has `check_tc == False`, so the two populations
      differ on the synthetic root (F-79). `SYNTHETIC_ROWS` is cited by many existing tests
      ("14 source rows", "8 candidates"), so add the row in a Phase 4 fixture that extends a copy,
      not in the shared constant.
- [ ] `protocol/examples/` instances for both new schemas and their `[tool.llm4polcheck]` entries.
- [ ] Edits to `tests/test_import_boundary.py` and `tests/test_governance.py` (table above).

## Security Domain

`security_enforcement` is `true`, ASVS level 1.

### Applicable ASVS categories

| Category | Applies | Control |
|----------|---------|---------|
| V2 Authentication | no | no accounts |
| V3 Session management | no | — |
| V4 Access control | no | local developer CLI |
| V5 Input validation | yes | JSON Schema on the problem spec and on every ledger line; `parse_constant` and `object_pairs_hook`; run id matched against its pattern before it becomes a path |
| V6 Cryptography | limited | `hashlib.sha256` for integrity, `secrets.token_hex` for the id suffix; nothing hand-rolled |
| V7 Errors and logging | yes | generic message, detail on stderr, no value of a secret in either |
| V8 Data protection | yes | redaction in `meta.json`; tracked summaries pass the history secret scan |
| V12 Files | yes | run directory created with `exist_ok=False`; ledger with `"xb"`; no path built from unvalidated input |

### Threat patterns

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| A ledger edited by hand or truncated | Tampering | LF rule, per-line schema, `seq`, selector sequence check on `resume`, `result_sha256` |
| A run id such as `../../x` given to `replay` | Tampering / Elevation | pattern match before joining the path |
| A provider key written to a tracked `meta.json` | Information disclosure | key-name rule, scanner test, gate's history scan |
| A PoLyInfo-derived summary tracked at M8 | Compliance (MatNavi terms) | governance test on the `snapshot` of tracked `meta.json` files (Pitfall 13) |
| `NaN` or a duplicate key in an input | Tampering | reader guards (F-39) |
| Population statistics reaching a hosted LLM | Information disclosure (A-4) | confinement to one event kind; Phase 6 payload test |
| Two writers on one run | Tampering | `seq` contiguity refuses the result; single writer assumed (A5) |

## Sources

### Primary (read or probed this session)

- `04-CONTEXT.md`, `DECISIONS-LOG.md`, `REQUIREMENTS.md`, `MASTER-PLAN.md`, `INVARIANTS.md`,
  `CHANGE-POLICY.md`, `ENGINEERING-OPERATING-MODEL.md`, `ADR/0001`, `ROADMAP.md`, `STATE.md`
- `src/llm4pol/evaluate/{__init__,contract,evaluator,cache,budget,registry,__main__}.py`,
  `evaluate/backends/table.py`, `src/llm4pol/data/{filters,load,snapshot,registry,__init__}.py`
- `pyproject.toml`, `scripts/check.py`, `scripts/history_secret_scan.py`, `.gitignore`,
  `.gitattributes`, `env/pixi.toml`, `.github/workflows/ci.yml`, `experiments/README.md`,
  `tests/{conftest,test_governance,test_import_boundary}.py`, both evaluator schemas
- LLM4MO (read-only): `src/llm4mo/{database_run,database_evaluator,database_metrics,contracts,random_policy,settings}.py`,
  `tests/{test_database_run,test_database_evaluator}.py`
- LLM2POR_Core_20260319 (read-only): `core/{logger,metrics,pipeline}.py`, `core/data.py:360-410`,
  `experiments/exp_p3_v0_pormake_123/{run_config,run_summary,iteration_001}.json`
- Probes in the pixi environment: populations, CSV, JSONL, schema drafts, reference size, run id and
  redaction rules, the run spike, a scratch git repository, a scratch import-linter tree, the gate

### Secondary (documentation)

- Context7 `/python/cpython/v3.13.9`: `csv`, `open` newline handling, `os.fsync`
- Context7 `/seddonym/import-linter`: forbidden contract options, absent source modules
- `git-scm.com/docs/gitignore`: negation and excluded parent directories

### Tertiary

- none

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new package; versions read from the environment
- Architecture: HIGH for the state-from-ledger rule and the file mechanics (spiked); MEDIUM for the
  population reference and the metric definitions, which await the owner (OQ-1 to OQ-4)
- Pitfalls: HIGH — each was observed in a probe or read in code, except Pitfall 13, which is a
  forward-looking inference from `experiments/README.md`
- Cross-platform bytes: MEDIUM until the two-platform CI run (A1, A2)

**Side effects of this research:** the GSD research cache wrote
`.planning/research/.cache/<key>.json` (untracked). The untracked directory
`.planning/phases/05-deterministic-end-to-end/` was present before this research wrote anything and
was read, not modified.

**Research date:** 2026-09-29
**Valid until:** 2026-10-29 for the mechanics; the population numbers hold while the snapshot stays
at `041e5834` and the candidate definition stays as ADR-0006 left it
