"""The candidate identity rule (charter section 6, CONTEXT D-03, D-6; DATA-04) pinned by vectors.

Every vector comes from RESEARCH F-32..F-35 (RDKit 2026.03 on the pinned
file) or from the synthetic fixture; none is copied from the data. The id is
``sha256(canonical_psmiles + "|" + tacticity)[:16]`` with a missing tacticity
spelled ``unknown`` so the id is total.
"""

from __future__ import annotations

import hashlib
import re

from conftest import SYNTHETIC_ROWS
from llm4pol.data import identity
from llm4pol.data.identity import (
    UNKNOWN_TACTICITY,
    candidate_id,
    canonical_psmiles,
    normalise_tacticity,
)

ID_PATTERN = re.compile(r"^[0-9a-f]{16}$")


def test_canonical_psmiles_merges_equivalent_raw_strings() -> None:
    merged = canonical_psmiles("*C(C*)(C)C(=O)OC")
    assert merged == canonical_psmiles("*C(C*)(C(=O)OC)C") == "*CC(*)(C)C(=O)OC"
    assert canonical_psmiles("*/C(=C/CC*)C") == "*CC/C=C(/*)C"
    assert canonical_psmiles("C(C*)(*)c1ccccc1") == "*CC(*)c1ccccc1"
    assert canonical_psmiles("*OC*") == "*CO*"


def test_canonical_psmiles_keeps_stereo_and_both_polymerisation_points() -> None:
    clockwise = canonical_psmiles("*C[C@H](*)C")
    assert clockwise is not None
    assert "@" in clockwise
    assert clockwise.count("*") == 2
    anticlockwise = canonical_psmiles("*C[C@@H](*)C")
    assert anticlockwise is not None
    assert anticlockwise != clockwise
    double_bond = canonical_psmiles("*/C(=C/CC*)C")
    assert double_bond is not None
    assert "/" in double_bond


def test_canonical_psmiles_returns_none_for_unparseable_and_comma_joined_lists() -> None:
    assert canonical_psmiles("*C(") is None
    assert canonical_psmiles("*CC*,*OC*") is None
    assert canonical_psmiles("") is None


def test_canonical_psmiles_is_idempotent() -> None:
    parseable = [
        canonical
        for canonical in (canonical_psmiles(str(row["smiles_list"])) for row in SYNTHETIC_ROWS)
        if canonical is not None
    ]
    assert len(parseable) == 12
    for canonical in parseable:
        assert canonical_psmiles(canonical) == canonical


def test_candidate_id_is_the_first_16_hex_of_sha256_canonical_pipe_tacticity() -> None:
    expected = hashlib.sha256(b"*CC*|unknown").hexdigest()[:16]
    assert candidate_id("*CC*", "unknown") == expected == "d220c5c57c4fae2e"
    assert ID_PATTERN.match(candidate_id("*CC*", "unknown"))


def test_candidate_id_maps_missing_tacticity_to_unknown() -> None:
    known = candidate_id("*CC*", "unknown")
    assert candidate_id("*CC*", None) == known
    assert candidate_id("*CC*", float("nan")) == known
    assert candidate_id("*CC*", "") == known
    assert normalise_tacticity("atactic") == "atactic"
    assert UNKNOWN_TACTICITY == "unknown"


def test_candidate_id_differs_across_tacticity_and_canonical() -> None:
    ids = {
        candidate_id("*CC*", "none"),
        candidate_id("*CC*", "atactic"),
        candidate_id("*CC(*)C", "none"),
    }
    assert len(ids) == 3
    assert all(ID_PATTERN.match(value) for value in ids)


# --- Plan 02-06: the ADR-0006 resolution rule (D-25, DATA-04) --------------
#
# `resolve_tacticity` is reached through the `identity` module object rather
# than imported by name: during this plan's RED commit the two helpers do not
# exist yet, and a `from ... import resolve_tacticity` at module level would
# turn that RED into a collection error that also fails the seven vectors
# above, which must stay green throughout (plan 02-06 Task 1 verify 3).
# Every string below is an invented repeat unit; none is read from the file.


def test_resolve_tacticity_takes_the_label_of_a_single_twin() -> None:
    """One labelled twin: the unknown entry takes that label, the rest are unchanged."""
    canonical = ["*CC*", "*CC*", "*CC*"]
    tacticity = ["atactic", UNKNOWN_TACTICITY, "atactic"]
    assert identity.resolve_tacticity(canonical, tacticity) == [
        "atactic",
        "atactic",
        "atactic",
    ]


def test_resolve_tacticity_keeps_unknown_without_a_twin() -> None:
    """No labelled twin anywhere for that canonical: every entry stays unknown."""
    canonical = ["*CC(*)C", "*CC(*)C"]
    tacticity = [UNKNOWN_TACTICITY, UNKNOWN_TACTICITY]
    assert identity.resolve_tacticity(canonical, tacticity) == [
        UNKNOWN_TACTICITY,
        UNKNOWN_TACTICITY,
    ]


def test_resolve_tacticity_keeps_unknown_when_two_labels_are_observed() -> None:
    """Two distinct labelled twins: the rule's own guard leaves the empty value unknown."""
    canonical = ["*CC(*)F", "*CC(*)F", "*CC(*)F"]
    tacticity = ["none", "atactic", UNKNOWN_TACTICITY]
    assert identity.resolve_tacticity(canonical, tacticity) == [
        "none",
        "atactic",
        UNKNOWN_TACTICITY,
    ]


def test_resolve_tacticity_is_order_preserving_and_total() -> None:
    """Same length, same order; every output is the input or a label that canonical carries."""
    canonical = ["*CC*", "*CC(*)C", "*CC*", "*CC(*)F", "*CC(*)C", "*CC(*)F"]
    tacticity = [
        UNKNOWN_TACTICITY,
        "none",
        "none",
        UNKNOWN_TACTICITY,
        UNKNOWN_TACTICITY,
        "atactic",
    ]
    resolved = identity.resolve_tacticity(canonical, tacticity)
    assert len(resolved) == len(canonical)
    assert resolved == ["none", "none", "none", "atactic", "none", "atactic"]
    seen = identity.observed_labels(canonical, tacticity)
    for canon, before, after in zip(canonical, tacticity, resolved, strict=True):
        assert after == before or after in seen[canon]


def test_observed_labels_maps_each_canonical_to_its_non_empty_labels() -> None:
    """The label map holds frozensets of real labels only; unknown is never a member."""
    canonical = ["*CC*", "*CC*", "*CC(*)C", "*CC(*)F"]
    tacticity = ["none", "atactic", UNKNOWN_TACTICITY, "isotactic"]
    seen = identity.observed_labels(canonical, tacticity)
    assert seen["*CC*"] == frozenset({"none", "atactic"})
    assert seen["*CC(*)C"] == frozenset()
    assert seen["*CC(*)F"] == frozenset({"isotactic"})
    assert all(UNKNOWN_TACTICITY not in labels for labels in seen.values())
