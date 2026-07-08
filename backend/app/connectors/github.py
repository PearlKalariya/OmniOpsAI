"""GitHub connector (repos + issues, read-only)."""

from app.connectors.base import get
from app.core.config import settings

API = "https://api.github.com"


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
