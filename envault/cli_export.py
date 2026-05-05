"""CLI sub-command: envault export.

Adds ``export`` to the argument parser and wires it to :mod:`envault.export`.
This module is imported by ``envault/cli.py``.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, _SubParsersAction
from getpass import getpass
from pathlib import Path

from envault.export import export, ExportError, SUPPORTED_FORMATS
from envault.vault import Vault, VaultError


def register(subparsers: _SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *export* sub-command onto *subparsers*."""
    parser: ArgumentParser = subparsers.add_parser(
        "export",
        help="Export all vault variables to stdout in a chosen format.",
    )
    parser.add_argument(
        "--format",
        "-f",
        dest="fmt",
        choices=SUPPORTED_FORMATS,
        default="dotenv",
        help="Output format (default: dotenv).",
    )
    parser.add_argument(
        "--vault",
        default=".envault",
        metavar="FILE",
        help="Path to the vault file (default: .envault).",
    )
    parser.set_defaults(func=_cmd_export)


def _cmd_export(args) -> int:  # type: ignore[no-untyped-def]
    """Handler for the *export* sub-command."""
    passphrase = getpass("Passphrase: ")
    vault = Vault(path=Path(args.vault), passphrase=passphrase)

    try:
        secrets = vault.all()
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        output = export(secrets, args.fmt)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(output)
    return 0
