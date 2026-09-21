# Deferred items — Phase 1 (01-foundation)

Out-of-scope discoveries logged during execution, not fixed (scope boundary).

## From 01-01

- **Untracked GSD runtime artifacts in the working tree.** `.gsd/dispatch-isolation-sentinel.json`
  and `.planning/state.json` were already untracked before plan 01-01 started (they are written
  by the GSD orchestrator, not by the plan). They make `git status --porcelain --branch` print two
  `??` lines beyond `## main...origin/main`. D-03 forbids editing `.gitignore` in this phase, so
  they were left alone. Decide at the next planning step whether to ignore them (`.gitignore`
  change with owner sign-off) or commit `.planning/state.json` as GSD state.
- **Plan grounding counts drifted.** The plan expected 8 pre-existing commits (`scanned 9` after
  RED, `scanned 12` before push); two commits landed between planning and execution
  (`9347f1e`, `4ec32b6`), so the actual lines are `scanned 11`, `scanned 12` and `scanned 14`.
  No action needed; recorded so the verifier does not read the delta as a shallow-clone symptom.
