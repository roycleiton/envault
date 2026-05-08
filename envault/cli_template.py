"""CLI sub-commands for template rendering."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.template import TemplateError, render_file
from envault.vault import Vault


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``template`` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "template",
        help="Render a template file by substituting vault secrets.",
    )
    p.add_argument("src", help="Path to the template file.")
    p.add_argument(
        "-o",
        "--output",
        metavar="DST",
        default=None,
        help="Write rendered output to DST instead of stdout.",
    )
    p.add_argument(
        "--no-strict",
        action="store_true",
        default=False,
        help="Leave unknown placeholders unchanged instead of failing.",
    )
    p.set_defaults(func=_cmd_template)


def _cmd_template(args: argparse.Namespace) -> int:
    """Execute the ``template`` command."""
    vault = Vault(Path(args.vault))
    src = Path(args.src)
    dst = Path(args.output) if args.output else None
    strict = not args.no_strict

    try:
        rendered = render_file(src, vault, args.passphrase, dst, strict=strict)
    except TemplateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if dst is None:
        print(rendered, end="")
    else:
        print(f"Rendered template written to {dst}")

    return 0
