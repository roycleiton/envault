"""Tests for envault.env_inject and the inject CLI sub-command."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from envault.env_inject import InjectError, inject_and_run
from envault.vault import Vault

PASSPHRASE = "hunter2"


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    v = Vault(str(tmp_path / "vault.env"))
    v.set("DB_HOST", "localhost", PASSPHRASE)
    v.set("DB_PORT", "5432", PASSPHRASE)
    v.set("API_KEY", "secret-key", PASSPHRASE)
    return v


# ---------------------------------------------------------------------------
# inject_and_run unit tests
# ---------------------------------------------------------------------------

def test_inject_runs_command(vault: Vault) -> None:
    result = inject_and_run(vault, PASSPHRASE, [sys.executable, "-c", "import sys; sys.exit(0)"])
    assert result.returncode == 0


def test_inject_all_keys_reported(vault: Vault) -> None:
    result = inject_and_run(vault, PASSPHRASE, [sys.executable, "-c", "pass"])
    assert set(result.injected) == {"DB_HOST", "DB_PORT", "API_KEY"}


def test_inject_subset_of_keys(vault: Vault) -> None:
    result = inject_and_run(
        vault, PASSPHRASE, [sys.executable, "-c", "pass"], keys=["DB_HOST"]
    )
    assert result.injected == ["DB_HOST"]


def test_inject_prefix_applied(vault: Vault) -> None:
    script = "import os, sys; sys.exit(0 if os.environ.get('APP_DB_HOST') == 'localhost' else 1)"
    result = inject_and_run(
        vault, PASSPHRASE, [sys.executable, "-c", script],
        prefix="APP_", keys=["DB_HOST"]
    )
    assert result.returncode == 0
    assert "APP_DB_HOST" in result.injected


def test_inject_no_override_skips_existing(vault: Vault, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "original")
    result = inject_and_run(
        vault, PASSPHRASE, [sys.executable, "-c", "pass"],
        keys=["DB_HOST"], override=False
    )
    assert "DB_HOST" in result.skipped
    assert "DB_HOST" not in result.injected


def test_inject_empty_command_raises(vault: Vault) -> None:
    with pytest.raises(InjectError, match="empty"):
        inject_and_run(vault, PASSPHRASE, [])


def test_inject_wrong_passphrase_raises(vault: Vault) -> None:
    with pytest.raises(InjectError):
        inject_and_run(vault, "wrong", [sys.executable, "-c", "pass"])


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "vault.env"


def run(vault_path: Path, *args: str) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    return subprocess.run(
        [sys.executable, "-m", "envault", *args],
        capture_output=True,
        text=True,
    )


def _seed(vault_path: Path) -> None:
    v = Vault(str(vault_path))
    v.set("MY_VAR", "hello", PASSPHRASE)


def test_cli_inject_exits_zero(vault_path: Path) -> None:
    _seed(vault_path)
    result = run(
        vault_path,
        "inject",
        "--vault", str(vault_path),
        "--passphrase", PASSPHRASE,
        "--", sys.executable, "-c", "pass",
    )
    assert result.returncode == 0


def test_cli_inject_no_command_returns_nonzero(vault_path: Path) -> None:
    _seed(vault_path)
    result = run(
        vault_path,
        "inject",
        "--vault", str(vault_path),
        "--passphrase", PASSPHRASE,
    )
    assert result.returncode != 0
