"""TTL (time-to-live) support for vault secrets.

Secrets can be given an expiry timestamp; expired secrets are flagged
on read and can be purged in bulk.
"""
from __future__ import annotations

import datetime
from typing import List, Optional

from envault.vault import Vault, VaultError

_TTL_META_PREFIX = "__ttl__:"


class TTLError(VaultError):
    """Raised for TTL-related failures."""


def _meta_key(secret_key: str) -> str:
    return f"{_TTL_META_PREFIX}{secret_key}"


def set_ttl(vault: Vault, key: str, expires_at: datetime.datetime) -> None:
    """Attach an expiry timestamp (UTC) to *key*."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    vault.set(_meta_key(key), expires_at.isoformat())


def get_ttl(vault: Vault, key: str) -> Optional[datetime.datetime]:
    """Return the expiry datetime for *key*, or None if none is set."""
    try:
        raw = vault.get(_meta_key(key))
    except VaultError:
        return None
    return datetime.datetime.fromisoformat(raw)


def is_expired(vault: Vault, key: str) -> bool:
    """Return True if *key* has an expiry that is in the past."""
    ttl = get_ttl(vault, key)
    if ttl is None:
        return False
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    return now >= ttl


def clear_ttl(vault: Vault, key: str) -> None:
    """Remove the expiry for *key* (no-op if none exists)."""
    mk = _meta_key(key)
    try:
        vault.delete(mk)
    except VaultError:
        pass


def purge_expired(vault: Vault) -> List[str]:
    """Delete all secrets whose TTL has elapsed.

    Returns the list of deleted keys.
    """
    deleted: List[str] = []
    for key in vault.list():
        if key.startswith(_TTL_META_PREFIX):
            continue
        if is_expired(vault, key):
            vault.delete(key)
            clear_ttl(vault, key)
            deleted.append(key)
    return deleted
