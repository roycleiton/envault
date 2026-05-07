"""Entry point: python -m envault."""

from __future__ import annotations

import argparse
import sys

from envault.cli import build_parser
from envault.cli_export import register as register_export
from envault.cli_rotate import register as register_rotate
from envault.cli_import import register as register_import
from envault.cli_diff import register as register_diff


def main() -> int:
    parser = build_parser()
    subparsers = parser._subparsers._group_actions[0]  # type: ignore[attr-defined]  # noqa: SLF001
    register_export(subparsers)
    register_rotate(subparsers)
    register_import(subparsers)
    register_diff(subparsers)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
