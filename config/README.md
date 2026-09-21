# config/

Machine-readable configuration that is committed, paired with a schema, and validated in the
test suite. Secrets never live here; they live in `.env`, which is git-ignored.

## Rules

- Every configuration file has a sibling `*.schema.json`, and the test suite validates the
  file against the schema. A configuration file with no schema is a defect.
- Values that identify a machine, an account or a queue are configuration. Values that
  identify a scientific choice are not: those belong in `protocol/` or in the charter, where
  they are reviewed as decisions.
- No configuration file contains a credential, a token, a password or a private host key.

## Expected contents, once the relevant milestones exist

| File | Purpose | Blocked on |
|---|---|---|
| `hpc.json` plus `hpc.schema.json` | Cluster, queue, gateway and path settings for the `hpc-submit` skill, which requires this file and `scripts/submit.py` and will refuse to run without them | A decision that this project submits jobs at all. The owner has recorded that the allocation is small and that simulation is a spot check, not an in-loop oracle (ADR-0003, D-06) |
| A provider configuration | Which language-model backends are available and how they are addressed | The provider and budget decision, D-14, which is open. No API key is set on this machine |

## Current contents

Empty apart from this file. Nothing here is guessed ahead of a decision.
