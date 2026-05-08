"""Tests for the `envault check` CLI sub-command."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PASSPHRASE = "cli-check-pass"


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, "-m", "envault", *args],
        capture_output=True,
        text=True,
        env=merged,
    )


def _seed(vault_path: Path) -> None:
    run("set", str(vault_path), "--passphrase", PASSPHRASE, "DB_URL", "postgres://localhost/db")
    run("set", str(vault_path), "--passphrase", PASSPHRASE, "API_KEY", "supersecret")


def test_check_exits_zero_when_env_matches(vault_path: Path) -> None:
    _seed(vault_path)
    env = {"DB_URL": "postgres://localhost/db", "API_KEY": "supersecret"}
    result = run("check", str(vault_path), "--passphrase", PASSPHRASE, env=env)
    assert result.returncode == 0


def test_check_output_contains_ok(vault_path: Path) -> None:
    _seed(vault_path)
    env = {"DB_URL": "postgres://localhost/db", "API_KEY": "supersecret"}
    result = run("check", str(vault_path), "--passphrase", PASSPHRASE, env=env)
    assert "OK" in result.stdout


def test_check_shows_missing_status(vault_path: Path) -> None:
    _seed(vault_path)
    # Don't set any env vars so both keys are missing
    result = run("check", str(vault_path), "--passphrase", PASSPHRASE)
    assert "MISSING" in result.stdout


def test_check_fail_on_mismatch_returns_nonzero(vault_path: Path) -> None:
    _seed(vault_path)
    result = run(
        "check", str(vault_path), "--passphrase", PASSPHRASE, "--fail-on-mismatch"
    )
    assert result.returncode == 1


def test_check_specific_keys_only(vault_path: Path) -> None:
    _seed(vault_path)
    env = {"DB_URL": "postgres://localhost/db"}
    result = run(
        "check", str(vault_path), "--passphrase", PASSPHRASE,
        "--keys", "DB_URL",
        env=env,
    )
    assert "DB_URL" in result.stdout
    assert "API_KEY" not in result.stdout


def test_check_wrong_passphrase_returns_nonzero(vault_path: Path) -> None:
    _seed(vault_path)
    result = run("check", str(vault_path), "--passphrase", "wrongpass")
    assert result.returncode == 1
    assert "error" in result.stderr.lower()
