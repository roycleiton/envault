"""CLI subcommands for vault snapshot management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    delete_snapshot,
)


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("snapshot", help="Manage vault snapshots")
    sub = p.add_subparsers(dest="snapshot_cmd", required=True)

    # create
    pc = sub.add_parser("create", help="Create a snapshot of the current vault")
    pc.add_argument("--label", default=None, help="Optional snapshot label")

    # list
    sub.add_parser("list", help="List available snapshots")

    # restore
    pr = sub.add_parser("restore", help="Restore vault from a snapshot")
    pr.add_argument("label", help="Snapshot label to restore")

    # delete
    pd = sub.add_parser("delete", help="Delete a snapshot")
    pd.add_argument("label", help="Snapshot label to delete")

    p.set_defaults(func=_cmd_snapshot)


def _cmd_snapshot(args: argparse.Namespace) -> int:
    vault_path = Path(args.vault)
    passphrase = args.passphrase

    try:
        if args.snapshot_cmd == "create":
            path = create_snapshot(vault_path, passphrase, label=args.label)
            print(f"Snapshot saved: {path}")

        elif args.snapshot_cmd == "list":
            labels = list_snapshots(vault_path)
            if not labels:
                print("No snapshots found.")
            else:
                for label in labels:
                    print(label)

        elif args.snapshot_cmd == "restore":
            count = restore_snapshot(vault_path, passphrase, label=args.label)
            print(f"Restored {count} secret(s) from snapshot '{args.label}'.")

        elif args.snapshot_cmd == "delete":
            delete_snapshot(vault_path, label=args.label)
            print(f"Deleted snapshot '{args.label}'.")

    except SnapshotError as exc:
        print(f"snapshot error: {exc}", file=sys.stderr)
        return 1

    return 0
