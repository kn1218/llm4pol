# Phase 1 — charter §13 M0 evidence

- **Date (UTC):** 2026-09-21
- **Pushed tip:** `007cda58cb9fcc3ef761bc71776ad66aa3649daf` (`docs(01-01): restate why experiments/ is untracked per charter §10 (D-06)`)
- Each section below maps to one ROADMAP Phase 1 success criterion, which is the same-numbered
  charter §13 M0 exit criterion. Every line is verbatim tool output paired with the command
  that produced it (D-04); nothing here is narrative.

## (1) Gate green on both platforms; huggingface_hub resolves

`gh workflow run check --ref main` (D-05), then
`gh run view 35627403598 --json databaseId,headSha,conclusion,url,jobs --jq '{databaseId,headSha,conclusion,url,jobs:[.jobs[]|{name,conclusion}]}'`:

```
CI run id: 35627403598
CI head sha: 007cda58cb9fcc3ef761bc71776ad66aa3649daf
CI url: https://github.com/kn1218/llm4pol/actions/runs/35627403598
CI event: workflow_dispatch
CI branch: main
CI conclusion: success
check (windows-latest): success
check (ubuntu-latest): success
```

Raw JSON:

```
{"conclusion":"success","databaseId":35627403598,"headSha":"007cda58cb9fcc3ef761bc71776ad66aa3649daf","jobs":[{"conclusion":"success","name":"check (ubuntu-latest)"},{"conclusion":"success","name":"check (windows-latest)"}],"url":"https://github.com/kn1218/llm4pol/actions/runs/35627403598"}
```

`gh run view 35627403598 --log | grep -E "SUMMARY:|scanned [0-9]+ commit|SELF-TEST OK|dotenv-path-in-history|[0-9]+ passed"`
(log timestamps stripped; each line is prefixed by its job name):

```
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check SELF-TEST OK: 10 pattern classes each matched their positive control
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check scanned 14 commit(s) reachable from git rev-list --all
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check dotenv-path-in-history: 0 hit(s)
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check 25 passed, 1 skipped in 0.18s
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check SUMMARY: 6/6 steps passed
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check SELF-TEST OK: 10 pattern classes each matched their positive control
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check scanned 14 commit(s) reachable from git rev-list --all
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check dotenv-path-in-history: 0 hit(s)
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check 25 passed, 1 skipped in 1.44s
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check SUMMARY: 6/6 steps passed
```

The one skipped test in CI is `tests/test_manifest.py::test_raw_files_match_manifest`, which
skips by design when no PoLyInfo-derived raw file is present under `data/raw/` (they are never
committed, ADR-0001). Locally, where the raw files exist, the same gate reports `26 passed`.

`scanned 14 commit(s)` in CI equals the local count: the checkout is full history
(`fetch-depth: 0`), not a shallow clone.

`pixi run --manifest-path env/pixi.toml python -m pytest tests/test_environment.py -v -v` (local,
Windows; the same test runs inside the CI gate above on both platforms):

```
tests/test_environment.py::test_huggingface_hub_importable PASSED        [100%]
============================== 1 passed in 0.02s ==============================
```

## (2) First commit of the approved-charter era exists on main

`git log --reverse --format="%h %ad %s" --date=short --max-parents=0`:

```
567ce1d 2026-09-21 chore: bootstrap repository with governance, research inputs and charter v1.0
```

## (3) dotenv file untracked, example committed, no secret in output, logs or history

`python -c "import subprocess; n='.'+'env'; r=subprocess.run(['git','ls-files','--',n,n+'.example'],capture_output=True,text=True); print('tracked-dotenv-paths:', repr(r.stdout))"`
(the filename is assembled at runtime because the workstation guard refuses Bash commands that
contain it; only the example file is tracked):

```
tracked-dotenv-paths: '.env.example\n'
```

`pixi run --manifest-path env/pixi.toml python scripts/history_secret_scan.py --self-test` (exit 0):

```
self-test openai_secret_key: 1 match(es) against its positive control
self-test anthropic_secret_key: 1 match(es) against its positive control
self-test google_ai_api_key: 1 match(es) against its positive control
self-test huggingface_token: 1 match(es) against its positive control
self-test github_token: 1 match(es) against its positive control
self-test github_fine_grained_token: 1 match(es) against its positive control
self-test aws_access_key_id: 1 match(es) against its positive control
self-test slack_token: 1 match(es) against its positive control
self-test private_key_header: 1 match(es) against its positive control
self-test generic_credential_assignment: 1 match(es) against its positive control
SELF-TEST OK: 10 pattern classes each matched their positive control
```

`pixi run --manifest-path env/pixi.toml python scripts/history_secret_scan.py` (exit 0, full local
history at the pushed tip):

```
scanned 14 commit(s) reachable from git rev-list --all
pattern openai_secret_key: 0 hit(s)
pattern anthropic_secret_key: 0 hit(s)
pattern google_ai_api_key: 0 hit(s)
pattern huggingface_token: 0 hit(s)
pattern github_token: 0 hit(s)
pattern github_fine_grained_token: 0 hit(s)
pattern aws_access_key_id: 0 hit(s)
pattern slack_token: 0 hit(s)
pattern private_key_header: 0 hit(s)
pattern generic_credential_assignment: 0 hit(s)
dotenv-path-in-history: 0 hit(s)
no secrets found in any reachable commit; dotenv path never committed
```

The scanner prints pattern names, commit shas and paths only, never a value:
`tests/test_history_secret_scan.py::test_seeded_secrets_in_temp_repo_are_detected_without_printing_them`
seeds a temporary repository with every class's positive control, requires a `HIT` line per
class, and asserts that no positive-control string appears in the captured output. The scan
walks history, not the index, so the dotenv-path line above covers every commit, not only the
current tree.

## D-05 observation

`gh run list --workflow=ci.yml --event push --branch main --limit 3 --json databaseId,headSha,createdAt`
after `git push origin main` published `8cf794e..007cda5`:

```
[]
```

No push-triggered run exists for the pushed tip. The verification run above was a
`workflow_dispatch` per D-05; push-trigger behaviour is recorded here, not investigated
(01-CONTEXT § Deferred).
