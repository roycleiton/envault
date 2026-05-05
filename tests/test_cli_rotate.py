"""Integration tests for the *rotate* CLI sub-command."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from envault.vault import Vault, VaultError


@pytest.fixture()
def vault_path(tmp_path) -> Path:
    path = tmp_path / "vault.enc"
    v = Vault(path, "old-pass")
    v.set("FOO", "bar")
    v.set("BAZ", "qux")
    return path


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "envault", *args],
        capture_output=True,
        text=True,
    )


def test_rotate_succeeds(vault_path):
    result = run(
        "rotate", str(vault_path),
        "--old-passphrase", "old-pass",
        "--new-passphrase", "new-pass",
    )
    assert result.returncode == 0
    assert "2 secret(s)" in result.stdout


def test_rotate_new_passphrase_works(vault_path):
    run(
        "rotate", str(vault_path),
        "--old-passphrase", "old-pass",
        "--new-passphrase", "new-pass",
    )
    v = Vault(vault_path, "new-pass")
    assert v.get("FOO") == "bar"


def test_rotate_wrong_old_passphrase(vault_path):
    result = run(
        "rotate", str(vault_path),
        "--old-passphrase", "wrong",
        "--new-passphrase", "new-pass",
    )
    assert result.returncode != 0
    assert "error" in result.stderr.lower()


def test_rotate_same_passphrase_fails(vault_path):
    result = run(
        "rotate", str(vault_path),
        "--old-passphrase", "old-pass",
        "--new-passphrase", "old-pass",
    )
    assert result.returncode != 0


def test_rotate_old_passphrase_rejected_afterwards(vault_path):
    run(
        "rotate", str(vault_path),
        "--old-passphrase", "old-pass",
        "--new-passphrase", "new-pass",
    )
    v = Vault(vault_path, "old-pass")
    with pytest.raises(VaultError):
        v.get("FOO")
