"""Tests for envault.policy."""

import pytest

from envault.policy import (
    PolicyError,
    PolicyViolation,
    enforce_policy,
    _check_key_pattern,
    _check_min_length,
    _check_forbidden_keys,
)
from envault.vault import Vault


PASS = "test-passphrase"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.enc", PASS)
    v.set("DB_PASSWORD", "supersecret123", PASS)
    v.set("API_KEY", "short", PASS)
    v.set("SECRET_TOKEN", "averylongsecrettoken", PASS)
    return v


# --- unit helpers ---

def test_check_key_pattern_match():
    assert _check_key_pattern("DB_PASSWORD", r"[A-Z_]+") is None


def test_check_key_pattern_no_match():
    v = _check_key_pattern("dbPassword", r"[A-Z_]+")
    assert v is not None
    assert v.rule == "key_pattern"
    assert v.severity == "error"


def test_check_key_pattern_invalid_regex():
    with pytest.raises(PolicyError):
        _check_key_pattern("KEY", r"[invalid")


def test_check_min_length_pass():
    assert _check_min_length("K", "longenough", 8) is None


def test_check_min_length_fail():
    v = _check_min_length("K", "hi", 8)
    assert v is not None
    assert v.rule == "min_length"
    assert v.severity == "warning"


def test_check_forbidden_keys_not_forbidden():
    assert _check_forbidden_keys("SAFE_KEY", ["BAD_KEY"]) is None


def test_check_forbidden_keys_forbidden():
    v = _check_forbidden_keys("BAD_KEY", ["BAD_KEY"])
    assert v is not None
    assert v.rule == "forbidden_keys"


# --- enforce_policy integration ---

def test_no_violations_clean_vault(vault):
    violations = enforce_policy(vault, PASS)
    assert violations == []


def test_key_pattern_violation_detected(vault):
    # Only uppercase + underscore allowed; all existing keys should pass
    violations = enforce_policy(vault, PASS, key_pattern=r"[A-Z_]+")
    assert all(v.rule == "key_pattern" for v in violations)
    assert len(violations) == 0  # all keys match


def test_key_pattern_catches_bad_key(vault):
    vault.set("badKey", "value", PASS)
    violations = enforce_policy(vault, PASS, key_pattern=r"[A-Z_]+")
    keys_flagged = [v.key for v in violations]
    assert "badKey" in keys_flagged


def test_min_length_violation_detected(vault):
    violations = enforce_policy(vault, PASS, min_length=10)
    short_violations = [v for v in violations if v.rule == "min_length"]
    assert any(v.key == "API_KEY" for v in short_violations)


def test_min_length_no_violation_when_all_long(vault):
    violations = enforce_policy(vault, PASS, min_length=3)
    assert not any(v.rule == "min_length" for v in violations)


def test_forbidden_keys_violation(vault):
    violations = enforce_policy(vault, PASS, forbidden_keys=["API_KEY"])
    assert any(v.key == "API_KEY" and v.rule == "forbidden_keys" for v in violations)


def test_multiple_rules_combined(vault):
    vault.set("bad_key", "x", PASS)
    violations = enforce_policy(
        vault,
        PASS,
        key_pattern=r"[A-Z_]+",
        min_length=8,
        forbidden_keys=["API_KEY"],
    )
    rules = {v.rule for v in violations}
    assert "key_pattern" in rules
    assert "min_length" in rules
    assert "forbidden_keys" in rules


def test_returns_list_of_policy_violation_instances(vault):
    violations = enforce_policy(vault, PASS, forbidden_keys=["DB_PASSWORD"])
    assert all(isinstance(v, PolicyViolation) for v in violations)


def test_invalid_key_pattern_raises_policy_error(vault):
    with pytest.raises(PolicyError):
        enforce_policy(vault, PASS, key_pattern=r"[broken")
