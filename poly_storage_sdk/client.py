from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from .errors import PolyStorageAPIError, PolyStorageAuthError


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/api/v1"):
        return normalized
    return f"{normalized}/api/v1"


class _BaseService:
    def __init__(self, client: "PolyStorageClient") -> None:
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        requires_auth: bool = False,
    ) -> Dict[str, Any]:
        if requires_auth and not self._client.api_key:
            raise PolyStorageAuthError(
                "API key is required for this endpoint. Set api_key or ENTITY_API_KEY.",
                status_code=401,
                detail="API key required",
            )

        url = f"{self._client.base_url}{path}"
        try:
            response = self._client.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self._client.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise PolyStorageAPIError(
                f"Network error while calling {url}: {exc}",
                status_code=None,
                detail=str(exc),
            ) from exc

        response_data: Any
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}

        if response.status_code >= 400:
            detail = (
                response_data.get("detail")
                or response_data.get("message")
                or response.text
                or "Request failed"
            )
            if response.status_code in (401, 403):
                raise PolyStorageAuthError(
                    f"Authentication failed ({response.status_code})",
                    status_code=response.status_code,
                    detail=str(detail),
                    response_body=response_data,
                )
            raise PolyStorageAPIError(
                f"Request failed ({response.status_code})",
                status_code=response.status_code,
                detail=str(detail),
                response_body=response_data,
            )

        if isinstance(response_data, dict):
            return response_data
        return {"data": response_data}


class SystemService(_BaseService):
    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")


class APIKeysService(_BaseService):
    def create(self, *, name: str, user_id: str) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/keys",
            params={"name": name, "user_id": user_id},
        )

    def list(self, *, user_id: str) -> Dict[str, Any]:
        return self._request("GET", "/keys", params={"user_id": user_id})

    def delete(self, *, key_id: str, user_id: str) -> Dict[str, Any]:
        return self._request(
            "DELETE",
            f"/keys/{key_id}",
            params={"user_id": user_id},
        )

    def get_last_used(self, *, key_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/keys/{key_id}/last-used")

    def get_name(self, *, key_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/keys/{key_id}/name")


class PolymarketService(_BaseService):
    def get_market_data(
        self,
        *,
        condition_id: str,
        date: str,
        offset: int = 0,
        limit: int = 10000,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/market/data",
            params={
                "condition_id": condition_id,
                "date": date,
                "offset": offset,
                "limit": limit,
            },
            requires_auth=True,
        )

    def get_orderbook_summary(
        self,
        *,
        condition_id: str,
        date: str,
        resolution: int = 60,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/market/orderbook-summary",
            params={
                "condition_id": condition_id,
                "date": date,
                "resolution": resolution,
            },
            requires_auth=True,
        )


class KalshiService(_BaseService):
    def get_market_data(
        self,
        *,
        ticker: str,
        date: str,
        offset: int = 0,
        limit: int = 10000,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/kalshi/market/data",
            params={
                "ticker": ticker,
                "date": date,
                "offset": offset,
                "limit": limit,
            },
            requires_auth=True,
        )

    def get_orderbook_summary(
        self,
        *,
        ticker: str,
        date: str,
        resolution: int = 60,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/kalshi/market/orderbook-summary",
            params={
                "ticker": ticker,
                "date": date,
                "resolution": resolution,
            },
            requires_auth=True,
        )


class PolyStorageClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://api.entityml.com",
        timeout_seconds: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("ENTITY_API_KEY")
        self.base_url = _normalize_base_url(base_url)
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "poly-storage-sdk/0.1.0",
            }
        )
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

        self.system = SystemService(self)
        self.api_keys = APIKeysService(self)
        self.polymarket = PolymarketService(self)
        self.kalshi = KalshiService(self)
