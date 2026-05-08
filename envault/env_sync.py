"""Sync secrets from a vault to a remote provider (e.g. environment file or shell export)."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class SyncError(Exception):
    """Raised when a sync operation fails."""


@dataclass
class SyncResult:
    pushed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def sync_to_env(vault_path: Path, passphrase: str, keys: Optional[List[str]] = None) -> SyncResult:
    """Sync secrets from the vault into the current process environment.

    Args:
        vault_path: Path to the vault file.
        passphrase: Passphrase to unlock the vault.
        keys: Optional list of keys to sync; if None, all keys are synced.

    Returns:
        SyncResult describing which keys were pushed, skipped, or errored.
    """
    result = SyncResult()
    try:
        vault = Vault(vault_path, passphrase)
        all_keys = vault.list()
    except VaultError as exc:
        raise SyncError(f"Failed to open vault: {exc}") from exc

    target_keys = keys if keys is not None else all_keys

    for key in target_keys:
        if key.startswith("__"):
            result.skipped.append(key)
            continue
        try:
            value = vault.get(key)
            os.environ[key] = value
            result.pushed.append(key)
        except VaultError as exc:
            result.errors.append(f"{key}: {exc}")
        except KeyError:
            result.errors.append(f"{key}: not found in vault")

    return result


def sync_to_dotenv(vault_path: Path, passphrase: str, dest: Path, overwrite: bool = False) -> SyncResult:
    """Write secrets from the vault into a .env file.

    Args:
        vault_path: Path to the vault file.
        passphrase: Passphrase to unlock the vault.
        dest: Destination .env file path.
        overwrite: If False, existing keys in the .env file are not overwritten.

    Returns:
        SyncResult describing which keys were pushed, skipped, or errored.
    """
    result = SyncResult()
    try:
        vault = Vault(vault_path, passphrase)
        all_keys = vault.list()
    except VaultError as exc:
        raise SyncError(f"Failed to open vault: {exc}") from exc

    existing: Dict[str, str] = {}
    if dest.exists():
        for line in dest.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()

    lines: List[str] = []
    for key in all_keys:
        if key.startswith("__"):
            result.skipped.append(key)
            continue
        if not overwrite and key in existing:
            result.skipped.append(key)
            continue
        try:
            value = vault.get(key)
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
            result.pushed.append(key)
        except VaultError as exc:
            result.errors.append(f"{key}: {exc}")

    if lines:
        with dest.open("a") as fh:
            fh.write("\n".join(lines) + "\n")

    return result
