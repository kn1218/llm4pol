"""The candidate definition (charter section 6, CONTEXT D-03): pure functions, no I/O.

``candidate_id = sha256(canonical_psmiles + "|" + tacticity)[:16]`` where
``canonical_psmiles`` is the RDKit canonical SMILES of the repeat unit with
its two ``*`` polymerisation points kept and stereo retained (D-6), and a
missing tacticity is the literal ``"unknown"`` so the id is total.
"""

from __future__ import annotations

import hashlib
import math

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
