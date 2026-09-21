"""Evaluator backends (charter section 6 row ``evaluate``; CONTEXT D-05).

Each backend implements ``llm4pol.evaluate.contract.Backend``. ``table``
answers from the candidate parquet of the pinned snapshot (M2). The RadonPy
backend named by the A-2 import-linter contract is built at M9 and does not
exist here (a stub is a blocker, CLAUDE.md). This package is never imported
by ``llm4pol.evaluate.__init__`` (RESEARCH F-49).
"""
