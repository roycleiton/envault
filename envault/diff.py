"""Diff secrets between two vaults or a vault and a dotenv file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from envault.vault import Vault
from envault.import_secrets import _parse_dotenv, _parse_json


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    left_value: Optional[str] = None
    right_value: Optional[str] = None


def _load_external(path: str) -> Dict[str, str]:
    """Load key/value pairs from a .env or .json file."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    if path.endswith(".json"):
        return _parse_json(raw)
    return _parse_dotenv(raw)


def diff_vaults(
    vault_a: Vault,
    passphrase_a: str,
    vault_b: Vault,
    passphrase_b: str,
) -> List[DiffEntry]:
    """Compare all secrets between two Vault instances."""
    left = vault_a.all(passphrase_a)
    right = vault_b.all(passphrase_b)
    return _compare(left, right)


def diff_vault_file(
    vault: Vault,
    passphrase: str,
    file_path: str,
) -> List[DiffEntry]:
    """Compare vault secrets against an external .env or .json file."""
    try:
        left = vault.all(passphrase)
    except Exception as exc:  # noqa: BLE001
        raise DiffError(f"Could not read vault: {exc}") from exc
    try:
        right = _load_external(file_path)
    except (OSError, ValueError) as exc:
        raise DiffError(f"Could not read file '{file_path}': {exc}") from exc
    return _compare(left, right)


def _compare(
    left: Dict[str, str],
    right: Dict[str, str],
) -> List[DiffEntry]:
    """Produce a sorted list of DiffEntry items."""
    all_keys = sorted(set(left) | set(right))
    entries: List[DiffEntry] = []
    for key in all_keys:
        in_left = key in left
        in_right = key in right
        if in_left and not in_right:
            entries.append(DiffEntry(key, "removed", left[key], None))
        elif in_right and not in_left:
            entries.append(DiffEntry(key, "added", None, right[key]))
        elif left[key] == right[key]:
            entries.append(DiffEntry(key, "unchanged", left[key], right[key]))
        else:
            entries.append(DiffEntry(key, "changed", left[key], right[key]))
    return entries
