"""CLI sub-commands for secret change history."""

from __future__ import annotations

import argparse
import sys

from envault.vault import Vault, VaultError
from envault.history import HistoryError, get_history, clear_history


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("history", help="Show or clear change history for a key")
    p.add_argument("key", help="Secret key name")
    p.add_argument("--vault", required=True, metavar="FILE", help="Path to vault file")
    p.add_argument("--passphrase", required=True, metavar="PASS")
    p.add_argument(
        "--clear",
        action="store_true",
        help="Clear the history for the given key",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=20,
        metavar="N",
        help="Maximum number of entries to display (default: 20)",
    )
    p.set_defaults(func=_cmd_history)


def _cmd_history(args: argparse.Namespace) -> int:
    vault = Vault(args.vault)

    try:
        if args.clear:
            clear_history(vault, args.passphrase, args.key)
            print(f"History cleared for '{args.key}'.")
            return 0

        entries = get_history(vault, args.passphrase, args.key)
    except (VaultError, HistoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not entries:
        print(f"No history found for '{args.key}'.")
        return 0

    shown = entries[-args.limit :]
    print(f"History for '{args.key}' ({len(shown)} of {len(entries)} entries):")
    for entry in shown:
        ts = entry.get("timestamp", "unknown")
        action = entry.get("action", "?")
        preview = entry.get("value_preview", "")
        suffix = f"  preview={preview}" if preview else ""
        print(f"  {ts}  {action}{suffix}")

    return 0
