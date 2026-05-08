"""Tests for envault.history."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.history import (
    HistoryError,
    clear_history,
    get_history,
    record_change,
)

PASS = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "test.vault")
    v.set("MY_KEY", "supersecret", PASS)
    return v


def test_record_set_creates_entry(vault):
    record_change(vault, PASS, "MY_KEY", "set", value="supersecret")
    history = get_history(vault, PASS, "MY_KEY")
    assert len(history) == 1
    assert history[0]["action"] == "set"


def test_record_delete_creates_entry(vault):
    record_change(vault, PASS, "MY_KEY", "delete")
    history = get_history(vault, PASS, "MY_KEY")
    assert history[0]["action"] == "delete"


def test_entry_has_timestamp(vault):
    record_change(vault, PASS, "MY_KEY", "set", value="val")
    entry = get_history(vault, PASS, "MY_KEY")[0]
    assert "timestamp" in entry
    assert entry["timestamp"].endswith("+00:00")


def test_value_preview_masked(vault):
    record_change(vault, PASS, "MY_KEY", "set", value="supersecret")
    entry = get_history(vault, PASS, "MY_KEY")[0]
    assert "value_preview" in entry
    assert entry["value_preview"].endswith("****")
    assert "supersecret" not in entry["value_preview"]


def test_short_value_fully_masked(vault):
    record_change(vault, PASS, "MY_KEY", "set", value="ab")
    entry = get_history(vault, PASS, "MY_KEY")[0]
    assert entry["value_preview"] == "****"


def test_delete_entry_has_no_value_preview(vault):
    record_change(vault, PASS, "MY_KEY", "delete")
    entry = get_history(vault, PASS, "MY_KEY")[0]
    assert "value_preview" not in entry


def test_multiple_entries_accumulate(vault):
    record_change(vault, PASS, "MY_KEY", "set", value="v1")
    record_change(vault, PASS, "MY_KEY", "set", value="v2")
    record_change(vault, PASS, "MY_KEY", "delete")
    history = get_history(vault, PASS, "MY_KEY")
    assert len(history) == 3
    assert [e["action"] for e in history] == ["set", "set", "delete"]


def test_max_entries_enforced(vault):
    for i in range(10):
        record_change(vault, PASS, "MY_KEY", "set", value=f"v{i}", max_entries=5)
    history = get_history(vault, PASS, "MY_KEY")
    assert len(history) == 5


def test_get_history_missing_key_returns_empty(vault):
    history = get_history(vault, PASS, "NONEXISTENT")
    assert history == []


def test_clear_history_removes_entries(vault):
    record_change(vault, PASS, "MY_KEY", "set", value="v")
    clear_history(vault, PASS, "MY_KEY")
    assert get_history(vault, PASS, "MY_KEY") == []


def test_clear_history_missing_key_noop(vault):
    clear_history(vault, PASS, "GHOST")  # should not raise


def test_invalid_action_raises(vault):
    with pytest.raises(HistoryError, match="Invalid action"):
        record_change(vault, PASS, "MY_KEY", "update")
