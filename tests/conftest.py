"""Shared pytest fixtures and path setup.

Inserts the repository's ``scripts/`` directory at the front of ``sys.path``
so tests can ``from history_secret_scan import ...`` -- the same module
``scripts/check.py`` runs as its ``history-secret-scan`` step. This is what
makes "the test exercises the scanner the gate runs" literally true rather
than a coincidence of two copied files.

``tests/`` has no ``__init__.py``, so this is a plain ``sys.path`` insertion,
not a dotted-package import.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def repo_root() -> Path:
    """The repository root directory."""
    return REPO_ROOT
