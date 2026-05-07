"""Policy enforcement: define and validate rules for secrets in a vault."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import Vault


class PolicyError(Exception):
    """Raised when policy operations fail."""


@dataclass
class PolicyViolation:
    key: str
    rule: str
    message: str
    severity: str = "error"  # "error" | "warning"


def _check_key_pattern(
    key: str, pattern: str
) -> Optional[PolicyViolation]:
    """Return a violation if *key* does not match the required regex pattern."""
    try:
        if not re.fullmatch(pattern, key):
            return PolicyViolation(
                key=key,
                rule="key_pattern",
                message=f"Key '{key}' does not match required pattern '{pattern}'",
            )
    except re.error as exc:
        raise PolicyError(f"Invalid key_pattern regex: {exc}") from exc
    return None


def _check_min_length(
    key: str, value: str, min_length: int
) -> Optional[PolicyViolation]:
    """Return a violation if *value* is shorter than *min_length*."""
    if len(value) < min_length:
        return PolicyViolation(
            key=key,
            rule="min_length",
            message=(
                f"Value for '{key}' is {len(value)} chars, "
                f"minimum is {min_length}"
            ),
            severity="warning",
        )
    return None


def _check_forbidden_keys(
    key: str, forbidden: List[str]
) -> Optional[PolicyViolation]:
    """Return a violation if *key* is in the forbidden list."""
    if key in forbidden:
        return PolicyViolation(
            key=key,
            rule="forbidden_keys",
            message=f"Key '{key}' is explicitly forbidden by policy",
        )
    return None


def enforce_policy(
    vault: Vault,
    passphrase: str,
    *,
    key_pattern: Optional[str] = None,
    min_length: int = 0,
    forbidden_keys: Optional[List[str]] = None,
) -> List[PolicyViolation]:
    """Run all enabled policy checks against every secret in *vault*.

    Returns a (possibly empty) list of :class:`PolicyViolation` objects.
    Raises :class:`PolicyError` on configuration problems.
    """
    forbidden_keys = forbidden_keys or []
    violations: List[PolicyViolation] = []

    keys = vault.list_keys()
    # Filter out internal meta-keys (prefixed with __)
    secret_keys = [k for k in keys if not k.startswith("__")]

    for key in secret_keys:
        value = vault.get(key, passphrase)

        if key_pattern is not None:
            v = _check_key_pattern(key, key_pattern)
            if v:
                violations.append(v)

        if min_length > 0:
            v = _check_min_length(key, value, min_length)
            if v:
                violations.append(v)

        if forbidden_keys:
            v = _check_forbidden_keys(key, forbidden_keys)
            if v:
                violations.append(v)

    return violations
