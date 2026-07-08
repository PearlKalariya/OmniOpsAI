"""Shared bits for enterprise connectors.

Connectors are thin, synchronous httpx clients around third-party APIs.
Tokens come from settings (server-side only — never echoed to clients).
Every call uses a hard timeout so a slow provider can't hang a request.
"""

import httpx

TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class ConnectorError(Exception):
    """Provider returned an error; message is safe to show the client."""


def get(url: str, *, headers: dict | None = None, params: dict | None = None) -> dict | list:
    return _request("GET", url, headers=headers, params=params)


def post(url: str, *, headers: dict | None = None, json: dict | None = None) -> dict | list:
    return _request("POST", url, headers=headers, json=json)


def _request(method: str, url: str, **kwargs) -> dict | list:
    try:
        response = httpx.request(method, url, timeout=TIMEOUT, **kwargs)
    except httpx.HTTPError as exc:
        raise ConnectorError(f"provider unreachable: {type(exc).__name__}") from exc
    if response.status_code >= 400:
        raise ConnectorError(f"provider returned HTTP {response.status_code}")
    return response.json()
