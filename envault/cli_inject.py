"""CLI sub-command: envault inject -- <command> [args...]"""
from __future__ import annotations

import argparse
import sys
from typing import List

from envault.env_inject import InjectError, inject_and_run
from envault.vault import Vault


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "inject",
        help="run a command with vault secrets injected into its environment",
    )
    p.add_argument("--vault", required=True, help="path to vault file")
    p.add_argument("--passphrase", required=True, help="vault passphrase")
    p.add_argument(
        "--prefix",
        default="",
        help="optional prefix prepended to every injected env-var name",
    )
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="inject only these keys (default: all)",
    )
    p.add_argument(
        "--no-override",
        action="store_true",
        help="do not overwrite env vars that already exist",
    )
    p.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="command to run (use -- to separate from envault flags)",
    )
    p.set_defaults(func=_cmd_inject)


def _cmd_inject(args: argparse.Namespace) -> int:
    command: List[str] = [c for c in args.command if c != "--"]
    if not command:
        print("error: no command supplied", file=sys.stderr)
        return 2

    vault = Vault(args.vault)
    try:
        result = inject_and_run(
            vault,
            args.passphrase,
            command,
            prefix=args.prefix or None,
            keys=args.keys or None,
            override=not args.no_override,
        )
    except InjectError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        f"injected {len(result.injected)} secret(s)"
        + (f", skipped {len(result.skipped)}" if result.skipped else ""),
        file=sys.stderr,
    )
    return result.returncode
