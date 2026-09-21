"""Locked-environment proof for FOUND-02 (charter §13 M0, D-02).

FOUND-02 says ``huggingface_hub`` is available in the locked environment on
both CI platforms. The proof is an import from that environment inside the
check gate -- not a grep of the lock file -- because an import is what makes
"available on both platforms" observable in the CI matrix. A missing package
fails at collection, which is the intended failure mode.
"""

from __future__ import annotations

import re

import huggingface_hub

MIN_MAJOR_MINOR = (1, 32)
MAX_MAJOR_EXCLUSIVE = 2
LEADING_MAJOR_MINOR = re.compile(r"^(\d+)\.(\d+)")


def test_huggingface_hub_importable() -> None:
    version = huggingface_hub.__version__
    match = LEADING_MAJOR_MINOR.match(version)
    assert match, f"huggingface_hub.__version__ {version!r} does not start with MAJOR.MINOR"
    major_minor = (int(match.group(1)), int(match.group(2)))
    assert major_minor >= MIN_MAJOR_MINOR, f"huggingface_hub {version} is older than 1.32"
    assert major_minor[0] < MAX_MAJOR_EXCLUSIVE, f"huggingface_hub {version} is 2.x or later"
