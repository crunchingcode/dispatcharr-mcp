"""Async HTTP client for the Dispatcharr REST API.

Authentication — two modes, checked in order:

  1. API Key (preferred, stateless):
       Set DISPATCHARR_API_KEY.
       Sends `Authorization: ApiKey <key>` on every request.
       No token lifecycle to manage. DISPATCHARR_USERNAME / PASSWORD not needed.

  2. JWT (fallback):
       Set DISPATCHARR_USERNAME and DISPATCHARR_PASSWORD.
       Tokens are fetched lazily on the first request. A 401 response tries the
       refresh token before falling back to a full password login.
       Dispatcharr throttles logins to 3/minute per IP, so one client must be
       shared for the life of the process; a client per call logs in per call.

  If DISPATCHARR_API_KEY is set, the username/password are never used — a
  rejected key surfaces as an error rather than silently falling back.

Errors:
  Non-2xx responses raise httpx.HTTPStatusError whose message carries the
  method, path, and Dispatcharr's response body (e.g. "Invalid API key" or a
  field-level validation error), so callers can see *why* a request failed.

Environment variables:
  DISPATCHARR_URL       - base URL, e.g. http://dispatcharr.example.com
  DISPATCHARR_API_KEY   - static API key (generate in Dispatcharr UI → Users)
  DISPATCHARR_USERNAME  - username  (JWT mode only)
  DISPATCHARR_PASSWORD  - password  (JWT mode only)
"""

import asyncio
import os
from typing import Any

import httpx

_TIMEOUT = 30.0
# Enough for DRF validation errors; stops an HTML error page flooding the output.
_MAX_ERROR_BODY = 500


def _raise_for_status(r: httpx.Response) -> None:
    """Like ``r.raise_for_status()``, but include the response body.

    httpx's own message is only the status line, which hides Dispatcharr's
    explanation — a bad API key and a missing permission both read as a bare
    401/403 without it.
    """
    if r.is_success:
        return
    body = r.text.strip()
    if len(body) > _MAX_ERROR_BODY:
        body = body[:_MAX_ERROR_BODY] + "…"
    message = f"{r.status_code} {r.reason_phrase} for {r.request.method} {r.request.url.path}"
    if body:
        message += f": {body}"
    raise httpx.HTTPStatusError(message, request=r.request, response=r)


class DispatcharrClient:
    def __init__(self) -> None:
        base_url = os.environ.get("DISPATCHARR_URL", "").rstrip("/")
        if not base_url:
            raise ValueError("DISPATCHARR_URL environment variable is required")

        self._base = base_url
        self._api_key: str | None = os.environ.get("DISPATCHARR_API_KEY") or None

        if not self._api_key:
            username = os.environ.get("DISPATCHARR_USERNAME", "")
            password = os.environ.get("DISPATCHARR_PASSWORD", "")
            if not username or not password:
                raise ValueError(
                    "Either DISPATCHARR_API_KEY or both DISPATCHARR_USERNAME and "
                    "DISPATCHARR_PASSWORD environment variables are required"
                )
            self._username = username
            self._password = password
        else:
            self._username = ""
            self._password = ""

        self._access_token: str | None = None
        self._refresh_token: str | None = None
        # Serialises re-authentication so concurrent tool calls share one login.
        self._auth_lock = asyncio.Lock()

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    def _auth_headers(self) -> dict:
        if self._api_key:
            return {
                "Authorization": f"ApiKey {self._api_key}",
                "Accept": "application/json",
            }
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    async def _login(self) -> None:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.post(
                self._url("/api/accounts/token/"),
                json={"username": self._username, "password": self._password},
            )
            _raise_for_status(r)
            data = r.json()
            self._access_token = data["access"]
            self._refresh_token = data.get("refresh")

    async def _refresh(self) -> bool:
        if not self._refresh_token:
            return False
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.post(
                self._url("/api/accounts/token/refresh/"),
                json={"refresh": self._refresh_token},
            )
            if r.status_code == 200:
                self._access_token = r.json()["access"]
                return True
        return False

    async def _ensure_token(self) -> None:
        if self._api_key or self._access_token:
            return
        async with self._auth_lock:
            if not self._access_token:
                await self._login()

    async def _reauthenticate(self, stale_token: str | None) -> None:
        async with self._auth_lock:
            # Another call already replaced the token while this one waited.
            if self._access_token != stale_token:
                return
            # Access tokens are short-lived; prefer refresh over re-login
            # to avoid sending the password over the wire unnecessarily.
            if not await self._refresh():
                await self._login()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        await self._ensure_token()
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            sent_token = self._access_token
            r = await c.request(method, self._url(path), headers=self._auth_headers(), **kwargs)
            if r.status_code == 401 and not self._api_key:
                await self._reauthenticate(sent_token)
                r = await c.request(method, self._url(path), headers=self._auth_headers(), **kwargs)
            _raise_for_status(r)
            return r.json() if r.content else {}

    async def get(self, path: str, params: dict | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: dict | None = None) -> Any:
        return await self._request("POST", path, json=data or {})

    async def patch(self, path: str, data: dict) -> Any:
        return await self._request("PATCH", path, json=data)

    async def put(self, path: str, data: dict | None = None) -> Any:
        return await self._request("PUT", path, json=data or {})

    async def delete(self, path: str, params: dict | None = None) -> dict:
        return await self._request("DELETE", path, params=params)

    async def delete_with_body(self, path: str, data: dict) -> dict:
        return await self._request("DELETE", path, json=data)
