# Phase 4 - charter section 13 M3 evidence

- **Date (UTC):** 2026-09-30
- **Tip when this file was written:** `0205a7f4110e8f52e08ddb8b84176d5a3b1648d7` (`docs(04-09): list the run-record schemas and examples in the protocol index (charter section 7, D-39)`). This file, the summary and the CI section are committed after it; the CI section names the pushed tip and the dispatched run.
- **Snapshot:** `polyomics:general_polymers@041e5834`
- Each numbered section below maps to one ROADMAP Phase 4 success criterion, which is the same-numbered charter section 13 M3 exit criterion. Every block is the command and its verbatim output from the Windows development machine, run from the repository root with `PYTHONPATH=src` inside `pixi run --manifest-path env/pixi.toml ...`. The `-v -v` runs are `python -m pytest <files> -v -v -k <expr>` (`addopts = "-q"` cancels a single `-v`); of their output only the result lines are kept, with pytest's progress percentages removed. The absolute path of the scratch directory is written `$SCRATCH` (the only edit made to any output). In the command-line blocks `$D` stands for a scratch directory outside the repository that holds a synthetic root, and `$R` for one that holds the run on the pinned table; no run directory is inside the repository and none is committed.
- Values printed for the synthetic table are invented fixture values. Counts printed for the pinned table are aggregates (see `## Data policy`).

## (1) A run interrupted and resumed records zero duplicate events

The tests: eighteen event boundaries (the header alone through the complete ledger), the rebuilt state at each, a closed run left untouched, seven duplicate-key defects refused, the three refusals of `resume`, and the same cut-and-resume on the pinned table (a copy cut after its eighth event).

```
$ PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_resume.py tests/test_run_ledger.py tests/test_run_real_file.py -v -v -k "test_resume_at_every_event_boundary_is_byte_identical or test_rebuilt_state_equals_the_recorded_spend or test_resume_appends_nothing_to_a_closed_run or test_duplicate_event_keys_are_refused or test_resume_refuses_a_torn_final_line or test_resume_refuses_a_different_snapshot_registry_version_or_code or test_resume_refuses_another_plan_or_a_doctored_selection or test_real_run_resumes_to_the_same_bytes"
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[0] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[1] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[2] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[3] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[4] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[5] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[6] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[7] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[8] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[9] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[10] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[11] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[12] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[13] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[14] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[15] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[16] PASSED
tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical[17] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[0] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[1] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[2] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[3] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[4] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[5] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[6] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[7] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[8] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[9] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[10] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[11] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[12] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[13] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[14] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[15] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[16] PASSED
tests/test_run_resume.py::test_rebuilt_state_equals_the_recorded_spend[17] PASSED
tests/test_run_resume.py::test_resume_appends_nothing_to_a_closed_run PASSED
tests/test_run_resume.py::test_resume_refuses_a_torn_final_line PASSED
tests/test_run_resume.py::test_resume_refuses_a_different_snapshot_registry_version_or_code[snapshot] PASSED
tests/test_run_resume.py::test_resume_refuses_a_different_snapshot_registry_version_or_code[registry] PASSED
tests/test_run_resume.py::test_resume_refuses_a_different_snapshot_registry_version_or_code[code] PASSED
tests/test_run_resume.py::test_resume_refuses_another_plan_or_a_doctored_selection PASSED
tests/test_run_ledger.py::test_duplicate_event_keys_are_refused[a second selection of one beam] PASSED
tests/test_run_ledger.py::test_duplicate_event_keys_are_refused[a no_match for a beam with a selection] PASSED
tests/test_run_ledger.py::test_duplicate_event_keys_are_refused[a selection for a beam with a no_match] PASSED
tests/test_run_ledger.py::test_duplicate_event_keys_are_refused[one candidate evaluated twice in one beam] PASSED
tests/test_run_ledger.py::test_duplicate_event_keys_are_refused[two iteration_opened for one iteration] PASSED
tests/test_run_ledger.py::test_duplicate_event_keys_are_refused[two iteration_closed for one iteration] PASSED
tests/test_run_ledger.py::test_duplicate_event_keys_are_refused[two run_opened] PASSED
tests/test_run_real_file.py::test_real_run_resumes_to_the_same_bytes PASSED
===================== 50 passed, 42 deselected in 18.95s ======================
```

The synthetic run on disk, first under the injected identity (fixed run id, constant clock), where the bytes of the resumed copy are compared with the bytes of the uninterrupted run. The ledger hash is also that of the committed fixture `tests/fixtures/run/reference-ledger.jsonl`.

```
$ python make_synth.py $D   # fixed identity: run, copy cut after event 9, resume under the constant clock
fixed-identity run: $SCRATCH\synth\fixed\uninterrupted\20260101T000000Z-00000000
resumed copy: $SCRATCH\synth\fixed\cut\20260101T000000Z-00000000 status completed appended 8

$ wc -l $D/fixed/uninterrupted/*/ledger.jsonl $D/fixed/cut/*/ledger.jsonl
   18 $D/fixed/uninterrupted/20260101T000000Z-00000000/ledger.jsonl
   18 $D/fixed/cut/20260101T000000Z-00000000/ledger.jsonl
   36 total

$ sha256sum $D/fixed/uninterrupted/*/ledger.jsonl $D/fixed/cut/*/ledger.jsonl
bc2370c0eff10b2904a325c597d070d1ee63384ba92fc786d29da7ec3839c457 *$D/fixed/uninterrupted/20260101T000000Z-00000000/ledger.jsonl
bc2370c0eff10b2904a325c597d070d1ee63384ba92fc786d29da7ec3839c457 *$D/fixed/cut/20260101T000000Z-00000000/ledger.jsonl

$ sha256sum <results.csv, usage.json, run_summary.json, meta.json of each run directory>
0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6 *$D/fixed/uninterrupted/20260101T000000Z-00000000/results.csv
0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6 *$D/fixed/cut/20260101T000000Z-00000000/results.csv
bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa *$D/fixed/uninterrupted/20260101T000000Z-00000000/usage.json
bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa *$D/fixed/cut/20260101T000000Z-00000000/usage.json
8190025ee895b71c9961d25a817015437f91285dbbff6b51413d70b20b9d20a9 *$D/fixed/uninterrupted/20260101T000000Z-00000000/run_summary.json
8190025ee895b71c9961d25a817015437f91285dbbff6b51413d70b20b9d20a9 *$D/fixed/cut/20260101T000000Z-00000000/run_summary.json
d388f2ce9f8811e4fc86e2786a639e68a550f89b3f5b638486bbc8efa588f5ed *$D/fixed/uninterrupted/20260101T000000Z-00000000/meta.json
d388f2ce9f8811e4fc86e2786a639e68a550f89b3f5b638486bbc8efa588f5ed *$D/fixed/cut/20260101T000000Z-00000000/meta.json
```

Then through the command-line verbs, which stamp the wall clock: `campaign run`, a copy cut after event 9, `campaign resume`. `results.csv` and `usage.json` are equal to the byte. The two ledgers differ only in the `ts` field of the eight events the resume appended (their hashes differ, and are equal once every `ts` is blanked); the byte-equal ledger comparison is therefore made above, under the injected clock, and at every boundary by the test of the first block.

```
$ pixi run --manifest-path env/pixi.toml campaign run --problem $D/problem.json --selector plan --plan $D/plan.json --root $D/root --experiments $D/exp
Pixi task (campaign): python -m llm4pol.run run --problem $SCRATCH/synth/problem.json --selector plan --plan $SCRATCH/synth/plan.json --root $SCRATCH/synth/root --experiments $SCRATCH/synth/exp
run_id: 20260930T091102Z-7f32f1eb
evals: 5
cpu_hours: 0.0
results_sha256: 0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6
exit code: 0

$ python cutcopy.py $D/exp/20260930T091102Z-7f32f1eb $D/exp-cut 9
cut copy: 20260930T091102Z-7f32f1eb holds the header and 9 events

$ pixi run --manifest-path env/pixi.toml campaign resume --run 20260930T091102Z-7f32f1eb --selector plan --plan $D/plan.json --root $D/root --experiments $D/exp-cut
Pixi task (campaign): python -m llm4pol.run resume --run 20260930T091102Z-7f32f1eb --selector plan --plan $SCRATCH/synth/plan.json --root $SCRATCH/synth/root --experiments $SCRATCH/synth/exp-cut
evals: 5
cpu_hours: 0.0
results_sha256: 0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6
exit code: 0

$ sha256sum $D/exp/*/results.csv $D/exp-cut/*/results.csv $D/exp/*/usage.json $D/exp-cut/*/usage.json
0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6 *$D/exp/20260930T091102Z-7f32f1eb/results.csv
0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6 *$D/exp-cut/20260930T091102Z-7f32f1eb/results.csv
bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa *$D/exp/20260930T091102Z-7f32f1eb/usage.json
bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa *$D/exp-cut/20260930T091102Z-7f32f1eb/usage.json

$ sha256sum $D/exp/*/ledger.jsonl $D/exp-cut/*/ledger.jsonl
20036c7ffcf9175395720f1ed94915830465bfba0db17ccfffd89da3a74a0f31 *$D/exp/20260930T091102Z-7f32f1eb/ledger.jsonl
c252cbb8bd991d1a5b4958b4ca1b84c3fd8d17cecfa2b4ef78b92ce73b506869 *$D/exp-cut/20260930T091102Z-7f32f1eb/ledger.jsonl

$ sed -E 's/"ts":"[^"]*"/"ts":"-"/' $D/<exp|exp-cut>/*/ledger.jsonl | sha256sum
0aa773a20b26aa077946b71e13fea68c7c256d167ced2ec8a601b9fd292fe919 *ledger.jsonl of exp with every ts field blanked
0aa773a20b26aa077946b71e13fea68c7c256d167ced2ec8a601b9fd292fe919 *ledger.jsonl of exp-cut with every ts field blanked
```

## (2) replay regenerates results.csv from the ledger alone, byte for byte

The tests: the tracer run, the three-file regeneration, the refusal of a file that differs, the committed fixture ledger reduced to the pinned bytes, replay and usage in a child interpreter with no table and no dataframe library, and the run on the pinned table replayed with `--out`.

```
$ PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_cli.py tests/test_run_replay.py tests/test_run_real_file.py -v -v -k "test_tracer_run_then_replay_through_the_module_entry_point or test_replay_regenerates_the_three_files_byte_identical or test_replay_refuses_a_file_that_differs or test_committed_fixture_ledger_reduces_to_the_pinned_bytes or test_replay_and_usage_need_no_table_and_no_dataframe_library or test_real_run_prints_both_populations_side_by_side"
tests/test_run_cli.py::test_tracer_run_then_replay_through_the_module_entry_point PASSED
tests/test_run_replay.py::test_replay_regenerates_the_three_files_byte_identical PASSED
tests/test_run_replay.py::test_replay_refuses_a_file_that_differs[results.csv] PASSED
tests/test_run_replay.py::test_replay_refuses_a_file_that_differs[usage.json] PASSED
tests/test_run_replay.py::test_replay_refuses_a_file_that_differs[run_summary.json] PASSED
tests/test_run_replay.py::test_committed_fixture_ledger_reduces_to_the_pinned_bytes PASSED
tests/test_run_replay.py::test_replay_and_usage_need_no_table_and_no_dataframe_library PASSED
tests/test_run_real_file.py::test_real_run_prints_both_populations_side_by_side PASSED
====================== 8 passed, 30 deselected in 16.96s ======================
```

`campaign replay` on the synthetic run of section (1). `results.csv` must print `0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6`.

```
$ pixi run --manifest-path env/pixi.toml campaign replay --run 20260930T091102Z-7f32f1eb --experiments $D/exp --out $D/replayed
Pixi task (campaign): python -m llm4pol.run replay --run 20260930T091102Z-7f32f1eb --experiments $SCRATCH/synth/exp --out $SCRATCH/synth/replayed
ledger_sha256: 20036c7ffcf9175395720f1ed94915830465bfba0db17ccfffd89da3a74a0f31
results_sha256: 0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6
result_sha256: 6c5c88357858d5c3d498cfb6009b3c0c3627665596161ec871df99fec0decd9c
exit code: 0

$ sha256sum $D/exp/*/results.csv $D/replayed/results.csv
0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6 *$D/exp/20260930T091102Z-7f32f1eb/results.csv
0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6 *$D/replayed/results.csv

$ cmp $D/exp/*/results.csv $D/replayed/results.csv && cmp $D/exp/*/usage.json $D/replayed/usage.json && cmp $D/exp/*/run_summary.json $D/replayed/run_summary.json && echo "three files identical"
three files identical
```

## (3) usage.json equals the ledger sums in two currencies

The tests: the sums in two currencies, the closed usage schema, the `usage` verb, and the two-currency rule of the ledger schema.

```
$ PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_reduce.py tests/test_run_ledger.py -v -v -k "test_usage_equals_the_ledger_sums_in_two_currencies or test_usage_schema_pins_names_and_types or test_usage_verb_prints_the_sums_and_compares_the_file or test_a3_ledger_schema_keeps_the_two_currencies_apart"
tests/test_run_reduce.py::test_usage_equals_the_ledger_sums_in_two_currencies PASSED
tests/test_run_reduce.py::test_usage_schema_pins_names_and_types PASSED
tests/test_run_reduce.py::test_usage_verb_prints_the_sums_and_compares_the_file PASSED
tests/test_run_ledger.py::test_a3_ledger_schema_keeps_the_two_currencies_apart PASSED
====================== 4 passed, 56 deselected in 0.57s =======================
```

`campaign usage` on the synthetic run of section (1), the sums taken independently from the ledger, and `sha256sum` of `usage.json`, which must print `bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa`.

```
$ pixi run --manifest-path env/pixi.toml campaign usage --run 20260930T091102Z-7f32f1eb --experiments $D/exp
Pixi task (campaign): python -m llm4pol.run usage --run 20260930T091102Z-7f32f1eb --experiments $SCRATCH/synth/exp
{
  "cpu_hours": 0.0,
  "evals": 5,
  "schema_version": 1,
  "tokens": 0,
  "usd": 0.0
}
exit code: 0

$ sha256sum $D/exp/*/usage.json
bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa *$D/exp/20260930T091102Z-7f32f1eb/usage.json

$ python -c "sum evals and cpu_hours over the evaluation events of ledger.jsonl"
evaluation events: 7
evals: 5
cpu_hours: 0.0
```

## Freezes of M3

The gate at the tree of this evidence (verbatim lines of `pixi run --manifest-path env/pixi.toml check`):

```
--- ruff check ---
PASS ruff check
--- ruff format --check ---
PASS ruff format --check
--- mypy ---
PASS mypy
--- import-linter ---
Contracts: 5 kept, 0 broken.
PASS import-linter
--- schema-inventory ---
llm4polcheck inventory: 9 entries, 16 instances processed
PASS schema-inventory
--- history-secret-scan ---
PASS history-secret-scan
--- pytest ---
392 passed in 126.74s (0:02:06)
PASS pytest
SUMMARY: 7/7 steps passed
```

The frozen files:

```
$ ls protocol/schemas
eval-request.json
eval-response.json
ledger-event.json
problem-spec.json
property-registry.json
run-meta.json
run-summary.json
run-usage.json
selection-plan.json

$ ls protocol/examples
eval-request.example.json
eval-response.example.json
ledger-event.evaluation.example.json
ledger-event.iteration_closed.example.json
ledger-event.iteration_opened.example.json
ledger-event.no_match.example.json
ledger-event.run_closed.example.json
ledger-event.run_opened.example.json
ledger-event.selection.example.json
ledger-header.example.json
problem-spec.example.json
run-meta.example.json
run-summary.example.json
run-usage.example.json
selection-plan.example.json
```

The A-3 and A-6 rows of `docs/governance/INVARIANTS.md` (quoted):

> | A-3 | The budget keeps `evals` and `cpu_hours` as two separately counted currencies; no combined score exists | `llm4pol.evaluate.budget.BudgetMeter` (exactly the two fields; `charge` returns a new meter; `remaining` / `exhausted` read `evals` only); `protocol/schemas/eval-response.json` `$defs/cost` (exactly `evals` and `cpu_hours`, `additionalProperties: false`); `tests/test_evaluate_cache_budget.py::test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies`. At M3 the same two-currency rule is guarded on the record: `protocol/schemas/ledger-event.json` `$defs/cost`, closed, on every recorded result and evaluation event; `tests/test_run_ledger.py::test_a3_ledger_schema_keeps_the_two_currencies_apart`. `usage.json` sums them apart: `llm4pol.run.reduce.usage_of` (`evals` an integer sum and `cpu_hours` an `fsum` of the recorded result costs, never combined); `protocol/schemas/run-usage.json` (closed; applied before the file is written); `tests/test_run_reduce.py::test_usage_equals_the_ledger_sums_in_two_currencies` |
>
> | A-6 | A run directory is append-only; a rerun gets a new id | `llm4pol.run.config.create_run_dir` (`mkdir(exist_ok=False)`, refusing an existing run directory with `run exists; use replay`); `llm4pol.run.ids.new_run_id` (a run id is a UTC timestamp and eight random hex characters, so a rerun cannot reuse one); `tests/test_run_config.py::test_a6_run_directory_refuses_to_be_created_twice`; `llm4pol.run.ledger.create` (exclusive binary open, so an existing ledger is refused); `llm4pol.run.ledger.append` (one complete LF-terminated line per binary append, fsynced); `tests/test_run_config.py::test_a6_a_rerun_gets_a_new_run_id`; `tests/test_run_ledger.py::test_a6_ledger_refuses_to_be_created_twice`; `tests/test_run_ledger.py::test_a6_every_append_keeps_the_previous_bytes_as_a_prefix`; `llm4pol.run.ledger.read` (the LF rule, `seq`, `event_key` and the lifecycle pass refuse a torn, repeated or out-of-order record and repair nothing); `tests/test_run_ledger.py::test_truncation_at_every_byte_of_the_last_line_is_refused`; `tests/test_run_ledger.py::test_duplicate_event_keys_are_refused`; `llm4pol.run.resume` (the ledger is the only state: the cache and the meter are rebuilt from the recorded `evaluation` events, a resumed run continues at the first unrecorded key, and a refusal appends nothing); `tests/test_run_resume.py::test_resume_at_every_event_boundary_is_byte_identical`; `tests/test_run_resume.py::test_resume_appends_nothing_to_a_closed_run` |

The four `test_a6_*` tests, the refusal matrix of the problem spec and the three schema tests (`meta.json`, `usage.json`, `run_summary.json`):

```
$ PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_config.py tests/test_run_ledger.py tests/test_run_reduce.py tests/test_run_replay.py -v -v -k "test_a6_ or test_problem_spec_refusals or test_meta_schema_pins_names_and_types or test_usage_schema_pins_names_and_types or test_summary_schema_pins_names_and_types"
tests/test_run_config.py::test_a6_a_rerun_gets_a_new_run_id PASSED
tests/test_run_config.py::test_a6_run_directory_refuses_to_be_created_twice PASSED
tests/test_run_config.py::test_problem_spec_refusals[barred_key_as_constraint] PASSED
tests/test_run_config.py::test_problem_spec_refusals[barred_key_as_objective] PASSED
tests/test_run_config.py::test_problem_spec_refusals[beams_zero] PASSED
tests/test_run_config.py::test_problem_spec_refusals[candidates_per_beam_zero] PASSED
tests/test_run_config.py::test_problem_spec_refusals[constraints_not_a_list] PASSED
tests/test_run_config.py::test_problem_spec_refusals[direction_up] PASSED
tests/test_run_config.py::test_problem_spec_refusals[extra_key_in_budget] PASSED
tests/test_run_config.py::test_problem_spec_refusals[extra_key_in_constraint] PASSED
tests/test_run_config.py::test_problem_spec_refusals[extra_key_in_objective] PASSED
tests/test_run_config.py::test_problem_spec_refusals[extra_top_level_key] PASSED
tests/test_run_config.py::test_problem_spec_refusals[form_pareto] PASSED
tests/test_run_config.py::test_problem_spec_refusals[form_weighted_sum] PASSED
tests/test_run_config.py::test_problem_spec_refusals[iterations_zero] PASSED
tests/test_run_config.py::test_problem_spec_refusals[no_schema_version] PASSED
tests/test_run_config.py::test_problem_spec_refusals[objective_is_also_constrained] PASSED
tests/test_run_config.py::test_problem_spec_refusals[op_strictly_less] PASSED
tests/test_run_config.py::test_problem_spec_refusals[repeated_constraint_property] PASSED
tests/test_run_config.py::test_problem_spec_refusals[schema_version_2] PASSED
tests/test_run_config.py::test_problem_spec_refusals[seed_boolean] PASSED
tests/test_run_config.py::test_problem_spec_refusals[seed_negative] PASSED
tests/test_run_config.py::test_problem_spec_refusals[table_of_another_dataset] PASSED
tests/test_run_config.py::test_problem_spec_refusals[threshold_as_string] PASSED
tests/test_run_config.py::test_problem_spec_refusals[unregistered_key] PASSED
tests/test_run_config.py::test_meta_schema_pins_names_and_types PASSED
tests/test_run_ledger.py::test_a6_ledger_refuses_to_be_created_twice PASSED
tests/test_run_ledger.py::test_a6_every_append_keeps_the_previous_bytes_as_a_prefix PASSED
tests/test_run_reduce.py::test_usage_schema_pins_names_and_types PASSED
tests/test_run_replay.py::test_summary_schema_pins_names_and_types PASSED
====================== 30 passed, 88 deselected in 0.84s ======================
```

## Deliverables of M3

The modules of `src/llm4pol/run` (the five of the charter row - `ids.py`, `ledger.py`, `config.py`, `resume.py`, `reduce.py` - among the ten modules of the package and its `__init__.py`), the head of `experiments/README.md`, and the two exit codes of `git check-ignore -q`: 1 means the path is not ignored (a summary is tracked), 0 means it is ignored (the ledger is not tracked; ADR-0007).

```
$ ls src/llm4pol/run
__init__.py
__main__.py
config.py
ids.py
jsonio.py
ledger.py
population.py
reduce.py
resume.py
selector.py
summary.py

$ head -12 experiments/README.md
# experiments/

Run outputs. Inside a run directory git tracks four small summaries and ignores the ledger and
everything else (ADR-0007; charter `docs/MASTER-PLAN.md` §10). Nothing in here is a result until it
has been reduced into `docs/` or a figure script; a tracked summary is the record a published number
is cited from.

## Layout of a run directory

`experiments/<run-id>/`, where the run id is `<UTC timestamp>-<8 hex>` (for example
`20260930T071500Z-3f9a1c2e`). Five files:


$ git check-ignore experiments/<run-id>/run_summary.json; echo $?
1
$ git check-ignore experiments/<run-id>/ledger.jsonl; echo $?
0
```

## The pinned table

The five tests of `tests/test_run_real_file.py` on `polyomics:general_polymers@041e5834`. They assert 39,454 `check_tc` and 40,212 `readme_triple` candidates, 24,497 and 24,589 served medians below 0.25, 39,449 distinct served values against 39,446 distinct medians over `check_tc`-passing rows only, 5,533 and 5,620 feasible members under `dielectric_const_dc <= 2.6`, `tg >= 400.0`, and two members served a value above the largest filtered median (research F-21, F-23, F-25 as corrected).

```
$ PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_real_file.py -v -v
tests/test_run_real_file.py::test_real_population_sizes PASSED
tests/test_run_real_file.py::test_real_reference_counts_on_served_values PASSED
tests/test_run_real_file.py::test_real_served_values_above_the_filtered_maximum PASSED
tests/test_run_real_file.py::test_real_run_prints_both_populations_side_by_side PASSED
tests/test_run_real_file.py::test_real_run_resumes_to_the_same_bytes PASSED
============================= 5 passed in 27.20s ==============================
```

A run of ten candidates in each of two beams on the pinned table, in a temporary directory, through the command-line verbs. The plan file was written by a short script that reads the ids from the parquet at run time; no id, repeat unit or per-candidate value is printed here. `cut -d, -f1-5,8` keeps the iteration, beam, population, `n_selected`, `n_ok` and `n_population` columns of `results.csv` (counts only). The byte length of the `run_opened` line is the measured size of the population block that ADR-0008 item 2 sends to this evidence: it is observed, not asserted.

```
$ pixi run --manifest-path env/pixi.toml campaign run --problem $R/problem.json --selector plan --plan $R/plan.json --root . --experiments $R/exp
Pixi task (campaign): python -m llm4pol.run run --problem $SCRATCH/real/problem.json --selector plan --plan $SCRATCH/real/plan.json --root . --experiments $SCRATCH/real/exp
run_id: 20260930T091133Z-d6d0f08e
evals: 20
cpu_hours: 0.0
results_sha256: 8a962134c0b45da38ba2bd3ca487f0a0deac4e59b5edcbbba57ac9fed5f78186
exit code: 0

$ ls $R/exp/<run-id>
ledger.jsonl
meta.json
results.csv
run_summary.json
usage.json

$ cut -d, -f1-5,8 $R/exp/<run-id>/results.csv
iteration,beam,population,n_selected,n_ok,n_population
1,full,check_tc,10,10,39454
1,full,readme_triple,10,10,40212
1,random,check_tc,10,10,39454
1,random,readme_triple,10,10,40212

$ python -c "byte length of the run_opened line (line 2 of ledger.jsonl, LF included)"
ledger lines: 27
header line bytes: 659
run_opened line bytes: 2904340
ledger.jsonl bytes: 2927882

$ campaign replay --run <run-id> --experiments $R/exp --out $R/replayed; cmp of the three files
Pixi task (campaign): python -m llm4pol.run replay --run 20260930T091133Z-d6d0f08e --experiments $SCRATCH/real/exp --out $SCRATCH/real/replayed
ledger_sha256: 14f9e8cd73b340836d7875840757fec482e25d6050b24c33f150f135b151ef0f
results_sha256: 8a962134c0b45da38ba2bd3ca487f0a0deac4e59b5edcbbba57ac9fed5f78186
result_sha256: f739950f126096035fe9380f22c4b93c5596f975cadc21bbe7b4ff90fa06a253
exit code: 0
results.csv identical
usage.json identical
run_summary.json identical

$ cat $R/exp/<run-id>/usage.json
{
  "cpu_hours": 0.0,
  "evals": 20,
  "schema_version": 1,
  "tokens": 0,
  "usd": 0.0
}
```

The two distinct counts of the objective table and their basis (counts only):

```
$ python real_counts.py   # counts only, from the pinned table
check_tc candidates: 39454
readme_triple candidates: 40212
distinct TC values, served medians, check_tc members: 39449
distinct TC values, medians over check_tc-passing rows only: 39446
```

## Owner notes

Choices made within the decisions; none is a conflict between sources.

1. **Exit codes (plan 04-05; CONTEXT D-07, R-9).** 2 for a record that cannot be read as a ledger or another input defect, 3 for a budget refusal recorded by that call, 4 for a readable ledger that cannot be trusted or continued (a `seq` gap, a repeated event key, the lifecycle order, a header that names other code, snapshot, registry version or selector, a recorded selection the selector does not give, a results file that is not what the ledger reduces to). `resume` on a run that is already closed returns 0 and appends nothing.

2. **The budget is enforced in `evals` only (plan 04-02).** The limit is `iterations * candidates_per_beam * beams`; the driver does not police `candidates_per_beam` or `beams`. `cpu_hours` is recorded and summed apart and never combined with `evals` (invariant A-3).

3. **`result_sha256` (plan 04-08).** It is the sha256 of the bytes of `results.csv`, `usage.json` and `run_summary.json`, in that order, laid end to end. `replay` prints it and nothing stores it.

4. **`status` in `run_summary.json` (plan 04-08).** It takes the values `open`, `completed` and `budget_exhausted`; the schema enumerates them and a run without a `run_closed` event is `open`.

5. **`usage.json` has five keys (plan 04-07; D-39).** The four of CONTEXT D-04 - `evals`, `cpu_hours`, `tokens`, `usd` - and `schema_version`. `tokens` and `usd` stay 0 until Phase 6.

6. **The fixture ids (plan 04-08).** They are hashes of public repeat units and tacticities, so some are also ids of the pinned table; the guards therefore read "fixture ids and invented values only" and do not claim that no id of the pinned table appears.

7. **Research F-25 is corrected (plan 04-09; correction of 2026-09-29).** 39,449 distinct served values (the `check_tc` objective array, served medians) and 39,446 distinct medians over `check_tc`-passing rows only; each is asserted on its own basis.

8. **Research cross-reference numbers (plans 04-01 to 04-09).** The research cross-reference tables cite some facts under shifted numbers (the spike as F-57..F-59, the baseline as F-60); the plans cite the facts table, where the spike is F-59..F-62 and the baseline F-77.

9. **The pre-registration file of Phase 7 needs its own re-include in `.gitignore` (plan 04-03; F-70).**

A note on the resume evidence (plan 04-09): the command-line verbs stamp the wall clock (`ids.utc_now`), so a run resumed through them differs from the uninterrupted run in the `ts` field of the events the resume appended; the byte-for-byte comparison of the ledger is made under the injected clock, at every boundary, on the synthetic table and on the pinned table.

## Data policy

This file quotes counts only from the pinned table: the sizes of the two populations, the counts below a threshold, the distinct counts, the feasible counts, and the byte lengths of the record the run wrote. No id, repeat unit, SMILES or per-candidate value of the pinned table appears in it. Every 16-hex token in it is a fixture id, and every per-candidate value an invented fixture value. The run on the pinned table lives in a temporary directory outside the repository; `git ls-files experiments data/` prints the four tracked files (the two manifests, the data README, the experiments README) and nothing else.

## CI

One `workflow_dispatch` run of the `check` workflow on the pushed tip, after the local gate printed `SUMMARY: 7/7 steps passed`, the history scan reported zero hits for every class and `dotenv-path-in-history: 0 hit(s)`, `git ls-files experiments` printed the README only and `git ls-files data/` the two manifests and the README only. The tip was pushed with `git push origin main` (`f850b2d..f52ff67`) before the run was dispatched with `gh workflow run check --ref main`; the run below is the one whose `headSha` equals that tip.

CI run id: 36695769247
CI head sha: f52ff6732eb130aca5e553509d1a3f3ed05ae491
check (windows-latest): success
check (ubuntu-latest): success

`gh run view 36695769247 --json databaseId,headSha,event,headBranch,conclusion,url,jobs`, reduced to the run fields and the name and conclusion of each job:

```
{"conclusion":"success","databaseId":36695769247,"event":"workflow_dispatch","headBranch":"main","headSha":"f52ff6732eb130aca5e553509d1a3f3ed05ae491","jobs":[{"conclusion":"success","name":"check (ubuntu-latest)"},{"conclusion":"success","name":"check (windows-latest)"}],"url":"https://github.com/kn1218/llm4pol/actions/runs/36695769247"}
```

The log lines of `gh run view 36695769247 --log` that match `SUMMARY:`, `Contracts: `, `llm4polcheck inventory` and `passed` (the job name and step are the log's own prefix; timestamps are the runners'):

```
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check	2026-09-30T09:23:28.5681600Z Contracts: 5 kept, 0 broken.
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check	2026-09-30T09:23:28.5682151Z llm4polcheck inventory: 9 entries, 16 instances processed
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check	2026-09-30T09:23:41.8635157Z 370 passed, 22 skipped in 9.26s
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check	2026-09-30T09:23:41.8635400Z SUMMARY: 7/7 steps passed
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check	2026-09-30T09:23:53.4179725Z Contracts: 5 kept, 0 broken.
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check	2026-09-30T09:23:53.4181184Z llm4polcheck inventory: 9 entries, 16 instances processed
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check	2026-09-30T09:24:29.3955734Z 370 passed, 22 skipped in 26.76s
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check	2026-09-30T09:24:29.3956803Z SUMMARY: 7/7 steps passed
```

Both legs print the three lines of the gate and one pytest summary line, and both report the same counts: `370 passed, 22 skipped`. The 22 skipped tests are the difference between the local run, where the pinned files are present and 392 tests pass, and a leg without them (392 = 370 + 22); the five tests of `tests/test_run_real_file.py` skip there by construction of the `real_processed` fixture, with its stated reason. The pinned fixture ledger reduced to the same sha256 on both platforms because `test_committed_fixture_ledger_reduces_to_the_pinned_bytes` is among the passed tests of both legs and cannot skip: it asks for no fixture that depends on a data file, it reads the committed `tests/fixtures/run/reference-ledger.jsonl` and compares the reduced `results.csv`, `usage.json` and `run_summary.json` with hashes that were derived by hand or recorded before this run. This section was committed after the run it cites.
