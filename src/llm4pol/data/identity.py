"""The candidate definition (charter section 6, CONTEXT D-03): pure functions, no I/O.

``candidate_id = sha256(canonical_psmiles + "|" + tacticity)[:16]`` where
``canonical_psmiles`` is the RDKit canonical SMILES of the repeat unit with
its two ``*`` polymerisation points kept and stereo retained (D-6), and a
missing tacticity is the literal ``"unknown"`` so the id is total.

``observed_labels`` and ``resolve_tacticity`` are the rule ADR-0006 decided:
an empty tacticity is to take the label of its twin when the same canonical
repeat unit carries exactly one non-empty label elsewhere in the snapshot. The
rule needs the whole table, so it will be applied over the in-scope frame by
``load.add_identity`` before the hash; as of this commit nothing calls it. The
identity formula and the spelling of a missing value are unchanged either way.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

from rdkit import Chem, RDLogger

# 0 parse failures on the pinned file (F-32); keep the log quiet for the
# synthetic bad inputs of the test fixture.
RDLogger.DisableLog("rdApp.*")

UNKNOWN_TACTICITY = "unknown"


def normalise_tacticity(value: object) -> str:
    """Map ``None``, float NaN and the empty string to ``"unknown"``; else ``str(value)``."""
    if value is None:
        return UNKNOWN_TACTICITY
    if isinstance(value, float) and math.isnan(value):
        return UNKNOWN_TACTICITY
    text = str(value)
    return text if text else UNKNOWN_TACTICITY


def canonical_psmiles(smiles: str) -> str | None:
    """RDKit canonical, isomeric SMILES of ``smiles``; ``None`` when it does not parse.

    The empty string is not a repeat unit (RDKit parses it as an empty
    molecule); a comma-joined list such as the cellulose rows' ``smiles_list``
    (F-32) fails to parse and is ``None`` like any other bad input.
    """
    if not smiles:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    canonical = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
    return canonical or None


def candidate_id(canonical: str, tacticity: object) -> str:
    """The frozen candidate id: first 16 hex of sha256 over ``canonical|tacticity``."""
    key = f"{canonical}|{normalise_tacticity(tacticity)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def observed_labels(
    canonical: Sequence[str], tacticity: Sequence[str]
) -> dict[str, frozenset[str]]:
    """Map each canonical repeat unit to the frozenset of non-empty labels it carries.

    ``UNKNOWN_TACTICITY`` is never a member: it spells the absence of a label,
    so it is not evidence of one (ADR-0006). Every key of ``canonical`` is
    present, with an empty frozenset when it was never labelled.
    """
    seen: dict[str, set[str]] = {}
    for key, label in zip(canonical, tacticity, strict=True):
        bucket = seen.setdefault(key, set())
        if label != UNKNOWN_TACTICITY:
            bucket.add(label)
    return {key: frozenset(labels) for key, labels in seen.items()}


def resolve_tacticity(canonical: Sequence[str], tacticity: Sequence[str]) -> list[str]:
    """Resolve each ``UNKNOWN_TACTICITY`` from its labelled twin (ADR-0006, D-25).

    An entry spelled ``unknown`` takes the single member of its canonical's
    observed label set when that set has exactly one member; every other entry
    is returned unchanged, so a repeat unit with no labelled twin -- or with
    more than one distinct one -- keeps ``unknown``. The rule is a lookup
    inside one snapshot, never an inference: no entry can leave with a label
    its own canonical was not observed to carry (D-11). Order-preserving and
    total, so the result stays positionally aligned with ``canonical``.
    """
    seen = observed_labels(canonical, tacticity)
    resolved: list[str] = []
    for key, label in zip(canonical, tacticity, strict=True):
        labels = seen[key]
        resolved.append(
            next(iter(labels)) if label == UNKNOWN_TACTICITY and len(labels) == 1 else label
        )
    return resolved
