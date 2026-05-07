"""Entry-point for ``python -m envault``."""
from __future__ import annotations

import sys

from envault.cli import build_parser
import envault.cli_export as cli_export
import envault.cli_rotate as cli_rotate
import envault.cli_import as cli_import
import envault.cli_diff as cli_diff
import envault.cli_tags as cli_tags
import envault.cli_snapshot as cli_snapshot
import envault.cli_ttl as cli_ttl


def main(argv: list[str] | None = None) -> int:
    parser, subparsers, parent = build_parser()

    cli_export.register(subparsers, parent)
    cli_rotate.register(subparsers, parent)
    cli_import.register(subparsers, parent)
    cli_diff.register(subparsers, parent)
    cli_tags.register(subparsers, parent)
    cli_snapshot.register(subparsers, parent)
    cli_ttl.register(subparsers, parent)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
