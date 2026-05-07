"""Snapshot support: capture and restore vault state at a point in time."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List

from envault.vault import Vault, VaultError


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_dir(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".snapshots")


def _snapshot_path(vault_path: Path, label: str) -> Path:
    return _snapshot_dir(vault_path) / f"{label}.json"


def create_snapshot(vault_path: Path, passphrase: str, label: str | None = None) -> Path:
    """Decrypt the vault and save a plaintext snapshot (JSON) to disk.

    Returns the path to the created snapshot file.
    """
    vault = Vault(str(vault_path), passphrase)
    secrets = vault.all()

    if not label:
        label = str(int(time.time()))

    snap_dir = _snapshot_dir(vault_path)
    snap_dir.mkdir(parents=True, exist_ok=True)

    snap_path = _snapshot_path(vault_path, label)
    if snap_path.exists():
        raise SnapshotError(f"Snapshot '{label}' already exists at {snap_path}")

    payload = {"label": label, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "secrets": secrets}
    snap_path.write_text(json.dumps(payload, indent=2))
    return snap_path


def list_snapshots(vault_path: Path) -> List[str]:
    """Return labels of all available snapshots, sorted oldest-first."""
    snap_dir = _snapshot_dir(vault_path)
    if not snap_dir.exists():
        return []
    return sorted(p.stem for p in snap_dir.glob("*.json"))


def restore_snapshot(vault_path: Path, passphrase: str, label: str) -> int:
    """Overwrite vault contents with the secrets stored in *label* snapshot.

    Returns the number of secrets restored.
    """
    snap_path = _snapshot_path(vault_path, label)
    if not snap_path.exists():
        raise SnapshotError(f"Snapshot '{label}' not found")

    payload = json.loads(snap_path.read_text())
    secrets: dict = payload.get("secrets", {})

    vault = Vault(str(vault_path), passphrase)
    for key, value in secrets.items():
        vault.set(key, value)

    return len(secrets)


def delete_snapshot(vault_path: Path, label: str) -> None:
    """Remove a snapshot by label."""
    snap_path = _snapshot_path(vault_path, label)
    if not snap_path.exists():
        raise SnapshotError(f"Snapshot '{label}' not found")
    snap_path.unlink()
