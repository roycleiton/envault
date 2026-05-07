"""Tests for envault.snapshot."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    delete_snapshot,
)

PASS = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.env"), PASS)
    v.set("DB_URL", "postgres://localhost/db")
    v.set("SECRET_KEY", "abc123")
    return tmp_path / "vault.env"


def test_create_snapshot_returns_path(vault):
    path = create_snapshot(vault, PASS, label="v1")
    assert path.exists()
    assert path.suffix == ".json"


def test_snapshot_contains_secrets(vault):
    path = create_snapshot(vault, PASS, label="v1")
    data = json.loads(path.read_text())
    assert data["secrets"]["DB_URL"] == "postgres://localhost/db"
    assert data["secrets"]["SECRET_KEY"] == "abc123"


def test_snapshot_has_metadata(vault):
    path = create_snapshot(vault, PASS, label="v1")
    data = json.loads(path.read_text())
    assert data["label"] == "v1"
    assert "created_at" in data


def test_create_snapshot_auto_label(vault):
    path = create_snapshot(vault, PASS)
    assert path.exists()
    # auto label is a unix timestamp string
    assert path.stem.isdigit()


def test_create_duplicate_label_raises(vault):
    create_snapshot(vault, PASS, label="v1")
    with pytest.raises(SnapshotError, match="already exists"):
        create_snapshot(vault, PASS, label="v1")


def test_list_snapshots_empty(vault):
    assert list_snapshots(vault) == []


def test_list_snapshots_returns_labels(vault):
    create_snapshot(vault, PASS, label="alpha")
    create_snapshot(vault, PASS, label="beta")
    labels = list_snapshots(vault)
    assert "alpha" in labels
    assert "beta" in labels


def test_restore_snapshot(vault, tmp_path):
    create_snapshot(vault, PASS, label="v1")
    # Overwrite a key in the vault
    v = Vault(str(vault), PASS)
    v.set("DB_URL", "changed")
    # Restore
    count = restore_snapshot(vault, PASS, label="v1")
    assert count == 2
    v2 = Vault(str(vault), PASS)
    assert v2.get("DB_URL") == "postgres://localhost/db"


def test_restore_missing_label_raises(vault):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(vault, PASS, label="ghost")


def test_delete_snapshot(vault):
    create_snapshot(vault, PASS, label="v1")
    delete_snapshot(vault, label="v1")
    assert "v1" not in list_snapshots(vault)


def test_delete_missing_snapshot_raises(vault):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot(vault, label="nope")
