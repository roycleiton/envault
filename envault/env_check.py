"""env_check.py — Compare vault secrets against the current process environment."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import Vault, VaultError


class EnvCheckError(Exception):
    """Raised when env-check cannot complete."""


@dataclass
class EnvCheckResult:
    key: str
    in_vault: bool
    in_env: bool
    value_matches: Optional[bool]  # None when either side is absent
    env_value: Optional[str] = field(default=None, repr=False)
    vault_value: Optional[str] = field(default=None, repr=False)

    @property
    def status(self) -> str:
        if not self.in_vault:
            return "env-only"
        if not self.in_env:
            return "missing"
        return "ok" if self.value_matches else "mismatch"


def check_env(
    vault: Vault,
    passphrase: str,
    env: Optional[dict] = None,
) -> List[EnvCheckResult]:
    """Compare every secret in *vault* against *env* (defaults to os.environ).

    Returns a list of :class:`EnvCheckResult` objects, one per vault key.
    Keys that are present in *env* but not in the vault are **not** reported
    (the vault is considered the source of truth).
    """
    import os

    if env is None:
        env = dict(os.environ)

    try:
        keys = vault.list()
    except VaultError as exc:
        raise EnvCheckError(f"Cannot read vault: {exc}") from exc

    results: List[EnvCheckResult] = []
    for key in sorted(keys):
        try:
            vault_val = vault.get(key, passphrase)
        except VaultError as exc:
            raise EnvCheckError(f"Cannot decrypt '{key}': {exc}") from exc

        in_env = key in env
        env_val = env.get(key)
        matches: Optional[bool] = (vault_val == env_val) if in_env else None

        results.append(
            EnvCheckResult(
                key=key,
                in_vault=True,
                in_env=in_env,
                value_matches=matches,
                env_value=env_val,
                vault_value=vault_val,
            )
        )

    return results
