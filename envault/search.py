"""Search secrets in a vault by key pattern or value substring."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import List, Optional

from .vault import Vault, VaultError


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchResult:
    key: str
    value: str
    match_source: str  # 'key' | 'value'


def search_vault(
    vault: Vault,
    passphrase: str,
    *,
    key_pattern: Optional[str] = None,
    value_substr: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Return secrets whose key or value matches the given criteria.

    Args:
        vault: An open :class:`~envault.vault.Vault` instance.
        passphrase: Passphrase used to decrypt values.
        key_pattern: Glob (or regex when *regex* is True) pattern matched
            against secret keys.
        value_substr: Plain substring (or regex when *regex* is True) matched
            against decrypted values.
        regex: Treat *key_pattern* and *value_substr* as regular expressions.
        case_sensitive: Perform case-sensitive matching.

    Returns:
        A list of :class:`SearchResult` objects for every matching secret.

    Raises:
        SearchError: If neither *key_pattern* nor *value_substr* is provided,
            or if a regex pattern is invalid.
        VaultError: Propagated from the vault on decryption failure.
    """
    if key_pattern is None and value_substr is None:
        raise SearchError("Provide at least one of key_pattern or value_substr.")

    flags = 0 if case_sensitive else re.IGNORECASE

    if regex and key_pattern is not None:
        try:
            key_re = re.compile(key_pattern, flags)
        except re.error as exc:
            raise SearchError(f"Invalid key regex: {exc}") from exc
    else:
        key_re = None

    if regex and value_substr is not None:
        try:
            val_re = re.compile(value_substr, flags)
        except re.error as exc:
            raise SearchError(f"Invalid value regex: {exc}") from exc
    else:
        val_re = None

    results: List[SearchResult] = []

    for key in vault.list_keys():
        key_cmp = key if case_sensitive else key.lower()

        # --- key matching ---
        key_matched = False
        if key_pattern is not None:
            if regex:
                key_matched = bool(key_re.search(key))
            else:
                pat = key_pattern if case_sensitive else key_pattern.lower()
                key_matched = fnmatch.fnmatch(key_cmp, pat)

        if key_matched:
            value = vault.get(key, passphrase)
            results.append(SearchResult(key=key, value=value, match_source="key"))
            continue

        # --- value matching (only if not already added) ---
        if value_substr is not None:
            value = vault.get(key, passphrase)
            val_cmp = value if case_sensitive else value.lower()
            if regex:
                val_matched = bool(val_re.search(value))
            else:
                needle = value_substr if case_sensitive else value_substr.lower()
                val_matched = needle in val_cmp
            if val_matched:
                results.append(SearchResult(key=key, value=value, match_source="value"))

    return results
