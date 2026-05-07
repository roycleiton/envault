"""Entry-point: build the argument parser and dispatch subcommands."""

from __future__ import annotations

import argparse
import sys

from envault import cli_export, cli_rotate, cli_import, cli_diff, cli_tags, cli_snapshot
from envault.vault import Vault, VaultError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Securely manage and sync environment variables.",
    )
    parser.add_argument("--vault", default=".envault", help="Path to vault file")
    parser.add_argument("--passphrase", required=True, help="Vault passphrase")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # set
    p_set = subparsers.add_parser("set", help="Store a secret")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.set_defaults(func=_cmd_set)

    # get
    p_get = subparsers.add_parser("get", help="Retrieve a secret")
    p_get.add_argument("key")
    p_get.set_defaults(func=_cmd_get)

    # delete
    p_del = subparsers.add_parser("delete", help="Remove a secret")
    p_del.add_argument("key")
    p_del.set_defaults(func=_cmd_delete)

    # list
    p_list = subparsers.add_parser("list", help="List all secret keys")
    p_list.set_defaults(func=_cmd_list)

    # plugin subcommands
    cli_export.register(subparsers)
    cli_rotate.register(subparsers)
    cli_import.register(subparsers)
    cli_diff.register(subparsers)
    cli_tags.register(subparsers)
    cli_snapshot.register(subparsers)

    return parser


def _cmd_set(args: argparse.Namespace) -> int:
    try:
        vault = Vault(args.vault, args.passphrase)
        vault.set(args.key, args.value)
        print(f"Set '{args.key}'.")
        return 0
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _cmd_get(args: argparse.Namespace) -> int:
    try:
        vault = Vault(args.vault, args.passphrase)
        print(vault.get(args.key))
        return 0
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _cmd_delete(args: argparse.Namespace) -> int:
    try:
        vault = Vault(args.vault, args.passphrase)
        vault.delete(args.key)
        print(f"Deleted '{args.key}'.")
        return 0
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _cmd_list(args: argparse.Namespace) -> int:
    try:
        vault = Vault(args.vault, args.passphrase)
        keys = vault.keys()
        for key in sorted(keys):
            print(key)
        return 0
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))
