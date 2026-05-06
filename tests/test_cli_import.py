"""Integration tests for the `envault import` CLI sub-command."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


PASSPHRASE = "s3cr3t"


@pytest.fixture()
def vault_path(tmp_path) -> Path:
    return tmp_path / "test.vault"


@pytest.fixture()
def dotenv_file(tmp_path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


@pytest.fixture()
def json_file(tmp_path) -> Path:
    p = tmp_path / "secrets.json"
    p.write_text(json.dumps({"ALPHA": "1", "BETA": "2"}))
    return p


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "envault", *args],
        capture_output=True,
        text=True,
    )


def test_import_dotenv_exits_zero(vault_path, dotenv_file):
    result = run("-v", str(vault_path), "-p", PASSPHRASE, "import", str(dotenv_file))
    assert result.returncode == 0


def test_import_dotenv_reports_count(vault_path, dotenv_file):
    result = run("-v", str(vault_path), "-p", PASSPHRASE, "import", str(dotenv_file))
    assert "Imported 2 secret(s)" in result.stdout


def test_import_json_format(vault_path, json_file):
    result = run(
        "-v", str(vault_path), "-p", PASSPHRASE,
        "import", str(json_file), "--format", "json",
    )
    assert result.returncode == 0
    assert "Imported 2 secret(s)" in result.stdout


def test_import_skips_existing_by_default(vault_path, dotenv_file):
    run("-v", str(vault_path), "-p", PASSPHRASE, "set", "FOO", "original")
    result = run("-v", str(vault_path), "-p", PASSPHRASE, "import", str(dotenv_file))
    assert "skipped 1 existing" in result.stdout
    get = run("-v", str(vault_path), "-p", PASSPHRASE, "get", "FOO")
    assert get.stdout.strip() == "original"


def test_import_overwrite_flag(vault_path, dotenv_file):
    run("-v", str(vault_path), "-p", PASSPHRASE, "set", "FOO", "original")
    run("-v", str(vault_path), "-p", PASSPHRASE, "import", "--overwrite", str(dotenv_file))
    get = run("-v", str(vault_path), "-p", PASSPHRASE, "get", "FOO")
    assert get.stdout.strip() == "bar"


def test_import_missing_file_returns_nonzero(vault_path):
    result = run(
        "-v", str(vault_path), "-p", PASSPHRASE, "import", "/no/such/file.env"
    )
    assert result.returncode != 0
    assert "file not found" in result.stderr
