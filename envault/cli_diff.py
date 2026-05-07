"""CLI subcommand: diff — compare vault secrets with another vault or file."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envault.diff import DiffEntry, DiffError, diff_vault_file
from envault.vault import Vault, VaultError

_STATUS_SYMBOLS = {
    "added": "+",
    "removed": "-",
    "changed": "~",
    "unchanged": " ",
}


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "diff",
        help="Compare vault secrets against a .env or .json file",
    )
    p.add_argument("vault_path", help="Path to the vault file")
    p.add_argument("file", help=".env or .json file to compare against")
    p.add_argument(
        "--passphrase", required=True, help="Vault passphrase"
    )
    p.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Also print unchanged keys",
    )
    p.set_defaults(func=_cmd_diff)


def _format_entries(entries: List[DiffEntry], show_unchanged: bool) -> str:
    lines = []
    for e in entries:
        if e.status == "unchanged" and not show_unchanged:
            continue
        sym = _STATUS_SYMBOLS[e.status]
        if e.status == "changed":
            lines.append(f"{sym} {e.key}  (vault={e.left_value!r} -> file={e.right_value!r})")
        elif e.status == "added":
            lines.append(f"{sym} {e.key}  (file value={e.right_value!r})")
        elif e.status == "removed":
            lines.append(f"{sym} {e.key}  (vault value={e.left_value!r})")
        else:
            lines.append(f"{sym} {e.key}")
    return "\n".join(lines)


def _cmd_diff(args: argparse.Namespace) -> int:
    vault = Vault(args.vault_path)
    try:
        entries = diff_vault_file(vault, args.passphrase, args.file)
    except (DiffError, VaultError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = _format_entries(entries, args.show_unchanged)
    if output:
        print(output)

    changed = sum(1 for e in entries if e.status != "unchanged")
    return 0 if changed == 0 else 2
