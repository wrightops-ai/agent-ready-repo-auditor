"""Deterministic, evidence-backed checks for public coding-agent readiness."""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterable
from typing import Any
from urllib.parse import quote

from .github import GitHubClient, RepositorySnapshot, TextFile
from .inputs import RepositoryRef, parse_repository_ref
from .models import AuditReport, CheckResult, Evidence


README_NAMES = ("readme.md", "readme.rst", "readme.txt", "readme")
AGENT_INSTRUCTION_PATHS = (
    "agents.md",
    "claude.md",
    ".github/copilot-instructions.md",
    ".cursorrules",
)
ENV_EXAMPLE_NAMES = (
    ".env.example",
    ".env.sample",
    ".env.template",
    "env.example",
    "example.env",
)
VERIFY_CONFIG_NAMES = (
    "makefile",
    "justfile",
    "package.json",
    "pyproject.toml",
    "tox.ini",
    "noxfile.py",
    "cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
)
VERIFY_PATH_PATTERNS = (
    "scripts/check*",
    "scripts/test*",
    "scripts/verify*",
    "bin/check*",
    "bin/test*",
    "bin/verify*",
    "test/**",
    "tests/**",
)
SETUP_RE = re.compile(
    r"(?i)\b(install|installation|setup|getting started|quickstart|requirements|prerequisites)\b"
)
COMMAND_RE = re.compile(
    r"(?i)(?:^|[\s`])(?:python(?:3)?|pytest|npm|pnpm|yarn|bun|make|just|cargo|go|mvn|gradle|dotnet)\s+[^\s`]"
)
VERIFY_RE = re.compile(r"(?i)\b(test|tests|testing|lint|typecheck|type-check|verify|verification|check)\b")
RISK_ACTION = (
    r"deploy|publish|delete|force[- ]push|spend|pay|contact|send|expose|record|download|"
    r"use credentials?|access production|handle (?:personal|private) data"
)
PROHIBITED_ACTION_RE = re.compile(
    rf"(?i)\b(?:do not|don't|never|must not)\s+(?:[a-z-]+\s+){{0,4}}(?:{RISK_ACTION})\b"
)
APPROVAL_ACTION_RE = re.compile(
    rf"(?i)(?:\b(?:{RISK_ACTION})\b.{{0,100}}\b(?:without|requires?|needs?|only after)\s+"
    rf"(?:explicit\s+)?(?:approval|permission|confirmation)\b|"
    rf"\b(?:ask before|requires? (?:explicit )?(?:approval|permission|confirmation))\b.{{0,100}}"
    rf"\b(?:{RISK_ACTION})\b)"
)


def audit_repository(
    repository: str | RepositoryRef,
    *,
    client: GitHubClient | None = None,
) -> AuditReport:
    """Audit one public GitHub default-branch snapshot without executing its code."""

    ref = parse_repository_ref(repository) if isinstance(repository, str) else repository
    github = client or GitHubClient()
    snapshot = github.snapshot(ref)
    paths = tuple(snapshot.files)
    path_by_lower = {path.lower(): path for path in paths}

    candidates = _content_candidates(paths, path_by_lower)
    text_files: dict[str, TextFile] = {}
    warnings: list[str] = []
    for path in candidates:
        item = github.read_text(snapshot, path)
        text_files[path] = item
        if item.warning:
            warnings.append(item.warning)

    checks = (
        _readme_check(snapshot, path_by_lower, text_files),
        _agent_instructions_check(snapshot, path_by_lower, text_files),
        _environment_check(snapshot, path_by_lower),
        _ci_check(snapshot, paths),
        _templates_check(snapshot, paths),
        _verification_check(snapshot, paths, text_files),
        _risky_action_check(snapshot, text_files),
    )
    next_steps = tuple(_next_step(check.check_id) for check in checks if check.score < check.max_score)
    repository_record: dict[str, Any] = {
        "api_url": snapshot.api_url,
        "archived": snapshot.archived,
        "default_branch": snapshot.default_branch,
        "full_name": snapshot.full_name,
        "requested": snapshot.requested.slug,
        "revision_sha": snapshot.revision_sha,
        "tree_sha": snapshot.tree_sha,
        "web_url": snapshot.web_url,
    }
    if snapshot.archived:
        warnings.append("Repository metadata marks this project as archived.")
    return AuditReport(
        repository=repository_record,
        checks=checks,
        inspected_files=tuple(text_files),
        inspection_warnings=tuple(warnings),
        next_steps=next_steps,
    )


def _content_candidates(paths: tuple[str, ...], path_by_lower: dict[str, str]) -> tuple[str, ...]:
    selected: set[str] = set()
    for name in (*README_NAMES, *AGENT_INSTRUCTION_PATHS, *VERIFY_CONFIG_NAMES):
        path = path_by_lower.get(name)
        if path:
            selected.add(path)
    workflows = sorted(
        (
            path for path in paths
            if path.lower().startswith(".github/workflows/")
            and path.lower().endswith((".yml", ".yaml"))
        ),
        key=str.lower,
    )
    selected.update(workflows[:5])
    for path in paths:
        lower = path.lower()
        if lower in {"contributing.md", ".github/contributing.md"}:
            selected.add(path)
    return tuple(sorted(selected, key=str.lower))


def _readme_check(
    snapshot: RepositorySnapshot,
    path_by_lower: dict[str, str],
    text_files: dict[str, TextFile],
) -> CheckResult:
    path = next((path_by_lower[name] for name in README_NAMES if name in path_by_lower), None)
    if not path:
        return _result("readme_setup", "README and setup guidance", 0, 20, "No root README was evidenced.")
    item = text_files.get(path)
    evidence = [_path_evidence(snapshot, path, "Root README exists.")]
    if not item or item.text is None:
        return _result(
            "readme_setup", "README and setup guidance", 8, 20,
            "A root README exists, but its setup content was not inspectable.", evidence,
        )
    setup_line = _first_line(item.text, SETUP_RE)
    command_line = _first_line(item.text, COMMAND_RE)
    if setup_line:
        evidence.append(_line_evidence(item, setup_line, "README includes setup-oriented guidance."))
    if command_line and command_line != setup_line:
        evidence.append(_line_evidence(item, command_line, "README includes an executable-looking command."))
    score = 8 + (7 if setup_line else 0) + (5 if command_line else 0)
    summary = "Root README and actionable setup evidence were found." if score == 20 else "Root README exists, but setup evidence is incomplete."
    return _result("readme_setup", "README and setup guidance", score, 20, summary, evidence)


def _agent_instructions_check(
    snapshot: RepositorySnapshot,
    path_by_lower: dict[str, str],
    text_files: dict[str, TextFile],
) -> CheckResult:
    paths = [path_by_lower[name] for name in AGENT_INSTRUCTION_PATHS if name in path_by_lower]
    if not paths:
        return _result(
            "agent_instructions", "Coding-agent instructions", 0, 20,
            "No recognized root coding-agent instruction file was evidenced.",
        )
    evidence = [_path_evidence(snapshot, path, "Recognized coding-agent instruction file exists.") for path in paths]
    inspectable = any(text_files.get(path) and text_files[path].text for path in paths)
    score = 20 if inspectable else 12
    summary = "A recognized, inspectable coding-agent instruction file was found." if inspectable else "An instruction file exists, but its content was not inspectable."
    return _result("agent_instructions", "Coding-agent instructions", score, 20, summary, evidence)


def _environment_check(snapshot: RepositorySnapshot, path_by_lower: dict[str, str]) -> CheckResult:
    paths = [path_by_lower[name] for name in ENV_EXAMPLE_NAMES if name in path_by_lower]
    if not paths:
        return _result(
            "environment_example", "Environment example", 0, 10,
            "No recognized root environment example was evidenced.",
        )
    evidence = [_path_evidence(snapshot, path, "Environment example file exists.") for path in paths]
    return _result("environment_example", "Environment example", 10, 10, "A root environment example was found.", evidence)


def _ci_check(snapshot: RepositorySnapshot, paths: tuple[str, ...]) -> CheckResult:
    workflows = sorted(
        (path for path in paths if path.lower().startswith(".github/workflows/") and path.lower().endswith((".yml", ".yaml"))),
        key=str.lower,
    )
    if not workflows:
        return _result("continuous_integration", "Continuous integration", 0, 15, "No GitHub Actions workflow was evidenced.")
    evidence = [_path_evidence(snapshot, path, "GitHub Actions workflow exists.") for path in workflows[:5]]
    return _result("continuous_integration", "Continuous integration", 15, 15, "At least one GitHub Actions workflow was found.", evidence)


def _templates_check(snapshot: RepositorySnapshot, paths: tuple[str, ...]) -> CheckResult:
    issue_paths = sorted(
        (path for path in paths if path.lower().startswith(".github/issue_template/") and not path.endswith("/")),
        key=str.lower,
    )
    pr_paths = sorted(
        (
            path for path in paths
            if path.lower() in {".github/pull_request_template.md", "pull_request_template.md"}
            or path.lower().startswith(".github/pull_request_template/")
        ),
        key=str.lower,
    )
    score = (5 if issue_paths else 0) + (5 if pr_paths else 0)
    evidence = [
        *[_path_evidence(snapshot, path, "Issue template exists.") for path in issue_paths[:2]],
        *[_path_evidence(snapshot, path, "Pull-request template exists.") for path in pr_paths[:2]],
    ]
    if score == 10:
        summary = "Issue and pull-request templates were found."
    elif score:
        summary = "Only one of issue or pull-request templates was found."
    else:
        summary = "No issue or pull-request template was evidenced."
    return _result("contribution_templates", "Issue and pull-request templates", score, 10, summary, evidence)


def _verification_check(
    snapshot: RepositorySnapshot,
    paths: tuple[str, ...],
    text_files: dict[str, TextFile],
) -> CheckResult:
    candidates = sorted(
        {
            path for path in paths
            if path.lower() in VERIFY_CONFIG_NAMES
            or any(fnmatch.fnmatch(path.lower(), pattern) for pattern in VERIFY_PATH_PATTERNS)
        },
        key=str.lower,
    )
    content_evidence: list[Evidence] = []
    for item in text_files.values():
        if item.text is None:
            continue
        line = _first_line(item.text, VERIFY_RE)
        if line:
            content_evidence.append(_line_evidence(item, line, "Verification-oriented guidance or configuration was found."))
    evidence = [
        *[_path_evidence(snapshot, path, "Verification-related file or path exists.") for path in candidates[:5]],
        *content_evidence[:3],
    ]
    if candidates and content_evidence:
        score, summary = 15, "Verification files and written verification evidence were found."
    elif candidates or content_evidence:
        score, summary = 8, "Some verification evidence was found, but it is incomplete."
    else:
        score, summary = 0, "No recognized verification script, configuration, or guidance was evidenced."
    return _result("verification", "Verification commands and automation", score, 15, summary, evidence)


def _risky_action_check(snapshot: RepositorySnapshot, text_files: dict[str, TextFile]) -> CheckResult:
    evidence: list[Evidence] = []
    for path, item in sorted(text_files.items(), key=lambda pair: pair[0].lower()):
        if item.text is None:
            continue
        for number, line in enumerate(item.text.splitlines(), start=1):
            if PROHIBITED_ACTION_RE.search(line) or APPROVAL_ACTION_RE.search(line):
                evidence.append(_line_evidence(item, number, "Explicit risky-action boundary language was found."))
                break
    if evidence:
        return _result(
            "risky_action_boundaries", "Risky-action boundaries", 10, 10,
            "At least one explicit approval or prohibition boundary was evidenced.", evidence[:5],
        )
    return _result(
        "risky_action_boundaries", "Risky-action boundaries", 0, 10,
        "No explicit approval or prohibition boundary for risky actions was evidenced in inspected guidance.",
    )


def _result(
    check_id: str,
    label: str,
    score: int,
    maximum: int,
    summary: str,
    evidence: Iterable[Evidence] = (),
) -> CheckResult:
    return CheckResult(check_id, label, score, maximum, summary, tuple(evidence))


def _path_evidence(snapshot: RepositorySnapshot, path: str, detail: str) -> Evidence:
    entry = snapshot.files[path]
    source_url = f"{snapshot.web_url}/blob/{snapshot.revision_sha}/{quote(path, safe='/')}"
    return Evidence("path", path, source_url, detail, api_url=entry.api_url)


def _line_evidence(item: TextFile, line: int, detail: str) -> Evidence:
    return Evidence("content", item.path, f"{item.source_url}#L{line}", detail, line=line, api_url=item.api_url)


def _first_line(text: str, pattern: re.Pattern[str]) -> int | None:
    for number, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            return number
    return None


def _next_step(check_id: str) -> str:
    return {
        "readme_setup": "Add or strengthen a root README with prerequisites and copy-paste setup commands.",
        "agent_instructions": "Add a root AGENTS.md (or another recognized instruction file) with repository-specific coding-agent guidance.",
        "environment_example": "Add a redacted root .env.example that names required configuration without real secrets.",
        "continuous_integration": "Add a GitHub Actions workflow that runs the repository's documented verification commands.",
        "contribution_templates": "Add both issue and pull-request templates for structured change requests and reviews.",
        "verification": "Document and automate repeatable test, lint, or type-check commands.",
        "risky_action_boundaries": "Document actions that require explicit approval, including destructive, deployment, credential, publishing, or payment operations.",
    }[check_id]
