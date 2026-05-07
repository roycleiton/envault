"""Lint vault secrets for common issues (weak values, missing TTL, untagged keys)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import Vault
from envault.ttl import get_ttl
from envault.tags import get_tags


class LintError(Exception):
    """Raised when lint cannot be performed."""


@dataclass
class LintIssue:
    key: str
    code: str
    message: str
    severity: str = "warning"  # "warning" | "error"


_WEAK_VALUES = {"password", "secret", "changeme", "admin", "12345", "123456", "test"}
_MIN_SECRET_LEN = 8


def _check_weak_value(key: str, value: str) -> Optional[LintIssue]:
    if value.strip().lower() in _WEAK_VALUES:
        return LintIssue(key=key, code="WEAK_VALUE",
                         message=f"'{key}' has a known-weak value.",
                         severity="error")
    if len(value) < _MIN_SECRET_LEN:
        return LintIssue(key=key, code="SHORT_VALUE",
                         message=f"'{key}' value is shorter than {_MIN_SECRET_LEN} characters.",
                         severity="warning")
    return None


def _check_missing_ttl(key: str, vault: Vault, passphrase: str) -> Optional[LintIssue]:
    if get_ttl(vault, key, passphrase) is None:
        return LintIssue(key=key, code="NO_TTL",
                         message=f"'{key}' has no TTL set.",
                         severity="warning")
    return None


def _check_missing_tags(key: str, vault: Vault, passphrase: str) -> Optional[LintIssue]:
    if not get_tags(vault, key, passphrase):
        return LintIssue(key=key, code="NO_TAGS",
                         message=f"'{key}' has no tags.",
                         severity="warning")
    return None


def lint_vault(
    vault: Vault,
    passphrase: str,
    *,
    check_weak: bool = True,
    check_ttl: bool = True,
    check_tags: bool = False,
) -> List[LintIssue]:
    """Return a list of LintIssue for every secret in *vault*."""
    issues: List[LintIssue] = []
    keys = vault.list(passphrase)
    for key in keys:
        value = vault.get(key, passphrase)
        if check_weak:
            issue = _check_weak_value(key, value)
            if issue:
                issues.append(issue)
        if check_ttl:
            issue = _check_missing_ttl(key, vault, passphrase)
            if issue:
                issues.append(issue)
        if check_tags:
            issue = _check_missing_tags(key, vault, passphrase)
            if issue:
                issues.append(issue)
    return issues
