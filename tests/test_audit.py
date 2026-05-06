"""Tests for envault.audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import AuditError, clear, read, record


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


def test_record_creates_audit_file(vault_path: Path) -> None:
    record(vault_path, "set", key="DB_URL")
    audit_file = vault_path.with_suffix(".audit.json")
    assert audit_file.exists()


def test_record_entry_has_required_fields(vault_path: Path) -> None:
    record(vault_path, "set", key="API_KEY")
    entries = read(vault_path)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["action"] == "set"
    assert entry["key"] == "API_KEY"
    assert "ts" in entry


def test_record_without_key(vault_path: Path) -> None:
    record(vault_path, "rotate")
    entries = read(vault_path)
    assert entries[0]["action"] == "rotate"
    assert "key" not in entries[0]


def test_record_with_extra_fields(vault_path: Path) -> None:
    record(vault_path, "export", extra={"format": "dotenv"})
    entries = read(vault_path)
    assert entries[0]["format"] == "dotenv"


def test_multiple_records_are_appended(vault_path: Path) -> None:
    record(vault_path, "set", key="FOO")
    record(vault_path, "set", key="BAR")
    record(vault_path, "delete", key="FOO")
    entries = read(vault_path)
    assert len(entries) == 3
    assert entries[0]["key"] == "FOO"
    assert entries[2]["action"] == "delete"


def test_read_returns_empty_list_when_no_log(vault_path: Path) -> None:
    entries = read(vault_path)
    assert entries == []


def test_clear_removes_audit_file(vault_path: Path) -> None:
    record(vault_path, "set", key="X")
    clear(vault_path)
    assert not vault_path.with_suffix(".audit.json").exists()


def test_clear_is_noop_when_no_file(vault_path: Path) -> None:
    # Should not raise even if the file does not exist.
    clear(vault_path)


def test_read_raises_on_corrupted_log(vault_path: Path) -> None:
    audit_file = vault_path.with_suffix(".audit.json")
    audit_file.write_text("not valid json", encoding="utf-8")
    with pytest.raises(AuditError):
        read(vault_path)


def test_audit_log_is_valid_json(vault_path: Path) -> None:
    record(vault_path, "set", key="SECRET")
    raw = vault_path.with_suffix(".audit.json").read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert isinstance(parsed, list)
