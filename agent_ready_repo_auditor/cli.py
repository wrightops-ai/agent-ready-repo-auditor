"""Command-line interface for the public repository auditor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audit import audit_repository
from .errors import AuditorError
from .github import GitHubClient
from .render import render_error, render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-ready-repo-auditor",
        description="Audit public GitHub evidence for coding-agent operational readiness.",
    )
    parser.add_argument("repository", help="owner/repository or canonical https://github.com/owner/repository URL")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path, help="write output to this path instead of stdout")
    parser.add_argument("--timeout", type=float, default=15.0, help="GitHub request timeout in seconds")
    parser.add_argument("--max-file-bytes", type=int, default=256_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.max_file_bytes <= 0:
        parser.error("--timeout and --max-file-bytes must be positive")
    client = GitHubClient(timeout_seconds=args.timeout, max_file_bytes=args.max_file_bytes)
    try:
        report = audit_repository(args.repository, client=client)
    except AuditorError as error:
        sys.stderr.write(render_error(error.to_dict()))
        return 2
    rendered = render_json(report) if args.format == "json" else render_markdown(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0
