"""CLI integration tests for the history sub-command."""

from __future__ import annotations

import subprocess
import sys

import pytest

from envault.vault import Vault
from envault.history import record_change

PASS = "testpass"


@pytest.fixture()
def vault_path(tmp_path):
    return tmp_path / "vault.bin"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "envault", *args],
        capture_output=True,
        text=True,
    )


def _seed(vault_path):
    v = Vault(vault_path)
    v.set("API_KEY", "secret123", PASS)
    record_change(v, PASS, "API_KEY", "set", value="secret123")
    return v


def test_history_exits_zero(vault_path):
    _seed(vault_path)
    result = run("history", "API_KEY", "--vault", str(vault_path), "--passphrase", PASS)
    assert result.returncode == 0


def test_history_shows_entries(vault_path):
    _seed(vault_path)
    result = run("history", "API_KEY", "--vault", str(vault_path), "--passphrase", PASS)
    assert "set" in result.stdout


def test_history_missing_key_exits_zero(vault_path):
    _seed(vault_path)
    result = run("history", "GHOST", "--vault", str(vault_path), "--passphrase", PASS)
    assert result.returncode == 0
    assert "No history" in result.stdout


def test_history_clear_exits_zero(vault_path):
    _seed(vault_path)
    result = run(
        "history", "API_KEY", "--vault", str(vault_path), "--passphrase", PASS, "--clear"
    )
    assert result.returncode == 0
    assert "cleared" in result.stdout


def test_history_clear_removes_entries(vault_path):
    _seed(vault_path)
    run("history", "API_KEY", "--vault", str(vault_path), "--passphrase", PASS, "--clear")
    result = run("history", "API_KEY", "--vault", str(vault_path), "--passphrase", PASS)
    assert "No history" in result.stdout


def test_history_limit_flag(vault_path):
    v = _seed(vault_path)
    for i in range(5):
        record_change(v, PASS, "API_KEY", "set", value=f"v{i}")
    result = run(
        "history", "API_KEY", "--vault", str(vault_path), "--passphrase", PASS, "--limit", "2"
    )
    assert result.returncode == 0
    lines = [l for l in result.stdout.splitlines() if l.startswith("  ")]
    assert len(lines) == 2


def test_history_wrong_passphrase_exits_nonzero(vault_path):
    _seed(vault_path)
    result = run(
        "history", "API_KEY", "--vault", str(vault_path), "--passphrase", "wrongpass"
    )
    assert result.returncode != 0
