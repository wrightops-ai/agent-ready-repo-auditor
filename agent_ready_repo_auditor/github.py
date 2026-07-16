"""A narrow unauthenticated GitHub API client with fail-closed boundaries."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from email.message import Message
from typing import Any, Callable, Mapping, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from .errors import (
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubResponseError,
    PrivateRepositoryError,
    RepositoryInaccessibleError,
    RepositoryTreeTruncatedError,
)
from .inputs import RepositoryRef


API_BASE = "https://api.github.com"
USER_AGENT = "agent-ready-repo-auditor/0.1"


@dataclass(frozen=True)
class TreeEntry:
    path: str
    sha: str
    api_url: str


@dataclass(frozen=True)
class RepositorySnapshot:
    requested: RepositoryRef
    full_name: str
    web_url: str
    api_url: str
    default_branch: str
    revision_sha: str
    tree_sha: str
    archived: bool
    files: Mapping[str, TreeEntry]


@dataclass(frozen=True)
class TextFile:
    path: str
    text: str | None
    source_url: str
    api_url: str
    warning: str | None = None


Transport = Callable[..., Any]


class GitHubClient:
    """Read public repository metadata and immutable blobs from api.github.com only."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        max_response_bytes: int = 8_000_000,
        max_file_bytes: int = 256_000,
        token: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        if token and any(character in token for character in "\r\n"):
            raise ValueError("GitHub token must not contain line breaks.")
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.max_file_bytes = max_file_bytes
        self.token = token or None
        self._transport = transport or urlopen

    def snapshot(self, ref: RepositoryRef) -> RepositorySnapshot:
        owner = quote(ref.owner, safe="")
        repository = quote(ref.repository, safe="")
        api_url = f"{API_BASE}/repos/{owner}/{repository}"

        try:
            metadata = self._get_json(f"/repos/{owner}/{repository}")
        except _GitHubNotFound as error:
            raise RepositoryInaccessibleError(
                "Repository is private, missing, or otherwise inaccessible through the public GitHub API.",
                details={"repository": ref.slug},
            ) from error

        if metadata.get("private") is True:
            raise PrivateRepositoryError(
                "Private repositories are not supported; this auditor uses public GitHub data only.",
                details={"repository": ref.slug},
            )
        if metadata.get("private") is not False:
            raise GitHubResponseError("GitHub repository metadata did not include a valid public/private state.")

        full_name = _required_string(metadata, "full_name")
        web_url = _required_github_url(metadata, "html_url", host="github.com")
        default_branch = _required_string(metadata, "default_branch")

        branch_path = quote(default_branch, safe="")
        try:
            commit = self._get_json(f"/repos/{owner}/{repository}/commits/{branch_path}")
        except _GitHubNotFound as error:
            raise RepositoryInaccessibleError(
                "The repository default branch could not be resolved through the public GitHub API.",
                details={"repository": full_name},
            ) from error

        revision_sha = _required_sha(commit, "sha")
        commit_record = commit.get("commit")
        if not isinstance(commit_record, dict) or not isinstance(commit_record.get("tree"), dict):
            raise GitHubResponseError("GitHub commit metadata did not include a tree reference.")
        tree_sha = _required_sha(commit_record["tree"], "sha")

        tree = self._get_json(
            f"/repos/{owner}/{repository}/git/trees/{quote(tree_sha, safe='')}?recursive=1"
        )
        if tree.get("truncated") is True:
            raise RepositoryTreeTruncatedError(
                "GitHub truncated the recursive repository tree; absence checks would be unreliable.",
                details={"repository": full_name, "tree_sha": tree_sha},
            )
        raw_entries = tree.get("tree")
        if not isinstance(raw_entries, list):
            raise GitHubResponseError("GitHub tree response did not include a file list.")

        files: dict[str, TreeEntry] = {}
        for item in raw_entries:
            if not isinstance(item, dict) or item.get("type") != "blob":
                continue
            path = item.get("path")
            sha = item.get("sha")
            item_url = item.get("url")
            if not isinstance(path, str) or not path or not isinstance(item_url, str):
                continue
            if not _is_sha(sha):
                continue
            if urlsplit(item_url).hostname != "api.github.com":
                continue
            files[path] = TreeEntry(path=path, sha=cast(str, sha), api_url=item_url)

        return RepositorySnapshot(
            requested=ref,
            full_name=full_name,
            web_url=web_url,
            api_url=api_url,
            default_branch=default_branch,
            revision_sha=revision_sha,
            tree_sha=tree_sha,
            archived=bool(metadata.get("archived", False)),
            files=dict(sorted(files.items(), key=lambda item: item[0].lower())),
        )

    def read_text(self, snapshot: RepositorySnapshot, path: str) -> TextFile:
        entry = snapshot.files.get(path)
        if entry is None:
            raise GitHubResponseError("Requested file was not present in the immutable repository tree.")

        owner, repository = snapshot.full_name.split("/", 1)
        web_path = quote(path, safe="/")
        source_url = (
            f"https://github.com/{quote(owner, safe='')}/{quote(repository, safe='')}"
            f"/blob/{snapshot.revision_sha}/{web_path}"
        )
        try:
            blob = self._get_json(
                f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}"
                f"/git/blobs/{quote(entry.sha, safe='')}"
            )
        except _GitHubNotFound as error:
            raise RepositoryInaccessibleError(
                "A repository file disappeared while reading its immutable public snapshot.",
                details={"path": path, "repository": snapshot.full_name},
            ) from error

        size = blob.get("size")
        if not isinstance(size, int) or size < 0:
            return TextFile(
                path=path,
                text=None,
                source_url=source_url,
                api_url=entry.api_url,
                warning=f"{path}: GitHub did not provide a valid file size; content was not inspected.",
            )
        if size > self.max_file_bytes:
            return TextFile(
                path=path,
                text=None,
                source_url=source_url,
                api_url=entry.api_url,
                warning=f"{path}: file exceeds the {self.max_file_bytes}-byte inspection limit.",
            )
        if blob.get("encoding") != "base64" or not isinstance(blob.get("content"), str):
            return TextFile(
                path=path,
                text=None,
                source_url=source_url,
                api_url=entry.api_url,
                warning=f"{path}: file was not returned as base64 text and was not inspected.",
            )

        try:
            encoded = "".join(blob["content"].split())
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as error:
            raise GitHubResponseError("GitHub returned invalid base64 file content.") from error
        if len(raw) > self.max_file_bytes:
            return TextFile(
                path=path,
                text=None,
                source_url=source_url,
                api_url=entry.api_url,
                warning=f"{path}: decoded file exceeds the inspection limit.",
            )
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return TextFile(
                path=path,
                text=None,
                source_url=source_url,
                api_url=entry.api_url,
                warning=f"{path}: file is not UTF-8 text and was not inspected.",
            )
        return TextFile(path=path, text=text, source_url=source_url, api_url=entry.api_url)

    def _get_json(self, path: str) -> dict[str, Any]:
        if not path.startswith("/"):
            raise ValueError("GitHub API path must be absolute.")
        url = f"{API_BASE}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers, method="GET")
        try:
            with self._transport(request, timeout=self.timeout_seconds) as response:
                final_url = response.geturl()
                if urlsplit(final_url).scheme != "https" or urlsplit(final_url).hostname != "api.github.com":
                    raise GitHubResponseError("GitHub API request redirected outside api.github.com.")
                content_length = _header_int(response.headers, "Content-Length")
                if content_length is not None and content_length > self.max_response_bytes:
                    raise GitHubResponseError("GitHub API response exceeded the configured size limit.")
                raw = response.read(self.max_response_bytes + 1)
                if len(raw) > self.max_response_bytes:
                    raise GitHubResponseError("GitHub API response exceeded the configured size limit.")
        except HTTPError as error:
            self._raise_http_error(error)
        except (TimeoutError, URLError) as error:
            raise GitHubAPIError(
                "GitHub API request failed before a complete public response was received.",
                details={"reason": _safe_reason(error)},
            ) from error

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GitHubResponseError("GitHub API returned invalid JSON.") from error
        if not isinstance(payload, dict):
            raise GitHubResponseError("GitHub API returned an unexpected JSON shape.")
        return payload

    def _raise_http_error(self, error: HTTPError) -> None:
        headers = error.headers or Message()
        remaining = _header_int(headers, "X-RateLimit-Remaining")
        reset = _header_int(headers, "X-RateLimit-Reset")
        retry_after = _header_int(headers, "Retry-After")
        if error.code == 429 or (error.code == 403 and remaining == 0):
            details: dict[str, Any] = {}
            if reset is not None:
                details["reset_epoch"] = reset
            if retry_after is not None:
                details["retry_after_seconds"] = retry_after
            raise GitHubRateLimitError(
                "GitHub public API rate limit was reached; no partial audit was emitted.",
                details=details,
            ) from error
        if error.code == 404:
            raise _GitHubNotFound() from error

        message = _read_http_error_message(error, self.max_response_bytes)
        raise GitHubAPIError(
            "GitHub API returned an error; no partial audit was emitted.",
            details={"http_status": error.code, "github_message": message},
        ) from error


class _GitHubNotFound(Exception):
    pass


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise GitHubResponseError(f"GitHub response did not include a valid {key} value.")
    return value


def _required_sha(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not _is_sha(value):
        raise GitHubResponseError(f"GitHub response did not include a valid {key} SHA.")
    return cast(str, value)


def _is_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value)


def _required_github_url(payload: Mapping[str, Any], key: str, *, host: str) -> str:
    value = _required_string(payload, key)
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname != host:
        raise GitHubResponseError(f"GitHub response included an invalid {key} URL.")
    return value


def _header_int(headers: Any, key: str) -> int | None:
    value = headers.get(key)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_reason(error: Exception) -> str:
    reason = getattr(error, "reason", error.__class__.__name__)
    return str(reason)[:160]


def _read_http_error_message(error: HTTPError, maximum: int) -> str:
    try:
        raw = error.read(min(maximum, 16_000))
        payload = json.loads(raw.decode("utf-8"))
        message = payload.get("message") if isinstance(payload, dict) else None
        if isinstance(message, str) and message:
            return message[:200]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    return "Unspecified GitHub API error"
