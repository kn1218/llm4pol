# experiments/

Run outputs. **Git-ignored except for this file.** Nothing in here is a source artifact and
nothing in here is a result until it has been reduced into `docs/` or a figure script.

## Why it is ignored

Two reasons, and both are binding:

1. Run directories contain feedback payloads and candidate tables derived from PoLyInfo data.
   Committing them would be redistribution of Processed DATA under the MatNavi terms
   (ADR-0001).
2. They are large, numerous and rewritten constantly. Version control is the wrong tool for
   them.

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
