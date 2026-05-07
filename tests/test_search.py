"""Tests for envault.search module."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.search import SearchError, SearchResult, search_vault

PASS = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.enc")
    v.set("DB_HOST", "localhost", PASS)
    v.set("DB_PORT", "5432", PASS)
    v.set("API_KEY", "secret-api-key", PASS)
    v.set("API_SECRET", "topsecret", PASS)
    v.set("DEBUG", "true", PASS)
    return v


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_no_criteria_raises(vault):
    with pytest.raises(SearchError, match="at least one"):
        search_vault(vault, PASS)


def test_invalid_key_regex_raises(vault):
    with pytest.raises(SearchError, match="Invalid key regex"):
        search_vault(vault, PASS, key_pattern="[invalid", regex=True)


def test_invalid_value_regex_raises(vault):
    with pytest.raises(SearchError, match="Invalid value regex"):
        search_vault(vault, PASS, value_substr="[invalid", regex=True)


# ---------------------------------------------------------------------------
# Key pattern matching
# ---------------------------------------------------------------------------

def test_glob_key_pattern_matches(vault):
    results = search_vault(vault, PASS, key_pattern="DB_*")
    keys = {r.key for r in results}
    assert keys == {"DB_HOST", "DB_PORT"}


def test_glob_key_case_insensitive_by_default(vault):
    results = search_vault(vault, PASS, key_pattern="api_*")
    keys = {r.key for r in results}
    assert keys == {"API_KEY", "API_SECRET"}


def test_glob_key_case_sensitive(vault):
    results = search_vault(vault, PASS, key_pattern="api_*", case_sensitive=True)
    assert results == []


def test_regex_key_pattern(vault):
    results = search_vault(vault, PASS, key_pattern=r"^DB_", regex=True)
    keys = {r.key for r in results}
    assert keys == {"DB_HOST", "DB_PORT"}


def test_match_source_is_key(vault):
    results = search_vault(vault, PASS, key_pattern="DEBUG")
    assert all(r.match_source == "key" for r in results)


# ---------------------------------------------------------------------------
# Value substring matching
# ---------------------------------------------------------------------------

def test_value_substr_matches(vault):
    results = search_vault(vault, PASS, value_substr="secret")
    keys = {r.key for r in results}
    assert keys == {"API_KEY", "API_SECRET"}


def test_value_substr_case_insensitive(vault):
    results = search_vault(vault, PASS, value_substr="SECRET")
    keys = {r.key for r in results}
    assert "API_SECRET" in keys


def test_value_regex_match(vault):
    results = search_vault(vault, PASS, value_substr=r"^\d+$", regex=True)
    keys = {r.key for r in results}
    assert keys == {"DB_PORT"}


def test_match_source_is_value(vault):
    results = search_vault(vault, PASS, value_substr="localhost")
    assert all(r.match_source == "value" for r in results)


# ---------------------------------------------------------------------------
# Combined criteria
# ---------------------------------------------------------------------------

def test_key_match_takes_priority_over_value(vault):
    """A key matched by key_pattern must not appear twice even if value also matches."""
    results = search_vault(vault, PASS, key_pattern="API_KEY", value_substr="secret")
    api_key_results = [r for r in results if r.key == "API_KEY"]
    assert len(api_key_results) == 1


def test_empty_vault_returns_empty_list(tmp_path):
    v = Vault(tmp_path / "empty.enc")
    results = search_vault(v, PASS, key_pattern="*")
    assert results == []


def test_result_contains_decrypted_value(vault):
    results = search_vault(vault, PASS, key_pattern="DEBUG")
    assert len(results) == 1
    assert results[0].value == "true"
