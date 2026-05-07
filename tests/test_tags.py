"""Tests for envault.tags."""
import pytest

from envault.vault import Vault, VaultError
from envault.tags import (
    TagError,
    add_tag,
    remove_tag,
    get_tags,
    list_by_tag,
    all_tags,
)

PASS = "hunter2"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.db", PASS)
    v.set(PASS, "DB_URL", "postgres://localhost/db")
    v.set(PASS, "API_KEY", "secret-key")
    v.set(PASS, "REDIS_URL", "redis://localhost")
    return v


def test_add_tag_returns_list(vault):
    tags = add_tag(vault, PASS, "DB_URL", "database")
    assert "database" in tags


def test_add_tag_persists(vault):
    add_tag(vault, PASS, "DB_URL", "database")
    assert "database" in get_tags(vault, PASS, "DB_URL")


def test_add_tag_idempotent(vault):
    add_tag(vault, PASS, "DB_URL", "database")
    tags = add_tag(vault, PASS, "DB_URL", "database")
    assert tags.count("database") == 1


def test_add_multiple_tags(vault):
    add_tag(vault, PASS, "DB_URL", "database")
    add_tag(vault, PASS, "DB_URL", "prod")
    tags = get_tags(vault, PASS, "DB_URL")
    assert "database" in tags
    assert "prod" in tags


def test_add_empty_tag_raises(vault):
    with pytest.raises(TagError):
        add_tag(vault, PASS, "DB_URL", "   ")


def test_remove_tag(vault):
    add_tag(vault, PASS, "DB_URL", "database")
    tags = remove_tag(vault, PASS, "DB_URL", "database")
    assert "database" not in tags


def test_remove_tag_not_present_raises(vault):
    with pytest.raises(TagError, match="not found"):
        remove_tag(vault, PASS, "DB_URL", "nonexistent")


def test_get_tags_empty_for_untagged(vault):
    assert get_tags(vault, PASS, "API_KEY") == []


def test_list_by_tag_returns_matching_keys(vault):
    add_tag(vault, PASS, "DB_URL", "infra")
    add_tag(vault, PASS, "REDIS_URL", "infra")
    keys = list_by_tag(vault, PASS, "infra")
    assert "DB_URL" in keys
    assert "REDIS_URL" in keys
    assert "API_KEY" not in keys


def test_list_by_tag_excludes_meta_keys(vault):
    add_tag(vault, PASS, "DB_URL", "infra")
    keys = list_by_tag(vault, PASS, "infra")
    assert all(not k.startswith("__tags__.") for k in keys)


def test_list_by_tag_sorted(vault):
    add_tag(vault, PASS, "REDIS_URL", "cache")
    add_tag(vault, PASS, "API_KEY", "cache")
    keys = list_by_tag(vault, PASS, "cache")
    assert keys == sorted(keys)


def test_all_tags_mapping(vault):
    add_tag(vault, PASS, "DB_URL", "database")
    add_tag(vault, PASS, "API_KEY", "external")
    mapping = all_tags(vault, PASS)
    assert mapping["DB_URL"] == ["database"]
    assert mapping["API_KEY"] == ["external"]
    assert "REDIS_URL" not in mapping


def test_all_tags_empty_vault(tmp_path):
    v = Vault(tmp_path / "empty.db", PASS)
    assert all_tags(v, PASS) == {}
