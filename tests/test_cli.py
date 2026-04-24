"""Tests for the envault CLI."""

import pytest
from pathlib import Path

from envault.cli import main


PASSPHRASE = "cli-test-secret"


@pytest.fixture
def vault_path(tmp_path) -> str:
    return str(tmp_path / "test.envault")


def run(*args, vault, passphrase=PASSPHRASE):
    """Helper to invoke main() with common flags."""
    return main(["--vault", vault, "--passphrase", passphrase, *args])


def test_set_and_get_roundtrip(vault_path):
    assert run("set", "MY_KEY", "hello", vault=vault_path) == 0
    assert run("get", "MY_KEY", vault=vault_path) == 0


def test_get_prints_value(vault_path, capsys):
    run("set", "TOKEN", "abc123", vault=vault_path)
    run("get", "TOKEN", vault=vault_path)
    captured = capsys.readouterr()
    assert captured.out.strip() == "abc123"


def test_get_missing_key_returns_nonzero(vault_path):
    assert run("get", "MISSING", vault=vault_path) == 1


def test_get_missing_key_prints_error(vault_path, capsys):
    run("get", "MISSING", vault=vault_path)
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_set_creates_vault_file(vault_path):
    run("set", "X", "1", vault=vault_path)
    assert Path(vault_path).exists()


def test_list_shows_keys(vault_path, capsys):
    run("set", "ALPHA", "1", vault=vault_path)
    run("set", "BETA", "2", vault=vault_path)
    run("list", vault=vault_path)
    captured = capsys.readouterr()
    assert "ALPHA" in captured.out
    assert "BETA" in captured.out


def test_list_empty_vault(vault_path, capsys):
    run("list", vault=vault_path)
    captured = capsys.readouterr()
    assert "empty" in captured.out


def test_delete_removes_key(vault_path, capsys):
    run("set", "TO_DELETE", "bye", vault=vault_path)
    run("delete", "TO_DELETE", vault=vault_path)
    run("list", vault=vault_path)
    captured = capsys.readouterr()
    assert "TO_DELETE" not in captured.out


def test_wrong_passphrase_returns_nonzero(vault_path):
    run("set", "SECRET", "value", vault=vault_path)
    result = run("get", "SECRET", vault=vault_path, passphrase="wrong-passphrase")
    assert result == 1


def test_wrong_passphrase_prints_error(vault_path, capsys):
    run("set", "SECRET", "value", vault=vault_path)
    run("get", "SECRET", vault=vault_path, passphrase="wrong-passphrase")
    captured = capsys.readouterr()
    assert "Error" in captured.err
