"""CLI sub-command: rotate — change the vault passphrase."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.rotate import RotateError, rotate_passphrase


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the *rotate* sub-command to *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "rotate",
        help="Re-encrypt the vault under a new passphrase.",
    )
    parser.add_argument("vault", type=Path, help="Path to the vault file.")
    parser.add_argument(
        "--old-passphrase",
        metavar="PASSPHRASE",
        default=None,
        help="Current passphrase (prompted if omitted).",
    )
    parser.add_argument(
        "--new-passphrase",
        metavar="PASSPHRASE",
        default=None,
        help="New passphrase (prompted if omitted).",
    )
    parser.set_defaults(func=_cmd_rotate)


def _cmd_rotate(args: argparse.Namespace) -> int:
    old_passphrase = args.old_passphrase or getpass.getpass("Current passphrase: ")
    new_passphrase = args.new_passphrase or getpass.getpass("New passphrase: ")
    confirm = args.new_passphrase or getpass.getpass("Confirm new passphrase: ")

    if new_passphrase != confirm:
        print("error: passphrases do not match.", file=sys.stderr)
        return 1

    try:
        count = rotate_passphrase(args.vault, old_passphrase, new_passphrase)
    except RotateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Rotated passphrase for {count} secret(s) in '{args.vault}'.")
    return 0
