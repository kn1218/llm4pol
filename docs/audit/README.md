# docs/audit/ -- data-foundation audit (2026-09-11)

## What this is

Verified outputs of the LLM4POL data-foundation audit run on 2026-09-11, before any charter
existed. The audit examined the two PoLyInfo-derived files in hand (`polymer_final_0824.csv`,
42,557 rows; `230227_Homopolymer_CanonicalSMILES.xlsx`, 13,725 rows) and the corrupt
`copolymer.zip`, the machine environment, the prior project's conventions
(CALF20_DiscoveryLoop), prior art, and the PoLyInfo licensing terms. Every numeric claim in
these files was produced by a script and, where a refutation lane was run, independently
re-derived; numbers that did not reproduce are listed in `DATA-FOUNDATION-REPORT.md`
section 1.11.

## Files

| file | content |
|---|---|
| `DATA-FOUNDATION-REPORT.md` | consolidated report: verified facts, severity-ranked defects, proposed domain model (a proposal, not a fact), candidate validator invariants, environment and conventions, prior art and licensing, candidate framings, open questions |
| `copolymer-csv.md` | CSV audit lane |
| `refute_csv/copolymer-csv-refutation.md` | independent refutation of the CSV lane |
| `homopolymer-xlsx.md` | XLSX audit lane |
| `homopolymer-xlsx-refutation.md` | independent refutation of the XLSX lane |
| `cross-linkage.md` | CSV-to-XLSX linkage lane |
| `refute-cross-linkage.md` | independent refutation of the linkage lane |
| `environment.md`, `environment-verification.md` | machine, tooling and prior-project facts, and their verification |
| `prior-art.md`, `citation-check.md` | literature map and citation verification |

## Provenance

- Produced in a Claude Code session on 2026-09-11 (session scratchpad
  `.../a0b03baf-5561-4462-b33d-bae34ea6a4be/scratchpad/audit/`).
- Only the Markdown outputs are copied here. The audit scripts (`r*.py`, `s*.py`,
  `refute_csv/r_*.py`, `refute_xlink/*.py`), their captured outputs (`out_*.txt`), pickled
  intermediates (`*.pkl`), extracted CSV side-tables and the downloaded reference PDFs remain
  in the session scratchpad and are **not** part of this repository. The pickles and CSV
  side-tables contain PoLyInfo-derived rows and must not be committed (see `data/README.md`).
- These documents are inputs to the charter (`docs/MASTER-PLAN.md`, to be written). They
  describe what the data is; they do not decide what the project does.
