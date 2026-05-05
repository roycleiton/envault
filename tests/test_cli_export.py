"""Integration tests for the 'envault export' CLI sub-command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from envault.vault import Vault


PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    path = tmp_path / ".envault"
    v = Vault(path=path, passphrase=PASSPHRASE)
    v.set("APP_ENV", "production")
    v.set("SECRET_KEY", "abc123")
    return path


def run(vault_path: Path, fmt: str):
    """Run 'envault export' and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "envault.cli", "--vault", str(vault_path), "export", "--format", fmt],
        input=PASSPHRASE + "\n",
        capture_output=True,
        text=True,
    )


def test_export_dotenv_contains_keys(vault_path: Path):
    result = run(vault_path, "dotenv")
    assert result.returncode == 0
    assert "APP_ENV" in result.stdout
    assert "SECRET_KEY" in result.stdout


def test_export_dotenv_format(vault_path: Path):
    result = run(vault_path, "dotenv")
    assert result.returncode == 0
    assert 'APP_ENV="production"' in result.stdout


def test_export_shell_format(vault_path: Path):
    result = run(vault_path, "shell")
    assert result.returncode == 0
    assert "export APP_ENV=" in result.stdout
    assert "export SECRET_KEY=" in result.stdout


def test_export_json_format(vault_path: Path):
    result = run(vault_path, "json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["APP_ENV"] == "production"
    assert data["SECRET_KEY"] == "abc123"


def test_export_wrong_passphrase_returns_nonzero(vault_path: Path):
    proc = subprocess.run(
        [sys.executable, "-m", "envault.cli", "--vault", str(vault_path), "export"],
        input="wrong-passphrase\n",
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "error" in proc.stderr.lower()


def test_export_missing_vault_returns_nonzero(tmp_path: Path):
    missing = tmp_path / "no_such_file"
    proc = subprocess.run(
        [sys.executable, "-m", "envault.cli", "--vault", str(missing), "export"],
        input=PASSPHRASE + "\n",
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
