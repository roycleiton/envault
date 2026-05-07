"""Integration tests for the TTL CLI sub-commands."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import datetime

import pytest

PASS = "s3cr3t"


@pytest.fixture()
def vault_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "vault.db"


def run(*args: str, vault: pathlib.Path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable, "-m", "envault",
        "--vault", str(vault),
        "--passphrase", PASS,
    ] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


def _seed(vault_path: pathlib.Path) -> None:
    run("set", "API_KEY", "abc123", vault=vault_path)
    run("set", "DB_URL", "postgres://localhost", vault=vault_path)


def test_ttl_set_exits_zero(vault_path: pathlib.Path) -> None:
    _seed(vault_path)
    future = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat()
    result = run("ttl", "set", "API_KEY", future, vault=vault_path)
    assert result.returncode == 0


def test_ttl_set_prints_confirmation(vault_path: pathlib.Path) -> None:
    _seed(vault_path)
    future = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat()
    result = run("ttl", "set", "API_KEY", future, vault=vault_path)
    assert "TTL set" in result.stdout
    assert "API_KEY" in result.stdout


def test_ttl_get_shows_expiry(vault_path: pathlib.Path) -> None:
    _seed(vault_path)
    future = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat()
    run("ttl", "set", "API_KEY", future, vault=vault_path)
    result = run("ttl", "get", "API_KEY", vault=vault_path)
    assert result.returncode == 0
    assert "valid" in result.stdout


def test_ttl_get_no_ttl_message(vault_path: pathlib.Path) -> None:
    _seed(vault_path)
    result = run("ttl", "get", "API_KEY", vault=vault_path)
    assert result.returncode == 0
    assert "No TTL" in result.stdout


def test_ttl_clear_exits_zero(vault_path: pathlib.Path) -> None:
    _seed(vault_path)
    future = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat()
    run("ttl", "set", "API_KEY", future, vault=vault_path)
    result = run("ttl", "clear", "API_KEY", vault=vault_path)
    assert result.returncode == 0
    assert "cleared" in result.stdout


def test_ttl_purge_removes_expired(vault_path: pathlib.Path) -> None:
    _seed(vault_path)
    past = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat()
    run("ttl", "set", "API_KEY", past, vault=vault_path)
    result = run("ttl", "purge", vault=vault_path)
    assert result.returncode == 0
    assert "purged" in result.stdout


def test_ttl_purge_no_expired_message(vault_path: pathlib.Path) -> None:
    _seed(vault_path)
    result = run("ttl", "purge", vault=vault_path)
    assert result.returncode == 0
    assert "No expired" in result.stdout


def test_ttl_set_invalid_datetime_exits_nonzero(vault_path: pathlib.Path) -> None:
    _seed(vault_path)
    result = run("ttl", "set", "API_KEY", "not-a-date", vault=vault_path)
    assert result.returncode != 0
