"""Small immutable data contracts used by the auditor and future wrappers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    kind: str
    path: str
    source_url: str
    detail: str
    line: int | None = None
    api_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "detail": self.detail,
            "kind": self.kind,
            "path": self.path,
            "source_url": self.source_url,
        }
        if self.line is not None:
            payload["line"] = self.line
        if self.api_url is not None:
            payload["api_url"] = self.api_url
        return payload


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    label: str
    score: int
    max_score: int
    summary: str
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    @property
    def status(self) -> str:
        if self.score == self.max_score:
            return "met"
        if self.score > 0:
            return "partial"
        return "not_evidenced"

    def to_dict(self) -> dict[str, Any]:
        evidence = sorted(
            self.evidence,
            key=lambda item: (item.path.lower(), item.line or 0, item.kind, item.detail),
        )
        return {
            "evidence": [item.to_dict() for item in evidence],
            "id": self.check_id,
            "label": self.label,
            "max_score": self.max_score,
            "score": self.score,
            "status": self.status,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class AuditReport:
    repository: dict[str, Any]
    checks: tuple[CheckResult, ...]
    inspected_files: tuple[str, ...]
    inspection_warnings: tuple[str, ...]
    next_steps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        earned = sum(check.score for check in self.checks)
        maximum = sum(check.max_score for check in self.checks)
        percentage = round(earned / maximum * 100) if maximum else 0
        return {
            "checks": [check.to_dict() for check in self.checks],
            "inspection": {
                "files": sorted(set(self.inspected_files), key=str.lower),
                "warnings": sorted(set(self.inspection_warnings)),
            },
            "limitations": [
                "This is an operational coding-agent readiness evidence review, not a vulnerability or security assessment.",
                "A missing public artifact means only that the auditor did not evidence it in the scanned default-branch snapshot.",
                "The auditor does not execute repository code, verify documentation accuracy, inspect private settings, or prove production safety.",
            ],
            "next_steps": list(self.next_steps),
            "ok": True,
            "repository": self.repository,
            "schema_version": "agent-ready-repo-audit.v1",
            "score": {
                "band": _score_band(percentage),
                "earned": earned,
                "maximum": maximum,
                "percentage": percentage,
            },
        }


def _score_band(score: int) -> str:
    if score >= 85:
        return "well_evidenced"
    if score >= 65:
        return "partially_evidenced"
    return "limited_public_evidence"
