"""Slack connector (list channels, post messages)."""

from app.connectors.base import ConnectorError, get, post
from app.core.config import settings

API = "https://slack.com/api"


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.slack_bot_token}"}


def is_configured() -> bool:
    return bool(settings.slack_bot_token)


def _check(data: dict) -> dict:
    # Slack returns HTTP 200 with ok=false on errors.
    if not data.get("ok"):
        raise ConnectorError(f"slack error: {data.get('error', 'unknown')}")
    return data


def list_channels(limit: int = 20) -> list[dict]:
    data = _check(
        get(f"{API}/conversations.list", headers=_headers(), params={"limit": limit, "types": "public_channel"})
    )
    return [
        {"id": c["id"], "name": c["name"], "is_member": c["is_member"]}
        for c in data.get("channels", [])
    ]


def _channel_id(name_or_id: str) -> str:
    """Resolve a channel name to its ID (join API needs IDs, not names)."""
    if name_or_id.startswith("C"):
        return name_or_id
    for c in list_channels(limit=200):
        if c["name"] == name_or_id.lstrip("#"):
            return c["id"]
    raise ConnectorError(f"slack error: channel {name_or_id!r} not found")


def send_message(channel: str, text: str) -> dict:
    payload = {"channel": channel, "text": text}
    try:
        data = _check(post(f"{API}/chat.postMessage", headers=_headers(), json=payload))
    except ConnectorError as exc:
        if "not_in_channel" not in str(exc):
            raise
        # Self-join (needs channels:join scope), then retry once.
        _check(post(f"{API}/conversations.join", headers=_headers(), json={"channel": _channel_id(channel)}))
        data = _check(post(f"{API}/chat.postMessage", headers=_headers(), json=payload))
    return {"channel": data["channel"], "ts": data["ts"]}
