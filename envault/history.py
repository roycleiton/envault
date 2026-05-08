"""Track a change history (set/delete) per secret key inside the vault."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from envault.vault import Vault, VaultError

_HISTORY_PREFIX = "__history__."
_MAX_ENTRIES = 50


class HistoryError(Exception):
    """Raised when a history operation fails."""


def _meta_key(key: str) -> str:
    return f"{_HISTORY_PREFIX}{key}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_change(
    vault: Vault,
    passphrase: str,
    key: str,
    action: str,
    value: str | None = None,
    *,
    max_entries: int = _MAX_ENTRIES,
) -> None:
    """Append a change entry for *key* to its history log.

    *action* should be ``'set'`` or ``'delete'``.
    """
    if action not in ("set", "delete"):
        raise HistoryError(f"Invalid action: {action!r}. Must be 'set' or 'delete'.")

    meta = _meta_key(key)
    try:
        raw = vault.get(meta, passphrase)
        entries: list[dict[str, Any]] = json.loads(raw)
    except VaultError:
        entries = []
    except json.JSONDecodeError as exc:
        raise HistoryError(f"Corrupted history for key {key!r}") from exc

    entry: dict[str, Any] = {"action": action, "timestamp": _now_iso()}
    if value is not None and action == "set":
        entry["value_preview"] = value[:4] + "****" if len(value) > 4 else "****"

    entries.append(entry)
    if len(entries) > max_entries:
        entries = entries[-max_entries:]

    vault.set(meta, json.dumps(entries), passphrase)


def get_history(
    vault: Vault,
    passphrase: str,
    key: str,
) -> list[dict[str, Any]]:
    """Return the list of change entries for *key*, oldest first."""
    meta = _meta_key(key)
    try:
        raw = vault.get(meta, passphrase)
        return json.loads(raw)
    except VaultError:
        return []
    except json.JSONDecodeError as exc:
        raise HistoryError(f"Corrupted history for key {key!r}") from exc


def clear_history(vault: Vault, passphrase: str, key: str) -> None:
    """Remove the history log for *key*."""
    meta = _meta_key(key)
    try:
        vault.delete(meta, passphrase)
    except VaultError:
        pass
