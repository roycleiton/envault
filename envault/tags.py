"""Tag management for vault secrets."""
from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class TagError(Exception):
    """Raised when a tag operation fails."""


_TAG_META_PREFIX = "__tags__."


def _meta_key(secret_key: str) -> str:
    return f"{_TAG_META_PREFIX}{secret_key}"


def add_tag(vault: Vault, passphrase: str, secret_key: str, tag: str) -> List[str]:
    """Add *tag* to *secret_key*. Returns the updated tag list."""
    if not tag.strip():
        raise TagError("Tag must not be empty.")
    tags = get_tags(vault, passphrase, secret_key)
    if tag in tags:
        return tags
    tags.append(tag)
    meta = ",".join(tags)
    vault.set(passphrase, _meta_key(secret_key), meta)
    return tags


def remove_tag(vault: Vault, passphrase: str, secret_key: str, tag: str) -> List[str]:
    """Remove *tag* from *secret_key*. Returns the updated tag list."""
    tags = get_tags(vault, passphrase, secret_key)
    if tag not in tags:
        raise TagError(f"Tag '{tag}' not found on key '{secret_key}'.")
    tags.remove(tag)
    meta = ",".join(tags)
    if meta:
        vault.set(passphrase, _meta_key(secret_key), meta)
    else:
        try:
            vault.delete(passphrase, _meta_key(secret_key))
        except VaultError:
            pass
    return tags


def get_tags(vault: Vault, passphrase: str, secret_key: str) -> List[str]:
    """Return the list of tags for *secret_key* (may be empty)."""
    try:
        raw = vault.get(passphrase, _meta_key(secret_key))
        return [t for t in raw.split(",") if t]
    except VaultError:
        return []


def list_by_tag(
    vault: Vault, passphrase: str, tag: str
) -> List[str]:
    """Return all secret keys that carry *tag*."""
    results: List[str] = []
    for key in vault.keys(passphrase):
        if key.startswith(_TAG_META_PREFIX):
            continue
        if tag in get_tags(vault, passphrase, key):
            results.append(key)
    return sorted(results)


def all_tags(vault: Vault, passphrase: str) -> Dict[str, List[str]]:
    """Return a mapping of secret_key -> [tags] for all tagged secrets."""
    mapping: Dict[str, List[str]] = {}
    for key in vault.keys(passphrase):
        if key.startswith(_TAG_META_PREFIX):
            continue
        tags = get_tags(vault, passphrase, key)
        if tags:
            mapping[key] = tags
    return mapping
