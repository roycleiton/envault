"""Tests for envault.env_sync."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_sync import SyncError, SyncResult, sync_to_dotenv, sync_to_env


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    v = Vault(tmp_path / "vault.db", "s3cret")
    v.set("API_KEY", "abc123")
    v.set("DB_PASSWORD", "hunter2")
    v.set("DEBUG", "true")
    return v


@pytest.fixture()
def vault_path(vault: Vault) -> Path:
    return vault._path  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# sync_to_env
# ---------------------------------------------------------------------------

def test_sync_to_env_pushes_all_keys(vault_path: Path, monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    result = sync_to_env(vault_path, "s3cret")
    assert "API_KEY" in result.pushed
    assert "DB_PASSWORD" in result.pushed
    assert result.success


def test_sync_to_env_sets_os_environ(vault_path: Path, monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    sync_to_env(vault_path, "s3cret")
    assert os.environ["API_KEY"] == "abc123"


def test_sync_to_env_subset_of_keys(vault_path: Path, monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    result = sync_to_env(vault_path, "s3cret", keys=["API_KEY"])
    assert result.pushed == ["API_KEY"]
    assert "DB_PASSWORD" not in result.pushed


def test_sync_to_env_wrong_passphrase_raises(vault_path: Path):
    with pytest.raises(SyncError):
        sync_to_env(vault_path, "wrong")


def test_sync_to_env_skips_meta_keys(vault_path: Path):
    vault = Vault(vault_path, "s3cret")
    vault.set("__meta_tag_API_KEY", "[\"tag1\"]")
    result = sync_to_env(vault_path, "s3cret")
    assert "__meta_tag_API_KEY" in result.skipped
    assert "__meta_tag_API_KEY" not in result.pushed


# ---------------------------------------------------------------------------
# sync_to_dotenv
# ---------------------------------------------------------------------------

def test_sync_to_dotenv_creates_file(vault_path: Path, tmp_path: Path):
    dest = tmp_path / "output.env"
    sync_to_dotenv(vault_path, "s3cret", dest)
    assert dest.exists()


def test_sync_to_dotenv_contains_all_keys(vault_path: Path, tmp_path: Path):
    dest = tmp_path / "output.env"
    result = sync_to_dotenv(vault_path, "s3cret", dest)
    content = dest.read_text()
    assert "API_KEY" in content
    assert "DB_PASSWORD" in content
    assert result.success


def test_sync_to_dotenv_values_quoted(vault_path: Path, tmp_path: Path):
    dest = tmp_path / "output.env"
    sync_to_dotenv(vault_path, "s3cret", dest)
    content = dest.read_text()
    assert 'API_KEY="abc123"' in content


def test_sync_to_dotenv_no_overwrite_by_default(vault_path: Path, tmp_path: Path):
    dest = tmp_path / "output.env"
    dest.write_text('API_KEY="old_value"\n')
    result = sync_to_dotenv(vault_path, "s3cret", dest, overwrite=False)
    assert "API_KEY" in result.skipped
    assert 'API_KEY="old_value"' in dest.read_text()


def test_sync_to_dotenv_overwrite_replaces_key(vault_path: Path, tmp_path: Path):
    dest = tmp_path / "output.env"
    dest.write_text('API_KEY="old_value"\n')
    result = sync_to_dotenv(vault_path, "s3cret", dest, overwrite=True)
    assert "API_KEY" in result.pushed


def test_sync_to_dotenv_wrong_passphrase_raises(vault_path: Path, tmp_path: Path):
    dest = tmp_path / "output.env"
    with pytest.raises(SyncError):
        sync_to_dotenv(vault_path, "wrong", dest)
