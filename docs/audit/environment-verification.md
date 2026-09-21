# Environment claims — independent verification (E01–E20)

Verifier run: 2026-09-11 15:02–15:08 KST. Target file: `audit/environment.md` (mtime 15:00:10).
Every number below was re-computed in this session; nothing copied from the audited file.

## Summary

| id | status | one-line note |
|----|--------|---------------|
| E01 | confirmed | Python 3.13.9 at C:\Users\molsim\anaconda3\python.exe; all 12 listed versions match; all 13 listed packages ABSENT |
| E02 | confirmed | 5 conda envs; llm2auto torch 2.2.0+cpu / transformers 5.5.0; pacman torch 2.13.0; both cuda False / None; mofviz & pacmof no torch |
| E03 | confirmed | RTX 5050 8151 MiB, driver 610.74, CUDA UMD 13.3; i5-14600K 14/20; RAM 33265072 KB = 31.7 GB; C: 930.6 GiB total. Free values drift (2.8 GB RAM, 400.3 GiB disk now) |
| E04 | confirmed | conda 26.1.1, pixi 0.80.0 at C:/Users/molsim/.pixi/bin/pixi, git 2.53.0.windows.2, gh 2.96.0 (kn1218, 5 scopes), node v24.14.0, npm 11.9.0, bun 1.3.10; uv/mise/poetry/hatch/pnpm/docker absent; WSL not installed |
| E05 | confirmed | exactly 5 global npm packages with the stated versions |
| E06 | confirmed | ProductVersion 1.4.167.0, CompanyName stablyai; asar package.json description/homepage match; 2487 asar entries, 0 README |
| E07 | confirmed | ~/.claude/commands and agents do not exist; 0 gsd-named files; 3 plugins as stated; gsd not on PATH. Note: text mentions of /gsd-* exist only in 2 session-memory .md files under ~/.claude/projects |
| E08 | confirmed | manifest 1.13.0 / full / claude / local / 2026-09-10T06:36:45.919Z; 72 gsd commands, 35 gsd agents, 28 gsd hooks (of 31); gsd-core and .planning exist |
| E09 | confirmed | package-identity.cjs line 6 packageName "@opengsd/gsd-core", line 16 npx -y --package=…; 2+2 npx string hits; settings.local.json line 196 Bash(npx gsd-core *) |
| E10 | confirmed | skills/ holds hpc-submit (+ 'learned'); transport.py 445 lines stdlib-only; 0 gpu/cuda hits in SKILL.md, transport.py, hpc.example.json; HPC-ENV.md at .planning/research/ line 21 lists cuda100/111 on dirac1 |
| E11 | confirmed | all 7 vars unset in process; User-scope match only PLAYWRIGHT_MCP_EXTENSION_TOKEN, Machine none; ~/.anthropic missing, credentials.json & codex auth.json present; .env (git-ignored) names match |
| E12 | confirmed | pixi.toml name/channels/platforms/features/python 3.13.*; env/pixi.lock tracked; ci.yml matrix + setup-pixi@v0.10.2 + v0.80.0 + check task |
| E13 | confirmed | 119 lines; all greps match; 3 forbidden contracts; calfcheck table present |
| E14 | confirmed | 3 scripts with matching docstrings; 6 test_*.py; tests/purity and tests/golden exist |
| E15 | confirmed | MASTER-PLAN 1548 lines / 169909 bytes; 28 docs files, 20 ADRs, 7-section MADR; no top-level README. Drift: an UNTRACKED config/README.md appeared at 15:02 today (after audit) |
| E16 | confirmed | CLAUDE.md 114 lines with precedence, two planes, 'GSD workflow only'; settings.local.json enabledPlugins omc false, env DISABLE_OMC=1 (line 207) |
| E17 | refuted | REQUIREMENTS.md:109 HPC-01 and ADR-0007 text match, BUT config/ NOW EXISTS (untracked; hpc.json, hpc.schema.json, README.md, transport-pin.json created 15:01:36–15:02:22 today, i.e. after environment.md was written at 15:00:10; hpc.json has job_prefix "calf20", remote_base "~/calf20-loop/"). Stale, not wrong-at-the-time |
| E18 | confirmed | 55 commits, main -> origin/main kn1218/calf20-discovery-loop.git; quoted commit subjects present in order; config.json none/true/yolo/end-of-phase |
| E19 | confirmed | 1 .git under Desktop depth<=2; LLM4POL not a repo, contents .omc + 3 files; 4 .git under 'Work to do' depth 3, 8 under Dropbox depth 3; SKILL.md line 91 Dropbox warning |
| E20 | refuted | installed_plugins.json and cache contents match exactly, hooks 10 / allows 42 / env empty match, BUT settings.json `model` is "opus", not "fable" (file mtime 14:59:38 today; settings.json.bak from 2026-08-03 also says opus) |

## Raw evidence (selected)

- E01: `python` -> C:\Users\molsim\anaconda3\python.exe, 3.13.9; pandas 2.3.3 numpy 2.3.5 scipy 1.16.3 scikit-learn 1.7.2 rdkit 2025.9.6 pyarrow 21.0.0 pydantic 2.12.4 pytest 8.4.2 ruff 0.12.0 mypy 1.17.1 openpyxl 3.1.5 jupyter 1.1.1; torch/transformers/peft/accelerate/lightgbm/xgboost/polars/duckdb/hydra-core/omegaconf/mlflow/wandb/dvc -> PackageNotFoundError.
- E02: llm2auto 3.11.14 torch 2.2.0+cpu transformers 5.5.0 cuda False None; mofviz 3.11.15 no torch; pacman 3.10.20 torch 2.13.0 cuda False None; pacmof 3.10.20 no torch.
- E03: `NVIDIA GeForce RTX 5050, 8151 MiB, 610.74`; header `CUDA UMD Version: 13.3`; TotalVisibleMemorySize 33265072 KB; FreePhysicalMemory 2968364 KB; C: Size 999204843520 FreeSpace 429859598336.
- E05: @anthropic-ai/claude-code@2.1.268, @marp-team/marp-cli@4.3.1, @openai/codex@0.154.0, oh-my-claude-sisyphus@4.15.6, opencode-ai@1.2.25.
- E06: asar bytes contain `"name": "orca", "version": "1.4.167", "description": "Next-gen IDE for parallel agentic development", "homepage": "https://github.com/stablyai/orca", "author": "stablyai"`; app-update.yml owner stablyai repo orca.
- E17: `git -C CALF20 status --short` shows `?? config/` (plus `?? .gsd/`, `?? src/calfloop/hpc/`, `?? .planning/milestone.lock`) — a concurrent CALF20 session is actively creating the HPC wiring right now.
- E20: `grep -n '"model"' ~/.claude/settings.json` -> `48:  "model": "opus",`.

## Extra findings
1. CALF20 working tree is being modified concurrently (untracked config/, src/calfloop/hpc/, .gsd/); any environment claim about CALF20 file presence can go stale within minutes.
2. conda env list prints `llm2auto` twice (duplicate entry in the env registry) — 5 distinct envs, 6 lines.
3. ~/.claude/skills also contains a `learned` entry besides hpc-submit (E10 says hpc-submit is the only skill; `learned` is a directory, contents not audited here).
4. Global npm package is `oh-my-claude-sisyphus` (4.15.6), while the plugin is `oh-my-claudecode@omc` 4.15.6 — both present, same version.
