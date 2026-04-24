"""CLI entry point for envault."""

import sys
import argparse
from pathlib import Path

from envault.vault import Vault, VaultError


DEFAULT_VAULT_PATH = Path(".envault")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Securely manage and sync environment variables.",
    )
    parser.add_argument(
        "--vault",
        default=str(DEFAULT_VAULT_PATH),
        metavar="PATH",
        help="Path to the vault file (default: .envault)",
    )
    parser.add_argument(
        "--passphrase",
        required=True,
        metavar="PASSPHRASE",
        help="Passphrase used to encrypt/decrypt the vault",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # set
    set_parser = subparsers.add_parser("set", help="Store an environment variable")
    set_parser.add_argument("key", help="Variable name")
    set_parser.add_argument("value", help="Variable value")

    # get
    get_parser = subparsers.add_parser("get", help="Retrieve an environment variable")
    get_parser.add_argument("key", help="Variable name")

    # delete
    del_parser = subparsers.add_parser("delete", help="Delete an environment variable")
    del_parser.add_argument("key", help="Variable name")

    # list
    subparsers.add_parser("list", help="List all stored variable names")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    vault = Vault(path=Path(args.vault), passphrase=args.passphrase)

    try:
        if args.command == "set":
            vault.set(args.key, args.value)
            print(f"Stored '{args.key}'.")

        elif args.command == "get":
            value = vault.get(args.key)
            if value is None:
                print(f"Key '{args.key}' not found.", file=sys.stderr)
                return 1
            print(value)

        elif args.command == "delete":
            vault.delete(args.key)
            print(f"Deleted '{args.key}'.")

        elif args.command == "list":
            keys = vault.list_keys()
            if keys:
                print("\n".join(sorted(keys)))
            else:
                print("(vault is empty)")

    except VaultError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
