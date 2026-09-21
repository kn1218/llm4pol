# docs/research — pre-charter research outputs (2026-09-11)

These documents were produced by a multi-agent research pass before any architecture was fixed.
They are **inputs to the PROJECT FOUNDATION PROPOSAL**, not decisions. Nothing here is approved.

| File | What it is | Verification |
|---|---|---|
| `LLM4MOF-ANATOMY.md` | LLM4MOF as a method and as code, written for the port: loop, agents, beams, ledger, oracle, metrics, module map with port verdicts, stable interfaces, known weaknesses | 25 claims independently re-checked; 22 confirmed, 3 refuted |
| `LLM4MOF-ANATOMY-FACTCHECK.md` | The adversarial fact-check of the above: verdict table, 13 extra findings, module-map spot checks | — |
| `POLYMER-LANDSCAPE.md` | Polymer-computation landscape for each LLM4MOF component: simulation oracles and costs, fast oracles, design-space libraries, 2024-2026 agents, interpretability precedents, evaluation practice, PFAS | 53 reference claims re-fetched |
| `POLYMER-CITATION-CHECK.md`, `CITATION-CHECK-POLYMER-LANDSCAPE.md` | Citation verification of the landscape, plus references it missed | — |
| `BOOTSTRAP-REPORT.md`, `VERIFY-REPORT.md` | How this repository was created and the independent re-verification of it | 14 claims, 13 confirmed |

Corrections already applied by the verification lanes (do not re-derive the original numbers):

- LLM4MOF discovery design space is **12,499,656**, the connectivity-matched sum over nine
  connectivity classes, **not** the plain product 518 x 156 x 952 = 76,929,216.
- The memory ledger excludes the random beam only from `global_best` / `frontier` /
  `geometry_envelope`; it does ingest the random beam's sampled rows for `beam_medians`
  history and the outside-promising detector. Nothing from it reaches Agent 1.

Source PDFs and the extraction scripts stay in the session scratchpad and are not committed.
Related: `docs/audit/` (data audit), `docs/reference/` (pre-charter concept document).
