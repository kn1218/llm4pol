# data/

## Policy

The project's data is derived from PoLyInfo (NIMS MatNavi). The MatNavi terms of use forbid
redistribution of the data, so **no data file is ever committed to this repository**, in any
form (raw, intermediate, processed, pickled, or embedded in a test fixture). The directories
`data/raw/`, `data/interim/` and `data/processed/` are git-ignored; only this README and
`MANIFEST.sha256` are tracked.

Derived artifacts that could reconstruct the data (row-level exports, per-record SMILES tables,
property tables) fall under the same rule. Aggregate statistics quoted in `docs/audit/` are
fine; rows are not.

## Expected raw files

`MANIFEST.sha256` lists each expected raw file as `<sha256>  <size_bytes>  <original filename>`:

| file | role | note |
|---|---|---|
| `polymer_final_0824.csv` | 42,557-row copolymer export | see `docs/audit/copolymer-csv.md` |
| `230227_Homopolymer_CanonicalSMILES.xlsx` | 13,725-row homopolymer export | see `docs/audit/homopolymer-xlsx.md` |
| `copolymer.zip` | 15 member CSVs | **known-corrupt**: valid zip, every member is NUL bytes (audit defect D16); listed only to fix its identity |

## How to place the files

1. Obtain the files from the owner (the working copies live outside this repository, in the
   owner's Dropbox folder `Work to do/LLM4POL`). Copy, never move.
2. Put them, with their original filenames, in `data/raw/`.
3. Verify:

   ```
   pixi run --manifest-path env/pixi.toml check
   ```

   `tests/test_manifest.py::test_raw_files_match_manifest` compares byte size and sha256 of
   every manifest entry that is present in `data/raw/`. Files that are absent make the test
   skip with a stated reason; a present file that does not match fails the gate.

   Manual check without the gate:

   ```
   cd data/raw && sha256sum polymer_final_0824.csv 230227_Homopolymer_CanonicalSMILES.xlsx copolymer.zip
   ```

## Adding a new raw file

Append one line to `MANIFEST.sha256` (sha256, byte size, original filename) in the same commit
that documents where the file came from and under which terms. Do not commit the file.
