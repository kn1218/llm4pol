# ADR-0001: Repository outside Dropbox; data never committed

- **Status:** Accepted
- **Date:** 2026-09-11
- **Deciders:** agent-proposed, owner-confirmed by acceptance of the bootstrap
- **Relates to:** `data/README.md`, `tests/test_manifest.py`, ADR-0002

## Context

The source data arrived in `C:\Users\molsim\Dropbox\Work to do\LLM4POL`. Two facts bear on
where the repository lives:

- The `hpc-submit` skill's own documentation warns that Dropbox file locks are unreliable and
  can corrupt an append-only ledger. Any future HPC work in this project would write such
  files.
- The prior project CALF20_DiscoveryLoop, whose conventions this repository follows, lives on
  the Desktop, outside Dropbox.

Separately, the data is PoLyInfo-derived. The NIMS MatNavi Service Terms of Use (rev.
2024-08-01), Art. 9.2 and Art. 10(1)-(3),(5), license the data for the user's own research
only and forbid copying, derivative use, distribution and bulk acquisition. The carve-out
covers "publication of deliverables of research and development", not the data itself. This
differs from LLM4MOF, which ships `hmof_index.json` and `qmof.csv` in its public repository.

## Decision

The repository lives at `C:\Users\molsim\Desktop\LLM4POL`, outside Dropbox. The original
files stay where they are, read-only; `data/raw/` holds copies. No data file is ever
committed.

## Alternatives considered

| Option | Why not |
|---|---|
| `git init` in the Dropbox folder | Sync conflicts with `.git`; the HPC skill's documented ledger-corruption warning |
| Git LFS for the data | Still redistribution; LFS storage is a copy under the terms |
| Commit a derived, "anonymised" table | Processed DATA is explicitly covered by Art. 10(1) |

## Consequences

- Reproducibility relies on `data/MANIFEST.sha256` plus a documented placement procedure
  rather than on the repository being self-contained.
- **Guard:** `data/raw/`, `data/interim/`, `data/processed/` are git-ignored, and
  `tests/test_manifest.py` verifies the sha256 and byte size of any file that is present.
- Anyone reproducing this work needs their own PoLyInfo access. This must be stated in any
  publication's data-availability section.
