# Review checklist

Authoring and review are separate passes. Nothing is approved in the context that wrote it.

## Every change

- [ ] The check gate passes on the author's machine
- [ ] No data file, secret or generated cache is staged
- [ ] Every new number cites its source, or is labelled unverified
- [ ] Any invariant the change touches is guarded, or the change adds the guard

## Changes that touch the data path

- [ ] The unit of every value is stated and converted once, at the boundary
- [ ] Row counts before and after each filter are recorded
- [ ] No row-level random split; the grouping key is stated
- [ ] Deduplication happens before any metric

## Changes that touch an evaluation or a claim

- [ ] The population each count is drawn from is named
- [ ] The replicate noise floor is measured before any effect is claimed
- [ ] Controls are pre-registered, including the no-feedback floor
- [ ] The oracle's scope and known bias are stated alongside the result
- [ ] Budget is reported in both currencies, evaluation count and compute hours

## Changes that touch an interface

- [ ] An ADR exists if the interface was frozen
- [ ] Both sides of the interface are updated and tested in the same change

## Completion claims

- [ ] The milestone's measurable exit criterion was reproduced, not merely attempted
- [ ] No placeholder note, skipped test, stub or unimplemented branch remains in the change
