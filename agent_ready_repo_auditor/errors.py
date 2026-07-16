"""Typed failures for the public GitHub repository auditor."""

from __future__ import annotations

from typing import Any, Mapping


class AuditorError(Exception):
    """Base error with a stable machine-readable representation."""

    code = "auditor_error"
    retryable = False

    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            payload["details"] = dict(sorted(self.details.items()))
        return payload


class InputValidationError(AuditorError):
    code = "invalid_repository_input"


class RepositoryInaccessibleError(AuditorError):
    code = "repository_inaccessible"


class PrivateRepositoryError(AuditorError):
    code = "private_repository_not_supported"


class RepositoryTreeTruncatedError(AuditorError):
    code = "repository_tree_truncated"


class GitHubRateLimitError(AuditorError):
    code = "github_rate_limited"
    retryable = True


class GitHubAPIError(AuditorError):
    code = "github_api_error"
    retryable = True


class GitHubResponseError(AuditorError):
    code = "invalid_github_response"


class FixPlanValidationError(AuditorError):
    code = "invalid_fix_plan_request"


class FixPlanVerificationError(AuditorError):
    code = "fix_plan_verification_failed"
    retryable = True
