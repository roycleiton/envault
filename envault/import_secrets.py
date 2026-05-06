"""Import secrets into a vault from external formats (dotenv, JSON)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Tuple


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env file into a dict, skipping comments and blank lines."""
    result: Dict[str, str] = {}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(
            r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(["\']?)(.*)\2', line
        )
        if not match:
            raise ImportError(f"Invalid .env syntax on line {lineno}: {raw!r}")
        key, _quote, value = match.group(1), match.group(2), match.group(3)
        result[key] = value
    return result


def _parse_json(text: str) -> Dict[str, str]:
    """Parse a JSON object of string key/value pairs."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object.")
    result: Dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ImportError(
                f"All JSON keys and values must be strings; got {k!r}: {v!r}"
            )
        result[k] = v
    return result


def from_file(
    vault,
    path: Path | str,
    *,
    fmt: str = "dotenv",
    overwrite: bool = False,
) -> Tuple[int, int]:
    """Import secrets from *path* into *vault*.

    Returns (imported_count, skipped_count).
    Raises ImportError on parse failures.
    """
    text = Path(path).read_text(encoding="utf-8")
    parsers = {"dotenv": _parse_dotenv, "json": _parse_json}
    if fmt not in parsers:
        raise ImportError(f"Unknown format {fmt!r}. Choose from: {list(parsers)}.")
    secrets = parsers[fmt](text)

    imported = skipped = 0
    for key, value in secrets.items():
        try:
            existing = vault.get(key)
        except Exception:
            existing = None
        if existing is not None and not overwrite:
            skipped += 1
            continue
        vault.set(key, value)
        imported += 1
    return imported, skipped
