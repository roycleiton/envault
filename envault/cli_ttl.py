"""CLI sub-commands for TTL management.

Registered sub-commands:
  ttl set  <key> <iso-datetime>   – attach an expiry to a secret
  ttl get  <key>                  – print the expiry for a secret
  ttl clear <key>                 – remove the expiry from a secret
  ttl purge                       – delete all expired secrets
"""
from __future__ import annotations

import argparse
import datetime
import sys

from envault.vault import Vault
import envault.ttl as ttl_mod


def register(subparsers: argparse._SubParsersAction, parent: argparse.ArgumentParser) -> None:  # noqa: SLF001
    p = subparsers.add_parser("ttl", help="Manage secret expiry (TTL)", parents=[parent])
    sub = p.add_subparsers(dest="ttl_cmd", required=True)

    # ttl set
    p_set = sub.add_parser("set", help="Set expiry for a secret")
    p_set.add_argument("key", help="Secret key")
    p_set.add_argument("expires_at", help="ISO-8601 datetime (UTC) e.g. 2025-12-31T00:00:00")

    # ttl get
    p_get = sub.add_parser("get", help="Show expiry for a secret")
    p_get.add_argument("key", help="Secret key")

    # ttl clear
    p_clear = sub.add_parser("clear", help="Remove expiry from a secret")
    p_clear.add_argument("key", help="Secret key")

    # ttl purge
    sub.add_parser("purge", help="Delete all expired secrets")

    p.set_defaults(func=_cmd_ttl)


def _cmd_ttl(args: argparse.Namespace) -> int:
    vault = Vault(args.vault, args.passphrase)
    cmd = args.ttl_cmd

    if cmd == "set":
        try:
            expires_at = datetime.datetime.fromisoformat(args.expires_at)
        except ValueError as exc:
            print(f"error: invalid datetime '{args.expires_at}': {exc}", file=sys.stderr)
            return 1
        ttl_mod.set_ttl(vault, args.key, expires_at)
        print(f"TTL set for '{args.key}': expires {expires_at.isoformat()}")
        return 0

    if cmd == "get":
        result = ttl_mod.get_ttl(vault, args.key)
        if result is None:
            print(f"No TTL set for '{args.key}'")
            return 0
        status = "EXPIRED" if ttl_mod.is_expired(vault, args.key) else "valid"
        print(f"{result.isoformat()}  [{status}]")
        return 0

    if cmd == "clear":
        ttl_mod.clear_ttl(vault, args.key)
        print(f"TTL cleared for '{args.key}'")
        return 0

    if cmd == "purge":
        deleted = ttl_mod.purge_expired(vault)
        if deleted:
            for k in deleted:
                print(f"purged: {k}")
            print(f"{len(deleted)} secret(s) purged.")
        else:
            print("No expired secrets found.")
        return 0

    return 1
