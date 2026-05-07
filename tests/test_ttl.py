"""Tests for envault.ttl."""
from __future__ import annotations

import datetime
import pathlib

import pytest

from envault.vault import Vault
from envault.ttl import (
    TTLError,
    set_ttl,
    get_ttl,
    is_expired,
    clear_ttl,
    purge_expired,
)

PASS = "hunter2"


@pytest.fixture()
def vault(tmp_path: pathlib.Path) -> Vault:
    v = Vault(tmp_path / "vault.db", PASS)
    v.set("API_KEY", "abc123")
    v.set("DB_URL", "postgres://localhost/dev")
    return v


def _future(seconds: int = 3600) -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=seconds)


def _past(seconds: int = 3600) -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(seconds=seconds)


def test_set_and_get_ttl_roundtrip(vault: Vault) -> None:
    exp = _future()
    set_ttl(vault, "API_KEY", exp)
    result = get_ttl(vault, "API_KEY")
    assert result is not None
    assert abs((result - exp).total_seconds()) < 1


def test_get_ttl_returns_none_when_unset(vault: Vault) -> None:
    assert get_ttl(vault, "API_KEY") is None


def test_is_expired_false_for_future(vault: Vault) -> None:
    set_ttl(vault, "API_KEY", _future())
    assert is_expired(vault, "API_KEY") is False


def test_is_expired_true_for_past(vault: Vault) -> None:
    set_ttl(vault, "API_KEY", _past())
    assert is_expired(vault, "API_KEY") is True


def test_is_expired_false_when_no_ttl(vault: Vault) -> None:
    assert is_expired(vault, "API_KEY") is False


def test_clear_ttl_removes_expiry(vault: Vault) -> None:
    set_ttl(vault, "API_KEY", _future())
    clear_ttl(vault, "API_KEY")
    assert get_ttl(vault, "API_KEY") is None


def test_clear_ttl_noop_when_unset(vault: Vault) -> None:
    # Should not raise
    clear_ttl(vault, "API_KEY")


def test_purge_expired_removes_expired_keys(vault: Vault) -> None:
    set_ttl(vault, "API_KEY", _past())
    deleted = purge_expired(vault)
    assert "API_KEY" in deleted
    assert "API_KEY" not in vault.list()


def test_purge_expired_keeps_live_keys(vault: Vault) -> None:
    set_ttl(vault, "API_KEY", _past())
    set_ttl(vault, "DB_URL", _future())
    purge_expired(vault)
    assert "DB_URL" in vault.list()


def test_purge_expired_returns_only_deleted(vault: Vault) -> None:
    set_ttl(vault, "API_KEY", _past())
    deleted = purge_expired(vault)
    assert deleted == ["API_KEY"]


def test_purge_expired_clears_ttl_metadata(vault: Vault) -> None:
    set_ttl(vault, "API_KEY", _past())
    purge_expired(vault)
    assert get_ttl(vault, "API_KEY") is None
