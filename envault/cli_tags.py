"""CLI sub-commands for tag management."""
from __future__ import annotations

import argparse
import sys

from envault.vault import Vault, VaultError
from envault.tags import (
    TagError,
    add_tag,
    remove_tag,
    get_tags,
    list_by_tag,
    all_tags,
)


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:  # noqa: SLF001
    p = subparsers.add_parser("tag", help="Manage tags on secrets.", parents=[common])
    tp = p.add_subparsers(dest="tag_cmd", required=True)

    # add
    pa = tp.add_parser("add", help="Add a tag to a secret key.")
    pa.add_argument("key", help="Secret key name.")
    pa.add_argument("tag", help="Tag to add.")

    # remove
    pr = tp.add_parser("remove", help="Remove a tag from a secret key.")
    pr.add_argument("key", help="Secret key name.")
    pr.add_argument("tag", help="Tag to remove.")

    # list
    pl = tp.add_parser("list", help="List tags for a key, or all keys for a tag.")
    pl.add_argument("--key", default=None, help="Show tags for this secret key.")
    pl.add_argument("--tag", default=None, help="Show all keys carrying this tag.")

    p.set_defaults(func=_cmd_tag)


def _cmd_tag(args: argparse.Namespace) -> int:
    vault = Vault(args.vault, args.passphrase)

    try:
        if args.tag_cmd == "add":
            tags = add_tag(vault, args.passphrase, args.key, args.tag)
            print(f"Tags for '{args.key}': {', '.join(tags)}")

        elif args.tag_cmd == "remove":
            tags = remove_tag(vault, args.passphrase, args.key, args.tag)
            label = ", ".join(tags) if tags else "(none)"
            print(f"Tags for '{args.key}': {label}")

        elif args.tag_cmd == "list":
            if args.key and args.tag:
                print("Specify --key or --tag, not both.", file=sys.stderr)
                return 1
            if args.key:
                tags = get_tags(vault, args.passphrase, args.key)
                print(", ".join(tags) if tags else "(no tags)")
            elif args.tag:
                keys = list_by_tag(vault, args.passphrase, args.tag)
                if keys:
                    print("\n".join(keys))
                else:
                    print(f"No keys tagged '{args.tag}'.")
            else:
                mapping = all_tags(vault, args.passphrase)
                if not mapping:
                    print("No tags defined.")
                else:
                    for key, tags in sorted(mapping.items()):
                        print(f"{key}: {', '.join(tags)}")

    except (TagError, VaultError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0
