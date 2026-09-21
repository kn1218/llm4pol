# experiments/

Run outputs. **Git-ignored except for this file.** Nothing in here is a source artifact and
nothing in here is a result until it has been reduced into `docs/` or a figure script.

## Why it is ignored

1. Run outputs are untracked by policy. They are large, numerous and rewritten constantly, and
   the charter (`docs/MASTER-PLAN.md` §10) keeps the run directory out of version control for
   every layer.
2. For the PolyOmics layer this is policy only: PolyOmics is CC BY 4.0, so a run directory
   derived from it carries no redistribution problem (charter §10).
3. Once M8 adds the PoLyInfo-derived experimental table (charter §13 M8), feedback payloads and
   candidate tables inside a run directory become PoLyInfo-derived content and may not be
   committed under the MatNavi terms (ADR-0001). The policy does not change at that point; only
   the second reason arrives.

## Expected layout, once runs exist

```
experiments/<run-id>/
  meta.json           what was run: inputs, versions, prompt versions, seed, provider, model
  <per-iteration>/    the artifacts that iteration produced
  usage.json          token and cost accounting
  results.csv         the reduced table that figures are built from
```

## Rules

- A run directory is append-only. A rerun gets a new identifier; it never overwrites.
- `meta.json` records the exact prompt version from `protocol/prompts/` and the exact
  configuration used, so a result can be traced to what produced it.
- Anything a figure or a claim depends on is reduced into a small committed file and cited
  from the document that uses it. The run directory itself is not a citable artifact, because
  it is not shared.
