"""Audit log for vault operations."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_FILE_SUFFIX = ".audit.json"


class AuditError(Exception):
    """Raised when the audit log cannot be read or written."""


def _audit_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(AUDIT_FILE_SUFFIX)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record(
    vault_path: Path,
    action: str,
    key: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """Append an audit entry to the log file next to *vault_path*."""
    entry: dict = {"ts": _now_iso(), "action": action}
    if key is not None:
        entry["key"] = key
    if extra:
        entry.update(extra)

    log_path = _audit_path(vault_path)
    entries = _read_entries(log_path)
    entries.append(entry)
    try:
        log_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise AuditError(f"Cannot write audit log: {exc}") from exc


def _read_entries(log_path: Path) -> List[dict]:
    if not log_path.exists():
        return []
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise AuditError(f"Cannot read audit log: {exc}") from exc


def read(vault_path: Path) -> List[dict]:
    """Return all audit entries for *vault_path* as a list of dicts."""
    return _read_entries(_audit_path(vault_path))


def clear(vault_path: Path) -> None:
    """Remove the audit log file for *vault_path* if it exists."""
    log_path = _audit_path(vault_path)
    try:
        if log_path.exists():
            log_path.unlink()
    except OSError as exc:
        raise AuditError(f"Cannot clear audit log: {exc}") from exc
