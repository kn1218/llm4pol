"""WR-05: redaction reads more secret-shaped names and looks at string values (review 04-REVIEW.md).

``redact`` returned ``secret_key``, ``private_key``, ``access_key`` and ``Authorization`` unchanged and
never inspected a value, so ``prompt_versions: {"v": "<key>"}`` was written as it came. The name
rule now covers those and the camel-case forms; a string value that has the shape of a credential
is masked too. The usage numbers ``tokens``, ``max_tokens`` and ``token_budget`` still survive.
Secret-shaped test values are the scanner's own positive controls, built at run time.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from history_secret_scan import PATTERNS
from llm4pol.run import config, redaction

MUST_REDACT = (
    "secret_key",
    "SECRET_KEY",
    "secretKey",
    "client_secret",
    "private_key",
    "PrivateKey",
    "privateKey",
    "access_key",
    "accessKey",
    "AWS_SECRET_ACCESS_KEY",
    "Authorization",
    "authorization",
    "x-authorization-header",
    "credentials",
    "credential",
    "db_password",
    "passwd",
    "token",
    "access_token",
    "GITHUB_TOKEN",
    "hf-token",
    "bearer",
    "auth",
    "api-key",
    "apiKey",
    "x_api_key",
    "openaiApiKey",
    "signing_key",
    # RR-6
    "api_keys",
    "apiKeys",
    "private_keys",
    "access_keys",
    "passphrase",
    "db_passphrase",
    "auth_header",
    "authHeader",
    "auth_mode",
    "auth_token",
    "oauth",
    "OAuth",
    "oauth_token",
    "x_oauth_client",
    "secrets",
    "passwords",
)
MUST_SURVIVE = (
    "tokens",
    "max_tokens",
    "maxTokens",
    "token_budget",
    "key",
    "keys",
    "author",
    "authors",
    "authority",
    "secretary",
    "monkey",
    "candidate_id",
    "code_git_sha",
    "provider_key_configured",
    "seed",
    "hypothesis",
    "authored_by",
    "author_name",
    "author_",
)
BOOL_NAMES = ("is_secret", "no_credentials", "secret_santa", "has_password", "auth_required")
CONTROLS = (
    "openai_secret_key",
    "anthropic_secret_key",
    "google_ai_api_key",
    "huggingface_token",
    "github_token",
    "github_fine_grained_token",
    "aws_access_key_id",
    "slack_token",
    "private_key_header",
)


def _control(name: str) -> str:
    return next(p.positive_control for p in PATTERNS if p.name == name)


@pytest.mark.parametrize("name", MUST_REDACT)
def test_a_secret_shaped_name_is_redacted_whatever_its_case_and_style(name: str) -> None:
    assert config.redact({name: "value-1", "other": 1}) == {name: config.REDACTED, "other": 1}


@pytest.mark.parametrize("name", MUST_SURVIVE)
def test_a_plain_name_and_a_usage_count_survive(name: str) -> None:
    assert config.redact({name: 12345}) == {name: 12345}
    assert config.redact({name: "v1"}) == {name: "v1"}


@pytest.mark.parametrize("control", CONTROLS)
def test_a_credential_shaped_value_is_masked_under_any_key(control: str) -> None:
    value = _control(control)
    assert config.redact({"prompt_versions": {"hypothesis": value}}) == {
        "prompt_versions": {"hypothesis": config.REDACTED}
    }
    assert config.redact({"notes": ["fine", f"see {value} here"]}) == {
        "notes": ["fine", config.REDACTED]
    }


def _jwt() -> str:
    """Three base64url segments, the first the encoding of ``{"alg":...``; built at run time."""
    return ".".join(("eyJ" + "hbGciOiJIUzI1NiJ9", "eyJ" + "zdWIiOiIxMjM0In0", "c2ln" + "-nature_1"))


def test_a_jwt_shaped_value_is_masked_under_any_key_and_inside_text() -> None:
    token = _jwt()
    assert config.redact({"prompt_versions": {"v": token}}) == {
        "prompt_versions": {"v": config.REDACTED}
    }
    assert config.redact({"notes": [f"header was {token}"]}) == {"notes": [config.REDACTED]}
    unsigned = ".".join(("eyJ" + "hbGciOiJub25lIn0", "eyJ" + "zdWIiOiIxIn0", ""))
    assert config.redact({"v": unsigned}) == {"v": config.REDACTED}


def test_things_that_only_start_like_a_jwt_are_kept() -> None:
    kept = {
        "a": "eyJ.a.b",  # too short to be a header
        "b": "eyJhbGciOiJIUzI1NiJ9",  # one segment
        "c": "eyJhbGciOiJIUzI1NiJ9.e30",  # two segments
        "d": "version.eyJhbGciOiJIUzI1NiJ9.a.b",  # not at the start of a token
        "e": "see docs/eyJ/one.two.three",
    }
    assert config.redact(kept) == kept


@pytest.mark.parametrize("name", BOOL_NAMES)
def test_a_boolean_under_a_secret_looking_name_is_never_turned_into_a_string(name: str) -> None:
    assert config.redact({name: True}) == {name: True}
    assert config.redact({name: False})[name] is False
    assert config.redact({"outer": [{name: True}]}) == {"outer": [{name: True}]}
    assert config.redact({name: "x"}) == {name: config.REDACTED}  # a string there is still masked
    assert config.redact({name: 0}) == {name: config.REDACTED}  # only a real bool is exempt


def test_values_that_only_look_a_little_like_a_key_are_kept() -> None:
    kept = {
        "a": "v1",
        "b": "plan:sha256:" + "ab" * 32,
        "c": "0" * 40,
        "d": "task-content-of-the-hypothesis",
        "e": "sk-short",
        "f": "hf_short",
        "g": "the bearer of this message",
    }
    assert config.redact(kept) == kept


def test_redact_does_not_change_its_argument_and_keeps_the_committed_meta_example() -> None:
    nested = {"usage": {"tokens": 812, "items": [{"secret_key": "x", "n": 3}]}}
    before = copy.deepcopy(nested)
    assert config.redact(nested)["usage"]["items"][0] == {"secret_key": config.REDACTED, "n": 3}
    assert nested == before
    example = json.loads(
        (REPO_ROOT / "protocol" / "examples" / "run-meta.example.json").read_text(encoding="utf-8")
    )
    assert config.redact(example) == example


def test_write_meta_masks_a_credential_shaped_value_of_prompt_versions(tmp_path: Path) -> None:
    value = _control("openai_secret_key")
    example = json.loads(
        (REPO_ROOT / "protocol" / "examples" / "run-meta.example.json").read_text(encoding="utf-8")
    )
    meta = {**example, "prompt_versions": {"hypothesis": value, "translator": "v1"}}
    written = config.write_meta(tmp_path, meta)
    text = written.read_text(encoding="utf-8")
    assert value not in text
    assert json.loads(text)["prompt_versions"] == {
        "hypothesis": config.REDACTED,
        "translator": "v1",
    }


def test_the_name_and_value_rules_are_reachable_as_predicates() -> None:
    assert redaction.is_secret_name("secretKey") and not redaction.is_secret_name("tokens")
    assert redaction.is_secret_value(_control("github_token"))
    assert not redaction.is_secret_value("v1")
