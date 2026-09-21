# Invariants

Rules that must hold. Each one names its **guard**: the test, schema or CI check that enforces
it. An invariant with guard "prose" is not yet enforced and is a candidate for promotion.

The data invariants below are derived from `docs/audit/DATA-FOUNDATION-REPORT.md` section 4.
They are architecture-neutral: they constrain the data, not the design. Architecture
invariants A-1..A-7 are declared in `docs/MASTER-PLAN.md` §4 with the milestone that adds
each guard; they are prose until that milestone. D-1..D-6 apply to the PoLyInfo loader
(first written at M8); D-7..D-10 apply to every table, PolyOmics included (guard at M1).

## Repository and process

| ID | Invariant | Guard |
|---|---|---|
| R-1 | No PoLyInfo-derived data file is ever committed | `.gitignore` plus `tests/test_manifest.py` |
| R-2 | Any file present in `data/raw/` matches `data/MANIFEST.sha256` in sha256 and byte size | `tests/test_manifest.py` |
| R-3 | No secret value is printed, logged or committed | `.gitignore`; a history secret scan is deferred until there is history |
| R-4 | The check gate passes before any commit | `scripts/check.py`, CI on two platforms |
| R-5 | `src/llm4pol/` contains production code only while `docs/MASTER-PLAN.md` declares `Status: Approved` (ADR-0005) | `tests/test_governance.py::test_charter_status_gates_production_code` |

## Data — enforced by the loader and validator once they exist

| ID | Invariant | Guard |
|---|---|---|
| D-1 | The copolymer CSV is read as UTF-8 with replacement, never as cp949. A cp949 read silently alters 16 cells in 15 rows | prose |
| D-2 | `composition_i` is bound to `component_i`, never to `smiles_i`. Position-based pairing is wrong for about 30 percent of resolvable rows and inverts the sign of the composition effect | prose |
| D-3 | Rows whose component-to-SMILES binding is undetermined are excluded, not guessed | prose |
| D-4 | Temperatures are stored in one unit throughout. The XLSX is Kelvin, the CSV is degrees Celsius | prose |
| D-5 | Electrical values are parsed by stripping the glued unit with an anchored expression, never by a greedy number match | prose |
| D-6 | Structural identity uses a stereo-aware key that does not merge topologically different polymers. The naive ring-closing key produces false merges | prose |
| D-7 | Rows that differ only in `sample_id` are deduplicated before any split or metric | prose |
| D-8 | Splits are grouped by polymer identity, never random at row level. Replicates would otherwise leak | prose |
| D-9 | A reported effect smaller than the measured replicate noise floor is not reported as an effect | prose |
| D-10 | Every reported count states the population it is drawn from. Matched-set sizes are recorded alongside every aggregate | prose |

## Promotion policy

An invariant is promoted from prose to a guard as soon as the code it constrains exists. A
change that adds code touching an unguarded invariant adds the guard in the same change.
