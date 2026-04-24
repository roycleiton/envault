"""Tests for the Vault module."""

import json
import pytest
from pathlib import Path

from envault.vault import Vault, VaultError


PASSPHRASE = "test-passphrase-123"


@pytest.fixture
def vault(tmp_path):
    """Return a Vault instance backed by a temporary directory."""
    return Vault(path=tmp_path / ".envault")


def test_set_and_get_roundtrip(vault):
    vault.set("DB_URL", "postgres://localhost/mydb", PASSPHRASE)
    assert vault.get("DB_URL", PASSPHRASE) == "postgres://localhost/mydb"


def test_vault_file_is_created(vault):
    vault.set("API_KEY", "secret", PASSPHRASE)
    assert vault.path.exists()


def test_vault_stores_encrypted_value(vault):
    vault.set("API_KEY", "secret", PASSPHRASE)
    raw = json.loads(vault.path.read_text())
    assert raw["API_KEY"] != "secret"


def test_get_wrong_passphrase_raises(vault):
    vault.set("TOKEN", "abc123", PASSPHRASE)
    with pytest.raises(Exception):
        vault.get("TOKEN", "wrong-passphrase")


def test_get_missing_key_raises(vault):
    with pytest.raises(VaultError, match="not found"):
        vault.get("MISSING", PASSPHRASE)


def test_set_empty_key_raises(vault):
    with pytest.raises(VaultError, match="empty"):
        vault.set("", "value", PASSPHRASE)


def test_list_keys(vault):
    vault.set("Z_KEY", "1", PASSPHRASE)
    vault.set("A_KEY", "2", PASSPHRASE)
    assert vault.list_keys() == ["A_KEY", "Z_KEY"]


def test_delete_key(vault):
    vault.set("TEMP", "value", PASSPHRASE)
    vault.delete("TEMP")
    assert "TEMP" not in vault.list_keys()


def test_delete_missing_key_raises(vault):
    with pytest.raises(VaultError, match="not found"):
        vault.delete("NONEXISTENT")


def test_export_returns_all_decrypted(vault):
    vault.set("FOO", "bar", PASSPHRASE)
    vault.set("BAZ", "qux", PASSPHRASE)
    result = vault.export(PASSPHRASE)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_empty_vault_list_keys(vault):
    assert vault.list_keys() == []
