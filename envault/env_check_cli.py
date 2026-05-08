"""CLI sub-command: envault check — compare vault secrets against the live environment."""

from __future__ import annotations

import argparse
import sys

from envault.env_check import check_env, EnvCheckError
from envault.vault import Vault, VaultError


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "check",
        help="Compare vault secrets against environment variables currently set in the shell.",
    )
    p.add_argument("vault_file", help="Path to the vault file.")
    p.add_argument("--passphrase", required=True, help="Vault passphrase.")
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Only check these specific keys (default: all keys).",
    )
    p.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit with code 1 if any key is missing or has a different value.",
    )
    p.set_defaults(func=_cmd_check)


def _cmd_check(args: argparse.Namespace) -> int:
    try:
        vault = Vault(args.vault_file, args.passphrase)
        results = check_env(vault, keys=args.keys)
    except (VaultError, EnvCheckError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No secrets to check.")
        return 0

    col_w = max(len(r.key) for r in results)
    any_issue = False
    for r in results:
        status_label = r.status.upper()
        print(f"{r.key:<{col_w}}  [{status_label}]")
        if r.status != "ok":
            any_issue = True

    if args.fail_on_mismatch and any_issue:
        return 1
    return 0
