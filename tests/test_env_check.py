"""Unit tests for envault.env_check."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_check import check_env, EnvCheckResult

PASSPHRASE = "unit-check-pass"


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    v = Vault(tmp_path / "check.vault", PASSPHRASE)
    v.set("DB_URL", "postgres://localhost/mydb")
    v.set("API_KEY", "topsecret")
    return v


def test_returns_one_result_per_vault_key(vault: Vault) -> None:
    results = check_env(vault)
    assert len(results) == 2


def test_result_keys_match_vault_keys(vault: Vault) -> None:
    results = check_env(vault)
    assert {r.key for r in results} == {"DB_URL", "API_KEY"}


def test_missing_status_when_key_not_in_env(vault: Vault, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DB_URL", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    results = check_env(vault)
    assert all(r.status == "missing" for r in results)


def test_ok_status_when_values_match(vault: Vault, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_URL", "postgres://localhost/mydb")
    monkeypatch.setenv("API_KEY", "topsecret")
    results = check_env(vault)
    assert all(r.status == "ok" for r in results)


def test_mismatch_status_when_value_differs(vault: Vault, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_URL", "postgres://other/db")
    monkeypatch.delenv("API_KEY", raising=False)
    results = check_env(vault)
    by_key = {r.key: r for r in results}
    assert by_key["DB_URL"].status == "mismatch"
    assert by_key["API_KEY"].status == "missing"


def test_filter_by_keys(vault: Vault, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_URL", "postgres://localhost/mydb")
    results = check_env(vault, keys=["DB_URL"])
    assert len(results) == 1
    assert results[0].key == "DB_URL"


def test_filter_nonexistent_key_raises(vault: Vault) -> None:
    from envault.env_check import EnvCheckError
    with pytest.raises(EnvCheckError):
        check_env(vault, keys=["DOES_NOT_EXIST"])


def test_result_is_dataclass(vault: Vault) -> None:
    results = check_env(vault)
    for r in results:
        assert hasattr(r, "key")
        assert hasattr(r, "status")
