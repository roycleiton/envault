"""CLI sub-command: envault import — import secrets from a file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault import import_secrets as imp
from envault.vault import Vault, VaultError


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the *import* sub-command to *subparsers*."""
    p: argparse.ArgumentParser = subparsers.add_parser(
        "import",
        help="Import secrets from a .env or JSON file into the vault.",
    )
    p.add_argument("file", help="Path to the source file.")
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["dotenv", "json"],
        default="dotenv",
        help="File format (default: dotenv).",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys (default: skip).",
    )
    p.set_defaults(func=_cmd_import)


def _cmd_import(args: argparse.Namespace) -> int:
    """Execute the import sub-command."""
    source = Path(args.file)
    if not source.exists():
        print(f"envault: import: file not found: {source}", file=sys.stderr)
        return 1

    try:
        vault = Vault(args.vault, args.passphrase)
        imported, skipped = imp.from_file(
            vault, source, fmt=args.fmt, overwrite=args.overwrite
        )
    except (VaultError, imp.ImportError) as exc:
        print(f"envault: import: {exc}", file=sys.stderr)
        return 1

    print(f"Imported {imported} secret(s), skipped {skipped} existing.")
    return 0
