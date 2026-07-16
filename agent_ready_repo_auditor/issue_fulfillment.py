"""GitHub issue-form fulfillment for free public-repository audit requests."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping

from .audit import audit_repository
from .errors import AuditorError, InputValidationError
from .github import GitHubClient
from .inputs import parse_repository_ref
from .models import AuditReport
from .render import render_markdown


PUBLIC_REPOSITORY_SECTION = re.compile(
    r"(?ms)^### Public repository\s*\n+(.*?)(?=^### |\Z)"
)


def extract_repository(body: str) -> str:
    """Extract and validate one repository from the GitHub issue form body."""

    match = PUBLIC_REPOSITORY_SECTION.search(body)
    value = match.group(1).strip() if match else ""
    if not value or value == "_No response_":
        raise InputValidationError("The Public repository issue field is required.")
    return parse_repository_ref(value).slug


def build_comment(report: AuditReport) -> str:
    """Render a transparent, non-commercial automated fulfillment comment."""

    return (
        "> This report was automatically generated from one immutable public GitHub "
        "snapshot. No repository code was cloned or executed.\n\n"
        + render_markdown(report)
        + "\n---\n"
        "The issue-form interest question is non-binding demand research. This repository "
        "does not accept payment or create a service contract. Do not post secrets, private "
        "repository details, credentials, or personal data.\n"
    )


def build_error_comment(error: AuditorError) -> str:
    """Render a bounded public failure without echoing issue content."""

    return (
        "> This automated public-repository audit could not be completed.\n\n"
        f"`{error.code}` — {error.message}\n\n"
        "No partial audit was emitted. Confirm that the issue contains one canonical public "
        "GitHub repository URL and try a new request.\n"
    )


def fulfill_event(
    event: Mapping[str, Any], *, token: str | None = None
) -> tuple[str, int]:
    issue = event.get("issue")
    if not isinstance(issue, dict) or not isinstance(issue.get("body"), str):
        error = InputValidationError("GitHub event did not contain an issue body.")
        return build_error_comment(error), 2
    try:
        repository = extract_repository(issue["body"])
        report = audit_repository(repository, client=GitHubClient(token=token))
    except AuditorError as error:
        return build_error_comment(error), 2
    return build_comment(report), 0


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    output_path = os.environ.get("AUDIT_REQUEST_COMMENT")
    if not event_path or not output_path:
        sys.stderr.write("GITHUB_EVENT_PATH and AUDIT_REQUEST_COMMENT are required.\n")
        return 2
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.stderr.write(f"Unable to read the GitHub issue event: {error.__class__.__name__}.\n")
        return 2
    if not isinstance(event, dict):
        sys.stderr.write("GitHub issue event must be a JSON object.\n")
        return 2

    comment, audit_status = fulfill_event(event, token=os.environ.get("GITHUB_TOKEN"))
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(comment, encoding="utf-8")
    if audit_status:
        sys.stderr.write("Audit request failed closed; a bounded error comment was prepared.\n")
    return 0
