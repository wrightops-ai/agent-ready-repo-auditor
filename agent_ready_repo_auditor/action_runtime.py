"""Safe GitHub composite-action runtime for the public repository auditor."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Mapping

from .audit import audit_repository
from .errors import AuditorError
from .github import GitHubClient
from .render import render_error, render_json, render_markdown


class ActionConfigurationError(ValueError):
    """Raised when action inputs cannot be executed safely."""


def run(environment: Mapping[str, str] | None = None) -> int:
    """Run one audit from action environment variables."""

    env = os.environ if environment is None else environment
    try:
        repository = _required_repository(env)
        output_format = _output_format(env)
        threshold = _threshold(env)
        workspace, report_path, relative_report_path = _report_path(env, output_format)
    except ActionConfigurationError as error:
        _write_configuration_error(str(error))
        return 2

    token = env.get("AUDIT_GITHUB_TOKEN") or env.get("AUDIT_DEFAULT_GITHUB_TOKEN") or None
    try:
        report = audit_repository(repository, client=GitHubClient(token=token))
    except AuditorError as error:
        sys.stderr.write(render_error(error.to_dict()))
        return 2

    payload = report.to_dict()
    rendered = render_json(report) if output_format == "json" else render_markdown(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(rendered, encoding="utf-8")

    _append_text(env.get("GITHUB_STEP_SUMMARY"), render_markdown(report))
    score = payload["score"]["percentage"]
    _append_text(
        env.get("GITHUB_OUTPUT"),
        "\n".join(
            (
                f"score={score}",
                f"band={payload['score']['band']}",
                f"report-path={relative_report_path.as_posix()}",
                f"revision={payload['repository']['revision_sha']}",
            )
        )
        + "\n",
    )
    if score < threshold:
        sys.stderr.write(
            f"Agent-ready evidence score {score} is below the configured threshold {threshold}.\n"
        )
        return 1
    return 0


def _required_repository(env: Mapping[str, str]) -> str:
    repository = (env.get("AUDIT_REPOSITORY") or env.get("GITHUB_REPOSITORY") or "").strip()
    if not repository:
        raise ActionConfigurationError("repository is required when GITHUB_REPOSITORY is unavailable")
    return repository


def _output_format(env: Mapping[str, str]) -> str:
    output_format = (env.get("AUDIT_FORMAT") or "markdown").strip().lower()
    if output_format not in {"json", "markdown"}:
        raise ActionConfigurationError("format must be 'json' or 'markdown'")
    return output_format


def _threshold(env: Mapping[str, str]) -> int:
    raw = (env.get("AUDIT_THRESHOLD") or "0").strip()
    try:
        threshold = int(raw)
    except ValueError as error:
        raise ActionConfigurationError("fail-threshold must be an integer from 0 through 100") from error
    if not 0 <= threshold <= 100:
        raise ActionConfigurationError("fail-threshold must be an integer from 0 through 100")
    return threshold


def _report_path(
    env: Mapping[str, str], output_format: str
) -> tuple[Path, Path, Path]:
    workspace = Path(env.get("GITHUB_WORKSPACE") or ".").resolve()
    configured = (env.get("AUDIT_OUTPUT_FILE") or "").strip()
    if not configured:
        configured = f"agent-ready-audit.{'json' if output_format == 'json' else 'md'}"
    relative = Path(configured)
    if relative.is_absolute():
        raise ActionConfigurationError("output-file must be relative to GITHUB_WORKSPACE")
    report_path = (workspace / relative).resolve()
    try:
        normalized_relative = report_path.relative_to(workspace)
    except ValueError as error:
        raise ActionConfigurationError("output-file must stay inside GITHUB_WORKSPACE") from error
    if report_path == workspace:
        raise ActionConfigurationError("output-file must name a file inside GITHUB_WORKSPACE")
    return workspace, report_path, normalized_relative


def _append_text(path_value: str | None, text: str) -> None:
    if not path_value:
        return
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def _write_configuration_error(message: str) -> None:
    sys.stderr.write(
        json.dumps(
            {
                "error": {
                    "code": "invalid_action_configuration",
                    "message": message,
                    "retryable": False,
                },
                "ok": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
