"""Strict parsing for the only accepted repository identifier shapes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from .errors import InputValidationError


OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


@dataclass(frozen=True)
class RepositoryRef:
    owner: str
    repository: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repository}"

    @property
    def web_url(self) -> str:
        return f"https://github.com/{self.slug}"


def parse_repository_ref(value: str) -> RepositoryRef:
    """Accept only ``owner/repo`` or a canonical HTTPS GitHub repository URL."""

    if not isinstance(value, str) or not value:
        raise InputValidationError("Repository input must be a non-empty string.")
    if value != value.strip():
        raise InputValidationError("Repository input must not contain surrounding whitespace.")
    if len(value) > 300:
        raise InputValidationError("Repository input is too long.")

    if "://" in value:
        owner, repository = _parse_url(value)
    else:
        owner, repository = _parse_slug(value)

    if not OWNER_RE.fullmatch(owner) or "--" in owner:
        raise InputValidationError("GitHub owner is not in a supported canonical form.")
    if not REPOSITORY_RE.fullmatch(repository) or repository in {".", ".."}:
        raise InputValidationError("GitHub repository name is not in a supported canonical form.")

    return RepositoryRef(owner=owner, repository=repository)


def _parse_url(value: str) -> tuple[str, str]:
    parsed = urlsplit(value)
    if parsed.scheme != "https":
        raise InputValidationError("Only HTTPS GitHub repository URLs are accepted.")
    if parsed.username or parsed.password or parsed.port is not None:
        raise InputValidationError("GitHub repository URLs must not contain credentials or ports.")
    if (parsed.hostname or "").lower() != "github.com":
        raise InputValidationError("Only github.com repository URLs are accepted.")
    if parsed.query or parsed.fragment:
        raise InputValidationError("GitHub repository URLs must not contain query strings or fragments.")
    if "%" in parsed.path:
        raise InputValidationError("Percent-encoded repository paths are not accepted.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise InputValidationError("GitHub URL must point directly to one owner/repository pair.")
    owner, repository = parts
    return owner, _strip_git_suffix(repository)


def _parse_slug(value: str) -> tuple[str, str]:
    if any(character.isspace() for character in value):
        raise InputValidationError("Repository slug must not contain whitespace.")
    parts = value.split("/")
    if len(parts) != 2 or not all(parts):
        raise InputValidationError("Repository slug must use the exact owner/repository form.")
    owner, repository = parts
    return owner, _strip_git_suffix(repository)


def _strip_git_suffix(repository: str) -> str:
    if repository.lower().endswith(".git"):
        repository = repository[:-4]
    if not repository:
        raise InputValidationError("Repository name must not be empty.")
    return repository
