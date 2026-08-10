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

Environment variables:
  DISPATCHARR_URL       - base URL, e.g. http://dispatcharr.example.com
  DISPATCHARR_API_KEY   - static API key (generate in Dispatcharr UI → Users)
  DISPATCHARR_USERNAME  - username  (JWT mode only)
  DISPATCHARR_PASSWORD  - password  (JWT mode only)
"""

import os
from typing import Any

import httpx

_TIMEOUT = 30.0


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
            r.raise_for_status()
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
        if not self._api_key and not self._access_token:
            await self._login()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        await self._ensure_token()
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.request(method, self._url(path), headers=self._auth_headers(), **kwargs)
            if r.status_code == 401 and not self._api_key:
                # Access tokens are short-lived; prefer refresh over re-login
                # to avoid sending the password over the wire unnecessarily.
                if not await self._refresh():
                    await self._login()
                r = await c.request(method, self._url(path), headers=self._auth_headers(), **kwargs)
            r.raise_for_status()
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
