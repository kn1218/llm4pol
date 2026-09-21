# LLM4POL bootstrap report

- Date: 2026-09-11 (session a0b03baf-5561-4462-b33d-bae34ea6a4be)
- Repository: `C:/Users/molsim/Desktop/LLM4POL` -- `git init -b main`, **0 commits** (left for the lead engineer to review and commit)
- Result: **all 14 steps completed; the check gate passes (5/5); nothing outside the new repository was modified.**

## 1. What was created

| step | artifact | note |
|---|---|---|
| 1 | directory + `git init -b main` | branch `main`, no commits |
| 2 | `.gitignore` | CALF20's rules (`.omc/`, `.claude/settings.local.json`, `.claude/hooks/node_modules/`, `.env`, `.env.*`, `!.env.example`, `*.egg-info/`, `.pixi/`, `env/.pixi/`) plus `data/raw/ data/interim/ data/processed/ *.pkl __pycache__/ .mypy_cache/ .ruff_cache/ .pytest_cache/ .import_linter_cache/`. `.claude/` and `.planning/` stay tracked exactly as in CALF20 (only `settings.local.json` and hook `node_modules` ignored). `git check-ignore -v` confirmed each rule. |
| 3 | `README.md` | goal (port LLM4MOF to polymers; charter not yet approved), status pre-charter (2026-09-11), layout, check gate, data policy, doc pointers |
| 4 | `CLAUDE.md` | precedence `docs/MASTER-PLAN.md (to be written) > .planning/REQUIREMENTS.md > CLAUDE.md > generated .claude/CLAUDE.md`; data policy; "no production code before the charter"; how to run checks; states that no OMC-disabling setting was written |
| 5 | `docs/audit/` | 10 audit `*.md` (top level) + `refute_csv/copolymer-csv-refutation.md` copied; `docs/audit/README.md` written (provenance, scripts stay in scratchpad, pickles/CSV side-tables must never be committed) |
| 6 | `docs/reference/LLM4Polymer_Research_Proposal_v1.0_2026-07.md` | verbatim copy (16,387 chars body; source sha256 `ea21e1ccdd698687782af8e03407d8c0387a95c34a655d3ac351ea2d005f6212`) with a 3-line blockquote header: pre-charter concept document, superseded by MASTER-PLAN.md once written |
| 7 | `data/README.md`, `data/MANIFEST.sha256`, `data/raw/*` | manifest format `<sha256>  <size>  <filename>`; copolymer.zip carries a KNOWN-CORRUPT comment; three files **copied** (`cp -p`) and re-hashed -- identical to source |
| 8 | `env/pixi.toml` + `env/pixi.lock` | `pixi install` succeeded, lock produced (212,798 bytes) |
| 9 | `pyproject.toml`, `src/llm4pol/__init__.py`, `scripts/check.py`, `tests/test_manifest.py` | see section 4 |
| 10 | `.github/workflows/ci.yml` | ubuntu-latest + windows-latest matrix, `actions/checkout@v7.0.1`, `prefix-dev/setup-pixi@v0.10.2` with `pixi-version: v0.80.0`, runs `pixi run --manifest-path env/pixi.toml check` |
| 11 | `.env.example` | `LLM_PROVIDER=`, `OPENAI_API_KEY=`, `GEMINI_API_KEY=`, `CLAUDE_API_KEY=` (empty) |
| 12 | GSD Core per-project install | see section 3 |
| 13 | check gate | 5/5 PASS (section 6) |
| 14 | no-modification verification | section 7 |

## 2. Final tree (depth 3; `.git`, `.pixi`, tool caches and the inside of `.claude/*` subfolders elided)

```
.
./.claude
./.claude/.gsd-profile
./.claude/.gsd-staging
./.claude/agents
./.claude/commands
./.claude/gsd-core
./.claude/gsd-file-manifest.json
./.claude/gsd-install-state.json
./.claude/hooks
./.claude/scripts
./.claude/settings.local.json
./.env.example
./.github
./.github/workflows
./.github/workflows/ci.yml
./.gitignore
./.import_linter_cache
./.import_linter_cache/.gitignore
./.import_linter_cache/342f2014b0105438d2fe99de1c7a1943112f534f.data.json
./.import_linter_cache/CACHEDIR.TAG
./.import_linter_cache/llm4pol.meta.json
./CLAUDE.md
./data
./data/interim
./data/MANIFEST.sha256
./data/processed
./data/raw
./data/raw/230227_Homopolymer_CanonicalSMILES.xlsx
./data/raw/copolymer.zip
./data/raw/polymer_final_0824.csv
./data/README.md
./docs
./docs/audit
./docs/audit/citation-check.md
./docs/audit/copolymer-csv.md
./docs/audit/cross-linkage.md
./docs/audit/DATA-FOUNDATION-REPORT.md
./docs/audit/environment.md
./docs/audit/environment-verification.md
./docs/audit/homopolymer-xlsx.md
./docs/audit/homopolymer-xlsx-refutation.md
./docs/audit/prior-art.md
./docs/audit/README.md
./docs/audit/refute_csv
./docs/audit/refute-cross-linkage.md
./docs/reference
./docs/reference/LLM4Polymer_Research_Proposal_v1.0_2026-07.md
./env
./env/pixi.lock
./env/pixi.toml
./pyproject.toml
./README.md
./scripts
./scripts/check.py
./src
./src/llm4pol
./src/llm4pol/__init__.py
./tests
./tests/test_manifest.py
```

Not shown at depth 3: `docs/audit/refute_csv/copolymer-csv-refutation.md`. `.claude/` holds
72 `commands/gsd-*.md`, 35 `agents/gsd-*.md`, 28 `hooks/gsd-*`, `gsd-core/` (VERSION 1.13.0),
`scripts/`, `.gsd-staging/user-artifacts/` (empty, installer-created), `.gsd-profile` = `full`.
`git status --short --untracked-files=all -- .claude` lists 770 files that would be tracked
(settings.local.json is ignored, as in CALF20). `.import_linter_cache/` at the repo root is
created by import-linter on each run and is git-ignored. `data/interim/` and `data/processed/`
are empty directories (git will not track them; they exist so the ignore rules are visible).

## 3. GSD install

Exact command, run from `C:/Users/molsim/Desktop/LLM4POL` with stdin from `/dev/null`:

```
npx -y --package=@opengsd/gsd-core@latest -- gsd-core --claude --local
```

- This is the `manualInstallCommand` form from CALF20's `.claude/gsd-core/bin/lib/package-identity.cjs`
  (`npx -y --package=@opengsd/gsd-core@latest -- gsd-core --<runtime> --<scope>`), and matches
  `.claude/gsd-core/workflows/update.md` line 388 (`npx -y --package=@opengsd/gsd-core@"$TAG" -- gsd-core "$RUNTIME_FLAG" --local`).
- `npm view @opengsd/gsd-core` reported `latest = 1.13.0` at install time -- the same version CALF20
  has (`.claude/gsd-core/VERSION` = 1.13.0, installed 2026-09-10, manifest mode full / runtime claude / scope local).
- Installer output: "Installed 72 commands to commands/ (gsd-<cmd>.md flat form)", agents, hooks
  (bundled), 28 hook configurations written into `.claude/settings.local.json`; statusLine skipped
  (local install); "[legacy-cleanup] Removed 0 legacy artifact(s)". Exit code 0. Full log:
  `gsd_install.log` next to this report.
- Verified: **72** `gsd-*.md` command files in `.claude/commands` (`diff` against CALF20's command
  list: identical), 35 agents, 28 hooks, profile `full`, runtime marker `claude`.
- `.claude/settings.local.json` contains only what the installer wrote: keys `hooks`, `worktree`,
  `permissions` (`allow`: `Bash(npx gsd-core *)`, `Read(.planning/*)`, `Edit(.planning/*)`,
  `Read(STATE.md)`, `Edit(STATE.md)`). It contains **no** `enabledPlugins` and **no**
  `env.DISABLE_OMC` (grep for "omc" = 0 hits). For the record: CALF20's `settings.local.json`
  additionally has `"enabledPlugins": {"oh-my-claudecode@omc": false}` and
  `"env": {"DISABLE_OMC": "1"}` (OMC is disabled in CALF20); that was deliberately not replicated.
- No `/gsd-new-project` or any planning command was run; `.planning/` does not exist yet.

## 4. Python scaffold

- `pyproject.toml`: name `llm4pol`, version `0.0.1`, `requires-python >= 3.13`, setuptools with
  `packages.find where = ["src"]`, pytest `testpaths = ["tests"]`, ruff line-length 100 with
  `extend-exclude = [".claude", ".planning", ".gsd", ".omc", "docs", "env", "data"]`, mypy
  `strict = true` on package `llm4pol` (`mypy_path = "src"`), `[tool.importlinter]` with
  `root_package = "llm4pol"`, `include_external_packages = true` and zero contracts (comment:
  contracts are added when the architecture is frozen).
- `src/llm4pol/__init__.py`: `__version__ = "0.0.1"` only.
- `scripts/check.py`: adapted from CALF20 -- steps `ruff check`, `ruff format --check`, `mypy`,
  `import-linter` (the console-script resolver `lint_imports_argv()` is kept), `pytest`; the
  CALF20-specific `[tool.calfcheck]` schema-inventory step and its `yaml`/`jsonschema` imports
  were dropped (no protocol files exist yet). `--fast` skips mypy, as in CALF20. UTF-8
  reconfiguration of stdout/stderr and of subprocess decoding kept (Korean-locale Windows).
- `tests/test_manifest.py`: imports `llm4pol` and checks `__version__`; parses
  `data/MANIFEST.sha256` (format `<sha256>  <size_bytes>  <filename>`, `#` comments); verifies
  size + sha256 of every manifest entry present in `data/raw/` (skips with a stated reason when
  none is present); asserts `docs/audit/DATA-FOUNDATION-REPORT.md` exists. On this machine (data
  present) all 4 tests run and pass.

## 5. pixi

- Manifest: `env/pixi.toml`, workspace `llm4pol-env`, channel `conda-forge`, platforms
  `win-64` + `linux-64`, features `base` (python 3.13.*, pandas, numpy, scipy, scikit-learn,
  rdkit, pyarrow, pydantic, openpyxl, jsonschema) and `dev` (pytest, ruff, mypy from conda-forge;
  `import-linter` as a pypi-dependency), environment `default = base + dev`; tasks
  `workspace-root-probe`, `check`, `check-fast` (cwd `..`, `PYTHONPATH=src`), same pattern as CALF20.
- `pixi install --manifest-path env/pixi.toml`: **28 s** wall-clock (solve + install, warm
  local package cache), exit 0, `env/pixi.lock` produced (212,798 bytes). Log: `pixi_install.log`.
- Resolved (default env, win-64): Python 3.13.15, pandas 3.0.5, rdkit 2026.03.6, pytest 9.1.1,
  ruff 0.16.6; all 13 declared packages import inside the environment.

## 6. Check gate (final run, last 30 lines)

Command: `pixi run --manifest-path env/pixi.toml check` -> exit 0 (log: `check_final.log`).

```
--- ruff check ---
All checks passed!
PASS ruff check
--- ruff format --check ---
5 files already formatted
PASS ruff format --check
--- mypy ---
Success: no issues found in 1 source file
PASS mypy
--- import-linter ---
=============
Import Linter
=============


---------
Contracts
---------

Analyzed 2 files, 1 dependencies.
---------------------------------


Contracts: 0 kept, 0 broken.
PASS import-linter
--- pytest ---
....                                                                     [100%]
4 passed in 0.03s
PASS pytest
SUMMARY: 5/5 steps passed
```

The first run (`check_run1.log`, before the GSD install) gave the identical 5/5 result; no lint
or format fixes were needed. ("5 files" = the 3 Python files plus README.md and CLAUDE.md, whose
fenced code blocks ruff 0.16 also inspects.)

## 7. Data hashes and no-modification verification

Manifest (`data/MANIFEST.sha256`) and `data/raw/` copies -- identical to the Dropbox source before and after:

| file | sha256 | bytes |
|---|---|---|
| `polymer_final_0824.csv` | `a11091838c5ed121a87210488ade3ed1469424cf1505af049b792b2fac478013` | 10,015,654 |
| `230227_Homopolymer_CanonicalSMILES.xlsx` | `06a8f059cd5618878e7a9cb3245c93e2e386c30ef55f3f342383f90bbff7ab0a` | 985,398 |
| `copolymer.zip` (KNOWN-CORRUPT) | `cf1c8684f565620dbd7eba237dfa3d6549c12515ac161d30a1ddf382354873e9` | 8,783 |

copolymer.zip precision: the file is a **valid zip container** (PK magic, 15 listable members:
dens_co, elec_all, elec_co, elong_all, elong_co, tensm_all, tensm_co, tenss_all, tenss_co, tg_all,
tg_co, tm_all, tm_co, vol_all, vol_co, 6.1 MB uncompressed) whose every member decompresses to
NUL bytes only. The raw 8,783-byte file itself is not all-NUL (6,892 of 8,783 bytes are NUL);
the manifest comment states this precisely and cites audit defect D16.

- Source mtimes in `C:/Users/molsim/Dropbox/Work to do/LLM4POL` before and after: csv
  `2026-07-21 11:04:54.9013505 +0900`, xlsx `2026-07-21 11:05:00.9174741 +0900`, zip
  `2026-07-21 11:05:11.0815307 +0900` -- unchanged; sha256 unchanged.
- Proposal source mtime `2026-07-21 10:56:07 +0900` -- unchanged (read only).
- `git -C C:/Users/molsim/Desktop/CALF20_DiscoveryLoop status --short` before and after: identical
  (`?? .gsd/`, `?? .planning/milestone.lock`, `?? .planning/phases/01-governance-repository-and-external-systems/.review-diagnostics/`
  -- pre-existing untracked entries, none attributable to this task). CALF20 `.claude/` mtime
  2026-09-11 09:14 and `.claude/settings.local.json` mtime 2026-09-10 15:38 predate this session's work.

## 8. Failures / deviations

- Two Bash heredoc batches failed to parse in the Bash tool (`unexpected EOF while looking for
  matching quote`) before writing anything; the affected files were written with the Write tool
  instead. No partial files resulted. All other commands exited 0.
- Wording deviation, for the lead engineer: the task text described copolymer.zip as
  "all-NUL"; the audit's phrase is "15 member CSVs, all NUL bytes". Verified in-session that the
  members are NUL and the container is valid; the manifest comment uses the precise wording.
- `CLAUDE.md` records that no OMC-disabling setting was written and leaves that decision to the
  owner at charter time (CALF20 disables OMC; the task said to report the fact, not replicate it).

## 9. Files in this scratchpad folder

`BOOTSTRAP-REPORT.md` (this), `pixi_install.log`, `pixi_start.txt` / `pixi_end.txt`,
`gsd_install.log`, `check_run1.log`, `check_final.log`, `tree.txt`.
