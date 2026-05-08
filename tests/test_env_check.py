"""Tests for envault.env_check."""
from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_check import EnvCheckError, EnvCheckResult, check_env


PASS = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.enc", PASS)
    v.set("DB_HOST", "localhost", PASS)
    v.set("DB_PORT", "5432", PASS)
    v.set("SECRET_KEY", "s3cr3t", PASS)
    return v


def test_returns_one_result_per_vault_key(vault):
    results = check_env(vault, PASS, env={})
    assert len(results) == 3


def test_result_keys_match_vault_keys(vault):
    results = check_env(vault, PASS, env={})
    assert {r.key for r in results} == {"DB_HOST", "DB_PORT", "SECRET_KEY"}


def test_missing_status_when_key_not_in_env(vault):
    results = check_env(vault, PASS, env={})
    assert all(r.status == "missing" for r in results)


def test_ok_status_when_values_match(vault):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "s3cr3t"}
    results = check_env(vault, PASS, env=env)
    assert all(r.status == "ok" for r in results)


def test_mismatch_status_when_values_differ(vault):
    env = {"DB_HOST": "remotehost", "DB_PORT": "5432", "SECRET_KEY": "s3cr3t"}
    results = check_env(vault, PASS, env=env)
    by_key = {r.key: r for r in results}
    assert by_key["DB_HOST"].status == "mismatch"
    assert by_key["DB_PORT"].status == "ok"


def test_value_matches_none_when_key_absent(vault):
    results = check_env(vault, PASS, env={})
    assert all(r.value_matches is None for r in results)


def test_in_env_flag_set_correctly(vault):
    env = {"DB_HOST": "localhost"}
    results = check_env(vault, PASS, env=env)
    by_key = {r.key: r for r in results}
    assert by_key["DB_HOST"].in_env is True
    assert by_key["DB_PORT"].in_env is False


def test_all_results_have_in_vault_true(vault):
    results = check_env(vault, PASS, env={})
    assert all(r.in_vault for r in results)


def test_wrong_passphrase_raises_env_check_error(vault):
    with pytest.raises(EnvCheckError):
        check_env(vault, "wrong-pass", env={})


def test_results_sorted_alphabetically(vault):
    results = check_env(vault, PASS, env={})
    keys = [r.key for r in results]
    assert keys == sorted(keys)


def test_empty_vault_returns_empty_list(tmp_path):
    v = Vault(tmp_path / "empty.enc", PASS)
    results = check_env(v, PASS, env={"DB_HOST": "localhost"})
    assert results == []
