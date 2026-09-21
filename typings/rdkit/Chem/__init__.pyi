# Minimal rdkit.Chem stub.
#
# Why it exists: rdkit 2026.03.6 ships a bundled `rdkit-stubs` package whose
# `Chem/rdchem.pyi` line 360 (`GetProp(self, key, autoConvert=False, default)`)
# is a syntax error that mypy 2.3.1 treats as blocking; `follow_imports = "skip"`
# and `ignore_errors = true` on `rdkit.*` do not suppress it. A package on
# `mypy_path` (pyproject.toml: `mypy_path = ["src", "typings"]`) is searched
# before installed stub packages, so this stub shadows the broken one.
#
# It declares only what `llm4pol.data.identity` calls. Widen it when a new
# call site appears; never copy the bundled stub.

class Mol: ...

def MolFromSmiles(smiles: str, sanitize: bool = ...) -> Mol | None: ...
def MolToSmiles(mol: Mol, isomericSmiles: bool = ..., canonical: bool = ...) -> str: ...
