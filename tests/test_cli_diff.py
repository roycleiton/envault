"""Integration tests for the `envault diff` CLI subcommand."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from envault.vault import Vault

PASS = "test-pass"


@pytest.fixture()
def vault_path(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "test.vault"
    v = Vault(str(p))
    v.set("ALPHA", "one", PASS)
    v.set("BETA", "two", PASS)
    return p


@pytest.fixture()
def dotenv_file(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "vars.env"
    p.write_text("ALPHA=one\nGAMMA=three\n")
    return p


@pytest.fixture()
def json_file(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "vars.json"
    p.write_text(json.dumps({"ALPHA": "one", "DELTA": "four"}))
    return p


def run(*args):
    """Run the envault CLI as a subprocess and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "envault", *args],
        capture_output=True,
        text=True,
    )


def test_diff_exits_two_when_differences(vault_path, dotenv_file):
    result = run("diff", str(vault_path), str(dotenv_file), "--passphrase", PASS)
    assert result.returncode == 2


def test_diff_shows_added_key(vault_path, dotenv_file):
    result = run("diff", str(vault_path), str(dotenv_file), "--passphrase", PASS)
    assert "GAMMA" in result.stdout
    assert "+" in result.stdout


def test_diff_shows_removed_key(vault_path, dotenv_file):
    result = run("diff", str(vault_path), str(dotenv_file), "--passphrase", PASS)
    assert "BETA" in result.stdout
    assert "-" in result.stdout


def test_diff_exits_zero_when_identical(vault_path, tmp_path):
    ef = tmp_path / "exact.env"
    ef.write_text("ALPHA=one\nBETA=two\n")
    result = run("diff", str(vault_path), str(ef), "--passphrase", PASS)
    assert result.returncode == 0


def test_diff_show_unchanged_flag(vault_path, dotenv_file):
    result = run(
        "diff", str(vault_path), str(dotenv_file),
        "--passphrase", PASS, "--show-unchanged",
    )
    assert "ALPHA" in result.stdout


def test_diff_wrong_passphrase_returns_nonzero(vault_path, dotenv_file):
    result = run("diff", str(vault_path), str(dotenv_file), "--passphrase", "wrong")
    assert result.returncode != 0


def test_diff_json_file(vault_path, json_file):
    result = run("diff", str(vault_path), str(json_file), "--passphrase", PASS)
    assert "DELTA" in result.stdout


def test_diff_missing_env_file_returns_nonzero(vault_path, tmp_path):
    """Passing a non-existent env file should exit with a non-zero return code."""
    missing = tmp_path / "nonexistent.env"
    result = run("diff", str(vault_path), str(missing), "--passphrase", PASS)
    assert result.returncode != 0
