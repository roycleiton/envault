"""Integration tests for the snapshot CLI subcommands."""

from __future__ import annotations

import subprocess
import sys
import pytest
from pathlib import Path


@pytest.fixture()
def vault_path(tmp_path):
    return tmp_path / "vault.env"


def run(*args, vault, passphrase="hunter2"):
    return subprocess.run(
        [
            sys.executable, "-m", "envault",
            "--vault", str(vault),
            "--passphrase", passphrase,
        ] + list(args),
        capture_output=True,
        text=True,
    )


def _seed(vault_path):
    run("set", "API_KEY", "secret", vault=vault_path)
    run("set", "DB_URL", "postgres://localhost", vault=vault_path)


def test_snapshot_create_exits_zero(vault_path):
    _seed(vault_path)
    result = run("snapshot", "create", "--label", "v1", vault=vault_path)
    assert result.returncode == 0


def test_snapshot_create_prints_path(vault_path):
    _seed(vault_path)
    result = run("snapshot", "create", "--label", "v1", vault=vault_path)
    assert "v1" in result.stdout


def test_snapshot_list_shows_label(vault_path):
    _seed(vault_path)
    run("snapshot", "create", "--label", "v1", vault=vault_path)
    result = run("snapshot", "list", vault=vault_path)
    assert result.returncode == 0
    assert "v1" in result.stdout


def test_snapshot_list_empty(vault_path):
    _seed(vault_path)
    result = run("snapshot", "list", vault=vault_path)
    assert result.returncode == 0
    assert "No snapshots" in result.stdout


def test_snapshot_restore_recovers_value(vault_path):
    _seed(vault_path)
    run("snapshot", "create", "--label", "v1", vault=vault_path)
    run("set", "API_KEY", "changed", vault=vault_path)
    run("snapshot", "restore", "v1", vault=vault_path)
    result = run("get", "API_KEY", vault=vault_path)
    assert result.stdout.strip() == "secret"


def test_snapshot_delete_removes_label(vault_path):
    _seed(vault_path)
    run("snapshot", "create", "--label", "v1", vault=vault_path)
    run("snapshot", "delete", "v1", vault=vault_path)
    result = run("snapshot", "list", vault=vault_path)
    assert "v1" not in result.stdout


def test_snapshot_restore_missing_returns_nonzero(vault_path):
    _seed(vault_path)
    result = run("snapshot", "restore", "ghost", vault=vault_path)
    assert result.returncode != 0
    assert "not found" in result.stderr


def test_snapshot_delete_missing_returns_nonzero(vault_path):
    _seed(vault_path)
    result = run("snapshot", "delete", "ghost", vault=vault_path)
    assert result.returncode != 0
