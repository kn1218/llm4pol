# LLM4POL — Environment and Project-Conventions Audit

Audit date: 2026-09-11. Auditor: environment lane of the multi-agent LLM4POL audit.
Every number below was computed on this machine during this session; nothing is inferred.
Secret VALUES were never printed; only env-var NAMES with present/absent.

Output location: `C:/Users/molsim/AppData/Local/Temp/claude/C--Users-molsim-Dropbox-Work-to-do-LLM4POL/a0b03baf-5561-4462-b33d-bae34ea6a4be/scratchpad/audit/environment.md`

---

## 1. Python toolchain

**Interpreter on PATH:** `python` = `C:\Users\molsim\anaconda3\python.exe`, Python **3.13.9** (Anaconda build, MSC v.1929 64-bit). This is the conda **base** environment.

Package presence in base (via `importlib.metadata`):

| Package | Version | | Package | Version |
|---|---|---|---|---|
| pandas | 2.3.3 | | pyarrow | 21.0.0 |
| numpy | 2.3.5 | | polars | ABSENT |
| scipy | 1.16.3 | | duckdb | ABSENT |
| scikit-learn | 1.7.2 | | pydantic | 2.12.4 |
| rdkit | 2025.9.6 | | pytest | 8.4.2 |
| torch | **ABSENT** | | ruff | 0.12.0 |
| transformers | ABSENT | | mypy | 1.17.1 |
| peft | ABSENT | | hydra-core | ABSENT |
| accelerate | ABSENT | | omegaconf | ABSENT |
| lightgbm | ABSENT | | mlflow | ABSENT |
| xgboost | ABSENT | | wandb | ABSENT |
| openpyxl | 3.1.5 | | dvc | ABSENT |
| jupyter | 1.1.1 (jupyterlab 4.4.7, notebook 7.4.5) | | | |

**Environment/package managers on PATH:**

| Tool | Location | Version |
|---|---|---|
| conda | `C:/Users/molsim/anaconda3/Scripts/conda` | 26.1.1 |
| pixi | `C:/Users/molsim/.pixi/bin/pixi` | 0.80.0 |
| uv | ABSENT | – |
| mise | ABSENT | – |
| poetry | ABSENT | – |
| hatch | ABSENT | – |

**conda env list** (4 named envs + base; `llm2auto` is printed twice by conda, same path):

| env | Python | torch | transformers | rdkit | pandas | CUDA available |
|---|---|---|---|---|---|---|
| base | 3.13.9 | ABSENT | ABSENT | 2025.9.6 | 2.3.3 | n/a |
| llm2auto | 3.11.14 | **2.2.0+cpu** | 5.5.0 | ABSENT | 3.0.1 | False (torch.version.cuda = None) |
| mofviz | 3.11.15 | ABSENT | ABSENT | ABSENT | 3.0.3 | – |
| pacman | 3.10.20 | **2.13.0** | ABSENT | ABSENT | 2.3.3 | False (torch.version.cuda = None) |
| pacmof | 3.10.20 | ABSENT | ABSENT | ABSENT | 2.3.3 | – |

Conclusion: **no environment on this machine has a CUDA-enabled torch.** The two torch installs (llm2auto 2.2.0+cpu, pacman 2.13.0) both report `torch.cuda.is_available() == False`. No env has peft/accelerate/lightgbm/xgboost; only llm2auto has transformers (5.5.0) and it lacks rdkit.

## 2. Hardware

| Item | Value | Source |
|---|---|---|
| GPU | NVIDIA GeForce RTX 5050, **8151 MiB** VRAM | `nvidia-smi --query-gpu` |
| Driver | 610.74 (KMD 610.74) | nvidia-smi |
| CUDA (driver UMD) | **13.3** | nvidia-smi header |
| CPU | Intel Core i5-14600K, 14 physical cores / 20 logical | Win32_Processor |
| RAM | 31.7 GB total, 2.3 GB free at audit time | Win32_OperatingSystem |
| Disk C: | 930.6 GB total, **400.5 GB free** | Win32_LogicalDisk |
| OS | Windows 11 Pro 10.0.26200 | Win32_OperatingSystem |

Note: driver-level CUDA 13.3 with an RTX 5050 (Blackwell) implies any torch wheel chosen must be a CUDA-12.8+/13.x build; the cpu-only torch in `llm2auto` will not use this GPU.

## 3. Dev tools

| Tool | Version / status |
|---|---|
| git | 2.53.0.windows.2 (`/mingw64/bin/git`) |
| gh | 2.96.0 (2026-07-02); `gh auth status`: logged in to github.com as **kn1218** via keyring, protocol https, scopes `gist, project, read:org, repo, workflow` (token not printed) |
| node | v24.14.0 (`C:/Program Files/nodejs`) |
| npm | 11.9.0 |
| pnpm | ABSENT |
| bun | 1.3.10 (`C:/Users/molsim/.bun/bin/bun`); `bun pm ls -g` reports no global package.json |
| Docker | ABSENT (no `docker` on PATH; `C:\Program Files\Docker` does not exist) |
| WSL | `wsl.exe` present but `wsl --status` prints "The Windows Subsystem for Linux is not installed" |

**Global npm packages** (`npm ls -g --depth=0`, prefix `C:\Users\molsim\AppData\Roaming\npm`):
`@anthropic-ai/claude-code@2.1.268`, `@marp-team/marp-cli@4.3.1`, `@openai/codex@0.154.0`, `oh-my-claude-sisyphus@4.15.6`, `opencode-ai@1.2.25`.

**ORCA ADE** — `C:/Users/molsim/AppData/Local/Programs/orca/`:
- `Orca.exe` VersionInfo: ProductName **Orca**, ProductVersion **1.4.167.0**, CompanyName **stablyai**.
- `resources/app.asar` → embedded `package.json`: `"name": "orca"`, `"version": "1.4.167"`, `"description": "Next-gen IDE for parallel agentic development"`, `"homepage": "https://github.com/stablyai/orca"`; bin `orca` → `./out/cli/index.js`. Notable deps: `node-pty`, `ssh2`, `agent-browser ~0.27.0`, `@linear/sdk`, `sherpa-onnx`, `electron-updater`.
- `resources/app-update.yml`: `owner: stablyai`, `repo: orca`, `provider: github`.
- `resources/bin/orca.cmd`, `orca.exe` (CLI shim); `resources/computer-use-windows`, `resources/agent-browser-win32-x64.exe`, `resources/plugins/launch`, `resources/onboarding/feature-wall`.
- No README.md inside the asar (0 `.md` files among its 2,487 entries) and none in the install folder. The only local description is the package.json description string above. The CALF20 project's CLAUDE.md describes it as "the agent development environment on the build plane" (see section 7). Not launched.

## 4. GSD availability

**Global scope:** NOT installed.
- `C:/Users/molsim/.claude/commands/` — does not exist. `C:/Users/molsim/.claude/agents/` — does not exist.
- `find ~/.claude -maxdepth 4 -iname '*gsd*'` → 0 hits; `-iname '*get-shit-done*'` → 0 hits.
- `~/.claude/skills/` contains only `hpc-submit` and an empty `learned/`.
- `~/.claude/plugins/installed_plugins.json` lists 3 plugins, none GSD (see section 5). `known_marketplaces.json` and `settings.json` contain no "gsd"/"get-shit-done".
- Global npm: no GSD package (list above). `gsd` / `get-shit-done` not on PATH.
- The only grep hits for "gsd" under `~/.claude/plugins` were base64 hash substrings inside `package-lock.json` files (e.g. `vANyubuqfZWTveU//DYVGsDG7RKL/vEw`) — false positives.
- Project `C:/Users/molsim/Dropbox/Work to do/LLM4POL/.claude/` — does not exist. LLM4POL contains only `.omc/state/` (OMC session state), the 3 data files, nothing else.

**Project-local scope — INSTALLED in `C:/Users/molsim/Desktop/CALF20_DiscoveryLoop/.claude/`:**
- `.claude/gsd-file-manifest.json`: `"manifestVersion": 2, "version": "1.13.0", "timestamp": "2026-09-10T06:36:45.919Z", "mode": "full", "runtime": "claude", "scope": "local"`.
- `.claude/commands/` — **72** `gsd-*.md` commands: gsd-add-tests, gsd-ai-integration-phase, gsd-audit-fix, gsd-audit-milestone, gsd-audit-uat, gsd-autonomous, gsd-capture, gsd-cleanup, gsd-code-review, gsd-complete-milestone, gsd-config, gsd-debug, gsd-discuss-phase, gsd-docs-update, gsd-eval-review, gsd-execute-phase, gsd-explore, gsd-extract-learnings, gsd-fast, gsd-forensics, gsd-graphify, gsd-health, gsd-help, gsd-import, gsd-inbox, gsd-ingest-docs, gsd-manager, gsd-map-codebase, gsd-mempalace-capture, gsd-mempalace-recall, gsd-milestone-summary, gsd-mvp-phase, gsd-new-milestone, gsd-new-project, gsd-next, gsd-ns-context, gsd-ns-ideate, gsd-ns-manage, gsd-ns-project, gsd-ns-review, gsd-ns-workflow, gsd-onboard, gsd-pause-work, gsd-phase, gsd-plan-phase, gsd-plan-review-convergence, gsd-pr-branch, gsd-profile-user, gsd-progress, gsd-quick, gsd-quick-batch, gsd-resume-work, gsd-review, gsd-review-backlog, gsd-secure-phase, gsd-settings, gsd-ship, gsd-sketch, gsd-spec-phase, gsd-spike, gsd-stats, gsd-surface, gsd-thread, gsd-ui-phase, gsd-ui-review, gsd-ultraplan-phase, gsd-undo, gsd-update, gsd-validate-phase, gsd-verify-work, gsd-workspace, gsd-workstreams.
- `.claude/agents/` — **35** `gsd-*.md` agents (gsd-planner, gsd-executor, gsd-verifier, gsd-code-reviewer, gsd-debugger, gsd-roadmapper, gsd-phase-researcher, gsd-security-auditor, and others).
- `.claude/hooks/` — 28 `gsd-*` hook scripts (js/sh) wired in `.claude/settings.local.json` (SessionStart, PreToolUse, PostToolUse, SubagentStop, Stop, PreCompact, FileChanged).
- `.claude/gsd-core/` — runtime: `bin/gsd-tools.cjs`, `bin/check-latest-version.cjs`, `bin/lib/package-identity.cjs`, `contexts/{dev,research,review}.md`, `references/*.md`, `templates/*.md`.
- `.gsd/dispatch-isolation-sentinel.json`, `.claude/.gsd-staging/`, `.claude/gsd-install-state.json` (5 applied migrations incl. `2026-06-02-rename-get-shit-done-to-gsd-core`).
- `.planning/` — GSD planning artifacts: `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `state.json`, `config.json`, `milestone.lock`, `research/{ARCHITECTURE,FEATURES,HPC-ENV,PITFALLS,STACK,SUMMARY}.md`, `phases/01-governance-repository-and-external-systems/` (01-01..01-11 PLAN.md, 01-01..01-06 SUMMARY.md, 01-CONTEXT/DISCUSSION-LOG/PATTERNS/RESEARCH/REVIEWS/SKELETON/VALIDATION.md, COVERAGE.md).

**How it is installed (verified from local files):** `.claude/gsd-core/bin/lib/package-identity.cjs` line 6: `const packageName = "@opengsd/gsd-core";` and line 16 builds the manual install as `npx -y --package=${packageName}@latest -- ${binName}${runtimeFlag} --${scope}`. Strings `npx @opengsd/gsd-core@latest` (2 hits) and `npx @opengsd/gsd-core@latest --global` (2 hits) appear in `.claude/`. `settings.local.json` allows `"Bash(npx gsd-core *)"`. So the observed install pattern is an **npx-driven per-project install of the npm package `@opengsd/gsd-core`** (scope `local`), not a global install. The file also documents a `--global` flag, but a global install was not exercised here.

## 5. Claude Code plugin / skill inventory

`~/.claude/plugins/installed_plugins.json` (schema v2), all scope `user`:

| Plugin | Version installed | installPath | installedAt / lastUpdated |
|---|---|---|---|
| oh-my-claudecode@omc | 4.15.6 | `plugins/cache/omc/oh-my-claudecode/4.15.6` | 2026-03-20 |
| context7@claude-plugins-official | 3b600518a637 | `plugins/cache/claude-plugins-official/context7/3b600518a637` | 2026-03-23 / 2026-09-10 |
| everything-claude-code@everything-claude-code | 1.9.0 | `plugins/cache/everything-claude-code/everything-claude-code/1.9.0` | 2026-04-02 |

Cache directories present: `omc/oh-my-claudecode/{4.9.0, 4.15.4, 4.15.6}`, `everything-claude-code/everything-claude-code/1.9.0`, `claude-plugins-official/context7/{0120fb83da5d, 3b600518a637, 3ea32df27be7, 85cce0381e78, b819188d2eea, ed404106fcd8, unknown}`.

`~/.claude/settings.json`: `enabledPlugins` = all three above `true`; `model: "fable"`; hooks registered for 10 events (UserPromptSubmit, Stop, StopFailure, SubagentStart, SubagentStop, TeammateIdle, PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest); `permissions.allow` has 42 entries; `env` block is empty (no API keys set via settings).

`~/.claude/skills/`: `hpc-submit/` (SKILL.md + `transport.py`, 445 lines, stdlib-only) and `learned/` (empty).

**hpc-submit skill — targets and project contract (quoted from SKILL.md):**
- Description: "Submit / monitor / retrieve / cancel HPC simulations (GCMC, Zeo++, RASPA, LAMMPS) on the dirac PBS clusters ... Routes through the ACTIVE project's submit entry point using that project's HPC config (conventionally scripts/submit.py + config/hpc.json; a project may place them elsewhere -- read its README/layout first) — never runs raw ssh/qsub by hand."
- Topology: "**Gateway = lab PC** (`DESKTOP-KQ6N3NT`) — the *only* machine that submits, polls, and writes the registry. Reaches `dirac1` / `dirac2` by key-auth SSH aliases in `~/.ssh/config`". "**Client = home PC** — cannot submit directly; it drops a write-once request file into the project's `registry/QUEUE/`". "Detect role at run time from `config/hpc.json` → `machine_roles[$COMPUTERNAME]`."
- Project must provide: "It must have an hpc config (conventionally `config/hpc.json`; copy from `config/hpc.example.json` and fill the two `machine_roles` COMPUTERNAMEs) and a submit entry point (conventionally `scripts/submit.py`). If either is missing, say so and stop — wiring a project is that project's KICKOFF, not this skill's job."
- Tier mapping: "Tier-0/1 Widom → dirac2 4-pack; Tier-2 GCMC → dirac1".
- Transport contract: `submit_remote(cfg, job_spec)`, `poll(cfg, handle)`, `fetch(cfg, handle, globs, local_dest)`, `cancel(cfg, handle)`.
- Scheduler rules: "Real compute goes through **`qas`** (not raw `qsub`...)"; "There is NO raw-`qsub` case. Ever."; success = the word `Done` then a `qinfo` row; cancel needs both `qdel` and `qrm`; never put `debug` in a job name; per-user core caps "dirac1 `ac` 102 / `amd` 80 / `aa` 38 / `ax` 32 ... dirac2 `aa` 176 of 1068"; `ssh_retries` ≤ 3, `idempotent=False` for submits.
- A `config/hpc.example.json` template is NOT in the skill folder; copies exist at `C:/Users/molsim/Dropbox/Work to do/Problem screening/config/hpc.example.json` (top-level keys: `_comment, crlf_to_lf_extensions, default_profile, fetch_globs, job_prefix, local_raw_root, machine_roles, pbs_bin_path, poll_interval_s, poll_max_hours, profiles{dirac1,dirac2: default_for_tiers, host, jobs_per_qsub, node_property, scheduler, submit_script}, queue_dir, remote_base, remote_executables, ssh_retries, ssh_retry_delays_s`; machine_roles placeholders `FILL_LAB_PC_COMPUTERNAME`, `FILL_HOME_PC_COMPUTERNAME`; no password/token keys).

**Does the HPC have GPUs?** SKILL.md and transport.py contain 0 occurrences of `gpu`/`cuda`; hpc.example.json contains none. The only related statement is in CALF20's `.planning/research/HPC-ENV.md` section 1 table: dirac1 modules include "`cuda100/111`" and "**gpaw**", dirac2 is "same minus cuda"; the compute node classes listed are CPU classes (`ac`, `amd`, `aa`, `ab`, `ax`, `xeonphi` on dirac1; `aa` 1,068 cores on dirac2). No GPU node class or `ngpus` resource is stated anywhere → **GPU availability on dirac: unknown / not stated** (presence of a cuda module on dirac1 is the only hint).

## 6. API access (names only)

Process environment at audit time:

| Env var | Status |
|---|---|
| ANTHROPIC_API_KEY | absent |
| OPENAI_API_KEY | absent |
| GOOGLE_API_KEY | absent |
| GEMINI_API_KEY | absent |
| HF_TOKEN | absent |
| HUGGINGFACE_HUB_TOKEN | absent |
| WANDB_API_KEY | absent |

Registry-persisted (User scope) vars matching `API_KEY|TOKEN|HF_`: only `PLAYWRIGHT_MCP_EXTENSION_TOKEN`. Machine scope: none. `~/.claude/settings.json` `env`: empty.

Config-file presence: `~/.anthropic` missing; `~/.claude.json` exists; `~/.claude/.credentials.json` **exists** (Claude Code OAuth); `~/.codex/auth.json` **exists**; `~/AppData/Roaming/GitHub CLI/hosts.yml` exists; `~/.openai`, `~/.cache/huggingface/token`, `~/.huggingface/token`, `~/.netrc`, `~/.wandb` missing.

CALF20 project keeps provider keys in a git-ignored `.env` whose NAMES are: `LLM_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY, CLAUDE_API_KEY, OPENAI_API_KEY_2` (values not read). So API keys exist for that project but are not in the ambient environment.

## 7. Prior project conventions — CALF20_DiscoveryLoop

Path: `C:/Users/molsim/Desktop/CALF20_DiscoveryLoop`. Git repo (`rev-parse` → true), branch `main` tracking `origin/main` = `https://github.com/kn1218/calf20-discovery-loop.git`, **55 commits**, working tree clean except untracked `.gsd/`, `.planning/milestone.lock`, `.planning/phases/01-.../.review-diagnostics/`.

**Top-level layout (depth 2):**
```
.claude/{.gsd-staging,agents,commands,gsd-core,hooks,scripts}   .env (git-ignored)  .github/workflows/ci.yml
.gsd/  .planning/{phases,research}  .omc/  .venv-bootstrap/ (ignored)
CLAUDE.md  pyproject.toml  .gitignore
docs/{MASTER-PLAN.md, ENGINEERING-OPERATING-MODEL.md, governance/{ADR/0001..0020, AMENDMENTS.md, CHANGE-POLICY.md, GENERATED-DOC-CORRECTIONS.md, INVARIANTS.md, PROGRESS-TRACKING.md, REVIEW-CHECKLIST.md}}
env/{pixi.toml, pixi.lock, adopted-tools.yaml, VERSION-REPORT.md, README.md, pacmof2/environment.yml}
protocol/{README.md, models.yaml, contracts/, critic/, descriptors/, detectors/, nulls/, panel/{settings_v1.yaml, settings_v1.schema.json, settings_v1.provenance.yaml, run_settings.schema.json, README.md}, prompts/, scheduler/, scoring/}
scripts/{check.py, history_secret_scan.py, version_report.py}
src/calfloop/{campaign,contracts,critic,ledger,provider,science,scoring,settingshash}/
tests/{conftest.py, golden/settings_hash_v1.json, purity/test_decision_purity.py, test_check_inventory.py, test_history_secret_scan.py, test_import_boundary.py, test_settings_hash.py, test_version_report.py}
```
No top-level README.md (only `protocol/README.md` and `protocol/panel/README.md`).

**Package manager / environment:** pixi, manifest at `env/pixi.toml` (not repo root). Quotes:
- `env/pixi.toml`: `name = "calf20-loop-env"`, `channels = ["conda-forge"]`, `platforms = ["win-64", "linux-64"]`; features `win-dev` (python 3.13.*, ase, pymatgen, rdkit, pydantic ==2.13.5, jsonschema, h5py, mdanalysis; pypi: mace-torch ==0.3.16, rfc8785, openai, anthropic, pyiast), `dev` (pytest ==9.1.1, hypothesis, ruff, mypy, import-linter ==2.15), `linux-sim` (zeopp-lsmo, raspa2); environments `default` and `linux-sim`.
- Tasks: `check = { cmd = "python scripts/check.py", cwd = "..", env = { PYTHONPATH = "src" } }` and `check-fast`.
- `env/README.md` headings: "Why pixi was adopted", "The three environments", "Local install (Windows laptop)", "Check command", "CI setup step", "dirac install", "Lock stability".
- `.gitignore`: `.pixi/`, `env/.pixi/` ignored; "`env/pixi.lock` itself is NOT ignored; it is committed and its hash is referenced by the campaign record." Also ignores `.omc/`, `.claude/settings.local.json`, `.env`, `.env.*` ("secrets (API keys) — never commit"), `*.egg-info/`.
- `env/adopted-tools.yaml` is the "per-tool version report source of truth. Rendered by scripts/version_report.py into env/VERSION-REPORT.md; never hand-edit the report itself".

**pyproject.toml:** `name = "calf20-loop"`, `version = "0.1.0"`, `requires-python = ">=3.13"`, setuptools backend, `packages.find where = ["src"]` (src layout). `[tool.pytest.ini_options] testpaths = ["tests"]`, `addopts = "-q"`. `[tool.ruff] line-length = 100`, `src = ["src","scripts","tests"]`, `extend-exclude = [".claude", ".planning", ".gsd", ".omc", "docs", "env"]`. `[tool.mypy] strict = true`, `packages = ["calfloop"]`. `[tool.importlinter]` with 3 forbidden contracts (e.g. "Decision packages never reach the LLM provider": `calfloop.{ledger,contracts,scoring,critic,campaign}` may not import `calfloop.provider`, `openai`, `anthropic`). Custom `[tool.calfcheck] validated = [...]` schema-validation inventory table. `dev` extra: import-linter==2.15, pytest==9.1.1, ruff, mypy, jsonschema==4.26.0, rfc8785==0.1.4, PyYAML, hypothesis, setuptools.

**Single check command:** `scripts/check.py` docstring: "The single local check command (D-16). One command, identical on Windows and Linux: ``ruff check``, ``ruff format --check``, ``mypy``, the LLM-free import boundary (import-linter...), the explicit schema-validation inventory..., and ``pytest``. Every external tool is invoked through ``sys.executable -m`` ... never a bare tool name, never ``shell=True``". "Does not read ``.env`` and does not print any environment-variable value."

**CI:** `.github/workflows/ci.yml` job `check`, matrix windows-latest/ubuntu-latest, `prefix-dev/setup-pixi@v0.10.2` with `pixi-version: v0.80.0`, `manifest-path: env/pixi.toml`, step `pixi run --manifest-path env/pixi.toml check`.

**Testing:** 6 test files under `tests/` (+ `tests/purity/`, `tests/golden/`), pytest; commits show TDD order ("test(01-05): add failing tests..." precedes "feat(01-05): implement..."). `scripts/history_secret_scan.py` = "Pre-push history secret scan (GOV-05...)".

**Config style:** YAML + JSON Schema pairs inside `protocol/` (`settings_v1.yaml` + `settings_v1.schema.json` + `settings_v1.provenance.yaml`), `protocol/models.yaml` for model pins ("Model identity ... is a **pin**, not a credential"), `.env` for secrets, JSON for HPC config (`config/hpc.json`, planned in REQUIREMENTS HPC-01; not yet present — no `config/` dir exists yet).

**HPC submit pattern:** REQUIREMENTS.md HPC-01: "`config/hpc.json` (from the hpc-submit `hpc.example.json`, with a new project-specific remote base and `job_prefix`) and `scripts/submit.py` / `status.py` / `kill.py` exist and route every cluster job through the hpc-submit `transport.py` contract (`submit_remote / poll / fetch / cancel`), detecting gateway vs client role from `machine_roles`." ADR-0007 Decision: "Development and smoke tests run on the Windows 11 laptop (~8 cores, no GPU). Sweeps and DFT route through the existing hpc-submit transport to the dirac PBS clusters. This laptop is the gateway". ROADMAP criterion: "One job submitted through `scripts/submit.py` reaches dirac via `qas` only, its `Done` line is verified by a `qinfo` row count...".

**Docs structure:** `docs/MASTER-PLAN.md` (1,548 lines / 169,909 bytes; Parts I–III, chapters 1–19+ visible: N1 Grounding ... N10 Ledger) is "the authoritative scientific source of truth"; `docs/ENGINEERING-OPERATING-MODEL.md`; `docs/governance/` with 20 ADRs in MADR form (headings: Status / Context / Decision Drivers / Considered Options / Decision / Consequences / Source), `INVARIANTS.md`, `CHANGE-POLICY.md` ("three mutability levels", "Change classes A/B/C"), `AMENDMENTS.md` ("MASTER-PLAN amendment proposals are recorded, never silently applied" — ADR-0017), `GENERATED-DOC-CORRECTIONS.md`, `PROGRESS-TRACKING.md` ("GitHub Issues and Projects are the only progress dashboard"), `REVIEW-CHECKLIST.md`.

**Planning artifacts:** GSD `.planning/` (PROJECT, REQUIREMENTS, ROADMAP, STATE, research/*.md, phases/NN-slug/NN-MM-PLAN.md + SUMMARY.md). `.planning/config.json`: `model_profile: "adaptive"`, `commit_docs: true`, `parallelization: true`, `git.branching_strategy: "none"`, `create_tag: true`, `workflow.research/plan_check/verifier/nyquist_validation/code_review/security_enforcement: true`, `human_verify_mode: "end-of-phase"`, `mode: "yolo"`.

**Governance precedence (CLAUDE.md):** "1. `docs/MASTER-PLAN.md` ... 2. `.planning/REQUIREMENTS.md` ... 3. This hand-authored `CLAUDE.md` ... 4. The machine-generated blocks of `.claude/CLAUDE.md`". "GSD planning artifacts ... are **subordinate engineering artifacts**." Two planes: "**Build plane** (ORCA ADE → GSD Core → coding agents → worktrees → code)" vs "**Science plane** (CALF Runtime → state machine → API agents → evidence/contracts → ledger)". ADR-0003 title: "scientific agents are API calls, never Claude Code subagents". ADR-0004: "LLM provider adapter (OpenAI + Anthropic) with per-role matrix in protocol/models.yaml". ADR-0008: "append-only JSONL tables plus a rebuildable SQLite index". ADR-0011: "explicit registry of pure functions, no plugin framework". ADR-0015: "thin vertical path first, then widen". ADR-0018: "Greenfield build; no prior code imported".

**Tooling stance (CLAUDE.md "Tooling"):** "This project uses the GSD workflow only. oh-my-claudecode is disabled here (`.claude/settings.local.json`); ignore OMC orchestration instructions from the global `~/.claude/CLAUDE.md` in this repository." `.claude/settings.local.json` confirms: `"enabledPlugins": {"oh-my-claudecode@omc": false}`, `"env": {"DISABLE_OMC": "1"}`, `"worktree": {"baseRef": "head"}`. ENGINEERING-OPERATING-MODEL: "Two coding agents, both build-plane only: Claude Code sessions (OAuth) do the primary implementation; Codex performs independent review. Both operate inside worktrees". Ceremony ladder: `/gsd-quick` (sub-file tasks), `/gsd-debug`, `/gsd-execute-phase` ("research → architecture → plan → plan check → ORCA worktree fan-out → integration → verification → Codex review").

**Commit convention (git log, 20 most recent of 55):** conventional commits with the GSD plan id as scope, e.g. `feat(01-06): add windows-latest/ubuntu-latest CI matrix (GOV-04, ENV-03)`, `test(01-05): add failing tests for calfloop.settingshash (ENV-03)`, `docs(01-06): complete CI enforcement and progress tracker plan`, `chore(01-03): sync machine-readable state timestamp`, `fix(01-06): clear ruff findings that a stale .ruff_cache hid locally`. Requirement ids (GOV-xx, ENV-xx, D-xx, T-xx) are cited in parentheses.

## 8. Location risk (facts only)

- `C:/Users/molsim/Desktop/CALF20_DiscoveryLoop` **is** a git repo (55 commits, remote on GitHub) and lives on the Desktop, outside Dropbox. It is the only `.git` under `C:/Users/molsim/Desktop` at depth ≤ 2.
- `C:/Users/molsim/Dropbox/Work to do/LLM4POL` is **not** a git repo (no `.git`, no `.claude/`; contains only `.omc/state/` and the 3 data files).
- `.git` directories under `C:/Users/molsim/Dropbox/Work to do` (maxdepth 3): **4** — `Cognix/.git`, `Paper review/.git`, `poster/posterskill/.git`, `Prob_screening/.git`.
- `.git` directories under `C:/Users/molsim/Dropbox` (maxdepth 3): **8** — `Antigravity/{ALkg, LLM2POR_Core_20260319, New folder, OGM, Paperfetcher}/.git` plus `Work to do/{Cognix, Paper review, Prob_screening}/.git` (the depth-3 `poster/posterskill` one falls outside this shallower search).
- The hpc-submit skill itself warns: "Do not bypass this (Dropbox file locks are unreliable → ledger corruption)."
- Sibling folders in `Work to do` include `Problem screening/` (has `config/hpc.json` + `config/hpc.example.json`) and `Prob_screening/` (git repo, `declare/hpc.json`) — prior HPC-wired projects that do live in Dropbox.
- The Bash tool sees Dropbox paths under `/c/Users/molsim/Dropbox/Work to do/...` with spaces; CALF20's ruff config had to exclude `.claude/.planning/.gsd/.omc` explicitly.

## 9. Gaps / open questions

1. No CUDA torch anywhere; the RTX 5050 (driver CUDA 13.3) is unused by every env. A fresh env (pixi, matching CALF20) with a CUDA 12.8+/13.x torch wheel would be needed before any GPU fine-tuning.
2. GSD is present only as a per-project install in CALF20 (`@opengsd/gsd-core` v1.13.0, scope local). LLM4POL has no `.claude/` at all; whether to install GSD locally there (same npx pattern) is a synthesizer decision.
3. Whether dirac has GPU nodes is not stated in any local file; only a `cuda100/111` module on dirac1 is recorded.
4. No API keys are in the ambient environment; CALF20 uses a per-project git-ignored `.env`. Claude Code OAuth (`~/.claude/.credentials.json`) and Codex auth (`~/.codex/auth.json`) exist.
5. RAM free at audit time was only 2.3 GB of 31.7 GB — other processes were consuming memory; not a hardware limit.
