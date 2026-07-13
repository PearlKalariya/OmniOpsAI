"""GitHub connector (repos + issues, read-only)."""

import re

from app.connectors.base import ConnectorError, get
from app.core.config import settings

API = "https://api.github.com"

# GitHub owner/repo charset. owner/repo are interpolated into the URL path,
# so anything outside this set (/, ?, #, ..) could traverse to other API
# endpoints using our token — reject before building the URL.
_SEGMENT = re.compile(r"^[A-Za-z0-9._-]+$")


def _safe_segment(value: str, name: str) -> str:
    if not _SEGMENT.match(value or ""):
        raise ConnectorError(f"invalid {name}: must match [A-Za-z0-9._-]")
    return value


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def is_configured() -> bool:
    return bool(settings.github_token)


def list_repos(limit: int = 10) -> list[dict]:
    data = get(f"{API}/user/repos", headers=_headers(), params={"per_page": limit, "sort": "updated"})
    return [
        {
            "full_name": r["full_name"],
            "private": r["private"],
            "description": r.get("description"),
            "updated_at": r["updated_at"],
            "open_issues": r["open_issues_count"],
        }
        for r in data
    ]


def list_issues(owner: str, repo: str, limit: int = 10) -> list[dict]:
    owner = _safe_segment(owner, "owner")
    repo = _safe_segment(repo, "repo")
    data = get(
        f"{API}/repos/{owner}/{repo}/issues",
        headers=_headers(),
        params={"per_page": limit, "state": "open"},
    )
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "state": i["state"],
            "is_pull_request": "pull_request" in i,
            "created_at": i["created_at"],
        }
        for i in data
    ]
