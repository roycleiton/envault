"""Tests for envault.diff module."""

from __future__ import annotations

import json
import pathlib

import pytest

from envault.vault import Vault
from envault.diff import diff_vaults, diff_vault_file, DiffError


PASS_A = "passphrase-a"
PASS_B = "passphrase-b"


@pytest.fixture()
def vault_a(tmp_path: pathlib.Path) -> Vault:
    v = Vault(str(tmp_path / "a.vault"))
    v.set("KEY1", "hello", PASS_A)
    v.set("KEY2", "world", PASS_A)
    v.set("SHARED", "same", PASS_A)
    return v


@pytest.fixture()
def vault_b(tmp_path: pathlib.Path) -> Vault:
    v = Vault(str(tmp_path / "b.vault"))
    v.set("KEY2", "changed!", PASS_B)
    v.set("KEY3", "new", PASS_B)
    v.set("SHARED", "same", PASS_B)
    return v


def test_diff_vaults_added(vault_a, vault_b):
    entries = {e.key: e for e in diff_vaults(vault_a, PASS_A, vault_b, PASS_B)}
    assert entries["KEY3"].status == "added"


def test_diff_vaults_removed(vault_a, vault_b):
    entries = {e.key: e for e in diff_vaults(vault_a, PASS_A, vault_b, PASS_B)}
    assert entries["KEY1"].status == "removed"


def test_diff_vaults_changed(vault_a, vault_b):
    entries = {e.key: e for e in diff_vaults(vault_a, PASS_A, vault_b, PASS_B)}
    assert entries["KEY2"].status == "changed"
    assert entries["KEY2"].left_value == "hello"
    assert entries["KEY2"].right_value == "changed!"


def test_diff_vaults_unchanged(vault_a, vault_b):
    entries = {e.key: e for e in diff_vaults(vault_a, PASS_A, vault_b, PASS_B)}
    assert entries["SHARED"].status == "unchanged"


def test_diff_vault_file_dotenv(vault_a, tmp_path):
    dotenv = tmp_path / "vars.env"
    dotenv.write_text('KEY1=hello\nKEY_NEW=brand_new\n')
    entries = {e.key: e for e in diff_vault_file(vault_a, PASS_A, str(dotenv))}
    assert entries["KEY_NEW"].status == "added"
    assert entries["KEY2"].status == "removed"
    assert entries["KEY1"].status == "unchanged"


def test_diff_vault_file_json(vault_a, tmp_path):
    jf = tmp_path / "vars.json"
    jf.write_text(json.dumps({"KEY1": "hello", "EXTRA": "val"}))
    entries = {e.key: e for e in diff_vault_file(vault_a, PASS_A, str(jf))}
    assert entries["EXTRA"].status == "added"


def test_diff_vault_file_missing_file(vault_a, tmp_path):
    with pytest.raises(DiffError, match="Could not read file"):
        diff_vault_file(vault_a, PASS_A, str(tmp_path / "no_such.env"))


def test_diff_results_sorted(vault_a, vault_b):
    entries = diff_vaults(vault_a, PASS_A, vault_b, PASS_B)
    keys = [e.key for e in entries]
    assert keys == sorted(keys)
