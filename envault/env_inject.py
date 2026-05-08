"""Inject vault secrets into a subprocess environment."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from envault.vault import Vault, VaultError


class InjectError(Exception):
    """Raised when secret injection fails."""


@dataclass
class InjectResult:
    injected: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    returncode: int = 0


def _collect_secrets(
    vault: Vault,
    passphrase: str,
    *,
    prefix: Optional[str] = None,
    keys: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    """Return a mapping of env-var name -> secret value from *vault*.

    If *keys* is given only those keys are collected.
    If *prefix* is given every key is prefixed before being added to the env.
    """
    all_keys = vault.list_keys() if keys is None else list(keys)
    secrets: Dict[str, str] = {}
    for k in all_keys:
        try:
            value = vault.get(k, passphrase)
        except VaultError as exc:
            raise InjectError(f"Failed to read key '{k}': {exc}") from exc
        env_name = f"{prefix}{k}" if prefix else k
        secrets[env_name] = value
    return secrets


def inject_and_run(
    vault: Vault,
    passphrase: str,
    command: Sequence[str],
    *,
    prefix: Optional[str] = None,
    keys: Optional[Sequence[str]] = None,
    override: bool = True,
) -> InjectResult:
    """Run *command* with vault secrets merged into its environment.

    Parameters
    ----------
    override:
        When *True* (default) vault values overwrite existing env vars.
        When *False* existing env vars are preserved.
    """
    if not command:
        raise InjectError("command must not be empty")

    secrets = _collect_secrets(vault, passphrase, prefix=prefix, keys=keys)
    env = os.environ.copy()
    injected: List[str] = []
    skipped: List[str] = []

    for name, value in secrets.items():
        if not override and name in env:
            skipped.append(name)
        else:
            env[name] = value
            injected.append(name)

    result = subprocess.run(list(command), env=env)  # noqa: S603
    return InjectResult(injected=injected, skipped=skipped, returncode=result.returncode)
