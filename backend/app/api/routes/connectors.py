"""Enterprise connector endpoints.

All routes: authenticated, rate-limited, 503 when the connector's token
is missing, 502 with a safe message when the provider errors.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.connectors import github, news, slack, weather
from app.connectors.base import ConnectorError
from app.core.ratelimit import limiter
from app.models.user import User

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


def _guard(configured: bool, name: str) -> None:
    if not configured:
        raise HTTPException(status_code=503, detail=f"{name} connector not configured: set token in backend/.env")


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ConnectorError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/github/repos")
@limiter.limit("30/minute")
def github_repos(request: Request, limit: int = 10, current_user: User = Depends(get_current_user)):
    _guard(github.is_configured(), "GitHub")
    return _call(github.list_repos, limit=max(1, min(limit, 30)))


@router.get("/github/issues")
@limiter.limit("30/minute")
def github_issues(
    request: Request,
    owner: str = Query(pattern=r"^[A-Za-z0-9._-]+$"),
    repo: str = Query(pattern=r"^[A-Za-z0-9._-]+$"),
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    _guard(github.is_configured(), "GitHub")
    return _call(github.list_issues, owner=owner, repo=repo, limit=max(1, min(limit, 30)))


@router.get("/weather")
@limiter.limit("30/minute")
def weather_current(request: Request, city: str, current_user: User = Depends(get_current_user)):
    _guard(weather.is_configured(), "Weather")
    return _call(weather.current, city=city)


@router.get("/news")
@limiter.limit("30/minute")
def news_search(request: Request, q: str, limit: int = 5, current_user: User = Depends(get_current_user)):
    _guard(news.is_configured(), "News")
    return _call(news.search, query=q, limit=max(1, min(limit, 20)))


@router.get("/slack/channels")
@limiter.limit("30/minute")
def slack_channels(request: Request, current_user: User = Depends(get_current_user)):
    _guard(slack.is_configured(), "Slack")
    return _call(slack.list_channels)


class SlackSendRequest(BaseModel):
    channel: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=4000)


@router.post("/slack/send")
@limiter.limit("10/minute")
def slack_send(request: Request, payload: SlackSendRequest, current_user: User = Depends(get_current_user)):
    _guard(slack.is_configured(), "Slack")
    return _call(slack.send_message, channel=payload.channel, text=payload.text)
