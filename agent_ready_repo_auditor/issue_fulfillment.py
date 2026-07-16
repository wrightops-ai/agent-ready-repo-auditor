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
PAID_INTEREST_SECTION = re.compile(
    r"(?ms)^### Fixed-price remediation interest\s*\n+(.*?)(?=^### |\Z)"
)
PAID_INTEREST_VALUES = frozenset({"Yes", "Maybe", "No"})


def extract_repository(body: str) -> str:
    """Extract and validate one repository from the GitHub issue form body."""

    match = PUBLIC_REPOSITORY_SECTION.search(body)
    value = match.group(1).strip() if match else ""
    if not value or value == "_No response_":
        raise InputValidationError("The Public repository issue field is required.")
    return parse_repository_ref(value).slug


def extract_paid_interest(body: str) -> str | None:
    """Return one exact issue-form interest value, failing closed on ambiguity."""

    matches = PAID_INTEREST_SECTION.findall(body)
    if len(matches) != 1:
        return None
    value = matches[0].strip()
    return value if value in PAID_INTEREST_VALUES else None


def has_commercial_interest(body: str) -> bool:
    """Return whether a canonical response indicates non-binding paid interest."""

    return extract_paid_interest(body) in {"Yes", "Maybe"}


def build_comment(report: AuditReport) -> str:
    """Render transparent automated fulfillment with an optional paid next step."""

    return (
        "> This report was automatically generated from one immutable public GitHub "
        "snapshot. No repository code was cloned or executed.\n\n"
        + render_markdown(report)
        + "\n---\n"
        "### Put the report to work\n\n"
        "Install the [free GitHub Action](https://github.com/wrightops-ai/"
        "agent-ready-repo-auditor#github-action) to keep the evidence check running. "
        "For exact next steps, the [$149 Agent-Ready Repo Fix Plan](https://github.com/"
        "wrightops-ai/agent-ready-repo-auditor/blob/main/docs/agent-ready-fix-plan.md) "
        "adds exactly three human-reviewed fix cards to this public issue within one "
        "business day. [Submit this completed audit for scope confirmation](https://"
        "github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template="
        "fix-plan-request.yml); a buyer-specific PayPal goods/services invoice is "
        "requested privately only after the fixed scope is confirmed. Do not post payment "
        "details here.\n\n"
        "The issue-form interest question is non-binding demand research. This repository "
        "does not accept payment through an issue or create a service contract merely by "
        "opening or replying to one. Do not post secrets, private repository details, "
        "credentials, payment identifiers, or personal data.\n"
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

    issue = event.get("issue")
    issue_body = issue.get("body") if isinstance(issue, dict) else None
    commercial_interest = (
        has_commercial_interest(issue_body) if isinstance(issue_body, str) else False
    )
    comment, audit_status = fulfill_event(event, token=os.environ.get("GITHUB_TOKEN"))
    _write_action_output(
        os.environ.get("GITHUB_OUTPUT"),
        "commercial-interest",
        "true" if commercial_interest and audit_status == 0 else "false",
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(comment, encoding="utf-8")
    if audit_status:
        sys.stderr.write("Audit request failed closed; a bounded error comment was prepared.\n")
    return 0


def _write_action_output(path_value: str | None, name: str, value: str) -> None:
    if not path_value:
        return
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")
