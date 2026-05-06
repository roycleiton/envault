"""Tests for envault/import_secrets.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.vault import Vault
from envault import import_secrets as imp


PASSPHRASE = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    return Vault(tmp_path / "test.vault", PASSPHRASE)


@pytest.fixture()
def dotenv_file(tmp_path):
    content = 'DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY="abc123"\n'
    p = tmp_path / ".env"
    p.write_text(content)
    return p


@pytest.fixture()
def json_file(tmp_path):
    data = {"API_KEY": "xyz", "REGION": "us-east-1"}
    p = tmp_path / "secrets.json"
    p.write_text(json.dumps(data))
    return p


def test_import_dotenv_imports_all_keys(vault, dotenv_file):
    imported, skipped = imp.from_file(vault, dotenv_file, fmt="dotenv")
    assert imported == 3
    assert skipped == 0


def test_import_dotenv_values_correct(vault, dotenv_file):
    imp.from_file(vault, dotenv_file, fmt="dotenv")
    assert vault.get("DB_HOST") == "localhost"
    assert vault.get("DB_PORT") == "5432"
    assert vault.get("SECRET_KEY") == "abc123"


def test_import_json_imports_all_keys(vault, json_file):
    imported, skipped = imp.from_file(vault, json_file, fmt="json")
    assert imported == 2
    assert skipped == 0


def test_import_json_values_correct(vault, json_file):
    imp.from_file(vault, json_file, fmt="json")
    assert vault.get("API_KEY") == "xyz"
    assert vault.get("REGION") == "us-east-1"


def test_skip_existing_keys_by_default(vault, dotenv_file):
    vault.set("DB_HOST", "original")
    imported, skipped = imp.from_file(vault, dotenv_file, fmt="dotenv")
    assert skipped == 1
    assert vault.get("DB_HOST") == "original"


def test_overwrite_flag_replaces_existing(vault, dotenv_file):
    vault.set("DB_HOST", "original")
    imp.from_file(vault, dotenv_file, fmt="dotenv", overwrite=True)
    assert vault.get("DB_HOST") == "localhost"


def test_invalid_dotenv_raises(vault, tmp_path):
    bad = tmp_path / "bad.env"
    bad.write_text("THIS IS NOT VALID\n")
    with pytest.raises(imp.ImportError, match="Invalid .env syntax"):
        imp.from_file(vault, bad, fmt="dotenv")


def test_invalid_json_raises(vault, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    with pytest.raises(imp.ImportError, match="Invalid JSON"):
        imp.from_file(vault, bad, fmt="json")


def test_json_non_string_values_raise(vault, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"PORT": 8080}))
    with pytest.raises(imp.ImportError, match="must be strings"):
        imp.from_file(vault, bad, fmt="json")


def test_unknown_format_raises(vault, dotenv_file):
    with pytest.raises(imp.ImportError, match="Unknown format"):
        imp.from_file(vault, dotenv_file, fmt="xml")
