"""Export vault contents to various shell-compatible formats."""

from __future__ import annotations

from typing import Dict


SUPPORTED_FORMATS = ("dotenv", "shell", "json")


class ExportError(Exception):
    """Raised when an export operation fails."""


def _quote_shell(value: str) -> str:
    """Single-quote a value for safe shell export, escaping inner single quotes."""
    escaped = value.replace("'", "'\"'\"'")
    return f"'{escaped}'"


def to_dotenv(secrets: Dict[str, str]) -> str:
    """Render secrets as a .env file (KEY=VALUE, double-quoted)."""
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def to_shell(secrets: Dict[str, str]) -> str:
    """Render secrets as export statements for POSIX shells."""
    lines = []
    for key, value in sorted(secrets.items()):
        lines.append(f"export {key}={_quote_shell(value)}")
    return "\n".join(lines) + ("\n" if lines else "")


def to_json(secrets: Dict[str, str]) -> str:
    """Render secrets as a JSON object."""
    import json
    return json.dumps(secrets, indent=2, sort_keys=True) + "\n"


def export(secrets: Dict[str, str], fmt: str) -> str:
    """Export *secrets* in the requested *fmt*.

    Parameters
    ----------
    secrets:
        Mapping of variable names to plaintext values.
    fmt:
        One of ``'dotenv'``, ``'shell'``, or ``'json'``.

    Raises
    ------
    ExportError
        If *fmt* is not a supported format.
    """
    if fmt == "dotenv":
        return to_dotenv(secrets)
    if fmt == "shell":
        return to_shell(secrets)
    if fmt == "json":
        return to_json(secrets)
    raise ExportError(
        f"Unsupported format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
    )
