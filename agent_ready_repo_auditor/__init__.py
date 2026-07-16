"""Public API for agent-ready-repo-auditor."""

from .audit import audit_repository
from .github import GitHubClient
from .inputs import RepositoryRef, parse_repository_ref
from .render import render_json, render_markdown

__all__ = [
    "GitHubClient",
    "RepositoryRef",
    "audit_repository",
    "parse_repository_ref",
    "render_json",
    "render_markdown",
]

__version__ = "0.1.0"
