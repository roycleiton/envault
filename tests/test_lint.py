"""Tests for envault.lint."""
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.ttl import set_ttl
from envault.tags import add_tag
from envault.lint import lint_vault, LintIssue

PASS = "hunter2"


@pytest.fixture
def vault(tmp_path: Path) -> Vault:
    v = Vault(tmp_path / "vault.enc", PASS)
    v.set("API_KEY", "supersecretvalue123", PASS)
    v.set("DB_PASS", "short", PASS)
    v.set("WEAK_SECRET", "password", PASS)
    return v


def test_no_issues_clean_vault(tmp_path: Path):
    v = Vault(tmp_path / "vault.enc", PASS)
    v.set("GOOD_KEY", "a-very-long-random-value-xyz", PASS)
    set_ttl(v, "GOOD_KEY", PASS, days=30)
    issues = lint_vault(v, PASS, check_weak=True, check_ttl=True, check_tags=False)
    assert issues == []


def test_weak_value_detected(vault: Vault):
    issues = lint_vault(vault, PASS, check_weak=True, check_ttl=False)
    codes = [i.code for i in issues]
    assert "WEAK_VALUE" in codes


def test_weak_value_issue_has_error_severity(vault: Vault):
    issues = lint_vault(vault, PASS, check_weak=True, check_ttl=False)
    weak = [i for i in issues if i.code == "WEAK_VALUE"]
    assert all(i.severity == "error" for i in weak)


def test_short_value_detected(vault: Vault):
    issues = lint_vault(vault, PASS, check_weak=True, check_ttl=False)
    codes = [i.code for i in issues]
    assert "SHORT_VALUE" in codes


def test_missing_ttl_detected(vault: Vault):
    issues = lint_vault(vault, PASS, check_weak=False, check_ttl=True)
    codes = [i.code for i in issues]
    assert "NO_TTL" in codes


def test_ttl_set_clears_no_ttl_issue(tmp_path: Path):
    v = Vault(tmp_path / "vault.enc", PASS)
    v.set("MY_KEY", "longvaluexyz99", PASS)
    set_ttl(v, "MY_KEY", PASS, days=7)
    issues = lint_vault(v, PASS, check_weak=False, check_ttl=True)
    assert not any(i.code == "NO_TTL" for i in issues)


def test_no_tags_issue_when_check_tags_enabled(vault: Vault):
    issues = lint_vault(vault, PASS, check_weak=False, check_ttl=False, check_tags=True)
    codes = [i.code for i in issues]
    assert "NO_TAGS" in codes


def test_tag_set_clears_no_tags_issue(tmp_path: Path):
    v = Vault(tmp_path / "vault.enc", PASS)
    v.set("TAGGED_KEY", "somevalue123", PASS)
    add_tag(v, "TAGGED_KEY", PASS, "production")
    issues = lint_vault(v, PASS, check_weak=False, check_ttl=False, check_tags=True)
    assert not any(i.code == "NO_TAGS" for i in issues)


def test_lint_issue_has_key_and_message(vault: Vault):
    issues = lint_vault(vault, PASS, check_weak=True, check_ttl=False)
    for issue in issues:
        assert isinstance(issue, LintIssue)
        assert issue.key
        assert issue.message
        assert issue.code


def test_check_tags_disabled_by_default(vault: Vault):
    issues = lint_vault(vault, PASS, check_weak=False, check_ttl=False)
    assert not any(i.code == "NO_TAGS" for i in issues)
