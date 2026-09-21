"""History secret scan: the guard for invariant R-3 (FOUND-03, D-01).

A push publishes every commit reachable from ``git rev-list --all``, not only
the files in the working tree. ``git ls-files`` or a working-tree grep would
miss a secret that was added and later deleted; this script walks reachable
*history* instead. It runs as the ``history-secret-scan`` step of
``scripts/check.py`` (locally and in CI on both platforms), so a secret-shaped
token anywhere in history turns the single gate red.

Two modes:

``--self-test``
    Builds a synthetic positive control for each pattern class and asserts
    every pattern matches its own control, then exits 0. This is what stops
    a mistyped regex from producing a green scan that never actually fires.

(default)
    Refuses a shallow clone (a one-commit history would scan green
    vacuously), walks every commit reachable from ``git rev-list --all``,
    matches each commit's patch text against the pattern set, and separately
    asserts that no path matching the withheld dotenv file name (or that
    name plus any suffix other than ``.example``) appears anywhere in
    ``git log --all --name-only``. Prints a per-pattern hit count and, for
    any hit, the pattern name, commit sha and path. Exits non-zero on any hit.

Every pattern prefix, the dotenv name and every synthetic positive-control
sample used by ``--self-test`` is assembled from string fragments at runtime.
No fragment sequence below is written as a single contiguous literal that
would itself match the pattern it helps define, so this script's own
committed source text cannot trip its own scan: a contiguous match only
exists in memory, after the fragments are joined, never in the file's raw
bytes.

Never prints a value: only pattern names, commit shas and paths. Does not
read the dotenv file.

Exit codes: 0 clean, 1 at least one hit, 2 shallow-clone refusal.

Design ported from CALF20_DiscoveryLoop/scripts/history_secret_scan.py (same owner).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _join(*fragments: str) -> str:
    """Concatenate fragments at runtime; the joined literal is never stored."""
    return "".join(fragments)


# --- Pattern fragments ------------------------------------------------------
# Every secret-shape prefix below is built from two or more fragments so no
# contiguous substring of this file's own source text matches the pattern it
# defines.

_OPENAI_PREFIX = _join("s", "k", "-")
_ANTHROPIC_PREFIX = _join(_OPENAI_PREFIX, "ant", "-")
_GOOGLE_PREFIX = _join("AI", "za")
_HF_PREFIX = _join("h", "f", "_")

_GH_LETTERS = ("p", "o", "u", "s", "r")
_GH_PREFIXES = tuple(_join("gh", letter, "_") for letter in _GH_LETTERS)
_GH_FINEGRAINED_PREFIX = _join("github", "_pat_")

_AWS_PREFIXES = (_join("AK", "IA"), _join("AS", "IA"))

_SLACK_LETTERS = ("b", "a", "p", "r", "s")
_SLACK_PREFIXES = tuple(_join("xox", letter, "-") for letter in _SLACK_LETTERS)

_DASH5 = "-" * 5
_PEM_KEY_TYPES = (
    _join("OPENSSH", " PRIVATE KEY"),
    _join("RSA", " PRIVATE KEY"),
    _join("EC", " PRIVATE KEY"),
    _join("DSA", " PRIVATE KEY"),
    _join("PGP", " PRIVATE KEY BLOCK"),
    _join("PRIVATE", " KEY"),
)
_PEM_HEADERS = tuple(_join(_DASH5, "BEGIN ", kind, _DASH5) for kind in _PEM_KEY_TYPES)

_CRED_WORDS = ("KEY", "SECRET", "TOKEN", "PASSWORD", "PASSWD", "CREDENTIAL", "APIKEY")

_DOTENV_NAME = _join(".", "env")
_DOTENV_ALLOWED = _join(_DOTENV_NAME, ".", "example")

# A word boundary before a bare prefix: without it, an ordinary hyphenated
# word like "task-content" contains the substring "sk-" and would
# false-positive as an OpenAI-shaped key.
_KEY_PREFIX_BOUNDARY = r"(?<![A-Za-z0-9_])"


@dataclass(frozen=True)
class PatternClass:
    """One secret-shape pattern plus a synthetic string it must match."""

    name: str
    regex: re.Pattern[str]
    positive_control: str
    # Optional post-match filter (applied in addition to the regex) for
    # pattern classes whose regex alone is too coarse -- e.g. the generic
    # assignment shape, which would otherwise flag ordinary config-key
    # constants such as `GIT_CONFIG_KEY_0: 'diff.ignoreSubmodules'`.
    extra_validate: Callable[[re.Match[str]], bool] | None = None


def _generic_value_is_secret_shaped(match: re.Match[str]) -> bool:
    """Filter for ``generic_credential_assignment``: reject config-key noise.

    Real high-entropy secrets mix letters and digits and are not dotted
    paths; ordinary source-level constants (config keys, enum values,
    identifier mirrors) are either dotted (``diff.ignoreSubmodules``) or
    purely alphabetic/underscored (``config_key_not_found``) and contain no
    digit at all.
    """
    value = match.group(1)
    if "." in value:
        return False
    return any(char.isdigit() for char in value)


def _matches(pattern: PatternClass, text: str) -> Iterator[re.Match[str]]:
    for match in pattern.regex.finditer(text):
        if pattern.extra_validate is None or pattern.extra_validate(match):
            yield match


def _alternation(prefixes: Iterable[str]) -> str:
    return _join("(?:", "|".join(re.escape(prefix) for prefix in prefixes), ")")


def _build_patterns() -> list[PatternClass]:
    """The ten pattern classes, in declared order (D-01 mandatory set first)."""
    long_body = _join("A1b2C3d4", "E5f6G7h8", "I9j0K1l2", "M3n4")
    return [
        PatternClass(
            "openai_secret_key",
            re.compile(
                _KEY_PREFIX_BOUNDARY + re.escape(_OPENAI_PREFIX) + r"(?!ant-)[A-Za-z0-9_-]{20,}"
            ),
            _join(_OPENAI_PREFIX, long_body),
        ),
        PatternClass(
            "anthropic_secret_key",
            re.compile(_KEY_PREFIX_BOUNDARY + re.escape(_ANTHROPIC_PREFIX) + r"[A-Za-z0-9_-]{20,}"),
            _join(_ANTHROPIC_PREFIX, long_body),
        ),
        PatternClass(
            "google_ai_api_key",
            re.compile(_KEY_PREFIX_BOUNDARY + re.escape(_GOOGLE_PREFIX) + r"[0-9A-Za-z_-]{35}"),
            _join(_GOOGLE_PREFIX, "Sy", "A" * 33),
        ),
        PatternClass(
            "huggingface_token",
            re.compile(_KEY_PREFIX_BOUNDARY + re.escape(_HF_PREFIX) + r"[A-Za-z0-9]{30,}"),
            _join(_HF_PREFIX, long_body, "opqr"),
        ),
        PatternClass(
            "github_token",
            re.compile(_alternation(_GH_PREFIXES) + r"[A-Za-z0-9]{36,}"),
            _join(_GH_PREFIXES[0], "A" * 36),
        ),
        PatternClass(
            "github_fine_grained_token",
            re.compile(re.escape(_GH_FINEGRAINED_PREFIX) + r"[A-Za-z0-9_]{20,}"),
            _join(_GH_FINEGRAINED_PREFIX, "A" * 22),
        ),
        PatternClass(
            "aws_access_key_id",
            re.compile(_alternation(_AWS_PREFIXES) + r"[0-9A-Z]{16}"),
            _join(_AWS_PREFIXES[0], "12345678", "90ABCDEF"),
        ),
        PatternClass(
            "slack_token",
            re.compile(_alternation(_SLACK_PREFIXES) + r"[0-9A-Za-z-]{10,}"),
            _join(_SLACK_PREFIXES[0], "12345678", "90abcdef"),
        ),
        PatternClass(
            "private_key_header",
            re.compile("|".join(re.escape(header) for header in _PEM_HEADERS)),
            _PEM_HEADERS[0],
        ),
        PatternClass(
            "generic_credential_assignment",
            re.compile(
                _join(r"[A-Za-z_][A-Za-z0-9_]*(?:", "|".join(_CRED_WORDS), r")[A-Za-z0-9_]*")
                + r"\s*[:=]\s*[\"']?([A-Za-z0-9+/_.\-]{20,})[\"']?"
            ),
            _join("MY_API_", "KEY", "=", "abcdEFGH", "12345678", "wxyz9012"),
            extra_validate=_generic_value_is_secret_shaped,
        ),
    ]


PATTERNS: list[PatternClass] = _build_patterns()


def is_dotenv_path(path: str) -> bool:
    """True if ``path``'s basename matches the withheld dotenv naming pattern.

    The ``.example`` form is the one deliberately-committed exception
    (variable names only, no values, per ``.gitignore``).
    """
    base = path.rsplit("/", 1)[-1]
    if base == _DOTENV_ALLOWED:
        return False
    return base == _DOTENV_NAME or base.startswith(_DOTENV_NAME + ".")


# --- Git plumbing -----------------------------------------------------------
# Every call takes the repository root as a parameter so the tests can point
# the scanner at a temporary repository and never touch the real one.


def _run_git(args: list[str], root: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed in {root}: {result.stderr.strip()}")
    return result.stdout


def _is_shallow(root: Path) -> bool:
    return _run_git(["rev-parse", "--is-shallow-repository"], root).strip() == "true"


def _iter_commit_hits(sha: str, root: Path) -> Iterator[tuple[str, str]]:
    """Yield (pattern_name, path) for every pattern hit in one commit's patch."""
    patch = _run_git(["show", "--no-color", "--format=", sha], root)
    current_path = "<unknown>"
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[len("+++ b/") :]
            continue
        if line.startswith(("--- ", "+++ ")):
            continue
        for pattern in PATTERNS:
            if any(True for _ in _matches(pattern, line)):
                yield pattern.name, current_path


def _check_dotenv_history(root: Path) -> list[str]:
    """Return every path in ``git log --all --name-only`` matching the dotenv shape."""
    log = _run_git(["log", "--all", "--name-only", "--pretty=format:"], root)
    paths = (line.strip() for line in log.splitlines())
    return [path for path in paths if path and is_dotenv_path(path)]


# --- Modes ------------------------------------------------------------------


def self_test() -> int:
    """Prove every pattern class fires on its own synthetic control."""
    failed: list[str] = []
    for pattern in PATTERNS:
        count = sum(1 for _ in _matches(pattern, pattern.positive_control))
        print(f"self-test {pattern.name}: {count} match(es) against its positive control")
        if count == 0:
            failed.append(pattern.name)
    if failed:
        print(f"SELF-TEST FAILED: zero-match pattern(s): {failed}", file=sys.stderr)
        return 1
    print(f"SELF-TEST OK: {len(PATTERNS)} pattern classes each matched their positive control")
    return 0


def scan_history(root: Path = ROOT) -> int:
    """Scan every reachable commit of the repository at ``root``.

    Returns 0 when clean, 1 on any hit, 2 when the clone is shallow (a
    depth-1 checkout would otherwise scan one commit and pass vacuously).
    """
    if _is_shallow(root):
        print(
            "history-secret-scan: refusing to scan a shallow repository "
            "(git rev-parse --is-shallow-repository = true); clone with full history "
            "(CI: actions/checkout fetch-depth: 0)",
            file=sys.stderr,
        )
        return 2

    commits = [sha.strip() for sha in _run_git(["rev-list", "--all"], root).splitlines()]
    commits = [sha for sha in commits if sha]

    hit_counts: dict[str, int] = {pattern.name: 0 for pattern in PATTERNS}
    hits: list[tuple[str, str, str]] = []
    for sha in commits:
        for pattern_name, path in _iter_commit_hits(sha, root):
            hit_counts[pattern_name] += 1
            hits.append((pattern_name, sha, path))

    dotenv_hits = _check_dotenv_history(root)

    print(f"scanned {len(commits)} commit(s) reachable from git rev-list --all")
    for name, count in hit_counts.items():
        print(f"pattern {name}: {count} hit(s)")
    print(f"dotenv-path-in-history: {len(dotenv_hits)} hit(s)")

    for pattern_name, sha, path in hits:
        print(f"HIT pattern={pattern_name} commit={sha} path={path}", file=sys.stderr)
    for path in dotenv_hits:
        print(f"HIT dotenv-path-in-history path={path}", file=sys.stderr)

    if hits or dotenv_hits:
        return 1
    print("no secrets found in any reachable commit; dotenv path never committed")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    # Output can contain characters that are not representable in the
    # platform's default console encoding; reconfigure so a report never
    # dies with UnicodeEncodeError (same treatment as scripts/check.py).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="assert every pattern class matches its synthetic positive control",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository to scan (default: this repository)",
    )
    args = parser.parse_args(list(argv) if argv is not None else sys.argv[1:])

    if args.self_test:
        return self_test()
    return scan_history(args.root)


if __name__ == "__main__":
    sys.exit(main())
