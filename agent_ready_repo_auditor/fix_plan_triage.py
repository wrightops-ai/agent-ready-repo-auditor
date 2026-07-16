"""Fail-closed triage for public Agent-Ready Repo Fix Plan requests."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .errors import (
    FixPlanValidationError,
    FixPlanVerificationError,
    InputValidationError,
)
from .inputs import parse_repository_ref


AUDIT_REPOSITORY = "wrightops-ai/agent-ready-repo-auditor"
CHECKOUT_URL = "https://www.paypal.com/ncp/payment/H9VVRGRGA3DCG"
REPORT_MARKER = (
    "This report was automatically generated from one immutable public GitHub snapshot."
)
MAX_RESPONSE_BYTES = 1_000_000
USER_AGENT = "agent-ready-repo-auditor/fix-plan-triage"

AUTHORIZATION_LABEL = (
    "I am authorized to commission a public review of this repository and understand "
    "that the request, evidence, and delivered fix cards will be public."
)
SCOPE_LABELS = (
    "I understand the $149 Fix Plan contains exactly three fix cards, at most 45 "
    "minutes of human review, and no implementation work.",
    "I reviewed the published scope, exclusions, correction, and refund terms before "
    "requesting scope confirmation.",
    "I understand that WrightOps will request payment only after confirming scope and "
    "that payment details must remain private.",
)

JsonFetcher = Callable[[str, Optional[str]], Any]


def extract_section(body: str, label: str) -> str:
    """Return exactly one GitHub issue-form section without echoing other fields."""

    pattern = re.compile(
        rf"(?ms)^### {re.escape(label)}\s*\n+(.*?)(?=^### |\Z)"
    )
    matches = pattern.findall(body)
    if len(matches) != 1:
        raise FixPlanValidationError(f"The {label} issue field is required exactly once.")
    value = matches[0].strip()
    if not value or value == "_No response_":
        raise FixPlanValidationError(f"The {label} issue field is required.")
    return value


def parse_audit_issue_number(value: str) -> int:
    """Accept only a canonical issue URL in the WrightOps audit repository."""

    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() != "github.com"
        or parsed.username
        or parsed.password
        or parsed.port is not None
        or parsed.query
        or parsed.fragment
        or "%" in parsed.path
    ):
        raise FixPlanValidationError(
            "Completed public audit issue must be a canonical HTTPS GitHub issue URL."
        )
    parts = [part for part in parsed.path.split("/") if part]
    if parts[:2] != AUDIT_REPOSITORY.split("/") or len(parts) != 4 or parts[2] != "issues":
        raise FixPlanValidationError(
            "Completed public audit issue must belong to the WrightOps audit repository."
        )
    if not parts[3].isdigit() or int(parts[3]) < 1:
        raise FixPlanValidationError("Completed public audit issue number is invalid.")
    return int(parts[3])


def extract_request(body: str) -> tuple[int, str, str]:
    """Extract and validate the bounded fields in a Fix Plan issue form body."""

    issue_number = parse_audit_issue_number(
        extract_section(body, "Completed public audit issue")
    )
    try:
        repository = parse_repository_ref(
            extract_section(body, "Public repository")
        ).slug
    except InputValidationError as error:
        raise FixPlanValidationError(error.message) from error
    priority = extract_section(body, "Highest-priority operational pain")
    if len(priority) > 1_000:
        raise FixPlanValidationError(
            "Highest-priority operational pain must be 1,000 characters or fewer."
        )

    authorization = extract_section(
        body, "Authorization and public-delivery acknowledgement"
    )
    _require_checked(authorization, (AUTHORIZATION_LABEL,))
    scope = extract_section(body, "Fixed-scope acknowledgement")
    _require_checked(scope, SCOPE_LABELS)
    return issue_number, repository, priority


def _require_checked(section: str, required_labels: Sequence[str]) -> None:
    checked = {
        match.group(1).strip()
        for line in section.splitlines()
        if (match := re.fullmatch(r"- \[[xX]\] (.+)", line.strip()))
    }
    if any(label not in checked for label in required_labels):
        raise FixPlanValidationError(
            "Every required authorization and fixed-scope acknowledgement must be checked."
        )


def verify_completed_audit(
    issue_number: int,
    repository: str,
    *,
    token: str | None = None,
    fetch_json: JsonFetcher | None = None,
) -> None:
    """Verify the referenced issue is a completed matching automated audit."""

    fetch = fetch_json or _fetch_github_json
    issue_path = f"/repos/{AUDIT_REPOSITORY}/issues/{issue_number}"
    issue = fetch(issue_path, token)
    if not isinstance(issue, dict):
        raise FixPlanVerificationError("GitHub returned an invalid audit issue record.")
    title = issue.get("title")
    labels = issue.get("labels")
    body = issue.get("body")
    if not isinstance(title, str) or not title.startswith("[Audit request]"):
        raise FixPlanValidationError(
            "The referenced issue is not a WrightOps automated audit request."
        )
    label_names = {
        item.get("name") for item in labels if isinstance(item, dict)
    } if isinstance(labels, list) else set()
    if "audit-request" not in label_names or not isinstance(body, str):
        raise FixPlanValidationError(
            "The referenced issue is not a WrightOps automated audit request."
        )
    try:
        referenced_repository = parse_repository_ref(
            extract_section(body, "Public repository")
        ).slug
    except InputValidationError as error:
        raise FixPlanValidationError(
            "The referenced automated audit contains an invalid public repository."
        ) from error
    if referenced_repository.lower() != repository.lower():
        raise FixPlanValidationError(
            "The Fix Plan repository does not match the referenced public audit."
        )

    comments = fetch(f"{issue_path}/comments?per_page=100", token)
    if not isinstance(comments, list):
        raise FixPlanVerificationError("GitHub returned an invalid audit comment list.")
    if not any(
        isinstance(comment, dict)
        and isinstance(comment.get("body"), str)
        and REPORT_MARKER in comment["body"]
        and "Evidence score:" in comment["body"]
        for comment in comments
    ):
        raise FixPlanValidationError(
            "The referenced automated audit has not completed successfully."
        )


def build_ready_comment() -> str:
    """Acknowledge a verified request without accepting scope or payment."""

    return (
        "### Scope review received\n\n"
        "Automated preflight verified that the completed public audit and requested "
        "repository match. WrightOps will confirm whether the request fits the fixed "
        "$149 scope within **one business day**.\n\n"
        "This acknowledgement is not scope acceptance and does not create a contract or "
        "payment obligation. **Do not pay until WrightOps posts scope confirmation on "
        "this issue.** After confirmation, use the dedicated [PayPal goods/services "
        f"checkout]({CHECKOUT_URL}).\n\n"
        "Keep payment, contact, customer, credential, and private-repository details off "
        "GitHub. The checkout quantity is limited to one, and the published refund and "
        "delivery terms continue to apply.\n"
    )


def build_correction_comment(error: FixPlanValidationError | FixPlanVerificationError) -> str:
    """Render a bounded correction request without reflecting submitted content."""

    return (
        "### Fix Plan request needs correction\n\n"
        f"`{error.code}` — {error.message}\n\n"
        "No scope was accepted and no payment is due. Confirm that the completed audit "
        "URL belongs to this repository, the public repository matches that audit, every "
        "required acknowledgement is checked, and the automated audit comment completed. "
        "Then open a new Fix Plan request. Do not post payment or private data.\n"
    )


def triage_event(
    event: Mapping[str, Any],
    *,
    token: str | None = None,
    fetch_json: JsonFetcher | None = None,
) -> tuple[str, bool]:
    issue = event.get("issue")
    body = issue.get("body") if isinstance(issue, dict) else None
    if not isinstance(body, str):
        error = FixPlanValidationError("GitHub event did not contain an issue body.")
        return build_correction_comment(error), False
    try:
        issue_number, repository, _priority = extract_request(body)
        verify_completed_audit(
            issue_number, repository, token=token, fetch_json=fetch_json
        )
    except (FixPlanValidationError, FixPlanVerificationError) as error:
        return build_correction_comment(error), False
    return build_ready_comment(), True


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    output_path = os.environ.get("FIX_PLAN_TRIAGE_COMMENT")
    if not event_path or not output_path:
        sys.stderr.write("GITHUB_EVENT_PATH and FIX_PLAN_TRIAGE_COMMENT are required.\n")
        return 2
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.stderr.write(f"Unable to read the GitHub issue event: {error.__class__.__name__}.\n")
        return 2
    if not isinstance(event, dict):
        sys.stderr.write("GitHub issue event must be a JSON object.\n")
        return 2

    comment, ready = triage_event(event, token=os.environ.get("GITHUB_TOKEN"))
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(comment, encoding="utf-8")
    _write_action_output(
        os.environ.get("GITHUB_OUTPUT"),
        "scope-review-ready",
        "true" if ready else "false",
    )
    return 0


def _fetch_github_json(path: str, token: str | None) -> Any:
    if not path.startswith("/") or any(character in path for character in "\r\n"):
        raise FixPlanVerificationError("GitHub API path was invalid.")
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        if any(character in token for character in "\r\n"):
            raise FixPlanVerificationError("GitHub token was invalid.")
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=15.0) as response:
            final = urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != "api.github.com":
                raise FixPlanVerificationError(
                    "GitHub API redirected outside api.github.com."
                )
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        if error.code == 404:
            raise FixPlanValidationError(
                "The referenced completed public audit issue was not found."
            ) from error
        raise FixPlanVerificationError(
            "GitHub could not verify the referenced audit right now."
        ) from error
    except (TimeoutError, URLError) as error:
        raise FixPlanVerificationError(
            "GitHub could not verify the referenced audit right now."
        ) from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise FixPlanVerificationError("GitHub response exceeded the verification limit.")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FixPlanVerificationError("GitHub returned invalid verification data.") from error


def _write_action_output(path_value: str | None, name: str, value: str) -> None:
    if not path_value:
        return
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")
