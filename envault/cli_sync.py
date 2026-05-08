"""CLI subcommand: envault sync — sync secrets to environment or .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.env_sync import SyncError, sync_to_dotenv, sync_to_env


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "sync",
        help="Sync secrets from the vault to the current environment or a .env file.",
    )
    p.add_argument("vault", help="Path to the vault file.")
    p.add_argument("passphrase", help="Vault passphrase.")
    p.add_argument(
        "--to",
        choices=["env", "dotenv"],
        default="env",
        dest="target",
        help="Sync target: 'env' (current process) or 'dotenv' (write .env file).",
    )
    p.add_argument(
        "--output",
        default=".env",
        help="Destination .env file path (only used with --to dotenv). Default: .env",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys in the destination .env file.",
    )
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to sync (default: all).",
    )
    p.set_defaults(func=_cmd_sync)


def _cmd_sync(args: argparse.Namespace) -> int:
    vault_path = Path(args.vault)

    try:
        if args.target == "dotenv":
            result = sync_to_dotenv(
                vault_path,
                args.passphrase,
                dest=Path(args.output),
                overwrite=args.overwrite,
            )
        else:
            result = sync_to_env(vault_path, args.passphrase, keys=args.keys)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for key in result.pushed:
        print(f"synced  {key}")
    for key in result.skipped:
        print(f"skipped {key}")
    for msg in result.errors:
        print(f"error   {msg}", file=sys.stderr)

    if not result.success:
        return 1

    total = len(result.pushed)
    print(f"\nDone. {total} secret(s) synced.")
    return 0
