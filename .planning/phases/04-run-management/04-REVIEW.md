---
phase: 04-run-management
reviewed: 2026-09-30T00:00:00Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - src/llm4pol/run/__init__.py
  - src/llm4pol/run/__main__.py
  - src/llm4pol/run/config.py
  - src/llm4pol/run/ids.py
  - src/llm4pol/run/jsonio.py
  - src/llm4pol/run/ledger.py
  - src/llm4pol/run/population.py
  - src/llm4pol/run/reduce.py
  - src/llm4pol/run/resume.py
  - src/llm4pol/run/selector.py
  - src/llm4pol/run/summary.py
  - protocol/schemas/ledger-event.json
  - protocol/schemas/problem-spec.json
  - protocol/schemas/run-meta.json
  - protocol/schemas/run-summary.json
  - protocol/schemas/run-usage.json
  - protocol/schemas/selection-plan.json
  - .gitignore
findings:
  critical: 1
  warning: 7
  info: 7
  total: 15
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-09-30
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

Reviewed all eleven `llm4pol.run` modules and the six run-record schemas in full, plus `.gitignore`.
`tests/fixtures/run/reference-ledger.jsonl` was checked only for being synthetic (zero code sha,
placeholder ids). The test files, `scripts/check.py`, `pyproject.toml` and `env/pixi.toml` were
spot-checked with grep (skips, placeholders, canonical/concurrency coverage), not read line by line.

The single-writer, single-process path is well built. Path traversal on `--run` is gated by a
fullmatch. The ledger is byte-strict on read. The torn-tail refusal, per-key duplicate refusal and
replay-prefix check are coherent. The subprocess calls use fixed argv with no shell.

The append-only guarantees, which are the core of this phase, hold only while exactly one writer runs
and the file is untouched. Nothing enforces either condition. One BLOCKER: two concurrent `resume`
calls corrupt a ledger beyond recovery (the design repairs nothing). Several WARNINGs follow on strict-reader
gaps, non-atomic outputs, a blindness hazard in the selector protocol, and secret-redaction holes.

Claims below marked "verified" were reproduced by running the code.

## Critical Issues

### CR-01: No writer exclusion or seq check on append, so two concurrent drivers corrupt the ledger irrecoverably

**File:** `src/llm4pol/run/ledger.py:337-341`, `src/llm4pol/run/resume.py:196-209`
**Issue:** `append` validates only the schema of the one event. It never checks that the file's last
line has `seq == event.seq - 1`, that the ledger is not already closed, or that no other process is
writing. `_Recorder.emit` computes `seq` as `len(self.events) + 1` from the process's own in-memory
snapshot, taken once in `drive` by `read()`. No lock file, `flock` or `msvcrt.locking` exists anywhere
in `src/llm4pol/run/`; I grepped for this. Two `python -m llm4pol.run resume --run X` invocations
(for example a second terminal after an apparent hang) both read N events. The selector is
deterministic, so both then emit the same `iteration_opened` at `seq` N+1, then the same `selection`
at N+2, and so on. The interleaved lines carry duplicate seqs and duplicate event keys. Every later
`read` raises `LedgerIntegrityError`, and `resume` refuses to repair anything (ADR-0008 item 7). The
run record is permanently unreadable. `replay` and `usage` fail too. The public `llm4pol.run.append`
also accepts an event for a closed ledger, or one with an arbitrary `seq`. Only the reader notices.
RUN-03 ("no duplicate (run_id, iteration, beam) events") is enforced after the damage, not before it.
**Fix:** Hold an exclusive lock for the lifetime of `drive`, and make `append` self-checking:

```python
# resume.drive(): before read(path)
with run_lock(run_dir):          # O_CREAT|O_EXCL "run.lock" holding pid, removed in finally;
    ...                          # or fcntl.flock / msvcrt.locking on the ledger fd

# ledger.append(): verify the tail before writing
def _require_next_seq(path: Path, seq: int) -> None:
    with path.open("rb") as fh:
        fh.seek(-min(fh.seek(0, os.SEEK_END), 1 << 20), os.SEEK_END)   # last line only
        last = fh.read().rstrip(b"\n").rsplit(b"\n", 1)[-1]
    tail = loads_strict(last.decode("utf-8"))
    if tail.get("seq", 0) != seq - 1 or tail.get("event") == "run_closed":
        raise LedgerIntegrityError(f"append at seq {seq} does not follow the recorded tail")
```

Add a test that runs two drivers over one ledger and asserts the second one refuses.

## Warnings

### WR-01: `loads_strict` does not deliver its documented refusals, and several parse failures escape as tracebacks

**File:** `src/llm4pol/run/jsonio.py:26-31, 56-63`; `src/llm4pol/run/ledger.py:356-360`; `src/llm4pol/run/__main__.py:85-98, 261`
**Issue:** All of the following are verified.
- `parse_constant` only catches the literals `NaN` and `Infinity`. `loads_strict("1e999")` returns
  `inf` (also inside lists), so the "refuses non-finite" docstring (F-39, F-54) is false for
  overflowing literals. Ledger population arrays and result values can therefore hold `inf`, and the
  read boundary accepts them. Only `_cell` or `canonical_bytes` fail later, far from the cause.
- A 5000-digit integer raises a bare `ValueError` (the 4300-digit limit) and deeply nested input
  raises `RecursionError`. `loads_strict` catches only `JSONDecodeError`, and `main()`'s
  `_INPUT_ERRORS` contains neither. A problem file, plan file or ledger line therefore ends in a
  traceback, not exit 2.
- `_dumps` calls `.encode("utf-8")` outside its `try`. A lone surrogate (`"\ud800"` parses fine)
  raises `UnicodeEncodeError`, which is not a `StrictJsonError`. `PlanSelector.__init__` and
  `_line_bytes` only catch `StrictJsonError`.
- `load_problem_spec` and `PlanSelector.from_file` call `read_text(encoding="utf-8")`. A non-UTF-8
  file raises `UnicodeDecodeError`, which is uncaught.

**Fix:**
```python
def _refuse_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise StrictJsonError(f"non-finite JSON number {text}")
    return value

def loads_strict(text):
    try:
        return json.loads(text, parse_constant=_refuse_constant, parse_float=_refuse_float,
                          object_pairs_hook=_refuse_repeated_keys)
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:   # ValueError last
        if isinstance(exc, StrictJsonError): raise
        raise StrictJsonError(f"invalid JSON: {exc}") from exc

# _dumps: move the encode inside the try and catch UnicodeEncodeError
# load_problem_spec / from_file / _parse_line: also catch UnicodeDecodeError
```

### WR-02: The strict reader does not enforce the canonical byte form it documents

**File:** `src/llm4pol/run/ledger.py:363-390` (docstring lines 1-17)
**Issue:** The module states that the file is canonical, one object per LF-terminated line, and
"holds no CR". `parse_bytes` never compares a line with `canonical_bytes(record)`, so all of these
are accepted:
- `{"a":1}\r`, because JSON whitespace includes CR (verified). A CRLF-converted ledger reads without
  complaint. `.gitattributes` `eol=lf` covers tracked files only, and `ledger.jsonl` is
  git-ignored, so a Windows copy or editor round-trip is not covered.
- Pretty-printed or reordered lines.
- Integers written as `2.0` (jsonschema treats it as `integer`; `int()` in `from_json` hides it).

The replay hashes `ledger_sha256` over raw bytes, so two semantically identical ledgers yield
different `run_summary.json`, `results_sha256` and `result_sha256`. The byte-identity claim (charter
M3) then depends on nobody touching the file. The reader is also the only guard for A-6, and it
does not check the form of a hand-edited line.
**Fix:** In the `parse_bytes` loop (and for the header line), after `_check`:
```python
if canonical_bytes(record) != line + _LF:
    raise LedgerFormatError(f"{where}: line is not in canonical form")
```
Add tests for a CR-terminated line, a spaced line, and `2.0` for an integer field.

### WR-03: Reduced outputs are written non-atomically, so a crash leaves a file that permanently blocks the run

**File:** `src/llm4pol/run/reduce.py:385-397`
**Issue:** `write_outputs` opens each absent file with `xb` and writes in place. If the process dies
mid-write, or the disk fills, a truncated `results.csv`, `usage.json` or `run_summary.json` remains.
The next `resume`, `replay` or `usage` sees `present.exists()`, finds different bytes, and raises
`LedgerIntegrityError("… differs from what the ledger reduces to")` with exit 4. The recovery
message points at the ledger, which is fine, and no code path allows regeneration. The message claims
tampering for what is only a crash. A second issue is that the existence check and the `xb` open are
not atomic, so a racing writer surfaces as a raw `FileExistsError` and exit 2.
**Fix:** Write each file to a temp name in the same directory, fsync, then `os.replace` (it fails
atomically on an existing target only if you first `os.link`/`O_EXCL` a sentinel). The simplest
form: write `name.tmp`, fsync, `os.replace(tmp, target)` only when `target` is absent. Treat a
present file whose bytes are a strict prefix of the expected bytes as a crash remnant that may be
replaced, and a non-prefix as tampering.

### WR-04: The selector protocol hands the hidden-table population arrays to Phase 5 in `history`

**File:** `src/llm4pol/run/resume.py:212-217, 257`; `src/llm4pol/run/selector.py:70-74, 201`
**Issue:** `Selector.select(problem, iteration, history)` is documented as receiving "every event
recorded before" the iteration. That includes the `run_opened` event, whose payload holds both full
population value arrays: the whole distribution, its size, and every percentile and threshold
derivable from it. Project invariants A-4 and D-19 say nothing sent to a hosted LLM may carry table
size, percentiles, thresholds or global statistics. The schema comment says "Population arrays are
admitted in the run_opened payload only, so no payload the feedback builder reads can carry them".
The protocol contradicts that intent, because the Phase 5 selector, and any feedback builder that
walks `history`, gets the arrays by default. Nothing here leaks today (`PlanSelector` ignores
history), but the blindness barrier depends on every future selector author remembering to skip one
event kind.
**Fix:** Do not pass `run_opened` to selectors:
```python
def _history_before(events, iteration):
    ...
    return tuple(e for e in events[:position] if e.event != "run_opened")
```
Apply the same filter in `verify_replay` (`selector.py:201`). Alternatively, define a `SelectorView`
without populations, and add a test that the history a selector receives contains no `populations` key.

### WR-05: Secret redaction misses common secret-shaped key names, and no value is ever inspected

**File:** `src/llm4pol/run/config.py:65-69, 282-295`
**Issue:** Verified with `redact(...)`: `secret_key`, `private_key`, `access_key` and `Authorization`
are all returned unchanged. The regex requires the credential word to be the final `_`-segment, so
any `<secret>_key` shape falls through, and so do `auth`, `authorization` and `bearer`. The values are
never checked, so `prompt_versions: {"v": "sk-…"}` is written as is. `prompt_versions` is the one open
mapping, and the docstring names it as exactly what this second defence is for. Redaction is also
silent: the value becomes `***REDACTED***` with no warning, which hides a caller bug.
**Fix:** Widen the rule and apply a value check to the open mapping:
```python
_NAME_RULE = re.compile(
    r"(?:^|_)(?:api_?key|secret(?:_?key)?|private_?key|access_?key|token|password|passwd|"
    r"credential|authorization|auth|bearer)$", re.IGNORECASE)
```
Also restrict `prompt_versions` values in `run-meta.json` with a pattern (a version label such as
`^[A-Za-z0-9._-]{1,64}$`), so a key cannot ride in as a value. Consider raising a `MetaError` on a
redaction hit rather than masking it.

### WR-06: No directory fsync after creating the ledger, `meta.json` or the outputs

**File:** `src/llm4pol/run/ledger.py:306-319`; `src/llm4pol/run/config.py:351-365`; `src/llm4pol/run/reduce.py:390-396`
**Issue:** Each new file is fsynced, but the directory entry is never made durable. On POSIX, after
a power loss, `ledger.jsonl` (or the whole run directory) can vanish although `create()` returned
and events were "durably" appended. The whole crash-safety story (fsync per append) then rests on a
file whose existence is not durable. `open_run` also creates the directory, then `meta.json`, then
the ledger. A crash between them leaves a run directory with no ledger, and `resume` fails with
"ledger does not exist" with no path to reuse or clean the directory, because `RunExists` blocks
only new ids and the id is fresh each time, so the directory is orphaned.
**Fix:** After creating a file, fsync the parent directory on POSIX:
```python
def _fsync_dir(path: Path) -> None:
    if os.name == "posix":
        fd = os.open(path, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
```
Call it after `create`, `write_meta` and each output write. Write the ledger header before
`meta.json` if the intent is "no meta without a ledger" (or document the order).

### WR-07: The run-id gate and schema patterns accept non-ASCII digits, and `$` admits a trailing LF

**File:** `src/llm4pol/run/ids.py:19`; `protocol/schemas/ledger-event.json:17,440`; `run-meta.json` (`run_id`, `created_at`); `problem-spec.json:70`; `selection-plan.json:52,65`
**Issue:** `RUN_ID_PATTERN = r"\d{8}T\d{6}Z-…"` is a `str` pattern, so `\d` matches any Unicode
decimal digit. `require_run_id("２０２６０９３０T120000Z-abcdef01")` returns the text (verified), and the
module docstring promises "none of which Windows forbids… 25 characters" and calls this "the gate
between text a caller supplies and a path" (T-04-02). Traversal is still impossible, because `/`
and `..` do not match. Non-ASCII names do reach the filesystem and the ledger header, and they break
the documented 25-character/ASCII form. The JSON Schema patterns use `^…$` with `re.search`, so a
trailing `\n` also matches. `selector.py` re-checks its own two patterns with `fullmatch` for exactly
this reason, but the ledger schema's `candidate_id`, `ts`, `table`, `code_git_sha` and `selection`
patterns get no such second check. A ledger candidate id such as `"0123456789abcdef\n"` passes.
**Fix:** Use `[0-9]` (or `re.ASCII`) in `RUN_ID_PATTERN`, and `\d` → `[0-9]` and `$` → `\z`-style
anchors are not available in JSON Schema (ECMA `$`), so either keep `^…$` and add a `fullmatch` in
the ledger reader for candidate ids, run ids and timestamps (as `selector.py` does), or add
`"maxLength"` (16 for candidate ids, 20 for `ts`) to each pattern so a trailing LF is rejected by length.

## Info

### IN-01: `resume` compares only `code_git_sha`, ignoring `dirty` and the recorded `snapshot_sha256`

**File:** `src/llm4pol/run/resume.py:363-376`
**Issue:** The check follows ADR-0008 item 7 as written. A resume under an edited working tree at the
same HEAD passes, since `code.dirty` is recorded only in `meta.json` and never compared. The snapshot
is compared by name only. `TableBackend` verifies the parquet's snapshot metadata name, but
`meta.json`'s `snapshot_sha256` is never re-checked. A rebuilt parquet under the same snapshot id
resumes into different served values. Consider refusing or warning on `dirty`, and comparing
`snapshot_sha256` to `population.candidate_metadata(root)`. This would change ADR-0008 item 7, so it is
an owner decision.

### IN-02: I/O failures during append are reported as "ERROR: input refused" (exit 2)

**File:** `src/llm4pol/run/__main__.py:85-98, 261-262`
**Issue:** `OSError` is in `_INPUT_ERRORS`. An `ENOSPC` or `EIO` raised inside `ledger._write`, which is
the event that leaves a torn tail, is reported as an input defect. The run is then unresumable, since
a torn tail is refused. Split `OSError` raised while reading operator-supplied paths from `OSError`
raised while writing the run record, and give the latter its own exit code and a message that names
the torn tail and its offset.

### IN-03: `replay --out` silently overwrites and is non-atomic

**File:** `src/llm4pol/run/__main__.py:228-231`
**Issue:** `(args.out / name).write_bytes(data)` replaces existing files in `--out`, while everything
else in the package "never overwrites". A rerun into a populated directory silently replaces earlier
replay output. Use `xb`, or refuse when any of the three names exist.

### IN-04: `_git` has no timeout and drops git's stderr

**File:** `src/llm4pol/run/config.py:253-267`
**Issue:** `subprocess.run(..., check=False)` has no `timeout`. A stuck `git` (index lock, network
filesystem) hangs `run` and `resume` indefinitely. On failure the message is only
`git <verb> failed in <repo>`; git's stderr (for example "detected dubious ownership") is captured and
discarded, so the failure cannot be diagnosed. Add `timeout=30` and include a sanitised first line of
stderr in the `CodeIdentityError`.

### IN-05: The real-table evidence tests skip whenever the parquets are absent, which is always in CI

**File:** `tests/test_run_real_file.py:60-70`
**Issue:** `data/processed/` is git-ignored, so CI on both platforms skips this module. The M3
exit-criterion evidence (39,454-member population etc.) is then reproduced locally only. This is
acceptable by the data policy, but the commit that records the M3 evidence should name that the
guard is local, and `04-VERIFICATION` should not read "two-platform CI" as covering it.

### IN-06: `_check_events` does not cross-check the ledger against its own header

**File:** `src/llm4pol/run/ledger.py:225-274`; `src/llm4pol/run/reduce.py:126-150`
**Issue:** Nothing checks that population constraint keys equal the problem's constraint properties,
that `primary` is one of the known population names, that a `run_closed(completed)` follows all
`budget.iterations` iterations, or that `evaluation` results cover the problem's property keys. A
hand-edited or foreign-writer ledger passes `read`. `_holds` then treats a missing constraint array as
"value None", so every member is infeasible and the reduction silently reports `hits_* = None`. Add
these checks to `_check_events`/`_check_populations`, since they are cheap and are the same class as
the checks already there.

### IN-07: Three separate cost aggregations and a mutable payload inside frozen events

**File:** `src/llm4pol/run/resume.py:162-190, 272-274`; `src/llm4pol/run/reduce.py:289-314`; `src/llm4pol/run/ledger.py:123-154`
**Issue:** `rebuild_state` sums result costs, `_cost` sums event `cost`, and `usage_of` sums result
costs after verifying the two agree. `Outcome.evals` therefore uses a different source than the
`usage.json` written in the same call. They agree only because `usage_of` runs first in `_finish`.
Derive `Outcome` from `usage_of(ledger)`. Separately, `Event` is a frozen dataclass whose `payload` is
the live parsed `dict` (population arrays included). It is passed by reference to the selector in
`history` and kept in `_Recorder.events`, so a selector mutating a payload would change the data
`_drive_iteration` and `_history_before` read for the rest of the run. Freeze it
(`types.MappingProxyType` with tuple-ised lists) or deep-copy at the selector boundary.

---

_Reviewed: 2026-09-30_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
