"""Template rendering: substitute vault secrets into template strings."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from envault.vault import Vault

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


def render_string(
    template: str,
    vault: Vault,
    passphrase: str,
    *,
    strict: bool = True,
) -> str:
    """Replace ``{{ KEY }}`` placeholders with values from *vault*.

    Parameters
    ----------
    template:
        The template string containing ``{{ KEY }}`` placeholders.
    vault:
        An open :class:`~envault.vault.Vault` instance.
    passphrase:
        Passphrase used to decrypt vault values.
    strict:
        When *True* (default) raise :class:`TemplateError` for any
        placeholder whose key is not found in the vault.  When *False*
        unknown placeholders are left unchanged.
    """
    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        try:
            return vault.get(key, passphrase)
        except Exception:  # noqa: BLE001
            if strict:
                missing.append(key)
            return match.group(0)

    result = _PLACEHOLDER.sub(_replace, template)

    if missing:
        raise TemplateError(
            f"Template references unknown vault key(s): {', '.join(sorted(missing))}"
        )
    return result


def render_file(
    src: Path,
    vault: Vault,
    passphrase: str,
    dst: Optional[Path] = None,
    *,
    strict: bool = True,
) -> str:
    """Render *src* template file and optionally write output to *dst*.

    Returns the rendered string regardless of whether *dst* is provided.
    """
    if not src.exists():
        raise TemplateError(f"Template file not found: {src}")

    content = src.read_text(encoding="utf-8")
    rendered = render_string(content, vault, passphrase, strict=strict)

    if dst is not None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(rendered, encoding="utf-8")

    return rendered
