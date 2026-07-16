"""Stable JSON and Markdown renderers."""

from __future__ import annotations

import json
from typing import Any

from .models import AuditReport


def render_json(report: AuditReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(report: AuditReport) -> str:
    payload = report.to_dict()
    repository = payload["repository"]
    score = payload["score"]
    lines = [
        "# Agent-Ready Repository Audit",
        "",
        f"Repository: [{_text(repository['full_name'])}]({repository['web_url']})",
        "",
        f"Immutable revision: `{repository['revision_sha']}` ({repository['default_branch']})",
        "",
        f"Evidence score: **{score['earned']}/{score['maximum']} ({score['percentage']}%)** — `{score['band']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Score | Finding |",
        "| --- | --- | ---: | --- |",
    ]
    for check in payload["checks"]:
        lines.append(
            f"| {_cell(check['label'])} | `{check['status']}` | {check['score']}/{check['max_score']} | {_cell(check['summary'])} |"
        )
    lines.extend(["", "## Evidence", ""])
    for check in payload["checks"]:
        lines.append(f"### {check['label']}")
        lines.append("")
        if not check["evidence"]:
            lines.append("- No public evidence recorded.")
        for evidence in check["evidence"]:
            location = f" line {evidence['line']}" if "line" in evidence else ""
            lines.append(
                f"- [{_text(evidence['path'])}{location}]({evidence['source_url']}): {_text(evidence['detail'])}"
            )
        lines.append("")
    lines.extend(["## Prioritized next steps", ""])
    if payload["next_steps"]:
        lines.extend(f"{number}. {step}" for number, step in enumerate(payload["next_steps"], start=1))
    else:
        lines.append("No missing check was identified by this limited public-evidence scan.")
    lines.extend(["", "## Inspection limits", ""])
    lines.extend(f"- {item}" for item in payload["limitations"])
    if payload["inspection"]["warnings"]:
        lines.extend(["", "## Inspection warnings", ""])
        lines.extend(f"- {_text(warning)}" for warning in payload["inspection"]["warnings"])
    return "\n".join(lines) + "\n"


def render_error(error: dict[str, Any]) -> str:
    return json.dumps({"error": error, "ok": False}, indent=2, sort_keys=True) + "\n"


def _cell(value: str) -> str:
    return _text(value).replace("|", "\\|")


def _text(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("\n", " ").replace("\r", " ")
    for character in ("[", "]", "*", "_", "<", ">"):
        escaped = escaped.replace(character, f"\\{character}")
    return escaped
