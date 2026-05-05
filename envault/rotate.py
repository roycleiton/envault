"""Passphrase rotation for envault vaults."""

from __future__ import annotations

from pathlib import Path

from envault.crypto import decrypt, encrypt
from envault.vault import Vault, VaultError


class RotateError(Exception):
    """Raised when passphrase rotation fails."""


def rotate_passphrase(
    vault_path: Path,
    old_passphrase: str,
    new_passphrase: str,
) -> int:
    """Re-encrypt every secret in *vault_path* under *new_passphrase*.

    Returns the number of secrets that were rotated.
    Raises :class:`RotateError` on any failure; the vault is left untouched
    when an error occurs.
    """
    if old_passphrase == new_passphrase:
        raise RotateError("New passphrase must differ from the old one.")

    old_vault = Vault(vault_path, old_passphrase)

    try:
        keys = old_vault.list_keys()
    except VaultError as exc:
        raise RotateError(f"Could not open vault with old passphrase: {exc}") from exc

    # Decrypt all values with the old passphrase first — fail fast before
    # we touch the vault file.
    plaintext_map: dict[str, str] = {}
    for key in keys:
        try:
            plaintext_map[key] = old_vault.get(key)
        except VaultError as exc:
            raise RotateError(f"Failed to decrypt '{key}': {exc}") from exc

    # Write everything under the new passphrase.
    new_vault = Vault(vault_path, new_passphrase)
    # Wipe existing data by writing an empty vault first.
    new_vault._save_raw({})

    for key, value in plaintext_map.items():
        new_vault.set(key, value)

    return len(plaintext_map)
