# Generated-document corrections

When a generated document states something false, the fix goes to the generator and the
correction is recorded here so the error is not reintroduced.

| # | Date | Document | What was wrong | Corrected value | Generator fix |
|---|---|---|---|---|---|
| 1 | 2026-09-11 | `docs/research/LLM4MOF-ANATOMY.md` | The LLM4MOF discovery design space was written as the plain product of the three library sizes | It is the connectivity-matched sum over nine connectivity classes, which is 6.2 times smaller than the plain product | Noted in `docs/research/README.md`. Never derive the space by multiplying library sizes |
| 2 | 2026-09-11 | `docs/research/LLM4MOF-ANATOMY.md` | The memory ledger was described as excluding the random beam entirely | It excludes that beam only from the best-so-far record, the frontier and the descriptor envelope. It does ingest the beam's sampled rows for per-iteration medians and the outside-promising detector. Nothing from it reaches the hypothesis agent | Noted in `docs/research/README.md` |
| 3 | 2026-09-11 | `docs/research/PORTING-MAP.md` | Framed the project as a component-by-component transplant of LLM4MOF | The owner has ruled that LLM4MOF supplies ideas and a development methodology, not an architecture to copy. The architecture is designed from the polymer problem | Superseded in framing. Retained as a study of what the parent system does and what could be reused |
