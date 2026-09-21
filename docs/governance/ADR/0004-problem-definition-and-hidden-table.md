# ADR-0004: The design problem is a thermally conductive electrical insulator; PolyOmics is the hidden table

- **Status:** Accepted
- **Date:** 2026-09-11
- **Deciders:** owner ("이 방향으로 가자"), on analysis presented by the agent
- **Relates to:** ADR-0003, `docs/research/databases/README.md`, DECISIONS-LOG D-08 to D-10

## Context

Three surveys established the polymer data landscape: simulated-property data on virtual
structures is abundant and openly licensed, first-principles data on real polymers does not
exist publicly at scale, and measured data is either contract-locked (PoLyInfo) or thin and
scattered. PolyOmics (RadonPy Consortium, CC BY 4.0) fills the role hMOF plays in LLM4MOF:
hypothetical structures with physics-simulated labels, computed by an engine that can also be
run on new candidates.

Direct analysis of PolyOmics `general_polymers` (`docs/research/databases/README.md`) showed
that thermal conductivity, dielectric constant and glass transition are jointly available on
43,561 polymers; that thermal conductivity and Tg are statistically independent (rank
correlation 0.010); that the thermal-conductivity versus permittivity trade-off is weak at the
tails (2.62% of polymers sit in the joint high-conductivity, low-permittivity corner against
2.5% under independence); and that this corner has a mechanistic signature in chain dimension,
free volume and cohesive energy density, all of which are computed in the same table as the
targets and none of which is a target.

The owner had kept four properties open (thermal conductivity, Tg, optical, dielectric). Three
of them are the specification of one industrial material: a heat-spreading, electrically
insulating, heat-resistant polymer for electronics packaging.

The chain-length layer was considered and rejected as a design axis on evidence: every
PolyOmics cell has Mw/Mn exactly 1.0, median Mn 7,491, median DP 23. These are simulation cell
settings, not material grades.

## Decision

1. The design problem is: **maximise thermal conductivity subject to low dielectric constant
   and adequate glass transition temperature**, framed as a thermally conductive electrical
   insulator. The exact objective form (constrained single objective versus Pareto) is a
   separate decision (D-16).
2. The **hidden table is PolyOmics** `general_polymers`, restricted to rows with a physical
   `dielectric_const_dc`, a thermal conductivity, and a Tg fit inside 100 to 900 K. The column
   `static_dielectric_const` is never used (it violates the Maxwell relation on 88.9% of rows).
3. **PoLyInfo is the experimental transfer-validation layer**, not a training or hidden table.
4. The **design layer is the repeat unit**, with tacticity held as a controlled variable.
   Molecular weight and dispersity are out of scope for this data.
5. The **intermediate variables** available to a design gate are chain dimension (`Rg`, `r2`),
   cohesive energy density (`sp_ced`) and fractional free volume. They are measured by the
   same simulation as the targets and are never the target.

## Alternatives considered

| Option | Why not |
|---|---|
| PoLyInfo experimental values as the hidden table | Cannot be published, so the benchmark is not reproducible; the two files in hand carry no thermal conductivity; live oracle would use a different protocol from the table |
| Tg alone as the target | Saturated literature; MD Tg carries a +40 to +120 K systematic offset; a single objective discards the industrial framing the owner asked for |
| Molecular weight or dispersity as a design axis | Not present in the data (Mw/Mn is 1.0 everywhere); would require new simulation at much higher DP, outside the compute available |
| A predicted-property database (polyOne, PolyUniverse) as the hidden table | Labels are ML extrapolations; a loop would be optimising another model's biases |

## Consequences

- The loader must select `dielectric_const_dc` and reject the broken column; a physics
  consistency check (permittivity at least the square of the refractive index) belongs in the
  validator. **Guard:** to be added with the loader.
- The sim-to-real check on the primary objective needs an experimental thermal-conductivity
  source. The PoLyInfo export in hand has none; PoLyInfo itself does hold the property, and
  OpenPoly (MIT, 741 polymers) carries it. This is decision D-17.
- Live-mode evaluation, if built, runs RadonPy's thermal-conductivity preset, at roughly
  1,500 to 3,000 CPU-hours per candidate. With a small allocation this bounds live evaluation
  to a handful of finalists (D-18).
- The PORTING-MAP's component transplant is not the architecture; the architecture is derived
  from this problem in the PROJECT FOUNDATION PROPOSAL.
