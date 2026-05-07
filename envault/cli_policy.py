"""CLI sub-commands for policy enforcement."""

from __future__ import annotations

import argparse
import sys

from envault.policy import PolicyError, enforce_policy
from envault.vault import Vault, VaultError


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "policy",
        help="Enforce naming and strength rules on vault secrets",
    )
    p.add_argument("vault_path", help="Path to the vault file")
    p.add_argument("passphrase", help="Vault passphrase")
    p.add_argument(
        "--key-pattern",
        metavar="REGEX",
        default=None,
        help="Required regex pattern that every key must fully match",
    )
    p.add_argument(
        "--min-length",
        metavar="N",
        type=int,
        default=0,
        help="Minimum character length for every secret value",
    )
    p.add_argument(
        "--forbidden-keys",
        metavar="KEY",
        nargs="+",
        default=None,
        help="Keys that must not exist in the vault",
    )
    p.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even when violations are found (print warnings)",
    )
    p.set_defaults(func=_cmd_policy)


def _cmd_policy(args: argparse.Namespace) -> int:
    try:
        vault = Vault(args.vault_path, args.passphrase)
        violations = enforce_policy(
            vault,
            args.passphrase,
            key_pattern=args.key_pattern,
            min_length=args.min_length,
            forbidden_keys=args.forbidden_keys,
        )
    except (VaultError, PolicyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not violations:
        print("Policy check passed — no violations found.")
        return 0

    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    for v in warnings:
        print(f"[warning] [{v.rule}] {v.message}")
    for v in errors:
        print(f"[error]   [{v.rule}] {v.message}")

    total = len(violations)
    print(
        f"\n{total} violation(s) found "
        f"({len(errors)} error(s), {len(warnings)} warning(s))."
    )

    if args.warn_only:
        return 0
    return 1 if errors else 0
