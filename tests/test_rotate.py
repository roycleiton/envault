"""Tests for envault.rotate."""

from __future__ import annotations

import pytest

from envault.rotate import RotateError, rotate_passphrase
from envault.vault import Vault, VaultError


@pytest.fixture()
def populated_vault(tmp_path):
    """Return a vault path pre-loaded with a few secrets."""
    path = tmp_path / "vault.enc"
    v = Vault(path, "old-pass")
    v.set("DB_URL", "postgres://localhost/mydb")
    v.set("API_KEY", "supersecret")
    v.set("DEBUG", "true")
    return path


def test_rotate_changes_passphrase(populated_vault):
    rotate_passphrase(populated_vault, "old-pass", "new-pass")
    new_vault = Vault(populated_vault, "new-pass")
    assert new_vault.get("DB_URL") == "postgres://localhost/mydb"
    assert new_vault.get("API_KEY") == "supersecret"
    assert new_vault.get("DEBUG") == "true"


def test_rotate_returns_secret_count(populated_vault):
    count = rotate_passphrase(populated_vault, "old-pass", "new-pass")
    assert count == 3


def test_old_passphrase_rejected_after_rotation(populated_vault):
    rotate_passphrase(populated_vault, "old-pass", "new-pass")
    old_vault = Vault(populated_vault, "old-pass")
    with pytest.raises(VaultError):
        old_vault.get("DB_URL")


def test_rotate_same_passphrase_raises(populated_vault):
    with pytest.raises(RotateError, match="must differ"):
        rotate_passphrase(populated_vault, "old-pass", "old-pass")


def test_rotate_wrong_old_passphrase_raises(populated_vault):
    with pytest.raises(RotateError):
        rotate_passphrase(populated_vault, "wrong-pass", "new-pass")


def test_rotate_preserves_all_keys(populated_vault):
    rotate_passphrase(populated_vault, "old-pass", "new-pass")
    new_vault = Vault(populated_vault, "new-pass")
    assert set(new_vault.list_keys()) == {"DB_URL", "API_KEY", "DEBUG"}


def test_rotate_empty_vault(tmp_path):
    path = tmp_path / "empty.enc"
    Vault(path, "old-pass")._save_raw({})
    count = rotate_passphrase(path, "old-pass", "new-pass")
    assert count == 0
