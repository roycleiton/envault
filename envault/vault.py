"""Vault module for storing and retrieving encrypted environment variables."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import decrypt, encrypt

DEFAULT_VAULT_PATH = Path(".envault")


class VaultError(Exception):
    """Raised when vault operations fail."""


class Vault:
    """Manages a local encrypted vault of environment variables."""

    def __init__(self, path: Path = DEFAULT_VAULT_PATH) -> None:
        self.path = Path(path)

    def _load_raw(self) -> Dict[str, str]:
        """Load the raw encrypted entries from disk."""
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            raise VaultError(f"Failed to read vault at {self.path}: {exc}") from exc

    def _save_raw(self, data: Dict[str, str]) -> None:
        """Persist the raw encrypted entries to disk."""
        try:
            with self.path.open("w") as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            raise VaultError(f"Failed to write vault at {self.path}: {exc}") from exc

    def set(self, key: str, value: str, passphrase: str) -> None:
        """Encrypt and store an environment variable."""
        if not key:
            raise VaultError("Key must not be empty.")
        data = self._load_raw()
        data[key] = encrypt(value, passphrase)
        self._save_raw(data)

    def get(self, key: str, passphrase: str) -> str:
        """Retrieve and decrypt an environment variable."""
        data = self._load_raw()
        if key not in data:
            raise VaultError(f"Key '{key}' not found in vault.")
        return decrypt(data[key], passphrase)

    def delete(self, key: str) -> None:
        """Remove an environment variable from the vault."""
        data = self._load_raw()
        if key not in data:
            raise VaultError(f"Key '{key}' not found in vault.")
        del data[key]
        self._save_raw(data)

    def list_keys(self) -> list:
        """Return all stored keys (names only, values stay encrypted)."""
        return sorted(self._load_raw().keys())

    def export(self, passphrase: str) -> Dict[str, str]:
        """Decrypt and return all variables as a plain dictionary."""
        data = self._load_raw()
        return {key: decrypt(token, passphrase) for key, token in data.items()}
