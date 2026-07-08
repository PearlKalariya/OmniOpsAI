"""NewsAPI connector (headline search)."""

from app.connectors.base import get
from app.core.config import settings

API = "https://newsapi.org/v2/everything"


def is_configured() -> bool:
    return bool(settings.newsapi_key)


def search(query: str, limit: int = 5) -> list[dict]:
    data = get(
        API,
        headers={"X-Api-Key": settings.newsapi_key},
        params={"q": query, "pageSize": limit, "sortBy": "publishedAt", "language": "en"},
    )
    return [
        {
            "title": a["title"],
            "source": a["source"]["name"],
            "published_at": a["publishedAt"],
            "url": a["url"],
        }
        for a in data.get("articles", [])
    ]
