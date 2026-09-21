# Phase 1: Foundation — Context

**Gathered:** 2026-09-22
**Source:** charter `docs/MASTER-PLAN.md` §13 M0, `INVARIANTS.md` R-1..R-5, and the house
precedent `C:/Users/molsim/Desktop/CALF20_DiscoveryLoop` (Phase 1 there: governance,
repository skeleton, single check command, CI matrix, history secret scan). The owner asked
that each step be re-checked carefully against how the prior project was built; no
discuss-phase interview was held because the owner is unavailable and the charter is the
input (ADR-0002).
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers charter M0: a reproducible development base whose single check gate is
green on both CI platforms, with the snapshot-fetch dependency locked, and with the
repository's secret-handling rule enforced on history, not only on the working tree.

**Already done before planning (verify, do not redo):**
- First commits exist on `main` (`567ce1d` bootstrap … `8cf794e` protocol placeholders).
- GitHub remote `kn1218/llm4pol` exists (public), CI run 35623670806 green on
  windows-latest and ubuntu-latest at `8cf794e`.
- `huggingface_hub >=1.32.0,<2` is in `env/pixi.toml` feature `base` and in `env/pixi.lock`.
- `.gitattributes` pins LF; `.env` is git-ignored; `.env.example` committed.

**Remaining work in this phase:** the R-3 history guard, the FOUND-02 import proof, the
Phase 1 verification evidence, and the `experiments/` policy note that the charter §10 changed
(PolyOmics-derived run outputs are not a licence problem; they stay untracked by policy).
</domain>

<decisions>
## Implementation Decisions

### D-01 History secret scan (R-3 guard, now applicable)
`INVARIANTS.md` R-3 says "a history secret scan is deferred until there is history". History
now exists. Port the precedent's `scripts/history_secret_scan.py` design: walks
`git rev-list --all` patches, pattern set assembled from fragments at runtime so the script's
own source cannot trip the scan, `--self-test` mode with synthetic positive controls that
must all fire, dotenv-path check over `git log --all --name-only` (excluding `.env.example`),
never prints a value. Add it as a step in `scripts/check.py` (`history-secret-scan`,
in-process call of the script's `main`, no `shell=True`) and a test that the self-test passes
and that a seeded fake key in a temp repo is detected. Pattern classes: OpenAI (`sk-…`),
Anthropic (`sk-ant-…`), Google AI (`AIza…`), Hugging Face (`hf_…`), GitHub (`ghp_`/`github_pat_`),
generic `KEY=<long token>` assignment in a tracked file. Promote R-3's guard entry in
`INVARIANTS.md` from ".gitignore; deferred" to the script + check step.

### D-02 FOUND-02 proof is an import, not a lock grep
The CI already installs the lock; prove `huggingface_hub` is importable by a test
(`tests/test_environment.py::test_huggingface_hub_importable`) that imports the package and
asserts a `__version__` matching `>=1.32,<2`. That is what makes "available on both platforms"
an observable, per the charter's exit-criterion rule.

### D-03 Do not add tooling the charter does not ask for
No version report, no pre-push hook installer, no SQLite, no schema-inventory step yet. The
schema-inventory check step (precedent `[tool.calfcheck]`) enters in Phase 2 with the first
schema (`protocol/schemas/property-registry.json`), so an empty inventory is never a passing
state.

### D-04 Verification is evidence, not narrative
Phase 1's `01-VERIFICATION.md` cites: the CI run id and per-job conclusions on both
platforms, `git ls-files .env` empty, the self-test output of the secret scan, and the
import test. Each maps to charter §13 M0 exit criteria (1) gate green both platforms, (2)
first commit exists, (3) `.env` untracked and no secret in output/logs/history.

### D-05 CI trigger
Push events did not create workflow runs on this repository twice in a row while
`workflow_dispatch` did. Plans must not rely on push-triggered runs for verification: verify
with `gh workflow run check --ref main` followed by `gh run watch`. Record the observation in
the verification; investigating the push trigger is not in scope.

### D-06 experiments/README.md wording
Charter §10 changed the reason run outputs are untracked: for the PolyOmics layer there is no
licence problem (CC BY 4.0), they are untracked by policy (size, churn, and PoLyInfo-derived
content once M8 exists). Update the README's "Why it is ignored" section accordingly. No
change to `.gitignore`.

### Claude's Discretion
- File layout of the secret-scan test and fixture repo (use `tmp_path` + `git init`).
- Exact regex fragments, as long as the self-test proves every pattern fires.
</decisions>

<specifics>
## Specific Ideas

- The precedent's scan lives at `C:/Users/molsim/Desktop/CALF20_DiscoveryLoop/scripts/history_secret_scan.py`
  and its test at `.../tests/test_history_secret_scan.py` — read both and port the design, not
  the calfloop-specific wording. It is MIT-style in-house code by the same owner; attribution
  in the module docstring ("ported from CALF20_DiscoveryLoop") is enough.
- `scripts/check.py` has an ordered `STEPS` list designed to be appended to; keep
  `history-secret-scan` before `pytest`.
- Commit messages follow conventional commits scoped by plan id: `feat(01-01): …`,
  `test(01-01): …` (tests first, TDD order visible in the log as in the precedent).
</specifics>

<deferred>
## Deferred Ideas

- Schema-inventory check step → Phase 2 (first schema).
- Version report of adopted tools → not requested by the charter; revisit if a platform
  discrepancy ever appears.
- Push-trigger investigation for GitHub Actions → out of scope; `workflow_dispatch` suffices.
</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-09-22 from the charter and the CALF20 precedent (owner asleep; no interview)*
